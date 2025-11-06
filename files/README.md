# Deadlock Detection using MapReduce (PySpark)

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Algorithm Design](#algorithm-design)
4. [Implementation Details](#implementation-details)
5. [Setup and Installation](#setup-and-installation)
6. [Usage Guide](#usage-guide)
7. [Input/Output Format](#inputoutput-format)
8. [Performance Characteristics](#performance-characteristics)
9. [Code Structure](#code-structure)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This project implements a **scalable deadlock detection system** for distributed systems by analyzing resource allocation logs using the **MapReduce programming paradigm with PySpark**. The system constructs a Resource Allocation Graph (RAG) from log events and detects cycles that represent deadlock conditions through iterative path propagation.

### Key Features

- ✅ **Distributed Cycle Detection**: Iterative MapReduce-based algorithm for detecting deadlock cycles up to length 25
- ✅ **Comprehensive Analytics**: Graph metrics, timeline analysis, and resource contention hotspots
- ✅ **Scalable Processing**: Handles datasets from hundreds to tens of thousands of log entries
- ✅ **Configurable Parallelism**: Supports single-core to multi-core execution with dynamic configuration
- ✅ **Robust Edge Construction**: Properly handles WAIT and HOLD events to build accurate directed graphs

### Problem Statement

The system analyzes resource allocation logs (up to 50,000 records) containing TIMESTAMP, LEVEL (WAIT/HOLD), PROCESS ID, and RESOURCE ID fields. It identifies deadlock cycles where processes are waiting for resources held by other processes in a circular dependency.

**Example Log Entries:**
```
2025-10-25 00:28:37 WAIT P105 R024
2025-10-25 00:28:44 HOLD R009 P110
2025-10-25 00:29:01 WAIT P174 R024
```

---

## System Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Log File      │
│  (hpc_rag.log)  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Parse & Map    │  ← Convert WAIT/HOLD events to directed edges
│   Phase         │     WAIT: Process → Resource
└────────┬────────┘     HOLD: Resource → Process
         │
         v
┌─────────────────┐
│ Edge RDD        │  ← Unique directed edges (Source, Destination)
│ Construction    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Iterative      │  ← Path propagation through graph
│ Cycle Detection │     Stop when cycles found or max length reached
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Result         │  ← Graph metrics, cycles, timeline, hotspots
│ Aggregation     │
└─────────────────┘
```

### MapReduce Workflow

1. **Map Phase**: Parse log entries and generate directed edges
2. **Reduce Phase (Iterative)**:
   - Initialize paths from each node
   - Extend paths by joining with edges
   - Detect cycles when path returns to start
   - Prune longer paths to maintain efficiency
3. **Final Aggregation**: Collect cycles, compute metrics, generate timeline

---

## Algorithm Design

### Core Algorithm: Iterative Path Propagation

The cycle detection algorithm works by propagating paths through the graph iteratively:

```
Initialize: paths = {(node, [node]) for each node}

For each iteration (up to max_cycle_length):
    1. Join paths with outgoing edges
    2. Extend paths to neighbors
    3. Detect cycles: if neighbor == start_node → cycle found
    4. Prune: keep only shortest path for each (start, current) pair
    5. Stop if no new paths generated
```

### Key Optimizations

1. **Shortest Path Pruning**: For each (start, current) node pair, only the shortest path is retained
   - Reduces state space from exponential to manageable size
   - Prevents memory exhaustion on large graphs

2. **Cycle Normalization**: Detected cycles are normalized to canonical form
   - Enables efficient deduplication
   - Ensures consistent output ordering

3. **RDD Caching**: Intermediate path RDDs are cached
   - Avoids recomputation in iterative loops
   - Trades memory for speed (beneficial when data reused)

4. **Early Termination**: Algorithm stops when no new paths are generated
   - Prevents unnecessary iterations
   - Automatically adapts to graph structure

5. **Local Aggregation**: Uses `reduceByKey` instead of `groupByKey`
   - Performs partial aggregation on mapper side
   - Reduces network shuffle overhead

---

## Implementation Details

### Data Structures

#### Edge Representation
- **Format**: `(source_node, destination_node)`
- **WAIT event**: `(PROCESS_ID, RESOURCE_ID)` - Process requests resource
- **HOLD event**: `(RESOURCE_ID, PROCESS_ID)` - Resource allocated to process

#### Path Representation
- **Format**: `((start_node, current_node), [node_list])`
- **Key**: `(start_node, current_node)` - enables efficient shortest-path reduction
- **Value**: `[start_node, n1, n2, ..., current_node]` - complete path history

#### Cycle Representation
- **Format**: `(n1, n2, ..., nk)` - tuple of nodes in cycle
- **Normalized**: Lexicographically smallest rotation, no repeated start node
- **Example**: Cycle `P1→R1→P2→R2→P1` stored as `('P1', 'R1', 'P2', 'R2')`

### Core Functions

#### `parse_log_line(line: str) -> Optional[Tuple]`
Parses a single log line into structured data.
- **Input**: Raw log line string
- **Output**: `(timestamp, event_type, node1, node2)` or `None` if invalid
- **Handles**: Whitespace variations, invalid formats

#### `create_edge_with_ts(parsed: Tuple) -> Optional[Tuple]`
Converts parsed log entry to directed edge with timestamp.
- **WAIT**: Returns `((process, resource), timestamp)`
- **HOLD**: Returns `((resource, process), timestamp)`

#### `normalize_cycle(path: List[str]) -> Tuple[str, ...]`
Normalizes cycle to canonical form for deduplication.
- Finds lexicographically smallest rotation
- Excludes repeated start node
- Enables set-based duplicate detection

#### `rdd_cycle_detection(sc, edges_rdd, max_cycle_length: int)`
Main cycle detection algorithm using iterative RDD operations.
- **Returns**: `(cycles, execution_time)`
- **Complexity**: O(V × E × max_length) worst case, but pruning reduces practical complexity

#### `get_cycle_formation_date(cycle, edge_ts)`
Determines when a cycle was first fully formed.
- Finds the **latest timestamp** among all edges in cycle
- Returns date component (YYYY-MM-DD)

---

## Setup and Installation

### Prerequisites

- **Operating System**: Linux (Ubuntu 24 or similar)
- **Python**: 3.8 or higher
- **Apache Spark**: 3.x
- **Java**: JDK 8 or 11 (required by Spark)

### Installation on Cluster

#### Step 1: Access Cluster
```bash
ssh username@cluster-address
```

#### Step 2: Load/Install Required Modules

**If using module system (e.g., SLURM):**
```bash
module load python/3.9
module load java/11
module load spark/3.3.0
```

**If installing manually:**
```bash
# Install Java
sudo apt-get update
sudo apt-get install openjdk-11-jdk

# Install PySpark
pip install pyspark --break-system-packages

# Verify installation
python3 -c "import pyspark; print(pyspark.__version__)"
spark-submit --version
```

#### Step 3: Set Environment Variables
Add to `~/.bashrc`:
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export SPARK_HOME=/path/to/spark
export PATH=$SPARK_HOME/bin:$PATH
export PYSPARK_PYTHON=python3
```

Apply changes:
```bash
source ~/.bashrc
```

#### Step 4: Verify Setup
```bash
# Test Spark
spark-submit --version

# Test PySpark
python3 << EOF
from pyspark import SparkContext, SparkConf
conf = SparkConf().setAppName("Test").setMaster("local[2]")
sc = SparkContext(conf=conf)
print("PySpark working!")
sc.stop()
EOF
```

---

## Usage Guide

### Basic Usage

```bash
spark-submit AOS_Assignment4.py <log_file_path> <num_cores>
```

**Parameters:**
- `log_file_path`: Path to the log file (e.g., `../test_files/hpc_rag.log`)
- `num_cores`: Number of CPU cores to use (e.g., `1`, `2`, `4`)

**Example:**
```bash
spark-submit AOS_Assignment4.py ../test_files/hpc_rag.log 4
```

### Output Location

All results are written to **`outputs.txt`** in the current directory.

### Advanced Usage

#### Running on SLURM Cluster

Create a job script `run_deadlock.sh`:
```bash
#!/bin/bash
#SBATCH --job-name=deadlock_detection
#SBATCH --output=deadlock_%j.out
#SBATCH --error=deadlock_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

# Load modules
module load python/3.9
module load spark/3.3.0

# Run analysis
spark-submit AOS_Assignment4.py ../test_files/hpc_rag.log 4
```

Submit job:
```bash
sbatch run_deadlock.sh
```

#### Performance Testing Script

Create `benchmark.sh`:
```bash
#!/bin/bash

LOG_FILE="../test_files/hpc_rag.log"
CORES=(1 2 4)

for core in "${CORES[@]}"; do
    echo "Testing with $core core(s)..."
    spark-submit AOS_Assignment4.py $LOG_FILE $core
    mv outputs.txt outputs_${core}core.txt
    echo "------------------------"
done
```

Run:
```bash
chmod +x benchmark.sh
./benchmark.sh
```

---

## Input/Output Format

### Input Format

**Log file structure:**
```
TIMESTAMP LEVEL PROCESS_ID RESOURCE_ID
TIMESTAMP LEVEL RESOURCE_ID PROCESS_ID
```

**Example:**
```
2025-10-25 00:28:37 WAIT P105 R024
2025-10-25 00:28:44 HOLD R009 P110
```

**Requirements:**
- Space-separated fields
- Timestamp format: `YYYY-MM-DD HH:MM:SS`
- LEVEL: Either `WAIT` or `HOLD`
- Process IDs: Start with `P` (e.g., `P105`)
- Resource IDs: Start with `R` (e.g., `R024`)

### Output Format

Results are written to `outputs.txt` in the following order:

```
<num_processes>          # Q1.2a: Total unique process nodes
<num_resources>          # Q1.2b: Total unique resource nodes
<num_edges>              # Q1.2c: Total unique directed edges
<execution_time>         # Q2.1 & Q3.2: Cycle detection time (seconds)
<num_cycles>             # Q2.2: Total deadlock cycles detected

# Cycle listings (Q2.2) - sorted by length, then lexicographically
<cycle_1_nodes>          # Space-separated node sequence
<cycle_2_nodes>
...

<num_unique_processes>   # Q2.3: Unique processes in deadlocks
<process_ids>            # Q2.3: Space-separated alphabetically sorted

# Timeline (Q3.1) - chronologically sorted
<date_1> <count_1>
<date_2> <count_2>
...

# Top 5 resources by in-degree (Q4) - descending order
<resource_id> <in_degree>
...

# Top 5 processes by out-degree (Q4) - descending order
<process_id> <out_degree>
...
```

**Example Output:**
```
99
49
1638
107.74
5
P102 R006 P159 R039 P143 R031
P105 R002 P156 R046 P145 R020
P150 R033 P152 R009 P186 R004 P189 R037
P117 R013 P146 R043 P177 R044 P164 R027 P183 R016
P104 R038 P125 R025 P132 R001 P163 R008 P169 R022 P195 R042 P199 R045 P113 R040 P171 R019 P112 R041 P162 R018 P142 R049
27
P102 P104 P105 P112 P113 P117 P125 P132 P142 P143 P145 P146 P150 P152 P156 P159 P162 P163 P164 P169 P171 P177 P183 P186 P189 P195 P199
2025-11-02 2
2025-11-04 1
2025-11-06 2
R032 72
R024 72
R012 72
R036 72
R028 72
P154 22
P158 22
P131 22
P139 22
P167 22
```

---

## Performance Characteristics

### Measured Performance

| Dataset Size | 1 Core (s) | 2 Cores (s) | 4 Cores (s) | Best Config |
|-------------|-----------|-------------|-------------|-------------|
| 500 logs    | 119.04    | 132.88      | 121.17      | 1 Core      |
| 5,000 logs  | 124.41    | 142.97      | 128.84      | 1 Core      |
| 20,000 logs | 138.97    | 151.27      | 132.33      | 4 Cores     |
| 50,000 logs | 161.87    | 163.91      | 147.15      | 4 Cores     |

### Key Observations

1. **Small Datasets (< 10K entries)**: Single-core execution often outperforms multi-core due to coordination overhead exceeding computational workload

2. **Large Datasets (20K+ entries)**: Multi-core execution becomes beneficial as computational work justifies parallelization overhead

3. **Scalability**: Execution time increases sublinearly (1.33x for 100x dataset increase), demonstrating good algorithmic efficiency

4. **Parallel Efficiency**: Ranges from -5% (small datasets) to 25% (large datasets), indicating significant room for optimization

### Recommendations

- **For datasets < 10,000 entries**: Use `num_cores=1` for optimal performance
- **For datasets ≥ 20,000 entries**: Use `num_cores=4` or higher for best results
- **Production deployment**: Use actual distributed cluster for datasets > 100,000 entries

---

## Code Structure

### File Organization

```
AOS_Assignment4.py
├── Imports
│   ├── sys, time - System and timing utilities
│   ├── pyspark - Spark context and configuration
│   └── typing - Type hints for clarity
│
├── Helper Functions
│   ├── parse_log_line() - Parse raw log entries
│   ├── create_edge_with_ts() - Convert to directed edges
│   ├── normalize_cycle() - Canonicalize cycle representation
│   └── get_cycle_formation_date() - Timeline analysis
│
├── Core Algorithm
│   └── rdd_cycle_detection() - Main iterative cycle detection
│       ├── Initialize paths from all nodes
│       ├── Iterative path propagation loop
│       ├── Cycle detection and normalization
│       ├── Shortest path pruning
│       └── Return detected cycles and timing
│
└── Main Function
    ├── Argument parsing and validation
    ├── Spark context initialization
    ├── Q1: RAG construction and metrics
    ├── Q2: Cycle detection
    ├── Q3: Performance and timeline analysis
    ├── Q4: Graph structure analysis
    └── Result output to file
```

### Key Code Sections

#### 1. Edge Construction (Lines ~340-365)
- Parses log entries
- Creates directed edges based on WAIT/HOLD events
- Builds RDD of unique edges with timestamps

#### 2. Cycle Detection Loop (Lines ~366-429)
- Initializes paths from each node
- Iteratively extends paths through graph
- Detects cycles when path returns to start
- Implements shortest-path pruning
- Collects unique cycles

#### 3. Result Aggregation (Lines ~475-564)
- Computes graph metrics (node counts, edge counts)
- Sorts and formats cycles
- Generates timeline of cycle formations
- Identifies resource contention hotspots

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Command not found: spark-submit"
**Solution**: Spark not in PATH or not installed
```bash
# Check if Spark is installed
which spark-submit

# Add to PATH if installed
export PATH=/path/to/spark/bin:$PATH

# Or install PySpark
pip install pyspark --break-system-packages
```

#### Issue: "Java not found" or "JAVA_HOME not set"
**Solution**: Install Java and set JAVA_HOME
```bash
sudo apt-get install openjdk-11-jdk
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
```

#### Issue: Very slow performance with small files
**Solution**: Use single-core execution
```bash
spark-submit AOS_Assignment4.py input.log 1
```

#### Issue: "Memory overhead exceeded"
**Solution**: Increase executor memory
```bash
spark-submit --executor-memory 4G \
             --driver-memory 2G \
             AOS_Assignment4.py input.log 4
```

#### Issue: No output file generated
**Solution**: Check current directory permissions
```bash
# Check write permissions
ls -la outputs.txt

# Run with explicit path
spark-submit AOS_Assignment4.py /full/path/to/log.log 2
```

#### Issue: "File not found" error
**Solution**: Use absolute paths or verify relative paths
```bash
# Use absolute path
spark-submit AOS_Assignment4.py /home/user/data/hpc_rag.log 2

# Or check current directory
pwd
ls ../test_files/
```

### Performance Optimization Tips

1. **Tune Spark Configuration**:
```bash
spark-submit --conf spark.default.parallelism=8 \
             --conf spark.sql.shuffle.partitions=8 \
             --conf spark.memory.fraction=0.8 \
             AOS_Assignment4.py input.log 4
```

2. **Enable Kryo Serialization**:
```bash
spark-submit --conf spark.serializer=org.apache.spark.serializer.KryoSerializer \
             AOS_Assignment4.py input.log 4
```

3. **Adjust Partition Count**: Modify line in code:
```python
edges_rdd = edges_with_ts_rdd.map(...).distinct().repartition(8).cache()
```

### Debugging Tips

1. **Enable Spark Logging**:
```python
# Change in code from:
sc.setLogLevel("ERROR")
# To:
sc.setLogLevel("INFO")
```

2. **Check Intermediate Results**:
```python
# Add after edge construction:
print(f"Sample edges: {edges_rdd.take(10)}")
```

3. **Monitor Execution**:
- Spark UI available at `http://localhost:4040` during execution
- Check stage completion and task distribution

---

## Additional Resources

### Documentation
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- [MapReduce Tutorial](https://hadoop.apache.org/docs/current/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html)
- [Graph Algorithms](https://spark.apache.org/docs/latest/graphx-programming-guide.html)

### Algorithm References
- **Cycle Detection**: Depth-First Search (DFS) and iterative graph algorithms
- **Distributed Computing**: MapReduce programming model (Dean & Ghemawat, 2004)
- **Deadlock Theory**: Coffman conditions and resource allocation graphs

### Contact and Support
For issues or questions about the implementation:
1. Check error messages in stderr output
2. Review Spark UI for execution details
3. Verify input file format matches specification
4. Test with smaller dataset first

---

## Summary

This MapReduce implementation provides a robust, scalable solution for deadlock detection in distributed systems. By leveraging PySpark's distributed computing capabilities and implementing careful optimizations (shortest-path pruning, RDD caching, efficient aggregation), the system can process tens of thousands of log entries and accurately identify all deadlock cycles. While parallel execution introduces overhead for smaller datasets, the algorithm demonstrates strong scalability characteristics for production-scale workloads.

**Key Strengths:**
- ✅ Accurate cycle detection with complete path tracking
- ✅ Configurable parallelism for different dataset sizes  
- ✅ Comprehensive output including metrics, timelines, and hotspots
- ✅ Efficient memory usage through aggressive pruning
- ✅ Well-documented and maintainable codebase

**Recommended Use Cases:**
- Production log analysis for large-scale distributed systems
- Post-mortem analysis of deadlock incidents
- Real-time monitoring with incremental updates (with modifications)
- Educational purposes for learning MapReduce and graph algorithms

---

**Last Updated**: November 2025  
**Version**: 1.0  
**License**: Academic Use
