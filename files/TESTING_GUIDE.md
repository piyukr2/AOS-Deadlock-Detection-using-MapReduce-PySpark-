# Testing Guide for AOS Assignment 4

## Quick Start

### 1. Test with Sample Log File
```bash
python3 AOS_Assignment4.py sample_log.txt 2
```

This will generate `outputs.txt` with the results.

### 2. Verify Output Format
Check that `outputs.txt` contains the following sections in order:

1. **Line 1:** Total unique Process nodes (integer)
2. **Line 2:** Total unique Resource nodes (integer)
3. **Line 3:** Total unique directed edges (integer)
4. **Line 4:** Execution time for cycle detection (float with 2 decimals)
5. **Line 5:** Number of deadlock cycles detected (integer)
6. **Lines 6+:** Each detected cycle (space-separated node IDs)
7. **Next line:** Count of unique processes in deadlocks (integer)
8. **Next line:** Space-separated list of all processes in deadlocks
9. **Next lines:** Deadlock formation timeline (format: YYYY-MM-DD count)
10. **Next lines:** Top 5 resources by in-degree (format: RESOURCE_ID degree)
11. **Last lines:** Top 5 processes by out-degree (format: PROCESS_ID degree)

### 3. Run with Different Core Counts (Performance Testing)
```bash
# Test with 1 core
python3 AOS_Assignment4.py sample_log.txt 1

# Test with 2 cores
python3 AOS_Assignment4.py sample_log.txt 2

# Test with 4 cores
python3 AOS_Assignment4.py sample_log.txt 4

# Test with 8 cores
python3 AOS_Assignment4.py sample_log.txt 8
```

Record the execution times from line 4 of each `outputs.txt` for your report.

## Validation Checklist

### Output Format Validation
- [ ] All numeric values are properly formatted
- [ ] Execution time has exactly 2 decimal places
- [ ] Cycles are sorted by length first, then lexicographically
- [ ] Process list is alphabetically sorted
- [ ] Dates are in chronological order
- [ ] Resources/Processes are sorted by degree (descending), then by ID

### Content Validation
- [ ] No duplicate cycles in output
- [ ] All cycle nodes exist in the graph
- [ ] Process nodes start with 'P'
- [ ] Resource nodes start with 'R'
- [ ] Each cycle forms a valid closed path

### File Operations
- [ ] `outputs.txt` is created successfully
- [ ] Previous `outputs.txt` is overwritten (not appended)
- [ ] Script doesn't include `outputs.txt` in submission

## Expected Behavior for Sample Log

For the provided `sample_log.txt`:
- Should detect simple cycles
- Processes: P105, P110, P120, P130, P140, P150, P174
- Resources: R009, R015, R020, R024, R025, R030

### Sample Expected Output Structure:
```
7       # 7 unique processes
6       # 6 unique resources
20      # 20 unique edges
X.XX    # Execution time in seconds
2       # 2 cycles detected
P105 R009 P110 R024   # First cycle (length 4)
P120 R020 P130 R025 P140 R030 P150 R015   # Second cycle (length 8)
6       # 6 processes involved
P105 P110 P120 P130 P140 P150
2025-10-25 2
R009 2
R015 2
...
```

## Common Issues and Solutions

### Issue 1: FileNotFoundError
**Solution:** Ensure the log file path is correct. Use relative or absolute paths.

```bash
# If in the same directory
python3 AOS_Assignment4.py sample_log.txt 2

# If in test_files folder
python3 AOS_Assignment4.py ../test_files/hpc_rag.log 4
```

### Issue 2: Spark Not Found
**Solution:** Ensure PySpark is installed and SPARK_HOME is set.

```bash
pip install pyspark
```

### Issue 3: Java Version Error
**Solution:** Ensure Java 11 is installed and is the active version.

```bash
java -version
# Should show version 11.x.x
```

### Issue 4: Permission Denied for outputs.txt
**Solution:** Ensure write permissions in the current directory.

