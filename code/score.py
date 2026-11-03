"""Score result files. Optionally compare two runs on the same claims (McNemar) and
check agreement with ClaimDB's released transcript for the same model.

  python score.py results\\qwen3_8b__A.jsonl results\\qwen3_8b__B.jsonl
  python score.py results\\qwen3_8b__A.jsonl --claimdb-release path\\to\\qwen3_8b.jsonl
"""
import argparse, json, math, random, collections
LABS = ["ENTAILED", "CONTRADICTED", "NOT ENOUGH INFO"]

def load(p):
    return {r["claim_id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}

def macro_f1(pairs):
    s = 0
    for L in LABS:
        tp = sum(g == L and p == L for g, p in pairs); fp = sum(g != L and p == L for g, p in pairs)
        fn = sum(g == L and p != L for g, p in pairs)
        pr = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
        s += 2 * pr * rc / (pr + rc) if pr + rc else 0
    return s / 3

def boot_ci(pairs, fn, B=2000, seed=0):
    rnd = random.Random(seed); vals = sorted(fn([rnd.choice(pairs) for _ in pairs]) for _ in range(B))
    return vals[int(0.025 * B)], vals[int(0.975 * B)]

def calls(r):
    return len(r.get("tool_log") or [])

def errtype(e):
    e = (e or "").lower()
    if not e: return None
    for k in ("no such table", "no such column", "syntax error", "timed out"):
        if k in e: return k
    return "other"

def summary(name, R):
    pairs = [(r["label"], r["verdict"]) for r in R.values()]
    n = len(pairs); acc = lambda ps: sum(g == p for g, p in ps) / len(ps)
    lo, hi = boot_ci(pairs, acc)
    tl = [t for r in R.values() for t in (r.get("tool_log") or [])]
    et = collections.Counter(errtype(t.get("error")) for t in tl); et.pop(None, None)
    print(f"\n== {name}  (n={n})")
    print(f"accuracy {acc(pairs):.3f}  [95% CI {lo:.3f}-{hi:.3f}]   macro-F1 {macro_f1(pairs):.3f}")
    print("recall: " + "  ".join(f"{L[:4]} {sum(g == L and p == L for g, p in pairs) / max(1, sum(g == L for g, _ in pairs)):.2f}" for L in LABS))
    print(f"predicted NOT ENOUGH INFO: {sum(p == 'NOT ENOUGH INFO' for _, p in pairs) / n:.2f} (gold {sum(g == 'NOT ENOUGH INFO' for g, _ in pairs) / n:.2f})"
          f"   failed runs (no verdict): {sum(not p for _, p in pairs)}")
    c = [calls(r) for r in R.values()]
    print(f"tool calls/claim: mean {sum(c) / n:.1f}  zero-call claims {sum(x == 0 for x in c) / n:.2f}  "
          f"4-8 calls {sum(4 <= x <= 8 for x in c) / n:.2f}   calls returning errors {sum(et.values()) / max(1, len(tl)):.2f} {dict(et)}")
    print(f"mean seconds/claim: {sum(r.get('seconds', 0) for r in R.values()) / n:.1f}")

def mcnemar(R1, R2):
    ids = sorted(set(R1) & set(R2))
    b = sum(R1[i]["verdict"] == R1[i]["label"] and R2[i]["verdict"] != R2[i]["label"] for i in ids)
    c = sum(R1[i]["verdict"] != R1[i]["label"] and R2[i]["verdict"] == R2[i]["label"] for i in ids)
    # exact two-sided binomial test
    n = b + c; k = min(b, c)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return len(ids), b, c, p

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--claimdb-release")
    a = ap.parse_args()
    runs = [(f, load(f)) for f in a.files]
    for f, R in runs: summary(f, R)
    for i in range(1, len(runs)):
        n, b, c, p = mcnemar(runs[0][1], runs[i][1])
        print(f"\nMcNemar {runs[0][0]} vs {runs[i][0]}: {n} shared claims, only-first-correct {b}, only-second-correct {c}, p={p:.4f}")
    if a.claimdb_release:
        rel = {r["claim_id"]: r for r in (json.loads(l) for l in open(a.claimdb_release, encoding="utf-8"))}
        R = runs[0][1]; ids = [i for i in R if i in rel]
        agree = sum(R[i]["verdict"] == rel[i].get("verdict") for i in ids) / max(1, len(ids))
        ra = sum(rel[i].get("verdict") == R[i]["label"] for i in ids) / max(1, len(ids))
        print(f"\nReproduction check on {len(ids)} claims: per-claim verdict agreement with ClaimDB release {agree:.2f}; "
              f"release accuracy on these claims {ra:.3f} vs ours {sum(R[i]['verdict'] == R[i]['label'] for i in ids) / max(1, len(ids)):.3f}")
