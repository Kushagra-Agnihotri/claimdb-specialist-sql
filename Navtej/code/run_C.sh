#!/bin/bash
# Condition C runner: judge SLM + Arctic NL2SQL builder, both served by Ollama.
# Results go to results/<name>/<claimset>/results.jsonl. Runs passes until every claim is done,
# resumes after crashes, and kills a pass that writes nothing for --stall-min minutes.
#
#   ./run_C.sh --model ministral-3:3b --name ministral-3b
#   ./run_C.sh --model ministral-3:8b --name ministral-8b --claims subsets/subset_1000.jsonl
set -u
CODE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$CODE_DIR")"

MODEL=""
NAME=""
BUILDER="a-kore/Arctic-Text2SQL-R1-7B"
CLAIMS="subsets/subset_210.jsonl"
DB_ROOT="${BIRD_DB_ROOT:-$HOME/bird/dev_databases}"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434/v1}"
RESULTS_ROOT="$REPO_DIR/results"
STALL_MIN=20
MAX_IDLE_PASSES=3
# errors that mean the server failed (not the model): these lines are dropped and retried
RETRY_ERRORS='status_code: (429|5[0-9][0-9])|Connection error|APIConnectionError|ConnectError|ReadTimeout'

usage() {
  cat <<EOF
Usage: $0 --model <ollama judge tag> [options]
  --model TAG          judge model, e.g. ministral-3:3b            (required)
  --name NAME          results folder name (default: tag with / and : replaced by _)
  --builder TAG        NL2SQL builder Ollama tag                   (default: $BUILDER)
  --claims FILE        claims .jsonl, relative to code/ or absolute (default: $CLAIMS)
  --db-root DIR        BIRD dev_databases folder                   (default: \$BIRD_DB_ROOT or ~/bird/dev_databases)
  --ollama-url URL     Ollama OpenAI-compatible URL                (default: \$OLLAMA_URL or http://localhost:11434/v1)
  --results-root DIR   where results/<name>/<claimset>/ is created (default: <repo>/results)
  --stall-min N        kill a pass that writes nothing for N minutes (default: $STALL_MIN)
  --once               run a single pass only (no retry loop)
EOF
  exit 1
}

ONCE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    --builder) BUILDER="$2"; shift 2 ;;
    --claims) CLAIMS="$2"; shift 2 ;;
    --db-root) DB_ROOT="$2"; shift 2 ;;
    --ollama-url) OLLAMA_URL="$2"; shift 2 ;;
    --results-root) RESULTS_ROOT="$2"; shift 2 ;;
    --stall-min) STALL_MIN="$2"; shift 2 ;;
    --once) ONCE=1; shift ;;
    -h|--help) usage ;;
    *) echo "unknown option: $1"; usage ;;
  esac
done
[ -z "$MODEL" ] && usage

cd "$CODE_DIR" || exit 1
[ -f .venv/bin/activate ] && source .venv/bin/activate
[ -f "$CLAIMS" ] || { echo "claims file not found: $CLAIMS"; exit 1; }
[ -d "$DB_ROOT" ] || { echo "BIRD db root not found: $DB_ROOT"; exit 1; }

[ -z "$NAME" ] && NAME="$(echo "$MODEL" | tr '/:' '__')"
CLAIMSET="$(basename "$CLAIMS" .jsonl)"
OUT_DIR="$RESULTS_ROOT/$NAME/$CLAIMSET"
OUT="$OUT_DIR/results.jsonl"
LOG="$OUT_DIR/run.log"
mkdir -p "$OUT_DIR/backups"
TOTAL=$(grep -c . "$CLAIMS")

log() { echo "$(date '+%Y-%m-%d %H:%M:%S %Z') | $*" | tee -a "$OUT_DIR/passes.log"; }
count() { [ -f "$OUT" ] && grep -c . "$OUT" || echo 0; }
mtime() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1"; }

# only one pass per output file at a time
if pgrep -f -- "--out $OUT" >/dev/null; then echo "a run is already writing to $OUT"; exit 1; fi

log "START model=$MODEL builder=$BUILDER claims=$CLAIMS ($TOTAL) out=$OUT lines=$(count)"
pass=0; idle=0
while :; do
  pass=$((pass+1)); before=$(count)
  log "pass $pass start, lines=$before"
  python -u run_judge.py --condition C --model "$MODEL" --builder "$BUILDER" \
    --claims "$CLAIMS" --db-root "$DB_ROOT" \
    --base-url "$OLLAMA_URL" --builder-url "$OLLAMA_URL" \
    --out "$OUT" >> "$LOG" 2>&1 &
  PID=$!
  # watchdog: kill the pass if neither the results nor the log change for STALL_MIN minutes
  while kill -0 $PID 2>/dev/null; do
    sleep 30
    last=$(mtime "$LOG"); [ -f "$OUT" ] && [ "$(mtime "$OUT")" -gt "$last" ] && last=$(mtime "$OUT")
    if [ $(( $(date +%s) - last )) -gt $((STALL_MIN*60)) ]; then
      log "pass $pass stalled for ${STALL_MIN} min, killing pid $PID"; kill $PID; sleep 5; kill -9 $PID 2>/dev/null
    fi
  done
  wait $PID 2>/dev/null
  if [ -f "$OUT" ]; then
    bak="$OUT_DIR/backups/results.$(date '+%Y%m%d_%H%M%S').pass$pass.jsonl"
    cp "$OUT" "$bak"
    nretry=$(grep -cE "$RETRY_ERRORS" "$bak")
    grep -vE "$RETRY_ERRORS" "$bak" > "$OUT"
  else
    nretry=0
  fi
  after=$(count)
  log "pass $pass end, dropped_for_retry=$nretry, lines=$after/$TOTAL, new=$((after-before))"
  [ "$after" -ge "$TOTAL" ] && { log "DONE: $after lines"; break; }
  [ "$ONCE" = 1 ] && { log "single pass requested, stopping"; break; }
  if [ "$after" -le "$before" ]; then idle=$((idle+1)); else idle=0; fi
  [ "$idle" -ge "$MAX_IDLE_PASSES" ] && { log "STOPPED: $MAX_IDLE_PASSES passes in a row with no new claims"; exit 2; }
  sleep 90
done