```bash
chmod 644 outputs.txt  # If file exists
# Or run from a directory with write permissions
```

### Issue 5: Empty or Incorrect Output
**Solution:** Check log file format. Each line should have:
```
YYYY-MM-DD HH:MM:SS LEVEL PROCESS_ID RESOURCE_ID
```

## Performance Testing Protocol

### Step 1: Baseline (Single Core)
```bash
python3 AOS_Assignment4.py ../test_files/hpc_rag.log 1
# Record execution time from outputs.txt line 4
```

### Step 2: Scaling Test
Test with: 2, 4, 8, 16 cores (if available)

### Step 3: Data Collection
Create a table:

| Cores | Time (s) | Speedup | Efficiency (%) |
|-------|----------|---------|----------------|
| 1     | T1       | 1.00    | 100            |
| 2     | T2       | T1/T2   | (T1/T2)/2 × 100|
| 4     | T4       | T1/T4   | (T1/T4)/4 × 100|
| 8     | T8       | T1/T8   | (T1/T8)/8 × 100|

### Step 4: Generate Graphs
Plot:
1. Cores vs. Execution Time (line graph)
2. Cores vs. Speedup (with ideal linear line for comparison)
3. Cores vs. Efficiency (bar chart)

## Debugging Tips

### Enable Spark Logging
Modify the script temporarily to see more details:
```python
sc.setLogLevel("INFO")  # Instead of "ERROR"
```

### Print Intermediate Results
Add debug prints:
```python
print(f"Edges collected: {len(edges_list)}")
print(f"Unique nodes: {len(set([e[0] for e in edges_list] + [e[1] for e in edges_list]))}")
```

### Verify Graph Construction
Check if edges are created correctly:
```python
# After edges_list = edges_rdd.collect()
print("Sample edges:", edges_list[:10])
```

### Check Cycle Detection
Verify cycles are valid:
```python
for cycle in cycles:
    print(f"Cycle: {' -> '.join(cycle)}")
```

## Cluster Execution (ada.iiit.ac.in)

### Login
```bash
ssh your_roll_number@ada.iiit.ac.in
```

### Upload Files
```bash
scp AOS_Assignment4.py your_roll_number@ada.iiit.ac.in:~/
```

### Create Job Script (optional for batch execution)
```bash
#!/bin/bash
#SBATCH --job-name=deadlock_detection
#SBATCH --output=output_%j.txt
#SBATCH --ntasks=8
#SBATCH --time=00:30:00

spark-submit AOS_Assignment4.py ../test_files/hpc_rag.log 8
```

### Submit Job
```bash
sbatch job_script.sh
```

### Interactive Execution
```bash
srun -n 4 spark-submit AOS_Assignment4.py ../test_files/hpc_rag.log 4
```

### Check Job Status
```bash
squeue -u your_roll_number
```

### View Output
```bash
cat outputs.txt
```

## Final Checklist Before Submission

- [ ] Test script with sample data
- [ ] Verify outputs.txt format matches specification
- [ ] Run performance tests with multiple core counts
- [ ] Generate graphs for report
- [ ] Complete Report.pdf with all observations
- [ ] Verify README.md has execution instructions
- [ ] Test spark-submit command format
- [ ] Ensure no hardcoded paths in code
- [ ] Verify submission structure matches requirements
- [ ] Clean up any debug prints or test files
- [ ] Do NOT include outputs.txt in submission

## Submission Structure Verification
```
<rollnumber>_Assignment4.zip
└── <rollnumber>_Assignment4/
    ├── AOS_Assignment4.py    ✓
    ├── Report.pdf            ✓
    └── README.md             ✓
```

Should NOT contain:
- outputs.txt (generated at runtime)
- requirements.txt (not needed)
- test files or logs
- __pycache__ or .pyc files
- IDE configuration files

## Contact for Help
If you encounter issues:
1. Check this testing guide first
2. Review the assignment document
3. Test with the sample log file
4. Check Spark and Python versions
5. Contact course staff via email

---

**Good luck with your assignment!**
