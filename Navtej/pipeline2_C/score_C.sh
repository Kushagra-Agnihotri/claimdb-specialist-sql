#!/bin/bash
# Score Condition C results without hardcoding paths: finds results/<name>/<builder>/<claimset>/results.jsonl,
# runs score.py on it and saves score.txt next to it.
#
#   ./pipeline2_C/score_C.sh --name ministral-8b                      (builder defaults to Arctic, claimset to subset_210)
#   ./pipeline2_C/score_C.sh --name ministral-8b --builder omnisql-7b-tag --claims subsets/test-public.jsonl
#   ./pipeline2_C/score_C.sh --all                                    (every results/*/*/*/results.jsonl)
#   add --claimdb-release ../qwen3_8b_release.jsonl for the per-claim ClaimDB comparison
set -u
# everything is resolved from the Navtej/ folder (one level above this script)
NAVTEJ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RESULTS_BASE="$NAVTEJ_DIR/results"
NAME=""; MODEL=""; CLAIMS="subsets/subset_210.jsonl"; ALL=0; RELEASE=""
BUILDER="a-kore/Arctic-Text2SQL-R1-7B"; BUILDER_NAME=""
builder_name() { local b="${1##*/}"; echo "${b%%:*}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --builder) BUILDER="$2"; shift 2 ;;
    --builder-name) BUILDER_NAME="$2"; shift 2 ;;
    --claims) CLAIMS="$2"; shift 2 ;;
    --results-root) RESULTS_BASE="$2"; shift 2 ;;
    --claimdb-release) RELEASE="$2"; shift 2 ;;
    --all) ALL=1; shift ;;
    *) echo "usage: $0 (--name NAME | --model TAG | --all) [--builder TAG | --builder-name NAME] [--claims FILE] [--claimdb-release FILE] [--results-root DIR]"; exit 1 ;;
  esac
done

RESULTS_ROOT="$RESULTS_BASE/pipeline2_C"
cd "$NAVTEJ_DIR" || exit 1
[ -f .venv/bin/activate ] && source .venv/bin/activate
EXTRA=(); [ -n "$RELEASE" ] && EXTRA=(--claimdb-release "$RELEASE")

score_one() {
  local f="$1"; local d; d="$(dirname "$f")"
  echo "== $d"
  python core/score.py "$f" ${EXTRA[@]+"${EXTRA[@]}"} 2>&1 | tee "$d/score.txt"
}

if [ "$ALL" = 1 ]; then
  found=0
  for f in "$RESULTS_ROOT"/*/*/*/results.jsonl; do [ -f "$f" ] && { score_one "$f"; found=1; }; done
  [ "$found" = 1 ] || { echo "no results found under $RESULTS_ROOT"; exit 1; }
else
  [ -z "$NAME" ] && [ -n "$MODEL" ] && NAME="$(echo "$MODEL" | tr '/:' '__')"
  [ -z "$NAME" ] && { echo "give --name, --model or --all"; exit 1; }
  [ -z "$BUILDER_NAME" ] && BUILDER_NAME="$(builder_name "$BUILDER")"
  f="$RESULTS_ROOT/$NAME/$BUILDER_NAME/$(basename "$CLAIMS" .jsonl)/results.jsonl"
  [ -f "$f" ] || { echo "not found: $f"; exit 1; }
  score_one "$f"
fi
