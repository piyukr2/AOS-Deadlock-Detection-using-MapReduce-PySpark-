import sys
import time
from datetime import datetime
from typing import List, Tuple, Dict, Iterable

from pyspark import SparkContext, SparkConf

def parse_log_line(line: str):
    """
    This function parses a log line; expected format (5+ tokens):
      YYYY-MM-DD HH:MM:SS LEVEL PROCESS_ID RESOURCE_ID
    and returns (timestamp_str, LEVEL, PROCESS_ID, RESOURCE_ID) or None if invalid.
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
    This function maps the parsed record to a directed edge with timestamp, as per the given rules:
      WAIT: Process -> Resource
      HOLD: Resource -> Process
    It returns (src, dst, timestamp) or None.
    """
    timestamp, level, process_id, resource_id = record
    lvl = level.upper()
    if lvl == 'WAIT':
        return (process_id, resource_id, timestamp)
    elif lvl == 'HOLD':
        return (resource_id, process_id, timestamp)
    return None



# Cycle detection: RDD-based iterative propagation
def normalize_cycle(path: List[str]) -> Tuple[str, ...]:
    """
    This function normalises a cycle (list of nodes, e.g., [P1, R1, P2, R2]) so
    that it starts from the lexicographically smallest node,
    preserving direction, for deterministic dedup/sort.
    """
    n = len(path)
    if n == 0:
        return tuple()
    # Find all indices with minimal node id (lexicographically)
    min_node = min(path)
    candidates = [i for i, v in enumerate(path) if v == min_node]
    # Choose rotation that yields lexicographically smallest tuple
    best = None
    for idx in candidates:
        rotated = tuple(path[idx:] + path[:idx])
        if best is None or rotated < best:
            best = rotated
    return best


def rdd_cycle_detection(sc: SparkContext,
                        edges_rdd,
                        max_cycle_length: int = 25):
    """
    This function detects cycles using an iterative MapReduce-style path propagation.
    edges_rdd: RDD[(src, dst)] with unique directed edges.

    It returns:
      cycles (List[List[str]]), found during propagation.
      exec_time_seconds (float) for the propagation portion.
    """
    # Persist edges; we'll reuse it many times
    edges_rdd = edges_rdd.distinct().cache()

    # For adjacency joins: (current -> next)
    # This is already edges_rdd
    # Initialize paths as single-edge paths:
    # records of ((start, current), path_list)
    paths = edges_rdd.map(lambda sd: ((sd[0], sd[1]), [sd[0], sd[1]])).cache()

    # For cycle detection results across iterations
    detected_cycles = set()

    start_t = time.time()

    for _iter in range(max_cycle_length - 1):
        # Extend: join on current node with edges
        # Prepare (key=current, value=(start, path))
        paths_by_current = paths.map(lambda kv: (kv[0][1], (kv[0][0], kv[1])))
        # Join with edges: (current, ( (start, path), next ))
        joined = paths_by_current.join(edges_rdd)  # edges as (current, next)

        # Map to extended paths or cycles
        # Output candidates as: either cycles (collected later) or new paths
        # We keep only shortest path for a given (start, new_current)
        def extend_or_cycle(rec):
            """
            rec: (current, ((start, path), next))
            Yields:
              - ('path', ((start, new_current), new_path_list))
              - or ('cycle', normalized_cycle_tuple)
            """
            _, (sp, nxt) = rec
            start_node, path = sp
            current_node = path[-1]
            next_node = nxt

            outs = []
            if next_node == start_node and len(path) >= 2:
                # Found a cycle; normalize WITHOUT repeating start
                norm = normalize_cycle(path[:])  # path already includes start once
                if norm and len(norm) >= 2:
                    outs.append(('cycle', norm))
            elif (next_node not in path) and (len(path) < max_cycle_length):
                new_path = path + [next_node]
                outs.append(('path', ((start_node, next_node), new_path)))
            return outs

        extended = joined.flatMap(extend_or_cycle)

        # Separate new paths and cycles
        new_paths = extended.filter(lambda x: x[0] == 'path') \
                            .map(lambda x: x[1])
        found_cycles = extended.filter(lambda x: x[0] == 'cycle') \
                               .map(lambda x: x[1]) \
                               .distinct() \
                               .collect()

        # Add newly found cycles to local set
        for cyc in found_cycles:
            detected_cycles.add(cyc)

        # Keep only the shortest path for each (start, current)
        def pick_shorter(a, b):
            return a if len(a) <= len(b) else b

        # If no new paths, stop
        if new_paths.isEmpty():
            break

        paths = new_paths.reduceByKey(pick_shorter).cache()

    end_t = time.time()
    exec_time = end_t - start_t

    # Convert to list of list[str] and sort as required
    cycles = [list(c) for c in detected_cycles]
    cycles.sort(key=lambda c: (len(c), c))
    return cycles, exec_time


