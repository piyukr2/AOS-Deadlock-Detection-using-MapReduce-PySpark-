import sys
import time
from datetime import datetime
from typing import List, Tuple, Dict, Set

from pyspark import SparkContext, SparkConf

def parse_log_line(line: str):
    """
    Parse a log line; expected format (5+ tokens):
      YYYY-MM-DD HH:MM:SS LEVEL PROCESS_ID RESOURCE_ID
    Returns (timestamp_str, LEVEL, PROCESS_ID, RESOURCE_ID) or None if invalid.
    """
    try:
        parts = line.strip().split()
        if len(parts) >= 5:
            timestamp = parts[0] + ' ' + parts[1]
            level = parts[2]
            process_id = parts[3]
            resource_id = parts[4]
            return (timestamp, level, process_id, resource_id)
    except Exception:
        pass
    return None


def create_edge_with_ts(record):
    """
    Maps parsed record to directed edge with timestamp:
      WAIT: Process -> Resource
      HOLD: Resource -> Process
    Returns (src, dst, timestamp) or None.
    """
    timestamp, level, process_id, resource_id = record
    lvl = level.upper()
    if lvl == 'WAIT':
        return (process_id, resource_id, timestamp)
    elif lvl == 'HOLD':
        return (resource_id, process_id, timestamp)
    return None


def normalize_cycle(path: List[str]) -> Tuple[str, ...]:
    """
    Normalizes a cycle so it starts from the lexicographically smallest node,
    preserving direction, for deterministic dedup/sort.
    """
    n = len(path)
    if n == 0:
        return tuple()
    min_node = min(path)
    candidates = [i for i, v in enumerate(path) if v == min_node]
    best = None
    for idx in candidates:
        rotated = tuple(path[idx:] + path[:idx])
        if best is None or rotated < best:
            best = rotated
    return best


def rdd_cycle_detection_optimized(sc: SparkContext,
                                   edges_rdd,
                                   max_cycle_length: int = 25):
    """
    Optimized cycle detection with:
    1. Early termination when no progress
    2. Proper unpersist of old RDDs
    3. Reduced intermediate collections
    4. Path count tracking
    """
    # Persist edges once
    edges_rdd = edges_rdd.distinct().persist()
    
    # Build adjacency list for efficiency
    adj_list = edges_rdd.groupByKey().mapValues(list).persist()
    
    # Initialize paths: ((start, current), [path_list])
    paths = edges_rdd.map(lambda sd: ((sd[0], sd[1]), [sd[0], sd[1]])).persist()
    
    detected_cycles = set()
    no_progress_count = 0
    previous_path_count = paths.count()
    
    start_t = time.time()
    
    for iteration in range(max_cycle_length - 1):
        # Prepare for join: (current_node, (start_node, path))
        paths_by_current = paths.map(lambda kv: (kv[0][1], (kv[0][0], kv[1])))
        
        # Join with adjacency list
        joined = paths_by_current.join(adj_list)
        
        # Extend paths or detect cycles
        def extend_or_cycle(rec):
            current, ((start_node, path), neighbors) = rec
            results = []
            
            for next_node in neighbors:
                # Cycle detected
                if next_node == start_node and len(path) >= 2:
                    norm = normalize_cycle(path[:])
                    if norm and len(norm) >= 2:
                        results.append(('cycle', norm))
                # Extend path (no revisits, length limit)
                elif next_node not in path and len(path) < max_cycle_length:
                    new_path = path + [next_node]
                    results.append(('path', ((start_node, next_node), new_path)))
            
            return results
        
        extended = joined.flatMap(extend_or_cycle).persist()
        
        # Separate paths and cycles
        new_paths = extended.filter(lambda x: x[0] == 'path').map(lambda x: x[1])
        found_cycles = extended.filter(lambda x: x[0] == 'cycle').map(lambda x: x[1]).distinct().collect()
        
        # Add new cycles
        cycles_added = 0
        for cyc in found_cycles:
            if cyc not in detected_cycles:
                detected_cycles.add(cyc)
                cycles_added += 1
        
        # Check for progress
        if new_paths.isEmpty():
            extended.unpersist()
            break
        
        # Keep shortest path for each (start, current)
        new_paths_reduced = new_paths.reduceByKey(lambda a, b: a if len(a) <= len(b) else b).persist()
        
        current_path_count = new_paths_reduced.count()
        
        # Early termination: if no new cycles and path count stopped growing
        if cycles_added == 0 and current_path_count >= previous_path_count:
            no_progress_count += 1
            if no_progress_count >= 3:  # No progress for 3 iterations
                new_paths_reduced.unpersist()
                extended.unpersist()
                break
        else:
            no_progress_count = 0
        
        previous_path_count = current_path_count
        
        # Unpersist old RDDs to free memory
        paths.unpersist()
        extended.unpersist()
        
        # Update paths for next iteration
        paths = new_paths_reduced
    
    end_t = time.time()
    exec_time = end_t - start_t
    
    # Cleanup
    paths.unpersist()
    edges_rdd.unpersist()
    adj_list.unpersist()
    
    # Sort cycles
    cycles = [list(c) for c in detected_cycles]
    cycles.sort(key=lambda c: (len(c), c))
    
    return cycles, exec_time


