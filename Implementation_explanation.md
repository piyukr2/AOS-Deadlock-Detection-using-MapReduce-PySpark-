# MapReduce Deadlock Detection using PySpark

## Table of Contents
1. [Overview](#overview)
2. [What is Deadlock Detection?](#what-is-deadlock-detection)
3. [Prerequisites](#prerequisites)
4. [Installation Guide](#installation-guide)
5. [Usage](#usage)
6. [Code Structure](#code-structure)
7. [Algorithm Explanation](#algorithm-explanation)
8. [Output Format](#output-format)
9. [Understanding the Results](#understanding-the-results)
10. [Troubleshooting](#troubleshooting)
11. [Performance Tips](#performance-tips)

---

## Overview

This project implements a scalable **deadlock detection algorithm** using the MapReduce programming model with PySpark. It analyzes resource allocation logs from distributed systems to identify circular dependencies (deadlocks) between processes and resources.

**Key Features:**
- Parses log files containing WAIT and HOLD events
- Constructs Resource Allocation Graphs (RAG)
- Detects cycles using iterative path propagation
- Provides comprehensive graph metrics and analysis
- Supports variable core counts for performance testing

---

## What is Deadlock Detection?

### The Problem

In distributed systems, processes compete for limited resources. A **deadlock** occurs when:
- Process A holds Resource R1 and waits for Resource R2
- Process B holds Resource R2 and waits for Resource R1
- Both processes are stuck waiting forever!

### Our Solution

We build a **Resource Allocation Graph (RAG)** where:
- **Nodes** represent processes (P1, P2, ...) and resources (R1, R2, ...)
- **Edges** represent relationships:
  - `Process → Resource`: Process is waiting for the resource (WAIT event)
  - `Resource → Process`: Resource is allocated to the process (HOLD event)

A **cycle** in this graph indicates a deadlock!

**Example Deadlock Cycle:**
```
P105 → R002 → P156 → R046 → P145 → R020 → P105
```
This means: P105 waits for R002, which is held by P156, who waits for R046, which is held by P145, who waits for R020, which is held by P105. They're all stuck!

---

## Prerequisites

### Software Requirements
- Python 3.7 or higher
- PySpark 3.0 or higher
- Java 8 or 11 (required by Spark)
- Access to a Linux cluster (optional, but recommended for large datasets)

### Knowledge Requirements
- Basic Python programming
- Understanding of command-line operations
- Familiarity with log files and distributed systems (helpful but not required)

---

## Installation Guide

### Step 1: Set Up Python Virtual Environment

```bash
# Create a virtual environment
python3 -m venv spark_env

# Activate the virtual environment
source spark_env/bin/activate  # On Linux/Mac
# OR
spark_env\Scripts\activate  # On Windows
```

### Step 2: Install PySpark

```bash
# Upgrade pip first
pip install --upgrade pip

# Install PySpark
pip install pyspark
```

### Step 3: Verify Installation

```bash
# Check PySpark version
python -c "import pyspark; print(pyspark.__version__)"

# Should output something like: 3.5.0
```

### Step 4: Verify Java Installation

```bash
# Check Java version
java -version

# Should show Java 8 or 11
# If not installed, install Java:
# sudo apt-get install openjdk-11-jdk  # On Ubuntu/Debian
```

### Step 5: Set Up on Cluster (if applicable)

If you're using a cluster with SLURM:

```bash
# SSH into the cluster
ssh your_username@ada.iiit.ac.in

# Load required modules (if available)
module load python/3.9
module load java/11

# Create and activate virtual environment
python3 -m venv ~/spark_env
source ~/spark_env/bin/activate

# Install PySpark
pip install pyspark

# Verify installation
which spark-submit
```

---

## Usage

### Basic Command Format

```bash
spark-submit Deadlock.py <log_file_path> <num_cores>
```

### Parameters
- `<log_file_path>`: Path to your log file (e.g., `../test_files/hpc_rag.log`)
- `<num_cores>`: Number of CPU cores to use (e.g., 1, 2, 4, or 8)

### Example Commands

**Example 1: Small dataset with 1 core**
```bash
spark-submit Deadlock.py ../test_files/small_log.log 1
```

**Example 2: Medium dataset with 4 cores**
```bash
spark-submit Deadlock.py ../test_files/medium_log.log 4
```

**Example 3: Large dataset with 8 cores**
```bash
spark-submit Deadlock.py ../test_files/large_log.log 8
```

### Running on SLURM Cluster

Create a job script (`run_deadlock.sh`):

```bash
#!/bin/bash
#SBATCH --job-name=deadlock_detection
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=01:00:00
#SBATCH --mem=8GB

# Activate virtual environment
source ~/spark_env/bin/activate

# Run the job
spark-submit Deadlock.py ../test_files/hpc_rag.log 4
```

Submit the job:
```bash
sbatch run_deadlock.sh
```

Check job status:
```bash
squeue -u your_username
```

View output:
```bash
cat slurm-<job_id>.out
```

---

## Code Structure

### Main Functions

#### 1. `parse_log_line(line: str)`
**Purpose:** Parses a single line from the log file.

**Input Format:**
```
2025-10-25 00:28:37 WAIT P105 R024
```

**Output:**
```python
('2025-10-25 00:28:37', 'WAIT', 'P105', 'R024')
```

**What it does:** Splits the line and extracts the timestamp, event type (WAIT/HOLD), process ID, and resource ID.

---

#### 2. `create_edge_with_ts(record)`
**Purpose:** Converts log events into graph edges.

**Rules:**
- **WAIT event** → `Process → Resource` (process requests resource)
- **HOLD event** → `Resource → Process` (resource allocated to process)

**Example:**
```python
Input:  ('2025-10-25 00:28:37', 'WAIT', 'P105', 'R024')
Output: ('P105', 'R024', '2025-10-25 00:28:37')

Input:  ('2025-10-25 00:28:37', 'HOLD', 'P105', 'R024')
Output: ('R024', 'P105', '2025-10-25 00:28:37')
```

---

#### 3. `normalize_cycle(path: List[str])`
**Purpose:** Normalizes a cycle for consistent comparison.

**Why needed?** The same cycle can be represented in multiple ways:
- `[P1, R1, P2, R2]`
- `[R1, P2, R2, P1]`
- `[P2, R2, P1, R1]`

**Solution:** Always start from the lexicographically smallest node.

**Example:**
```python
Input:  ['P102', 'R006', 'P159', 'R039', 'P143', 'R031']
Output: ('P102', 'R006', 'P159', 'R039', 'P143', 'R031')
# P102 is the smallest, so cycle starts from P102
```

---

#### 4. `rdd_cycle_detection(sc, edges_rdd, max_cycle_length=25)`
**Purpose:** The heart of the algorithm - detects cycles using MapReduce.

**How it works:**
1. **Initialize:** Start with all edges as single-edge paths
2. **Iterate:** For each iteration:
   - Extend paths by joining with edges
   - Check if path returns to starting node (cycle found!)
   - Keep only shortest path between any two nodes
   - Stop if no new paths can be formed
3. **Return:** All detected cycles and execution time

**Example iteration:**
```
Iteration 1: P1→R1
Iteration 2: P1→R1→P2 (joined R1→P2)
Iteration 3: P1→R1→P2→R2 (joined P2→R2)
Iteration 4: P1→R1→P2→R2→P1 (cycle detected! 🎉)
```

---

#### 5. `get_cycle_formation_date(cycle, edge_ts)`
**Purpose:** Determines when a cycle was first fully formed.

**Logic:** A cycle is complete when its **last edge** appears in the logs. We find the latest timestamp among all edges in the cycle.

**Example:**
```
Cycle: P1 → R1 → P2 → R2 → P1
Edge timestamps:
  P1→R1: 2025-11-01 10:00:00
  R1→P2: 2025-11-01 11:00:00
  P2→R2: 2025-11-02 09:00:00  ← Latest!
  R2→P1: 2025-11-01 15:00:00
  
Formation date: 2025-11-02 (when P2→R2 appeared)
```

---

### Main Execution Flow

```python
1. Read command-line arguments (log file path, num cores)
2. Configure Spark with specified cores
3. Q1: Parse logs and build unique edges
   - Count processes, resources, and edges
4. Q2: Detect cycles using iterative MapReduce
   - Measure execution time
   - List all detected cycles
   - Extract involved processes
5. Q3: Analyze deadlock timeline
   - Determine formation dates
6. Q4: Compute graph metrics
   - Top 5 resources by in-degree
   - Top 5 processes by out-degree
7. Write all results to outputs.txt
```

---

## Algorithm Explanation

### The MapReduce Cycle Detection Algorithm

**Goal:** Find all cycles in a directed graph using distributed computing.

**Key Idea:** Iteratively propagate paths through the graph until they either:
- Form a cycle (return to starting node)
- Cannot be extended further
- Exceed maximum length (25 nodes)

### Detailed Steps

**Step 1: Initialization**
```python
# Convert each edge into a path of length 1
edges = [(P1, R1), (R1, P2), (P2, R2), (R2, P1)]
paths = [
    ((P1, R1), [P1, R1]),
    ((R1, P2), [R1, P2]),
    ((P2, R2), [P2, R2]),
    ((R2, P1), [R2, P1])
]
# Format: ((start_node, current_node), [path_list])
```

**Step 2: Path Extension (Join Operation)**
```python
# Join paths with edges based on current_node
paths_by_current = {
    R1: [(P1, [P1, R1])],
    P2: [(R1, [R1, P2])],
    ...
}

edges_by_source = {
    P1: [R1],
    R1: [P2],
    P2: [R2],
    R2: [P1]
}

# Join: For each path ending at X, extend with edges starting from X
# Path [P1, R1] + Edge (R1 → P2) = [P1, R1, P2]
```

**Step 3: Cycle Detection**
```python
# Check if next_node equals start_node
if next_node == start_node and len(path) >= 2:
    # Cycle found!
    cycles.add(normalize_cycle(path))
```

**Step 4: Pruning**
```python
# Avoid infinite loops: Don't revisit nodes in the same path
if next_node not in path:
    new_path = path + [next_node]
    # Continue exploring

# Keep only shortest path for each (start, end) pair
paths = paths.reduceByKey(pick_shorter)
```

### Why This Works

1. **Completeness:** Every possible path is explored systematically
2. **Efficiency:** 
   - Paths that can't lead to cycles are pruned
   - Duplicate paths are eliminated
   - We keep only the shortest path between any two nodes
3. **Correctness:** Normalization ensures we don't count the same cycle twice

### Time Complexity

- **Worst case:** O(V × E × L) where:
  - V = number of vertices (processes + resources)
  - E = number of edges
  - L = maximum cycle length (25)
- **Average case:** Much better due to pruning and early termination

---

## Output Format

The program writes all results to `outputs.txt` in this exact format:

```
99                    # Q1.2a: Number of processes
49                    # Q1.2b: Number of resources
1638                  # Q1.2c: Number of edges
107.74                # Q2/Q3.2: Execution time (seconds)
5                     # Q2.2: Number of cycles found

# Q2.2: List of detected cycles (sorted by length, then alphabetically)
P102 R006 P159 R039 P143 R031
P105 R002 P156 R046 P145 R020
P150 R033 P152 R009 P186 R004 P189 R037
...

27                    # Q2.3: Number of unique processes in deadlocks
P102 P104 P105 ...   # Q2.3: List of processes

# Q3.1: Deadlock formation timeline
2025-11-02 2
2025-11-04 1
2025-11-06 2

# Q4: Top 5 resources by in-degree
R032 72
R024 72
...

# Q4: Top 5 processes by out-degree
P154 22
P158 22
...
```

---

## Understanding the Results

### Q1: Graph Metrics

**Number of Processes:** Unique process nodes (P1, P2, ...) in the RAG.

**Number of Resources:** Unique resource nodes (R1, R2, ...) in the RAG.

**Number of Edges:** Unique directed edges. Each edge represents either:
- A process waiting for a resource
- A resource allocated to a process

---

### Q2: Cycle Detection

**Cycle Example:**
```
P105 R002 P156 R046 P145 R020
```

**Reading the cycle:**
- P105 waits for R002
- R002 is held by P156
- P156 waits for R046
- R046 is held by P145
- P145 waits for R020
- R020 is held by P105 (back to start - deadlock!)

**Cycle Length:** Number of nodes in the cycle (6 in this example).

**Sorting:** Cycles are sorted first by length (shorter cycles first), then alphabetically if lengths are equal.

---

### Q3: Timeline Analysis

**Example:**
```
2025-11-02 2
2025-11-04 1
```

**Interpretation:**
- On November 2nd, 2 deadlocks were fully formed
- On November 4th, 1 more deadlock was fully formed

**Why is this useful?** Helps identify when system congestion peaks or when problematic workloads run.

---

### Q4: Hotspot Analysis

**High In-Degree Resources:**
```
R032 72
```
Resource R032 is requested by 72 different processes - it's a bottleneck!

**High Out-Degree Processes:**
```
P154 22
```
Process P154 is waiting for 22 different resources - it's resource-greedy!

**Practical Value:** 
- High in-degree resources should be replicated or have capacity increased
- High out-degree processes may need refactoring to reduce resource dependencies

---

## Troubleshooting

### Issue 1: "spark-submit: command not found"

**Solution:**
```bash
# Find spark-submit location
find ~ -name "spark-submit" 2>/dev/null

# Add to PATH (replace with your actual path)
export PATH=$PATH:/path/to/spark/bin

# Make permanent (add to ~/.bashrc)
echo 'export PATH=$PATH:/path/to/spark/bin' >> ~/.bashrc
source ~/.bashrc
```

---

### Issue 2: "Java not found" or "JAVA_HOME not set"

**Solution:**
```bash
# Install Java
sudo apt-get install openjdk-11-jdk  # Ubuntu/Debian
sudo yum install java-11-openjdk     # CentOS/RHEL

# Set JAVA_HOME
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$PATH:$JAVA_HOME/bin

# Make permanent
echo 'export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64' >> ~/.bashrc
source ~/.bashrc
```

---

### Issue 3: Out of Memory Error

**Symptom:** "java.lang.OutOfMemoryError: Java heap space"

**Solution:**
```bash
# Increase driver and executor memory
spark-submit \
  --driver-memory 4g \
  --executor-memory 4g \
  Deadlock.py ../test_files/large_log.log 4
```

---

### Issue 4: Slow Performance with Multiple Cores

**Why?** Our performance analysis shows that more cores don't always help!

**Recommendations:**
- Datasets < 5K records: Use 1 core
- Datasets 5K-15K: Use 2 cores
- Datasets 15K-30K: Use 2-4 cores
- Datasets > 30K: Use 4-8 cores

---

### Issue 5: "Permission denied" when writing outputs.txt

**Solution:**
```bash
# Check current directory permissions
ls -la

# Create outputs in a writable directory
cd /tmp
spark-submit /path/to/Deadlock.py ../test_files/log.log 4

# Or change permissions
chmod 755 /current/directory
```

---

### Issue 6: Empty or Missing Output File

**Causes:**
- Program crashed before completing
- Wrong file path in command
- Log file format incorrect

**Debug steps:**
```bash
# Check for error messages
cat slurm-*.out | grep -i error

# Test with small sample
head -100 large_log.log > small_sample.log
spark-submit Deadlock.py small_sample.log 1

# Verify log file format
head -5 your_log_file.log
# Should show: YYYY-MM-DD HH:MM:SS WAIT/HOLD P### R###
```

---

## Performance Tips

### 1. Choose the Right Number of Cores

Based on our analysis:
```
Dataset Size  →  Recommended Cores
200-5K        →  1 core
5K-15K        →  2 cores  
15K-30K       →  2-4 cores
30K+          →  4-8 cores
```

**Why?** Parallelization has overhead. Small datasets don't benefit from multiple cores.

---

### 2. Optimize Memory Usage

```bash
# For large datasets (50K+ records)
spark-submit \
  --driver-memory 8g \
  --executor-memory 8g \
  --conf spark.driver.maxResultSize=4g \
  Deadlock.py large_file.log 8
```

---

### 3. Use Appropriate Log Levels

```python
# In the code, we set:
sc.setLogLevel("ERROR")

# For debugging, temporarily change to:
sc.setLogLevel("INFO")  # More detailed logs
sc.setLogLevel("DEBUG") # Very verbose (slow!)
```

---

### 4. Persist Important RDDs

The code already caches key RDDs:
```python
edges_rdd = edges_rdd.distinct().cache()
paths = paths.reduceByKey(pick_shorter).cache()
```

**Why?** Caching prevents recomputation when the same RDD is used multiple times.

---

### 5. Monitor Resource Usage

```bash
# While job is running, check resource usage
top -u your_username

# Memory usage
free -h

# Check Spark UI (if available)
# Usually at http://localhost:4040 during execution
```

---

## Additional Notes

### Log File Format

Your log file must follow this format:
```
YYYY-MM-DD HH:MM:SS LEVEL PROCESS_ID RESOURCE_ID
2025-10-25 00:28:37 WAIT P105 R024
2025-10-25 00:28:44 HOLD P110 R009
```

**Important:**
- Five space-separated fields
- Date format: YYYY-MM-DD
- Time format: HH:MM:SS
- Level must be WAIT or HOLD
- Process IDs start with 'P'
- Resource IDs start with 'R'

---

### Synthetic Data Generator

The provided C++ generator creates test data:

```cpp
// Creates logs with specific cycle patterns
// Adjust loop limit for different sizes:
for (int i = 1; i < 25000; ++i)  // 50K logs
for (int i = 1; i < 5000; ++i)   // 10K logs
for (int i = 1; i < 2500; ++i)   // 5K logs
```

---

### Understanding Execution Time

**What's measured:** Only the cycle detection phase (Q2), not the entire program.

**Why?** Cycle detection is the computationally intensive MapReduce part. Setup, parsing, and I/O are excluded to focus on the algorithm's scalability.

---

## Summary

This implementation provides a complete solution for deadlock detection in distributed systems using PySpark. Key points:

✅ **Scalable:** Handles datasets from hundreds to tens of thousands of records  
✅ **Accurate:** Detects all cycles using proven graph algorithms  
✅ **Configurable:** Supports variable core counts for performance tuning  
✅ **Comprehensive:** Provides detailed metrics and analysis  

**Remember:** More cores ≠ better performance for small datasets. Always profile with your specific workload!

---

## Contact and Support

For questions about the implementation:
1. Check the error messages in `slurm-*.out` files
2. Verify your log file format matches the specification
3. Review the troubleshooting section above
4. Test with a small sample dataset first

Happy deadlock hunting! 🔍🔄
