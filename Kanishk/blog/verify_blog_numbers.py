"""Recompute every number in the blog (v3) from the raw result files and compare with what the blog says.

Run from the Kanishk folder:   python blog/verify_blog_numbers.py
Optional:                       python blog/verify_blog_numbers.py --db-root ../sqljudge/data/dev_databases/dev_databases
Only the Python standard library is needed. Each line prints OK or CHECK, the blog's number and the recomputed one.
"""
import argparse, collections, csv, gzip, json, math, os, random, sqlite3, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "results")
ARC = "hf.co_mradermacher_Arctic-Text2SQL-R1-7B-GGUF_Q8_0"
NEI, ENT, CON = "NOT ENOUGH INFO", "ENTAILED", "CONTRADICTED"
n_ok = n_check = 0


def load(name):
    with gzip.open(os.path.join(R, name + ".jsonl.gz"), "rt", encoding="utf-8") as f:
        rows = [json.loads(l) for l in f]
    return {str(r["claim_id"]): r for r in rows}


def jl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f]


def right(r):
    return r is not None and r.get("verdict") == r.get("label")


def acc(rows, ids=None):
    ids = list(rows) if ids is None else [i for i in ids if i in rows]
    return 100 * sum(right(rows[i]) for i in ids) / len(ids)


def mcnemar(a, b, ids):
    ids = [i for i in ids if i in a and i in b]
    only_b = sum(right(b[i]) and not right(a[i]) for i in ids)
    only_a = sum(right(a[i]) and not right(b[i]) for i in ids)
    n, k = only_a + only_b, min(only_a, only_b)
    p = min(1.0, 2 * sum(math.comb(n, j) for j in range(k + 1)) / 2 ** n) if n else 1.0
    return only_a, only_b, p


def check(what, blog, got, tol=0.05):
    """blog and got are numbers (or strings for exact match)."""
    global n_ok, n_check
    good = (abs(float(blog) - float(got)) <= tol) if isinstance(blog, (int, float)) else (str(blog) == str(got))
    n_ok += good; n_check += (not good)
    g = f"{got:.2f}" if isinstance(got, float) else str(got)
    print(f"  {'OK   ' if good else 'CHECK'}  {what:<70} blog {blog:<10} data {g}")


def pcheck(what, blog_rule, p):
    """blog_rule: 'sig' (p<0.05), 'ns' (p>=0.05), '<0.001', or a number like 0.70."""
    global n_ok, n_check
    if blog_rule == "sig": good = p < 0.05
    elif blog_rule == "ns": good = p >= 0.05
    elif blog_rule == "<0.001": good = p < 0.001
    else: good = abs(round(p, 2) - blog_rule) <= 0.011 or abs(round(p, 3) - blog_rule) <= 0.0011
    n_ok += good; n_check += (not good)
    print(f"  {'OK   ' if good else 'CHECK'}  {what:<70} blog p {blog_rule!s:<8} data p {p:.2g}")


def head(t):
    print("\n" + t)


ap = argparse.ArgumentParser(); ap.add_argument("--db-root", default=None); args = ap.parse_args()
test = {str(c["claim_id"]): c for c in jl(os.path.join(ROOT, "code", "subsets", "test-public.jsonl"))}
sub = [str(c["claim_id"]) for c in jl(os.path.join(ROOT, "code", "subsets", "subset_210.jsonl"))]
with gzip.open(os.path.join(ROOT, "router", "labels.jsonl.gz"), "rt", encoding="utf-8") as f:
    labels = [json.loads(l) for l in f]
lab = {str(x["claim_id"]): x for x in labels if x["split"] == "test"}
ALL = list(test)