def get_cycle_formation_date(cycle: List[str],
                             edge_ts: Dict[Tuple[str, str], str]) -> str:
    """
    Finds the date when cycle was fully formed (latest edge timestamp).
    """
    latest_ts = None
    n = len(cycle)
    for i in range(n):
        src = cycle[i]
        dst = cycle[(i + 1) % n]
        ts = edge_ts.get((src, dst))
        if ts is not None:
            if (latest_ts is None) or (ts > latest_ts):
                latest_ts = ts
    if latest_ts:
        return latest_ts.split()[0]
    return None


def main():
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: spark-submit Deadlock.py <log_file_path> <num_cores>\n")
        sys.exit(1)

    log_file_path = sys.argv[1]
    num_cores = sys.argv[2]

    # Configure Spark
    conf = SparkConf().setAppName("DeadlockDetection")
    conf = conf.setMaster(f"local[{num_cores}]")
    
    # Optimize Spark settings
    conf.set("spark.driver.memory", "4g")
    conf.set("spark.executor.memory", "4g")
    conf.set("spark.default.parallelism", num_cores)
    conf.set("spark.sql.shuffle.partitions", num_cores)
    
    sc = SparkContext(conf=conf)
    sc.setLogLevel("ERROR")

    output_file = None
    try:
        output_file = open('outputs.txt', 'w')

        # Q1: Read & build unique edges
        log_rdd = sc.textFile(log_file_path, minPartitions=int(num_cores))
        parsed_rdd = log_rdd.map(parse_log_line).filter(lambda x: x is not None)
        edges_with_ts_rdd = parsed_rdd.map(create_edge_with_ts).filter(lambda x: x is not None)

        # Unique edges (src, dst)
        edges_rdd = edges_with_ts_rdd.map(lambda x: (x[0], x[1])).distinct().cache()

        # Build edge timestamp dictionary (earliest timestamp per edge)
        edge_min_ts_rdd = edges_with_ts_rdd.map(lambda e: ((e[0], e[1]), e[2])) \
                                           .reduceByKey(lambda a, b: a if a <= b else b)
        edge_timestamps = dict(edge_min_ts_rdd.collect())

        # Compute node statistics
        nodes_rdd = edges_rdd.flatMap(lambda sd: [sd[0], sd[1]]).distinct()
        nodes = set(nodes_rdd.collect())
        process_nodes = sorted([n for n in nodes if n.startswith('P')])
        resource_nodes = sorted([n for n in nodes if n.startswith('R')])

        num_processes = len(process_nodes)
        num_resources = len(resource_nodes)
        num_edges = edges_rdd.count()

        # Write Q1.2 metrics
        output_file.write(f"{num_processes}\n")
        output_file.write(f"{num_resources}\n")
        output_file.write(f"{num_edges}\n")

        # Q2: Cycle detection (optimized)
        cycles, exec_time = rdd_cycle_detection_optimized(sc, edges_rdd, max_cycle_length=25)

        # Q3.2 execution time (2 decimals)
        output_file.write(f"{exec_time:.2f}\n")

        # Q2.2 number of cycles + listing
        output_file.write(f"{len(cycles)}\n")
        for cyc in cycles:
            output_file.write(" ".join(cyc) + "\n")

        # Q2.3 unique processes involved in cycles
        proc_in_deadlock = sorted({node for cyc in cycles for node in cyc if node.startswith('P')})
        output_file.write(f"{len(proc_in_deadlock)}\n")
        if proc_in_deadlock:
            output_file.write(" ".join(proc_in_deadlock) + "\n")
        else:
            output_file.write("\n")

        # Q3.1: Deadlock formation timeline
        date_counts: Dict[str, int] = {}
        for cyc in cycles:
            d = get_cycle_formation_date(cyc, edge_timestamps)
            if d:
                date_counts[d] = date_counts.get(d, 0) + 1

        for d, c in sorted(date_counts.items()):
            output_file.write(f"{d} {c}\n")

        # Q4: Graph structure analysis
        in_deg_rdd = edges_rdd.map(lambda sd: (sd[1], 1)).reduceByKey(lambda a, b: a + b)
        out_deg_rdd = edges_rdd.map(lambda sd: (sd[0], 1)).reduceByKey(lambda a, b: a + b)

        # Top-5 resources by in-degree
        top_resources = in_deg_rdd.filter(lambda kv: kv[0].startswith('R')).collect()
        top_resources.sort(key=lambda x: (-x[1], x[0]))
        for r, deg in top_resources[:5]:
            output_file.write(f"{r} {deg}\n")

        # Top-5 processes by out-degree
        top_processes = out_deg_rdd.filter(lambda kv: kv[0].startswith('P')).collect()
        top_processes.sort(key=lambda x: (-x[1], x[0]))
        for p, deg in top_processes[:5]:
            output_file.write(f"{p} {deg}\n")

        output_file.flush()

    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise
    finally:
        try:
            if output_file is not None:
                output_file.close()
        finally:
            sc.stop()


if __name__ == "__main__":
    main()
