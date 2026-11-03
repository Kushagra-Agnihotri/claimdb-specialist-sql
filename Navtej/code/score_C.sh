#!/bin/bash
# Score Condition C results without hardcoding paths: finds results/<name>/<claimset>/results.jsonl,
# runs score.py on it and saves score.txt next to it.
#
#   ./score_C.sh --name ministral-3b                      (claimset defaults to subset_210)
#   ./score_C.sh --name ministral-8b --claims subsets/subset_1000.jsonl
#   ./score_C.sh --all                                    (every results/*/*/results.jsonl)
#   add --claimdb-release ../qwen3_8b_release.jsonl for the per-claim ClaimDB comparison
set -u
CODE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$CODE_DIR")"
RESULTS_ROOT="$REPO_DIR/results"
NAME=""; MODEL=""; CLAIMS="subsets/subset_210.jsonl"; ALL=0; RELEASE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --claims) CLAIMS="$2"; shift 2 ;;
    --results-root) RESULTS_ROOT="$2"; shift 2 ;;
    --claimdb-release) RELEASE="$2"; shift 2 ;;
    --all) ALL=1; shift ;;
    *) echo "usage: $0 (--name NAME | --model TAG | --all) [--claims FILE] [--claimdb-release FILE] [--results-root DIR]"; exit 1 ;;
  esac
done

cd "$CODE_DIR" || exit 1
[ -f .venv/bin/activate ] && source .venv/bin/activate
EXTRA=(); [ -n "$RELEASE" ] && EXTRA=(--claimdb-release "$RELEASE")

score_one() {
  local f="$1"; local d; d="$(dirname "$f")"
  echo "== $d"
  python score.py "$f" ${EXTRA[@]+"${EXTRA[@]}"} 2>&1 | tee "$d/score.txt"
}

if [ "$ALL" = 1 ]; then
  found=0
  for f in "$RESULTS_ROOT"/*/*/results.jsonl; do [ -f "$f" ] && { score_one "$f"; found=1; }; done
  [ "$found" = 1 ] || { echo "no results found under $RESULTS_ROOT"; exit 1; }
else
  [ -z "$NAME" ] && [ -n "$MODEL" ] && NAME="$(echo "$MODEL" | tr '/:' '__')"
  [ -z "$NAME" ] && { echo "give --name, --model or --all"; exit 1; }
  f="$RESULTS_ROOT/$NAME/$(basename "$CLAIMS" .jsonl)/results.jsonl"
  [ -f "$f" ] || { echo "not found: $f"; exit 1; }
  score_one "$f"
fi
