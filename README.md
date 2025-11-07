# MapReduce Deadlock Detection - ADA Cluster Guide

##  Setup on ADA Cluster

### Step 1: Login to ADA Cluster
```bash
ssh cs3304.085@ada.iiit.ac.in
# Enter the password when prompted
```

### Step 2: Upload Your Files
```bash
# From our local machine, we upload files to ADA
scp AOS_Assignment4.py cs3304.085@ada.iiit.ac.in:~/
scp pyspark_runner.sh cs3304.085@ada.iiit.ac.in:~/
scp aos_runner.sh cs3304.085@ada.iiit.ac.in:~/
```

### Step 3: Setup PySpark Environment (One-Time Setup)
```bash
# Make the setup script executable
chmod +x pyspark_runner.sh

# Submit the setup job
sbatch pyspark_runner.sh

# Wait for completion (check status)
squeue -u cs3304.085

# Verify setup was successful
cat setup_pyspark_env.*.out
```

This creates a virtual environment at `~/pyspark_env` with PySpark installed.

---

## Running the Program

### Method 1: Using SLURM Job Script 

**Edit `aos_runner.sh` before running:**
```bash
# Open the script
nano aos_runner.sh

# Update these lines with your details:
VENV_DIR="/home/cs3304.085/pyspark_env"  # Our username
LOG="/home/cs3304.085/test_files/sample_hpc_rag.log"  # Our log file path
```

**Submit the job:**
```bash
# Make script executable
chmod +x aos_runner.sh

# Submit job with desired number of cores
sbatch --cpus-per-task=1 aos_runner.sh   # For 1 core
sbatch --cpus-per-task=2 aos_runner.sh   # For 2 cores
sbatch --cpus-per-task=4 aos_runner.sh   # For 4 cores
sbatch --cpus-per-task=8 aos_runner.sh   # For 8 cores
```

**Check job status and output:**
```bash
# Check if job is running
squeue -u cs3304.085

# View output when complete
cat aos4.*.out

# Check for errors (if any)
cat aos4.*.err
```

### Method 2: Direct Execution (For Testing)

```bash
# Activate the virtual environment
source ~/pyspark_env/bin/activate

# Run directly using spark-submit
spark-submit AOS_Assignment4.py ../test_files/log_file.log 4

# Or using python3 (for local testing)
python3 AOS_Assignment4.py ../test_files/log_file.log 4
```

---

## Testing with Different Dataset Sizes

### Prepare Your Test Files
```bash
# Create test_files directory
mkdir -p ~/test_files

# Upload your log files
scp small_size_log.log cs3304.085@ada.iiit.ac.in:~/test_files/
scp medium_size_log.log cs3304.085@ada.iiit.ac.in:~/test_files/
scp large_size_log.log cs3304.085@ada.iiit.ac.in:~/test_files/
```

### Run Performance Tests

**For 200 logs with different cores:**
```bash
sbatch --cpus-per-task=1 aos_runner.sh  # Update LOG path in script first
sbatch --cpus-per-task=2 aos_runner.sh
sbatch --cpus-per-task=4 aos_runner.sh
sbatch --cpus-per-task=8 aos_runner.sh
```

**For 5000 logs:**
```bash
# Edit aos_runner.sh to point to 5000-log file
nano aos_runner.sh
# Change: LOG="/home/cs3304.085/test_files/log_5000.log"

# Submit with different cores
sbatch --cpus-per-task=1 aos_runner.sh
sbatch --cpus-per-task=2 aos_runner.sh
# ... and so on
```

**Repeat for each dataset size:** 10K, 20K, 50K logs

### Downloading the output
```bash
# Download to local machine (from your local terminal)
scp cs3304.085@ada.iiit.ac.in:/home/cs3304.085/pyspark_runner.sh ~/Downloads/
# you can replace ~/Downloads/ with absolute path of destination folder in local system
```
---

## Output Location

The program writes output to:
```
outputs.txt  # In the same directory where we ran the program
```

To view results:
```bash
cat outputs.txt
```

---

## Quick Reference Commands

```bash
# Check running jobs
squeue -u cs3304.085

# Cancel a job
scancel <job_id>


---

## Troubleshooting

**Issue: "Virtual environment not found"**
```bash
# Re-run the setup
sbatch pyspark_runner.sh
```

**Issue: "Permission denied"**
```bash
# Make scripts executable
chmod +x *.sh
```

**Issue: "spark-submit not found"**
```bash
# Check if virtual environment is activated
source ~/pyspark_env/bin/activate
which spark-submit  # Should point to ~/pyspark_env/bin/spark-submit
```

**Issue: Job fails immediately**
```bash
# Check error log
cat aos4.*.err

# Verify log file exists
ls -lh ~/test_files/
```

---

## Environment Details

The ADA cluster setup includes:
- **Python:** 3.10.12
- **Apache Spark:** 3.4.1  
- **Java:** 11.0.27

**No additional installations needed** - everything is configured in the virtual environment.

---


