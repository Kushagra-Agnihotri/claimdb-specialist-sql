"""Aggregate every results/*.jsonl run (any judge x condition x builder) into one comparison table --
the "Table 2" style multi-model view -- by reusing score.py's load()/macro_f1() so every number here
matches what `python score.py <file>` would print for that same file.

Recalibrated to add a `run_fail_rate` column: the fraction of claims where the WHOLE judge_one() call
failed (empty verdict + an error -- a 404 dead model, an exhausted quota, a crash), as opposed to the
model running fine but writing a bad SQL query (which score.py's existing tool_error_rate already
covers). That distinction is exactly what was missing to describe the last batch of result files: three
of five had run_fail_rate == 1.0 (every claim's underlying API call 404'd) and would otherwise have
looked, in a table of accuracy numbers alone, like "a model that's just bad at this" rather than "a
model tag that doesn't exist on this provider any more."

  python aggregate_results.py                                     # every run in results/
  python aggregate_results.py --glob "results/*__A.jsonl"         # just Condition A, e.g. the judge sweep
  python aggregate_results.py --glob "results/*__C__*.jsonl"      # just Condition C, e.g. the builder sweep
  python aggregate_results.py --csv table2.csv                    # also write a CSV for the report/slides
  python aggregate_results.py --verbose                           # plus score.py's full per-file summary()
"""
import argparse
import csv
import glob

from score import load, macro_f1, summary


def tool_call_stats(R):
    calls = [len(r.get("tool_log") or []) for r in R.values()]
    n = len(calls) or 1
    tool_logs = [t for r in R.values() for t in (r.get("tool_log") or [])]
    errs = sum(1 for t in tool_logs if t.get("error"))
    return {"calls_mean": sum(calls) / n, "zero_call": sum(c == 0 for c in calls) / n,
            "err_rate": errs / max(1, len(tool_logs))}


def row_for(path):
    R = load(path)
    if not R:
        return None
    pairs = [(r["label"], r["verdict"]) for r in R.values()]
    n = len(pairs)
    some = next(iter(R.values()))
    cs = tool_call_stats(R)
    run_fails = sum(1 for r in R.values() if not r.get("verdict") and r.get("error"))

    def recall(label):
        gold = [g for g, _ in pairs if g == label]
        return sum(g == label and p == label for g, p in pairs) / max(1, len(gold))

    row = {
        "model": some.get("model"), "condition": some.get("condition"), "builder": some.get("builder") or "",
        "n": n, "accuracy": round(sum(g == p for g, p in pairs) / n, 4), "macro_f1": round(macro_f1(pairs), 4),
        "recall_E": round(recall("ENTAILED"), 3), "recall_C": round(recall("CONTRADICTED"), 3),
        "recall_NEI": round(recall("NOT ENOUGH INFO"), 3),
        "run_fail_rate": round(run_fails / n, 3),
        "avg_tool_calls": round(cs["calls_mean"], 2), "zero_call_rate": round(cs["zero_call"], 3),
        "tool_error_rate": round(cs["err_rate"], 3),
        "mean_seconds": round(sum(r.get("seconds", 0) for r in R.values()) / n, 1),
        "file": path,
    }
    if run_fails:
        sample_err = next(r["error"] for r in R.values() if not r.get("verdict") and r.get("error"))
        row["_sample_error"] = sample_err[:160]
    return row


HEADERS = ["model", "condition", "builder", "n", "accuracy", "macro_f1", "recall_E", "recall_C",
           "recall_NEI", "run_fail_rate", "avg_tool_calls", "zero_call_rate", "tool_error_rate", "mean_seconds"]


def print_table(rows):
    widths = {h: max(len(h), max((len(str(r[h])) for r in rows), default=0)) for h in HEADERS}
    print(" | ".join(h.ljust(widths[h]) for h in HEADERS))
    print("-+-".join("-" * widths[h] for h in HEADERS))
    for r in rows:
        print(" | ".join(str(r[h]).ljust(widths[h]) for h in HEADERS))
        if r.get("run_fail_rate", 0) >= 0.5:
            flag = "ALL claims failed" if r["run_fail_rate"] == 1.0 else f"{r['run_fail_rate']:.0%} of claims failed"
            print(f"  ^^ {flag} the underlying model call (not a scoring result) -- sample error: "
                  f"{r.get('_sample_error', '(none captured)')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="results/*.jsonl")
    ap.add_argument("--csv", default=None)
    ap.add_argument("--verbose", action="store_true", help="also print score.py's full per-file summary()")
    a = ap.parse_args()

    files = sorted(glob.glob(a.glob))
    if not files:
        raise SystemExit(f"no files matched {a.glob!r}")
    rows = [r for r in (row_for(f) for f in files) if r]
    rows.sort(key=lambda r: (r["condition"], r["model"], r["builder"]))

    print_table(rows)

    dead = [r for r in rows if r["run_fail_rate"] == 1.0]
    if dead:
        print(f"\n{len(dead)}/{len(rows)} result file(s) are 100% run failures (every claim's model call "
              f"errored) -- these are not real accuracy numbers, exclude them from any report table:")
        for r in dead:
            print(f"  {r['file']}  ({r['model']})")

    if a.verbose:
        for r in rows:
            summary(r["file"], load(r["file"]))

    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=HEADERS)
            w.writeheader()
            for r in rows:
                w.writerow({h: r[h] for h in HEADERS})
        print(f"\nwrote {a.csv}")
