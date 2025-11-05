#!/bin/bash
#SBATCH --job-name=aos4
#SBATCH --partition=u22
#SBATCH --time=00:10:00
#SBATCH --mem=12G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --output=aos4.%j.out
#SBATCH --error=aos4.%j.err

set -euo pipefail

VENV_DIR="/home/cs3304.085/pyspark_env"
source "$VENV_DIR/bin/activate"

# Ensure Spark uses the venv's Python
export PYSPARK_PYTHON="$VENV_DIR/bin/python"
export PYSPARK_DRIVER_PYTHON="$VENV_DIR/bin/python"

# === set your log file here ===
LOG="/home/cs3304.085/test_files/sample_hpc_rag.log"
CORES="${SLURM_CPUS_PER_TASK:-4}"

echo "Running $VENV_DIR/bin/spark-submit on $LOG with $CORES cores"
"$VENV_DIR/bin/spark-submit" AOS_Assignment4.py "$LOG" "$CORES"

echo "Job finished. If your script writes outputs.txt, it will be in $(pwd)"
