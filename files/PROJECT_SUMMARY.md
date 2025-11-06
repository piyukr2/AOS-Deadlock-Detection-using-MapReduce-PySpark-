# AOS Assignment 4 - Complete Implementation Package
## Deadlock Detection using MapReduce (PySpark)

---

## 📦 Package Contents

This package contains everything you need to complete Assignment 4:

### Core Files (Required for Submission)
1. **AOS_Assignment4.py** - Main PySpark script implementing all questions (Q1-Q4)
2. **README.md** - Execution instructions and project documentation
3. **Report_Template.md** - Template for creating your Report.pdf

### Supporting Files (For Development & Testing)
4. **TESTING_GUIDE.md** - Comprehensive testing instructions
5. **validate_output.py** - Script to validate outputs.txt format
6. **prepare_submission.py** - Automated submission preparation tool
7. **sample_log.txt** - Sample log file for testing

---

## 🚀 Quick Start Guide

### Step 1: Test the Script
```bash
# Make validate_output.py and prepare_submission.py executable
chmod +x validate_output.py prepare_submission.py

# Test with sample data
python3 AOS_Assignment4.py sample_log.txt 2

# Verify output format
python3 validate_output.py outputs.txt
```

### Step 2: Run Performance Tests
```bash
# Test with different core counts
for cores in 1 2 4 8; do
    echo "Testing with $cores cores..."
    python3 AOS_Assignment4.py sample_log.txt $cores
    echo "Execution time:"
    head -4 outputs.txt | tail -1
done
```

### Step 3: Create Your Report
- Use `Report_Template.md` as a guide
- Fill in your performance data
- Create graphs (execution time vs cores, speedup vs cores)
- Write observations on scalability
- Export as Report.pdf

### Step 4: Prepare Submission
```bash
# Automated preparation
python3 prepare_submission.py YOUR_ROLL_NUMBER

# Or manually:
mkdir YOUR_ROLL_NUMBER_Assignment4
cp AOS_Assignment4.py README.md Report.pdf YOUR_ROLL_NUMBER_Assignment4/
zip -r YOUR_ROLL_NUMBER_Assignment4.zip YOUR_ROLL_NUMBER_Assignment4/
```

---

## 📋 Implementation Details

### Key Features of AOS_Assignment4.py

#### ✅ Q1: RAG Construction and Graph Metrics
- **Q1.1**: Parses log file and creates directed edges
  - WAIT events → Process → Resource edges
  - HOLD events → Resource → Process edges
- **Q1.2**: Reports:
  - Total unique Process nodes
  - Total unique Resource nodes  
  - Total unique directed edges

#### ✅ Q2: Cycle Detection (Deadlock Detection)
- **Q2.1**: MapReduce-based cycle detection algorithm
  - Path propagation approach
  - Maximum cycle length: 25 nodes
  - Measures and reports execution time
- **Q2.2**: Outputs detected cycles
  - Sorted by length first
  - Lexicographically sorted for same length
  - No duplicate final node in cycle output
- **Q2.3**: Lists all unique processes involved in deadlocks

#### ✅ Q3: Performance and Time-Series Analysis
- **Q3.1**: Deadlock formation timeline
  - Tracks when each cycle was fully formed
  - Reports frequency per day
- **Q3.2**: Scalability analysis support
  - Configurable core count via command line
  - Execution time measurement
- **Q3.3**: Observations (in your report)

#### ✅ Q4: Graph Structure Analysis
- Top 5 Resources with highest in-degree
- Top 5 Processes with highest out-degree
- Sorted by degree (descending), then by ID

### Output Format

The script writes to **outputs.txt** (overwrites each run):

```
99                                          # Q1.2a: Process count
49                                          # Q1.2b: Resource count
1638                                        # Q1.2c: Edge count
107.74                                      # Q2.1: Execution time (seconds)
5                                           # Q2.2: Cycle count
P102 R006 P159 R039 P143 R031              # Cycle 1 (sorted by length)
P105 R002 P156 R046 P145 R020              # Cycle 2
...                                         # More cycles
27                                          # Q2.3: Process count in deadlocks
P102 P104 P105 ... P199                    # Q2.3: Process list (alphabetical)
2025-11-02 2                               # Q3.1: Timeline (date count)
2025-11-04 1
2025-11-06 2
R032 72                                     # Q4: Top 5 resources (ID degree)
R024 72
R012 72
R036 72
R028 72
P154 22                                     # Q4: Top 5 processes (ID degree)
P158 22
P131 22
P139 22
P167 22
```

---

## 🔧 Technical Specifications

### Requirements (Pre-installed on cluster)
- Python: 3.10.12
- Apache Spark: 3.4.1
- Java: 11.0.27

### Command Line Usage

**Local Testing:**
```bash
python3 AOS_Assignment4.py <log_file_path> <num_cores>
```

**Cluster Execution (Final Evaluation):**
```bash
spark-submit AOS_Assignment4.py ../test_files/log_file_name num_cores
```

**Example:**
```bash
spark-submit AOS_Assignment4.py ../test_files/hpc_rag.log 4
```

---

## 📊 Performance Testing Protocol

### Data Collection
Run the script with different core counts:

```bash
# Collect data
echo "Cores,Time(s)" > performance.csv
for cores in 1 2 4 8 16; do
    python3 AOS_Assignment4.py ../test_files/hpc_rag.log $cores
    time=$(head -4 outputs.txt | tail -1)
    echo "$cores,$time" >> performance.csv
done
```

### Analysis
Calculate for your report:
- **Speedup**: S(n) = T(1) / T(n)
- **Efficiency**: E(n) = S(n) / n × 100%
- **Scalability**: Compare to ideal linear speedup

