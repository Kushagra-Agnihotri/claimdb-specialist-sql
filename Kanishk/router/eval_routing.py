"""Pathway #3, step 4: what each router does to verification accuracy and time.

Usage: python eval_routing.py            (cheap path = A, judge writes its own SQL; writes routing_results.md)
       python eval_routing.py --cheap S  (cheap path = S, simple path with the Python lookup tool; writes routing_results_S.md)

For every judge that has both an A run (judge writes its own SQL) and a C run (Arctic builder), on the claims
both runs share: route claims the router marks positive to A, the rest to C, and compare with
always-C, always-A, a random router sending the same share to A, and the perfect router (true label).
Writes router/routing_results.md and prints it.
"""
import argparse, csv, glob, json, math, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
BUILDER = "hf.co_mradermacher_Arctic-Text2SQL-R1-7B-GGUF_Q8_0"

def load(path):
    out = {}
    for l in open(path, encoding="utf-8"):
        try:
            r = json.loads(l); out[r["claim_id"]] = r
        except Exception:
            pass
    return out

def mcnemar(a, b):
    n = a + b
    return min(1.0, 2 * sum(math.comb(n, j) for j in range(min(a, b) + 1)) / 2 ** n) if n else 1.0

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cheap", default="A", choices=["A", "S"]); cheap = ap.parse_args().cheap
    labels = {json.loads(l)["claim_id"]: json.loads(l) for l in open(os.path.join(HERE, "labels.jsonl"), encoding="utf-8")}
    truth = {
        "complexity_strict": lambda r: r["simple_strict"] == 1,
        "complexity_loose": lambda r: r["simple_loose"] == 1,
        "answerability": lambda r: r["label"] == "NOT ENOUGH INFO",
    }
    what = {"A": "A (judge writes its own SQL)", "S": "S (simple path: judge + Python lookup tool)"}[cheap]
    lines = [f"# Routing results (pathway #3), cheap path = {cheap}", "",
             f"Positive = sent to {what}; negative = sent to C (Arctic builder). Seconds = mean judge time per claim.", ""]
    for afile in sorted(glob.glob(os.path.join(RES, f"*__{cheap}.jsonl"))):
        judge = os.path.basename(afile)[:-len(f"__{cheap}.jsonl")]
        cfile = os.path.join(RES, f"{judge}__C__{BUILDER}.jsonl")
        if not os.path.exists(cfile):
            continue
        A, C = load(afile), load(cfile)
        ids = [i for i in A if i in C and i in labels]
        n = len(ids)
        ok = lambda R, i: R[i]["verdict"] == R[i]["label"]
        accA, accC = sum(ok(A, i) for i in ids) / n, sum(ok(C, i) for i in ids) / n
        sec = lambda R, i: float(R[i].get("seconds") or 0)
        secA, secC = sum(sec(A, i) for i in ids) / n, sum(sec(C, i) for i in ids) / n
        lines += [f"## {judge} ({n} claims with both {cheap} and C)", "",
                  f"Always {cheap} {100 * accA:.1f} ({secA:.1f} s)  |  Always C {100 * accC:.1f} ({secC:.1f} s)  |  "
                  f"Perfect per-claim choice {100 * sum(ok(A, i) or ok(C, i) for i in ids) / n:.1f}", "",
                  f"| Router | Sent to {cheap} | Accuracy | vs always C | McNemar p vs C | Random router, same share | Seconds per claim |",
                  "|---|---|---|---|---|---|---|"]
        for task, tfun in truth.items():
            pos = [i for i in ids if tfun(labels[i])]
            ps = set(pos)
            acc = (sum(ok(A, i) for i in pos) + sum(ok(C, i) for i in ids if i not in ps)) / n
            s_ = sum(sec(A if i in ps else C, i) for i in ids) / n
            lines.append(f"| {task}, true label | {100 * len(pos) / n:.0f}% | {100 * acc:.1f} | {100 * (acc - accC):+.1f} | | | {s_:.1f} |")
            for pf in sorted(glob.glob(os.path.join(HERE, "preds", f"{task}__*.csv"))):
                model = os.path.basename(pf)[:-4].split("__")[1]
                pred = {int(r["claim_id"]): int(r["pred"]) for r in csv.DictReader(open(pf, encoding="utf-8"))}
                route = {i: (A if pred.get(i, 0) else C) for i in ids}
                acc = sum(ok(route[i], i) for i in ids) / n
                share = sum(pred.get(i, 0) for i in ids) / n
                b = sum(ok(route[i], i) and not ok(C, i) for i in ids)
                c = sum(ok(C, i) and not ok(route[i], i) for i in ids)
                rnd = random.Random(0); k = round(share * n); sims = []
                for _ in range(200):
                    s = set(rnd.sample(ids, k))
                    sims.append(sum(ok(A if i in s else C, i) for i in ids) / n)
                s_ = sum(sec(route[i], i) for i in ids) / n
                lines.append(f"| {task}, {model} | {100 * share:.0f}% | {100 * acc:.1f} | {100 * (acc - accC):+.1f} | "
                             f"{mcnemar(b, c):.2g} | {100 * sum(sims) / len(sims):.1f} | {s_:.1f} |")
        lines.append("")
    open(os.path.join(HERE, "routing_results.md" if cheap == "A" else f"routing_results_{cheap}.md"), "w",
         encoding="utf-8").write("\n".join(lines))
    print("\n".join(lines))

if __name__ == "__main__":
    main()
