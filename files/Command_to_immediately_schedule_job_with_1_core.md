# 1 core, smaller mem/time (easier to schedule)
sbatch --cpus-per-task=1 --mem=4G --time=00:05:00 aos_runner.sh
