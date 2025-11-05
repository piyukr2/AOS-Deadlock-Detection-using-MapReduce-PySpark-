#!/bin/bash
#SBATCH --job-name=setup_pyspark_env
#SBATCH --partition=u22
#SBATCH --time=00:10:00
#SBATCH --mem=8G
#SBATCH --ntasks=1
#SBATCH --output=setup_pyspark_env.%j.out
#SBATCH --error=setup_pyspark_env.%j.err

set -euo pipefail

echo "=== PySpark environment setup starting ==="
python3 --version || { echo "Python3 not found"; exit 1; }

VENV_DIR="/home/cs3304.085/pyspark_env"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating venv at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
else
  echo "Using existing venv at $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m ensurepip --upgrade
python -m pip install --upgrade pip
# Match assignment Spark version
python -m pip install "pyspark==3.4.1"

echo "=== Versions ==="
python -V
python -c "import pyspark; print('PySpark:', pyspark.__version__)"
echo "=== Setup complete ==="
echo "=== Binaries in venv ==="
which python || true
which pip || true
which spark-submit || true

echo "=== Versions ==="
python -V
python -c "import pyspark; print('PySpark:', pyspark.__version__)"
echo "=== Setup complete ==="
