#!/bin/bash
# SLURM GPU job for the ClaimDB / Small-Judge-Specialist-SQL sweep on Sharanga.
#
# Submit ONE of these PER JUDGE MODEL (and separately for the builder/Arctic sweeps) -- do not try to
# run the whole 7-model sweep in a single job. Sharanga caps any job at 24h (the GPU-FAQ page says jobs
# over that limit are auto-terminated by Slurm), and your own local run showed qwen3:8b taking
# 100-500+s/claim with thinking-mode reasoning traces -- 210 claims at that rate alone can exceed 24h,
# before counting 6 more models. Running per-model also means one model's failure doesn't cost you the
# whole night, and the resumability fix in sweep_lib.py (a claim only counts "done" if it actually
# succeeded) means a job that hits the wall and gets killed mid-model is simply safe to `sbatch` again --
# it continues from wherever it stopped instead of re-paying for finished claims.
#
# Usage (from the Sharanga LOGIN node, after running sharanga_setup.sh once):
#   sbatch sharanga_job.sbatch qwen3:8b A
#   sbatch sharanga_job.sbatch llama3.1:8b A
#   sbatch --test-only sharanga_job.sbatch qwen3:8b A      # preview scheduling without submitting
#
# $1 = judge model tag (must already be `ollama pull`-ed by sharanga_setup.sh)
# $2 = condition: A or B
#
# NOT verified against Sharanga's actual docs (the GPU-FAQ page didn't cover these): job status/cancel
# commands below (squeue/scancel) are standard SLURM and should work, but confirm on the WhatsApp group
# if unsure. Same for the exact `module load` line -- "cuda-11.0.2" is only what Sharanga's OWN example
# script showed, not guaranteed to still be the current module; run `module avail` first and adjust.

#SBATCH -p gpu
#SBATCH -N 1
#SBATCH -n 4
#SBATCH --mem 32G
#SBATCH -t 0-20:00
#SBATCH --job-name="claimdb_judge"
#SBATCH -o slurm.%j.out
#SBATCH -e slurm.%j.err
#SBATCH --gres=gpu:1
#SBATCH --mail-user=f20240718@pilani.bits-pilani.ac.in
#SBATCH --mail-type=ALL

set -euo pipefail

MODEL="${1:?usage: sbatch sharanga_job.sbatch <model_tag> <condition>}"
CONDITION="${2:?usage: sbatch sharanga_job.sbatch <model_tag> <condition>}"

# $SCRATCH on this account is a non-exported shell variable (confirmed: it's /scratch/kudhru, but
# absent from `env`), so a SLURM job -- which only inherits exported variables -- may not see it either.
# Fall back to the known concrete path rather than depending on export having been set permanently.
PROJECT_DIR="${SCRATCH:-/scratch/$USER}/kushagra_claimdb"
cd "$PROJECT_DIR/code"

# Run `module avail` once on the login node and replace this with whatever CUDA module actually exists
# today -- this exact name is only what Sharanga's own example script showed, it may be stale.
module load cuda-11.0.2 2>/dev/null || echo "WARNING: cuda module load failed/skipped -- check 'module avail' and edit this line"

source "$PROJECT_DIR/venv/bin/activate"

# --- start Ollama locally on this job's allocated GPU, reading the weights sharanga_setup.sh already
#     cached -- this step needs NO network, so it works even if this compute node has none.
export PATH="$PROJECT_DIR/ollama/bin:$PATH"
export OLLAMA_MODELS="$PROJECT_DIR/ollama/models"
# offset the port by job ID so two of your own jobs landing on the same physical node (if it has >1 GPU)
# don't collide on 127.0.0.1:11434
OLLAMA_PORT=$((11000 + SLURM_JOB_ID % 1000))
export OLLAMA_HOST="127.0.0.1:$OLLAMA_PORT"
nohup "$PROJECT_DIR/ollama/bin/ollama" serve > "$PROJECT_DIR/results/ollama.$SLURM_JOB_ID.log" 2>&1 &
OLLAMA_PID=$!

# wait for the server to actually be up rather than a fixed sleep guess
for i in $(seq 1 30); do
    curl -s "http://$OLLAMA_HOST/v1/models" > /dev/null 2>&1 && break
    sleep 2
done

echo "=== running judge=$MODEL condition=$CONDITION against http://$OLLAMA_HOST ==="
python run_judge.py \
    --claims "$PROJECT_DIR/data/subset_210.jsonl" \
    --db-root "$PROJECT_DIR/data/dev_databases" \
    --model "$MODEL" \
    --condition "$CONDITION" \
    --provider ollama \
    --base-url "http://$OLLAMA_HOST/v1" \
    --out "$PROJECT_DIR/results/$(echo "$MODEL" | tr '/:' '__')__${CONDITION}.jsonl"

kill "$OLLAMA_PID" 2>/dev/null || true
echo "=== done: $MODEL / $CONDITION. If Slurm killed this before finishing (hit the 20h wall), ==="
echo "=== just 'sbatch sharanga_job.sbatch $MODEL $CONDITION' again -- it resumes, not restarts. ==="
