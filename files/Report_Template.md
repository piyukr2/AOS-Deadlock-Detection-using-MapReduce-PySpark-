# CS3.304 - Advanced Operating Systems: Assignment 4
## Deadlock Detection using MapReduce (PySpark)
### Performance Analysis and Observations Report

**Student Name:** [Your Name]  
**Roll Number:** [Your Roll Number]  
**Date:** [Submission Date]

---

## Executive Summary
This report presents the performance analysis and observations from implementing a scalable deadlock detection algorithm using PySpark. The system processes resource allocation logs to construct a Resource Allocation Graph (RAG) and detect cycles representing deadlocks in distributed systems.

---

## 1. Implementation Overview

### 1.1 System Architecture
- **Input:** Log file with WAIT/HOLD events
- **Processing:** PySpark RDD transformations
- **Output:** Deadlock cycles, metrics, and analysis

### 1.2 Key Components
1. **Log Parser:** Extracts timestamp, event type, process ID, and resource ID
2. **RAG Constructor:** Builds directed edges based on WAIT/HOLD semantics
3. **Cycle Detector:** Implements MapReduce pattern for path propagation
4. **Metrics Calculator:** Computes graph statistics and timelines

---

## 2. Results Summary

### 2.1 Graph Metrics (Q1)
| Metric | Value |
|--------|-------|
| Unique Process Nodes | [Value from Q1.2a] |
| Unique Resource Nodes | [Value from Q1.2b] |
| Total Directed Edges | [Value from Q1.2c] |

### 2.2 Deadlock Detection (Q2)
- **Total Cycles Detected:** [Value from Q2.2]
- **Execution Time:** [Value from Q2.1] seconds
- **Processes Involved:** [Value from Q2.3] unique processes

#### Sample Detected Cycles
```
[List 2-3 example cycles from your output]
```

### 2.3 Timeline Analysis (Q3.1)
```
[Paste deadlock formation timeline from outputs.txt]
```

### 2.4 Resource Contention (Q4)
**Top 5 Resources by In-Degree:**
```
[Paste top 5 resources from outputs.txt]
```

**Top 5 Processes by Out-Degree:**
```
[Paste top 5 processes from outputs.txt]
```

---

## 3. Performance Analysis (Q3.2 & Q3.3)

### 3.1 Scalability Testing Methodology
The cycle detection algorithm (Q2) was executed with varying numbers of CPU cores to measure scalability. The following configurations were tested:

| Cores | Execution Time (s) | Speedup | Efficiency |
|-------|-------------------|---------|------------|
| 1     | [Time]           | 1.0x    | 100%       |
| 2     | [Time]           | [Value] | [Value]    |
| 4     | [Time]           | [Value] | [Value]    |
| 8     | [Time]           | [Value] | [Value]    |
| 16    | [Time]           | [Value] | [Value]    |

**Speedup Calculation:** Speedup(n) = Time(1 core) / Time(n cores)  
**Efficiency Calculation:** Efficiency(n) = Speedup(n) / n × 100%

### 3.2 Performance Graph

[Insert graph here showing:]
- **X-axis:** Number of cores
- **Y-axis:** Execution time (seconds)
- **Plot type:** Line graph or bar chart

[Insert second graph showing:]
- **X-axis:** Number of cores
- **Y-axis:** Speedup
- Include ideal linear speedup line for comparison

### 3.3 Detailed Observations

#### 3.3.1 Scalability Characteristics

**Observed Trends:**
1. **Linear Scaling Region:** [Describe the range where near-linear speedup was observed]
2. **Diminishing Returns:** [Discuss when additional cores provide marginal benefits]
3. **Optimal Configuration:** [Identify the best core count for this workload]

#### 3.3.2 Performance Bottlenecks

**Key Observations:**
1. **Communication Overhead:** As core count increases, inter-process communication overhead grows, reducing efficiency.
2. **Task Granularity:** The cycle detection algorithm involves iterative refinement, which may limit parallelization effectiveness.
3. **Data Shuffling:** MapReduce operations require data shuffling between partitions, impacting performance at higher core counts.

#### 3.3.3 Amdahl's Law Analysis

