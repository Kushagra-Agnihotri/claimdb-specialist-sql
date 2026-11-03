#!/bin/bash
# One-time setup to run on the Sharanga LOGIN node (ssh kudhru@hpc.bits-hyderabad.ac.in).
# Everything here needs internet, which login nodes on most HPC clusters have and compute nodes often
# don't -- so every network-dependent step (venv/pip install, Ollama install, model pulls) happens here,
# once, and the actual GPU job (sharanga_job.sbatch) only ever reads what this script already cached.
#
# Usage:
#   scp sharanga_setup.sh kudhru@hpc.bits-hyderabad.ac.in:~/
#   ssh kudhru@hpc.bits-hyderabad.ac.in
#   bash sharanga_setup.sh
#
# Per the storage FAQ/login banner: $HOME is a 40GB quota (backed up); $SCRATCH is unlimited but wiped
# 30 days after last modification (not backed up -- the docs page said 15 days, but the live login
# banner says 30 under a "revised policy", so trust whatever the banner says when you read this).
# Model weights and venvs are large and not precious -> $SCRATCH.
# Your actual code/results are small and you want them safe -> keep copying them back to your own
# machine regularly; don't treat $SCRATCH as permanent storage for anything that matters.
set -euo pipefail

# $SCRATCH is confirmed to be /scratch/kudhru on this account, but it's set as a plain (non-exported)
# shell variable there, not an environment variable -- `env | grep scratch` doesn't show it, so a child
# process (this script, or later a SLURM job) won't see it even though `echo $SCRATCH` does in your
# interactive shell. Falling back to the known concrete path avoids depending on export at all; do the
# same permanently with `echo 'export SCRATCH=/scratch/kudhru' >> ~/.bashrc` so sbatch jobs see it too.
PROJECT_DIR="${SCRATCH:-/scratch/$USER}/kushagra_claimdb"
mkdir -p "$PROJECT_DIR"/{code,data,venv,ollama,results}
cd "$PROJECT_DIR"

echo "=== 1. Python venv (in \$SCRATCH, not \$HOME) ==="
python3 -m venv "$PROJECT_DIR/venv"
source "$PROJECT_DIR/venv/bin/activate"
pip install --upgrade pip
pip install pydantic pydantic-ai openai
# add torch/transformers here too ONLY if you plan to use builder.py's backend="hf" path
# (the FINER-SQL/SLM-SQL entries in sweep_builders.py) -- it's a large install, skip it if unused:
#   pip install torch transformers --index-url https://download.pytorch.org/whl/cu118

echo "=== 2. Code + data ==="
echo "Put common.py run_judge.py builder.py score.py sweep_lib.py sweep_judges.py sweep_builders.py"
echo "sweep_arctic.py aggregate_results.py providers.py check_providers.py into: $PROJECT_DIR/code/"
echo "Put subset_*.jsonl and the BIRD dev_databases/ folder into:                $PROJECT_DIR/data/"
echo "(scp/rsync from your machine, or git clone, from THIS login node -- not from inside the GPU job)"

echo "=== 3. Ollama, no root needed ==="
cd "$PROJECT_DIR"
# Ollama's real Linux package is .tar.zst (zstd), not .tgz -- per docs.ollama.com/linux. `-f` makes curl
# itself fail on a bad URL (HTTP 4xx/5xx) instead of silently saving the error page's text as "ollama.zst"
# and only discovering the problem when tar chokes on it later, which is what happened with the old .tgz
# URL (curl "succeeded", tar got 9 bytes of "Not Found").
curl -fL https://ollama.com/download/ollama-linux-amd64.tar.zst -o ollama.tar.zst
if tar --help 2>&1 | grep -q zstd; then
    tar --zstd -xf ollama.tar.zst -C "$PROJECT_DIR/ollama"
elif command -v zstd > /dev/null; then
    zstd -dc ollama.tar.zst | tar -x -C "$PROJECT_DIR/ollama"
else
    echo "ERROR: neither GNU tar's built-in zstd support nor a standalone 'zstd' binary is available." >&2
    echo "Check 'module avail' for a zstd module, or ask the HPC team; can't extract .tar.zst without one." >&2
    exit 1
fi
rm ollama.tar.zst
export PATH="$PROJECT_DIR/ollama/bin:$PATH"
export OLLAMA_MODELS="$PROJECT_DIR/ollama/models"   # keep weights in $SCRATCH, not the 40GB $HOME quota
mkdir -p "$OLLAMA_MODELS"

# Sanity-check the extraction actually produced a working binary, rather than assuming success because
# the commands above returned 0 -- exactly the assumption that let the bad .tgz URL get this far before.
if ! "$PROJECT_DIR/ollama/bin/ollama" --version > /dev/null 2>&1; then
    echo "ERROR: extracted, but '$PROJECT_DIR/ollama/bin/ollama --version' doesn't run. Extraction likely" >&2
    echo "produced the wrong layout -- run 'find $PROJECT_DIR/ollama -maxdepth 2' and check by hand." >&2
    exit 1
fi
echo "Ollama OK: $("$PROJECT_DIR/ollama/bin/ollama" --version)"

echo "=== 4. Start Ollama once, here on the login node, just to pull weights ==="
echo "(pulling is a download, not inference -- it doesn't need a GPU, so the login node is fine for this)"
"$PROJECT_DIR/ollama/bin/ollama" serve > "$PROJECT_DIR/ollama_pull.log" 2>&1 &
OLLAMA_PULL_PID=$!
sleep 5

for m in qwen3:4b qwen3:8b qwen3:14b mistral-nemo:12b mistral:7b llama3.2:3b llama3.1:8b; do
    echo "pulling $m ..."
    "$PROJECT_DIR/ollama/bin/ollama" pull "$m"
done
# if you're using the Arctic builder from an Ollama/GGUF mirror, pull it too, e.g.:
#   ollama pull hf.co/mradermacher/Arctic-Text2SQL-R1-7B-GGUF:Q4_K_M

kill "$OLLAMA_PULL_PID"

echo
echo "=== Done. Everything the GPU job needs is now cached in $PROJECT_DIR ==="
echo "Next: submit sharanga_job.sbatch (one per judge model) from this same login node."