### Graphs to Create
1. **Execution Time vs Cores** (line graph)
2. **Speedup vs Cores** (line graph with ideal linear line)
3. **Efficiency vs Cores** (bar chart)

---

## ✅ Validation Checklist

### Before Testing
- [ ] All required files present
- [ ] Python 3.10+ installed
- [ ] PySpark installed (if testing locally)
- [ ] Java 11 installed

### During Testing
- [ ] Script runs without errors
- [ ] outputs.txt is created
- [ ] Output format matches specification
- [ ] Validate with validate_output.py
- [ ] Test with multiple core counts

### Before Submission
- [ ] Run with actual test data
- [ ] Complete performance testing
- [ ] Create all graphs for report
- [ ] Fill out Report_Template.md → Report.pdf
- [ ] Update README.md with your info
- [ ] Verify submission structure
- [ ] **DO NOT include outputs.txt**
- [ ] Test spark-submit command format

---

## 🎯 Submission Structure (Mandatory)

```
YOUR_ROLL_NUMBER_Assignment4.zip
└── YOUR_ROLL_NUMBER_Assignment4/
    ├── AOS_Assignment4.py    ✓ Main script
    ├── Report.pdf            ✓ Performance analysis
    └── README.md             ✓ Documentation
```

**Important:** Do NOT include:
- outputs.txt (generated at runtime)
- requirements.txt (not needed)
- Test files or logs
- Python cache files
- IDE configuration

---

## 🐛 Troubleshooting

### Common Issues

**"FileNotFoundError: log file not found"**
```bash
# Use correct relative path
python3 AOS_Assignment4.py ../test_files/hpc_rag.log 4
```

**"Spark initialization error"**
```bash
# Check Spark is installed
python3 -c "import pyspark; print(pyspark.__version__)"
```

**"Output format validation failed"**
```bash
# Run validator to see specific issues
python3 validate_output.py outputs.txt
```

**"Wrong number of cycles detected"**
- Check log file format
- Verify edge creation logic
- Test with sample_log.txt first

---

## 📚 Additional Resources

### Files Description

| File | Purpose | When to Use |
|------|---------|-------------|
| AOS_Assignment4.py | Main implementation | Required in submission |
| README.md | Documentation | Required in submission |
| Report_Template.md | Report guide | Create Report.pdf from this |
| TESTING_GUIDE.md | Testing instructions | During development |
| validate_output.py | Format validator | After each test run |
| prepare_submission.py | Submission packager | Before final submission |
| sample_log.txt | Test data | For local testing |

### Useful Commands

```bash
# Quick validation
python3 validate_output.py

# Performance comparison
grep -A 0 "^[0-9]*\.[0-9]*$" outputs.txt

# Count cycles
head -5 outputs.txt | tail -1

# View timeline
grep "^2025-" outputs.txt
```

---

## 💡 Tips for Success

### Code Quality
1. Script accepts command line arguments (no hardcoded paths)
2. Opens outputs.txt in write mode ('w') to overwrite
3. Outputs match exact format specification
4. Handles edge cases (empty graphs, no cycles, etc.)

### Performance Analysis
1. Run multiple times and average results
2. Test on the actual cluster (ada.iiit.ac.in)
3. Consider warm-up runs before measuring
4. Document any anomalies in observations

### Report Writing
1. Include all required graphs
2. Explain speedup trends clearly
3. Discuss Amdahl's Law implications
4. Provide actionable insights
5. Compare theoretical vs actual performance

---

## 📞 Support

### Getting Help
1. Read TESTING_GUIDE.md thoroughly
2. Validate output with validate_output.py
3. Check Spark and Python versions
4. Test with sample_log.txt first
5. Contact course staff if issues persist

### Common Questions

**Q: Can I use additional libraries?**
A: No, use only standard library and PySpark. The evaluation environment won't have additional packages.

**Q: Should outputs.txt be in submission?**
A: **NO!** It's generated when the script runs. Including it will violate submission guidelines.

**Q: How do I test spark-submit locally?**
A: If you have Spark installed: `spark-submit AOS_Assignment4.py sample_log.txt 2`

**Q: What if my log file has extra fields?**
A: The script should handle it. It only reads the first 5 fields per line.

---

## 🎓 Learning Objectives

By completing this assignment, you will:
- ✅ Understand MapReduce programming paradigm
- ✅ Implement distributed graph algorithms
- ✅ Analyze scalability and performance
- ✅ Work with PySpark RDD operations
- ✅ Detect cycles in directed graphs
- ✅ Interpret resource allocation patterns

---

## 📈 Expected Outcomes

After successful completion:
1. **Functional script** that passes all test cases
2. **Comprehensive report** with performance analysis
3. **Clear documentation** in README
4. **Understanding** of distributed deadlock detection
5. **Insights** on parallel algorithm scalability

---

## ⚠️ Important Reminders

1. **DO NOT hardcode paths** - use command line arguments
2. **DO NOT include outputs.txt** in submission
3. **DO write to outputs.txt** in write mode ('w')
4. **DO test with spark-submit** before submitting
5. **DO validate output format** with provided validator
6. **DO complete performance testing** with multiple cores
7. **DO follow exact submission structure** or risk zero marks

---

## 🏁 Final Steps

1. ✅ Test script with sample data
2. ✅ Validate output format
3. ✅ Run performance tests (1, 2, 4, 8 cores)
4. ✅ Create graphs and complete Report.pdf
5. ✅ Update README.md with your information
6. ✅ Run prepare_submission.py
7. ✅ Verify zip file structure
8. ✅ Submit on time!

---

## 📄 License & Attribution

This implementation is for CS3.304 Advanced Operating Systems Assignment 4.
Created for educational purposes.

**Good luck with your assignment!**

---

*For the latest updates or clarifications, check the course announcement page or contact your instructor.*
