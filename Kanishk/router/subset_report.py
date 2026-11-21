"""Sir's 15 Nov checks on a fixed claim subset (default: code/subsets/subset_210.jsonl, 70 per label, seed 13).

For every judge that has A, C (Arctic) and S results, restricted to subset claims present in all three:
  1. Accuracy, seconds and tool calls per claim for A, S and C  (point 6: NL2SQL vs SQL writing, x n calls)
  2. S vs C on the claims the non-answerable router sends to S  (point 4: are the routed claims comparable?)
  3. S vs C on one table claims (strict router, and true strict label)
  4. End to end routing on the subset: router yes -> S, else C; and "router yes -> answer NEI directly, else C"
Only existing result files are read; nothing is rerun. Writes router/subset_report_<subset>.md and prints it.

  python subset_report.py                         (subset_210)
  python subset_report.py --claims ..\\code\\subsets\\other.jsonl
"""
import argparse, csv, json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
ARC = "hf.co_mradermacher_Arctic-Text2SQL-R1-7B-GGUF_Q8_0"
NEI = "NOT ENOUGH INFO"


def load(path):
    out = {}
    if os.path.exists(path):
        for l in open(path, encoding="utf-8"):
            try:
                r = json.loads(l); out[r["claim_id"]] = r
            except Exception:
                pass
    return out


def preds(task):
    return {int(r["claim_id"]): int(r["pred"]) for r in csv.DictReader(open(os.path.join(HERE, "preds", f"{task}__linear.csv"), encoding="utf-8"))}


def mcnemar(b, c):
    n = b + c
    return min(1.0, 2 * sum(math.comb(n, j) for j in range(min(b, c) + 1)) / 2 ** n) if n else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", default=os.path.join(HERE, "..", "code", "subsets", "subset_210.jsonl"))
    a = ap.parse_args()
    sub = [json.loads(l) for l in open(a.claims, encoding="utf-8") if l.strip()]
    sub_ids = [c["claim_id"] for c in sub]
    name = os.path.basename(a.claims)[:-6]
    AN, ST = preds("answerability"), preds("complexity_strict")
    lab = {json.loads(l)["claim_id"]: json.loads(l) for l in open(os.path.join(HERE, "labels.jsonl"), encoding="utf-8")}
    ok = lambda R, i: R[i]["verdict"] == R[i]["label"]
    pct = lambda xs: f"{100 * sum(xs) / len(xs):.1f}" if xs else "n/a"
    L = [f"# Subset report: {name} ({len(sub_ids)} claims)", "",
         "Router = logistic regression on frozen embeddings (threshold tuned on held out databases). "
         "S = judge + Python lookup tool, C = judge + Arctic builder, A = judge writes SQL. p = exact McNemar.", ""]
    for af in sorted(f for f in os.listdir(RES) if f.endswith("__A.jsonl")):
        judge = af[:-len("__A.jsonl")]
        A, C, S = load(os.path.join(RES, af)), load(os.path.join(RES, f"{judge}__C__{ARC}.jsonl")), load(os.path.join(RES, f"{judge}__S.jsonl"))
        ids = [i for i in sub_ids if i in A and i in C and i in S]
        L.append(f"## {judge}: {len(ids)} of {len(sub_ids)} subset claims have A, S and C")
        if not ids:
            L += ["", "S not run on this subset yet.", ""]; continue
        sec = lambda R: f"{sum(float(R[i].get('seconds') or 0) for i in ids) / len(ids):.1f}"
        calls = lambda R: f"{sum(len(R[i].get('tool_log') or []) for i in ids) / len(ids):.2f}"
        L += ["", "| Setup | Accuracy | Seconds per claim | Tool calls per claim |", "|---|---|---|---|"]
        for nm, R in (("A (judge writes SQL)", A), ("S (Python lookup tool)", S), ("C (Arctic builder)", C)):
            L.append(f"| {nm} | {pct([ok(R, i) for i in ids])} | {sec(R)} | {calls(R)} |")
        L += ["", "| Claims (within the subset) | n | S | C | only S right / only C right | p | Seconds S / C |", "|---|---|---|---|---|---|---|"]
        groups = [("non-answerable router says yes", lambda i: AN[i] == 1),
                  ("  of which gold NEI", lambda i: AN[i] == 1 and lab[i]["label"] == NEI),
                  ("  of which gold ENTAILED or CONTRADICTED", lambda i: AN[i] == 1 and lab[i]["label"] != NEI),
                  ("strict router says simple", lambda i: ST[i] == 1),
                  ("truly one table (strict label)", lambda i: lab[i]["simple_strict"] == 1)]
        for gname, f in groups:
            g = [i for i in ids if f(i)]
            if not g:
                continue
            b = sum(ok(S, i) and not ok(C, i) for i in g); c = sum(ok(C, i) and not ok(S, i) for i in g)
            ss = sum(float(S[i].get("seconds") or 0) for i in g) / len(g); sc = sum(float(C[i].get("seconds") or 0) for i in g) / len(g)
            L.append(f"| {gname} | {len(g)} | {pct([ok(S, i) for i in g])} | {pct([ok(C, i) for i in g])} | {b} / {c} | {mcnemar(b, c):.2g} | {ss:.1f} / {sc:.1f} |")
        L += ["", "| Routing on the subset | Accuracy | p vs always C | Seconds per claim |", "|---|---|---|---|"]
        alwaysC = [ok(C, i) for i in ids]
        L.append(f"| always C | {pct(alwaysC)} | | {sec(C)} |")
        for rname, pick in (("non-answerable yes -> S, else C", lambda i: (S if AN[i] else C)),
                            ("strict simple yes -> S, else C", lambda i: (S if ST[i] else C))):
            res = [ok(pick(i), i) for i in ids]
            b = sum(r and not c for r, c in zip(res, alwaysC)); c = sum(c and not r for r, c in zip(res, alwaysC))
            s_ = sum(float(pick(i)[i].get("seconds") or 0) for i in ids) / len(ids)
            L.append(f"| {rname} | {pct(res)} | {mcnemar(b, c):.2g} | {s_:.1f} |")
        res = [(lab[i]["label"] == NEI) if AN[i] else ok(C, i) for i in ids]
        b = sum(r and not c for r, c in zip(res, alwaysC)); c = sum(c and not r for r, c in zip(res, alwaysC))
        s_ = sum(0 if AN[i] else float(C[i].get("seconds") or 0) for i in ids) / len(ids)
        L += [f"| non-answerable yes -> answer NEI directly (no judge), else C | {pct(res)} | {mcnemar(b, c):.2g} | {s_:.1f} |", ""]
    out = os.path.join(HERE, f"subset_report_{name}.md")
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