def get_cycle_formation_date(cycle: List[str],
                             edge_ts: Dict[Tuple[str, str], str]) -> str:
    """
    For a given cycle (sequence of nodes), this function finds the date when the cycle
    was first fully formed (the last required edge timestamp).
    We choose the **latest timestamp** among edges in the cycle and
    return its date component (YYYY-MM-DD).
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
        sys.stderr.write("Usage: spark-submit AOS_Assignment4.py <log_file_path> <num_cores>\n")
        sys.exit(1)

    log_file_path = sys.argv[1]
    num_cores = sys.argv[2]

    # Configure Spark; local[num_cores] works on the compute node
    conf = SparkConf().setAppName("DeadlockDetection")
    # If user passes cores, use local mode with that many threads
    # (On a cluster without a manager, this matches your SLURM cpus-per-task.)
    conf = conf.setMaster(f"local[{num_cores}]")
    sc = SparkContext(conf=conf)
    sc.setLogLevel("ERROR")

    output_file = None
    try:
        output_file = open('outputs.txt', 'w')

        
        #### Q1: Read & build unique edges
        
        log_rdd = sc.textFile(log_file_path)
        parsed_rdd = log_rdd.map(parse_log_line).filter(lambda x: x is not None)
        edges_with_ts_rdd = parsed_rdd.map(create_edge_with_ts).filter(lambda x: x is not None)

        # Unique edges (src, dst)
        edges_rdd = edges_with_ts_rdd.map(lambda x: (x[0], x[1])).distinct().cache()

        # For Q3 timeline (use earliest timestamp observed for each edge)
        # Build ( (src,dst), ts ) with min ts
        edge_min_ts_rdd = edges_with_ts_rdd.map(lambda e: ((e[0], e[1]), e[2])) \
                                           .reduceByKey(lambda a, b: a if a <= b else b)
        edge_timestamps = dict(edge_min_ts_rdd.collect())

        # All distinct nodes
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

        
        #### Q2: Cycle detection (RDD iterative propagation)
        
        cycles, exec_time = rdd_cycle_detection(sc, edges_rdd, max_cycle_length=25)

        # Q3.2 time for Q2 (seconds, 2 decimals)
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

        
        #### Q3.1: Deadlock formation timeline (date,count)
        
        # Count per date based on "last edge appears" rule
        date_counts: Dict[str, int] = {}
        for cyc in cycles:
            d = get_cycle_formation_date(cyc, edge_timestamps)
            if d:
                date_counts[d] = date_counts.get(d, 0) + 1

        for d, c in sorted(date_counts.items()):
            output_file.write(f"{d} {c}\n")

        
        #### Q4: Graph structure analysis
        
        # In-degree per node (as destination)
        in_deg_rdd = edges_rdd.map(lambda sd: (sd[1], 1)).reduceByKey(lambda a, b: a + b)
        # Out-degree per node (as source)
        out_deg_rdd = edges_rdd.map(lambda sd: (sd[0], 1)).reduceByKey(lambda a, b: a + b)

        # Top-5 resources by in-degree (desc degree, then ID)
        top_resources = in_deg_rdd.filter(lambda kv: kv[0].startswith('R')) \
                                  .map(lambda kv: (kv[0], kv[1])) \
                                  .collect()
        top_resources.sort(key=lambda x: (-x[1], x[0]))
        top_resources = top_resources[:5]
        for r, deg in top_resources:
            output_file.write(f"{r} {deg}\n")

        # Top-5 processes by out-degree (desc degree, then ID)
        top_processes = out_deg_rdd.filter(lambda kv: kv[0].startswith('P')) \
                                   .map(lambda kv: (kv[0], kv[1])) \
                                   .collect()
        top_processes.sort(key=lambda x: (-x[1], x[0]))
        top_processes = top_processes[:5]
        for p, deg in top_processes:
            output_file.write(f"{p} {deg}\n")

        output_file.flush()

    except Exception as e:
        # Send errors to stderr only
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