The observed speedup can be analyzed using Amdahl's Law:
```
Speedup = 1 / ((1 - P) + P/N)
```
Where:
- P = Parallelizable fraction of the workload
- N = Number of cores

Based on empirical results:
- **Estimated P value:** [Calculate from your data]
- **Theoretical maximum speedup:** [Calculate]
- **Actual vs. Theoretical:** [Compare and explain differences]

#### 3.3.4 MapReduce Efficiency

**Strengths:**
- Effective parallelization of edge creation and graph construction
- Good load balancing for uniform graphs
- Efficient RDD caching reduces redundant computation

**Limitations:**
- Iterative path propagation requires multiple MapReduce rounds
- Cycle detection inherently has sequential dependencies
- Small graphs may not benefit from high parallelism due to overhead

#### 3.3.5 Resource Utilization

**CPU Utilization:**
- [Describe CPU usage patterns observed during execution]

**Memory Usage:**
- [Discuss memory consumption across different core counts]

**I/O Impact:**
- [Comment on disk I/O for log file reading and output writing]

---

## 4. Algorithm Analysis

### 4.1 Time Complexity
- **Edge Construction:** O(n) where n = number of log entries
- **Cycle Detection:** O(V × E × L) where V = vertices, E = edges, L = max cycle length
- **Graph Metrics:** O(E) for in-degree/out-degree calculations

### 4.2 Space Complexity
- **Edge Storage:** O(E)
- **Path Propagation:** O(V × L) in worst case
- **Cycle Storage:** O(C × L) where C = number of cycles

### 4.3 Scalability Factors

**Positive Factors:**
1. Log parsing is embarrassingly parallel
2. Independent edge creation scales linearly
3. RDD partitioning enables distributed processing

**Limiting Factors:**
1. Cycle detection has iterative dependencies
2. Global synchronization required between iterations
3. Result collection creates a bottleneck at the driver

---

## 5. Key Insights

### 5.1 Deadlock Patterns
- **Most Common Cycle Length:** [Analyze your results]
- **Peak Formation Period:** [Identify when most deadlocks formed]
- **Resource Hotspots:** [Discuss the most contested resources]

### 5.2 System Behavior
- **Process Behavior:** [Analyze processes with highest out-degree]
- **Resource Contention:** [Discuss resources with highest in-degree]
- **Temporal Patterns:** [Any trends in deadlock formation over time]

### 5.3 Practical Implications
1. **Prevention Strategies:** [Suggest strategies based on hotspot analysis]
2. **Resource Allocation:** [Recommendations for resource management]
3. **Monitoring:** [Key metrics to monitor in production systems]

---

## 6. Conclusions

### 6.1 Summary
- Successfully implemented distributed deadlock detection using PySpark
- Achieved [X]x speedup with [Y] cores compared to single-core execution
- Identified [Z] deadlock cycles in the test dataset

### 6.2 Performance Takeaways
1. **Optimal Core Count:** [Recommend based on efficiency analysis]
2. **Scalability Limits:** [Discuss practical limits observed]
3. **Trade-offs:** [Balance between execution time and resource usage]

### 6.3 Future Improvements
1. **Algorithm Optimization:** [Suggest improvements to cycle detection]
2. **Distributed Cycle Detection:** [Propose more scalable approaches]
3. **Real-time Detection:** [Consider streaming approaches]

---

## 7. References
1. Spark Documentation: https://spark.apache.org/docs/latest/
2. MapReduce Programming Model
3. Graph Cycle Detection Algorithms
4. Deadlock Detection in Distributed Systems

---

## Appendix

### A. Test Environment
- **Cluster:** ada.iiit.ac.in
- **Spark Version:** 3.4.1
- **Python Version:** 3.10.12
- **Java Version:** 11.0.27

### B. Sample Output
```
[Paste complete outputs.txt for one test run]
```

### C. Execution Commands
```bash
# Local testing
python3 AOS_Assignment4.py ../test_files/hpc_rag.log 4

# Cluster execution
spark-submit AOS_Assignment4.py ../test_files/hpc_rag.log 8
```

### D. Additional Graphs
[Include any additional visualizations or data tables]

---

**Note:** Replace all placeholder values [in brackets] with actual results from your experiments.