# ------------------------------------------------------------------ data
head("DATA (How we tested, Router section, Next steps)")
lc = collections.Counter(c["label"] for c in test.values())
check("test claims", 1000, len(test)); check("ENTAILED", 333, lc[ENT]); check("CONTRADICTED", 331, lc[CON]); check("NEI", 336, lc[NEI])
check("databases in test set", 11, len({c["db_name"] for c in test.values()}))
sc = collections.Counter(test[i]["label"] for i in sub)
check("subset size", 210, len(sub)); check("subset claims per label (min)", 70, min(sc.values())); check("subset claims per label (max)", 70, max(sc.values()))
sp = collections.Counter(x["split"] for x in labels)
check("router training claims", 40652, sp["train"]); check("held out claims for threshold", 5834, sp["val"])
check("held out databases", 7, len({x["db_name"] for x in labels if x["split"] == "val"}))
check("labelled training claims (train + held out)", 46486, sp["train"] + sp["val"])
check("one table claims in training split", 8053, sum(x["simple_strict"] for x in labels if x["split"] == "train"))
check("one table claims in test set", 215, sum(x["simple_strict"] for x in lab.values()))
if args.db_root:
    tabs, rows = [], 0
    for db in sorted({c["db_name"] for c in test.values()}):
        con = sqlite3.connect(f"file:{os.path.join(args.db_root, db, db + '.sqlite')}?mode=ro", uri=True)
        ts = [t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        tabs.append(len(ts)); rows += sum(con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in ts); con.close()
    check("fewest tables in a test database", 3, min(tabs)); check("most tables in a test database", 13, max(tabs))
    check("total rows, millions (about 3.9)", 3.9, rows / 1e6, tol=0.05)
else:
    print("  SKIP   table and row counts (pass --db-root to check 3 to 13 tables and 3.9 million rows)")

# ------------------------------------------------------------------ RQ1
A8, C8, S8 = load("qwen3_8b__A"), load(f"qwen3_8b__C__{ARC}"), load("qwen3_8b__S")
head("RQ1 (Part 1, Qwen3 8B, 1,000 claims)")
check("setup A accuracy", 56.0, acc(A8)); check("setup C accuracy", 76.0, acc(C8)); check("gain", 20.0, acc(C8) - acc(A8))
oa, ob, p = mcnemar(A8, C8, ALL)
check("claims only C gets right", 283, ob); check("claims only A gets right", 83, oa); pcheck("A vs C", "<0.001", p)
rnd = random.Random(0); diffs = []
d = [(right(C8[i]) - right(A8[i])) for i in ALL]
for _ in range(10000):
    diffs.append(100 * sum(d[rnd.randrange(1000)] for _ in range(1000)) / 1000)
diffs.sort()
check("95% interval low (paired bootstrap, 10,000 resamples)", 16.4, diffs[249], tol=0.4)
check("95% interval high", 23.5, diffs[9749], tol=0.4)
gaps = []
for db in sorted({c["db_name"] for c in test.values()}):
    ids = [i for i in ALL if test[i]["db_name"] == db]; gaps.append(acc(C8, ids) - acc(A8, ids))
check("databases where C is ahead", 11, sum(g > 0 for g in gaps)); check("smallest per database gap", 8.9, min(gaps)); check("largest per database gap", 34.1, max(gaps))
def recall(rows, label): ids = [i for i in ALL if test[i]["label"] == label]; return acc(rows, ids)
check("recall ENTAILED, A", 31.5, recall(A8, ENT)); check("recall ENTAILED, C", 64.9, recall(C8, ENT))
check("recall CONTRADICTED, A", 39.3, recall(A8, CON)); check("recall CONTRADICTED, C", 80.1, recall(C8, CON))
check("recall NEI, A (The price of setup C)", 96.7, recall(A8, NEI)); check("recall NEI, C", 83.0, recall(C8, NEI))
ge = [i for i in ALL if any(("no such table" in str(t.get("error") or "") or "no such column" in str(t.get("error") or "")) for t in A8[i]["tool_log"])]
check("claims where A queried a missing table or column", 482, len(ge)); check("accuracy on those, A", 43.8, acc(A8, ge)); check("accuracy on those, C", 73.7, acc(C8, ge))
check("tool calls per claim, A", 2.7, statistics.mean(len(A8[i]["tool_log"]) for i in ALL), tol=0.05)
check("tool calls per claim, C (about 1)", 1.0, statistics.mean(len(C8[i]["tool_log"]) for i in ALL), tol=0.05)

# ------------------------------------------------------------------ RQ2
head("RQ2 (Figure 4, Table 1)")
for m, a_, c_ in [("qwen3_4b", 54.3, 68.3), ("qwen3_1.7b", 35.9, 54.7), ("llama3.1_8b", 35.7, 54.7), ("llama3.2_3b", 32.1, 45.2)]:
    A, C = load(f"{m}__A"), load(f"{m}__C__{ARC}")
    check(f"{m} setup A", a_, acc(A)); check(f"{m} setup C", c_, acc(C)); pcheck(f"{m} A vs C", "sig", mcnemar(A, C, ALL)[2])
C14 = load(f"qwen3_14b__C__{ARC}")
check("qwen3_14b setup C", 76.5, acc(C14)); pcheck("qwen3_14b vs qwen3_8b in C", 0.76, mcnemar(C8, C14, ALL)[2])
B8 = load("qwen3_8b__B"); V8 = load(f"qwen3_8b__C__{ARC}__vals3")
check("setup B on subset", 61.0, acc(B8, sub)); check("setup A on subset", 59.0, acc(A8, sub)); pcheck("B vs A", 0.70, mcnemar(A8, B8, sub)[2])
check("example values on subset", 78.1, acc(V8, sub)); check("setup C on subset", 74.3, acc(C8, sub)); pcheck("example values vs C", 0.23, mcnemar(C8, V8, sub)[2])
C4 = load(f"qwen3_4b__C__{ARC}")
for name, blog_v, blog_base, blog_p, base in [("qwen3_4b__C__hf.co_mradermacher_OmniSQL-7B-GGUF_Q8_0", 65.5, 68.3, 0.10, C4),
                                              ("llama3.1_8b__C__hf.co_mradermacher_OmniSQL-7B-GGUF_Q8_0", 54.0, 54.7, 0.73, load(f"llama3.1_8b__C__{ARC}"))]:
    X = load(name); check(f"OmniSQL: {name.split('__')[0]}", blog_v, acc(X)); check("   Arctic on same claims", blog_base, acc(base, list(X))); pcheck("   OmniSQL vs Arctic", blog_p, mcnemar(base, X, list(X))[2])
for name, n, blog_v, blog_base in [("qwen3_4b__C__cycloneboy_SLM-SQL-1.5B", 676, 54.1, 67.8), ("qwen3_4b__C__qwen2.5-coder_7b-instruct-q8_0", 63, 42.9, 77.8)]:
    X = load(name); check(f"{name.split('__')[2]} claims run", n, len(X)); check("   accuracy", blog_v, acc(X)); check("   Arctic on same claims", blog_base, acc(C4, list(X)))
    pcheck("   vs Arctic", "<0.001", mcnemar(C4, X, list(X))[2])
fa = sum(1 for i in sub for t in A8[i]["tool_log"] if t.get("error")); fb = sum(1 for i in sub for t in B8[i]["tool_log"] if t.get("error"))
check("failed queries on subset, A", 219, fa); check("failed queries on subset, B", 5, fb)
noq = [i for i in sub if not B8[i]["tool_log"]]
check("subset claims where B made no query", 121, len(noq)); check("   of those answered NEI", 121, sum(B8[i]["verdict"] == NEI for i in noq))

# ------------------------------------------------------------------ RQ3
head("RQ3 (setup S)")
check("setup S accuracy, Qwen3 8B, 1,000 claims", 61.8, acc(S8)); pcheck("S vs A", "<0.001", mcnemar(A8, S8, ALL)[2])
fig9 = {"qwen3_8b": (59.0, 59.0, 74.3), "qwen3_4b": (51.4, 62.4, 67.6), "qwen3_1.7b": (34.8, 36.2, 55.7), "llama3.1_8b": (39.0, 23.3, 53.3), "llama3.2_3b": (35.2, 15.2, 44.3)}
def noverdict(r): return r.get("error") not in (None, "", "None") or r.get("verdict") not in (ENT, CON, NEI)
for m, (a_, s_, c_) in fig9.items():
    A, S, C = load(f"{m}__A"), load(f"{m}__S"), load(f"{m}__C__{ARC}")
    check(f"{m} subset A / S / C", f"{a_}/{s_}/{c_}", f"{acc(A, sub):.1f}/{acc(S, sub):.1f}/{acc(C, sub):.1f}")
    nv = sum(noverdict(S[i]) for i in sub if i in S)
    if m == "llama3.1_8b": check("   claims with no verdict in S", 81, nv)
    elif m == "llama3.2_3b": check("   claims with no verdict in S", 104, nv)
    else: check("   claims with no verdict in S (blog: 0 to 2)", "0-2", "0-2" if nv <= 2 else nv)

# ------------------------------------------------------------------ routers
head("ROUTERS (Figure 8)")
met = json.load(open(os.path.join(ROOT, "router", "router_metrics.json")))
check("AUC unanswerable", 0.95, met["answerability__linear"]["test_auc"], tol=0.005)
check("AUC one table", 0.72, met["complexity_strict__linear"]["test_auc"], tol=0.005)
check("AUC two tables or fewer", 0.64, met["complexity_loose__linear"]["test_auc"], tol=0.005)
best = max(met[k]["test_auc"] for k in met if k.endswith("mlp2") or k.endswith("mlp3"))
for kind in ["answerability", "complexity_strict", "complexity_loose"]:
    lr = met[f"{kind}__linear"]["test_auc"]; nn = max(met[f"{kind}__mlp2"]["test_auc"], met[f"{kind}__mlp3"]["test_auc"])
    check(f"neural network within 0.01 AUC of LR or worse ({kind})", "yes", "yes" if nn <= lr + 0.01 else f"no ({nn} vs {lr})")
def preds(kind):
    with open(os.path.join(ROOT, "router", "preds", f"{kind}__linear.csv")) as f:
        return {str(r["claim_id"]): int(r["pred"]) for r in csv.DictReader(f)}
P_un, P_st, P_lo = preds("answerability"), preds("complexity_strict"), preds("complexity_loose")

# ------------------------------------------------------------------ RQ4
head("RQ4 (Figure 10, Table 2, NEI direct)")
routed = [i for i in ALL if P_un[i] == 1]
check("claims the unanswerable router sends to S", 340, len(routed))
tru = [i for i in routed if test[i]["label"] == NEI]; mis = [i for i in routed if test[i]["label"] != NEI]
check("   truly unanswerable", 282, len(tru)); check("   answerable, sent by mistake", 58, len(mis))
for nm, ids, s_, c_, rule in [("all routed", routed, 84.4, 82.9, "ns"), ("truly unanswerable", tru, 94.0, 85.1, "sig"), ("sent by mistake", mis, 37.9, 72.4, "sig")]:
    check(f"S on {nm}", s_, acc(S8, ids)); check(f"C on {nm}", c_, acc(C8, ids)); pcheck(f"   S vs C on {nm}", rule, mcnemar(C8, S8, ids)[2])
ts, tc = statistics.mean(S8[i]["seconds"] for i in routed), statistics.mean(C8[i]["seconds"] for i in routed)
check("seconds per claim on routed, S", 19.1, ts, tol=0.1); check("seconds per claim on routed, C", 27.8, tc, tol=0.1); check("S faster by %", 31, 100 * (1 - ts / tc), tol=1)
one = [i for i in ALL if lab[i]["simple_strict"] == 1]
check("S on 215 one table claims", 74.9, acc(S8, one)); check("C on 215 one table claims", 76.7, acc(C8, one)); pcheck("   S vs C", 0.64, mcnemar(C8, S8, one)[2])
s1, c1 = statistics.mean(S8[i]["seconds"] for i in one), statistics.mean(C8[i]["seconds"] for i in one)
check("S faster on one table claims, % (blog: about a third)", 33, 100 * (1 - s1 / c1), tol=5)
check("S seconds per claim, all 1,000", 27.2, statistics.mean(S8[i]["seconds"] for i in ALL), tol=0.1)
check("C seconds per claim, all 1,000", 29.0, statistics.mean(C8[i]["seconds"] for i in ALL), tol=0.1)
sent_st = [i for i in sub if P_st[i] == 1]
check("subset claims the one table router sends to S", 75, len(sent_st)); check("   of those truly one table", 23, sum(lab[i]["simple_strict"] for i in sent_st)); check("one table claims in the subset", 41, sum(lab[i]["simple_strict"] for i in sub))
check("subset claims the two table router sends to S", 145, sum(P_lo[i] for i in sub)); check("subset claims the unanswerable router flags", 71, sum(P_un[i] for i in sub))
t2 = {"qwen3_8b": (74.3, 70.5, 61.9, 73.3, 73.3), "qwen3_4b": (67.6, 65.2, 60.0, 71.9, 71.9), "qwen3_1.7b": (55.7, 50.0, 44.3, 53.3, 53.3),
      "llama3.1_8b": (53.3, 40.5, 34.8, 47.6, 59.0), "llama3.2_3b": (44.3, 33.8, 22.9, 34.8, 53.8)}
for m, exp in t2.items():
    S, C = load(f"{m}__S"), load(f"{m}__C__{ARC}")
    def mix(P): return 100 * sum(right(S[i] if P[i] else C[i]) for i in sub) / len(sub)
    nei = 100 * sum((test[i]["label"] == NEI) if P_un[i] else right(C[i]) for i in sub) / len(sub)
    got = (acc(C, sub), mix(P_st), mix(P_lo), mix(P_un), nei)
    check(f"Table 2 row {m}", "/".join(f"{x:.1f}" for x in exp), "/".join(f"{x:.1f}" for x in got))
C32 = load(f"llama3.2_3b__C__{ARC}")
pv = mcnemar(C32, {i: dict(C32[i], verdict=NEI) if P_un[i] else C32[i] for i in sub}, sub)[2]
pcheck("llama3.2_3b NEI direct vs always C (blog p = 0.002)", 0.002, pv)
for m, before, after in [("qwen3_4b", 68.3, 72.1), ("llama3.1_8b", None, None), ("llama3.2_3b", None, None)]:
    C = load(f"{m}__C__{ARC}"); base = acc(C); new = 100 * sum((test[i]["label"] == NEI) if P_un[i] else right(C[i]) for i in ALL) / 1000
    if before: check(f"NEI direct on 1,000: {m} before", before, base); check(f"   after", after, new)
    else: print(f"  INFO   NEI direct on 1,000: {m} gains {new - base:.1f} points (blog says the two Llama judges gain 8 and 11)")

# ------------------------------------------------------------------ S failures
head("WHY S FAILS ON ONE TABLE CLAIMS (Figure 11)")
wrong = [i for i in one if not right(S8[i])]
check("wrong one table claims", 54, len(wrong))
cat = collections.Counter()
for i in wrong:
    r = S8[i]; looks = [t for t in r["tool_log"] if t.get("tool") == "lookup"]
    if not looks: cat["never looked anything up"] += 1; cat["   of those, still answered NEI"] += (r["verdict"] == NEI)
    elif r["verdict"] in (ENT, CON): cat["fetched data, wrong call"] += 1
    elif all(t.get("error") for t in looks): cat["errors or no verdict"] += 1
    elif all(not t.get("n_match") for t in looks): cat["got 0 rows, gave up"] += 1
    else: cat["got rows, still said NEI"] += 1
for k, v in [("fetched data, wrong call", 30), ("never looked anything up", 9), ("   of those, still answered NEI", 8), ("got 0 rows, gave up", 8), ("got rows, still said NEI", 5), ("errors or no verdict", 2)]:
    check(k, v, cat[k])

# ------------------------------------------------------------------ examples in the figures
head("EXAMPLES SHOWN IN FIGURES 2, 6 AND 7 (read these by eye)")
def show(tag, rows, cid):
    r = rows[cid]; print(f"  [{tag}] claim {cid}: verdict {r['verdict']} (gold {r['label']}), {r['seconds']} s, {len(r['tool_log'])} calls")
    for t in r["tool_log"]:
        print("      ", (t.get("sql") or json.dumps(t.get("args")) or "")[:150], "| error:", t.get("error"), "| rows:", t.get("n_match", t.get("n_rows")))
show("A", A8, "5584"); show("C", C8, "5584"); show("S", S8, "1005"); show("C", C8, "1005")
print("  claim 2687 text:", test["2687"]["claim"]); show("S", S8, "2687")

print(f"\n{n_ok} OK, {n_check} CHECK")
print("Not recomputable from this repo (taken from docs/claimdb-setup-and-baseline-analysis.md and the ClaimDB paper):")
print("  20.8% vs 43.8% and r = -0.88 (ClaimDB released runs), ClaimDB's own model scores (52.1, 74.0, 78.7, ...), Arctic's 68.9% on BIRD dev.")
