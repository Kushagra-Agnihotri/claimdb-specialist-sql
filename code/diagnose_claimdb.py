"""Diagnostic analysis of ClaimDB's released public-test transcripts.
Usage: python -I diagnose_claimdb.py <claimdb_repo_dir> <runs_dir> <out_json>
Reads transcripts line by line (some files are ~1 GB)."""
import json, sys, re, pathlib, collections, math

repo, runs, out = map(pathlib.Path, sys.argv[1:4])
LABS = ["ENTAILED", "CONTRADICTED", "NOT ENOUGH INFO"]
SIZE = {"qwen3:1.7b":1.7,"qwen3:4b":4,"qwen3:8b":8,"qwen3:14b":14,"qwen3:32b":32,"qwen3-coder:30b":30,
        "ministral-3:3b":3,"ministral-3:8b":8,"ministral-3:14b":14,"llama3.2:1b":1,"llama3.2:3b":3,"llama3.1:8b":8,
        "mistral-nemo:12b":12,"gpt-oss:20b":20,"nemotron-3-nano:30b":30,"cogito:14b":14}

gold = {}
for l in open(repo/"final-benchmark/test-public.jsonl"):
    d = json.loads(l); gold[d["claim_id"]] = d
src = {}
for l in open(repo/"final-benchmark/BIRD-source.jsonl"):
    d = json.loads(l); src[d["bird_id"]] = d

def complexity(sql):
    s = sql.upper()
    joins = s.count(" JOIN ")
    agg = len(re.findall(r"\b(COUNT|SUM|AVG|MAX|MIN)\s*\(", s))
    return joins, agg

def calls_and_returns(r):
    calls, rets = [], []
    for m in r.get("all_messages") or []:
        for p in m.get("parts", []):
            if p.get("tool_name") == "final_result": continue
            if p.get("part_kind") == "tool-call": calls.append(str(p.get("args")))
            elif p.get("part_kind") == "tool-return": rets.append(str(p.get("content")))
            elif p.get("part_kind") == "retry-prompt" and p.get("tool_name") not in (None, "final_result"):
                rets.append("error: " + str(p.get("content"))[:300])
    for m in r.get("to_input_list") or []:
        if m.get("type") == "function_call": calls.append(str(m.get("arguments")))
        elif m.get("type") == "function_call_output": rets.append(str(m.get("output")))
    return calls, rets

def err_type(ret):
    low = ret[:400].lower()
    if "no such table" in low: return "no_such_table"
    if "no such column" in low: return "no_such_column"
    if "syntax error" in low or "unrecognized token" in low or "incomplete input" in low: return "syntax"
    if "timeout" in low or "interrupted" in low: return "timeout"
    if "error" in low[:120] or "no such function" in low: return "other_error"
    return None

def is_schema(call):
    c = call.lower()
    return ("sqlite_master" in c or "pragma" in c or "information_schema" in c or "sqlite_schema" in c)

def macro_f1(pairs):
    s = 0
    for L in LABS:
        tp = sum(g == L and p == L for g, p in pairs); fp = sum(g != L and p == L for g, p in pairs); fn = sum(g == L and p != L for g, p in pairs)
        pr = tp/(tp+fp) if tp+fp else 0; rc = tp/(tp+fn) if tp+fn else 0
        s += 2*pr*rc/(pr+rc) if pr+rc else 0
    return s/3

results = {}
for path in sorted(runs.glob("*.jsonl")):
    model = path.stem
    recs = []
    with open(path) as f:
        for line in f:
            try: r = json.loads(line)
            except Exception: continue
            cid = r.get("claim_id")
            if cid not in gold: continue
            calls, rets = calls_and_returns(r)
            errs = [err_type(x) for x in rets]
            g = gold[cid]; s = src.get(g["bird_id"], {})
            j, a = complexity(s.get("SQL", ""))
            recs.append(dict(gold=g["label"], pred=(r.get("verdict") or ""), n=len(calls),
                             schema=sum(map(is_schema, calls)), errs=[e for e in errs if e],
                             last_ok=(errs[-1] is None) if errs else None,
                             difficulty=s.get("difficulty"), joins=j, aggs=a, category=g.get("category")))
    n = len(recs)
    if n < 900: print("skip", model, n); continue
    tot = sum(x["n"] for x in recs); E = collections.Counter(e for x in recs for e in x["errs"])
    ec = [x for x in recs if x["gold"] != "NOT ENOUGH INFO"]
    def grp(sub):
        return dict(n=len(sub), acc=(sum(x["gold"] == x["pred"] for x in sub)/len(sub)) if sub else None,
                    nei=(sum(x["pred"] == "NOT ENOUGH INFO" for x in sub)/len(sub)) if sub else None)
    ground = lambda x: any(e in ("no_such_table", "no_such_column") for e in x["errs"])
    res = dict(
        size_b=SIZE.get(model), n=n,
        acc=sum(x["gold"] == x["pred"] for x in recs)/n,
        macro_f1=macro_f1([(x["gold"], x["pred"]) for x in recs]),
        recall={L: sum(x["pred"] == L for x in recs if x["gold"] == L)/sum(x["gold"] == L for x in recs) for L in LABS},
        pred_nei=sum(x["pred"] == "NOT ENOUGH INFO" for x in recs)/n,
        no_verdict=sum(not x["pred"] for x in recs)/n,
        calls_mean=tot/n, zero_call=sum(x["n"] == 0 for x in recs)/n,
        over20=sum(x["n"] >= 20 for x in recs)/n,
        schema_share=sum(x["schema"] for x in recs)/max(tot, 1),
        err_share=sum(len(x["errs"]) for x in recs)/max(tot, 1),
        err_types=dict(E),
        claims_with_grounding_err=sum(map(ground, recs))/n,
        ec_zero_calls=grp([x for x in ec if x["n"] == 0]),
        ec_grounding_err=grp([x for x in ec if x["n"] > 0 and ground(x)]),
        ec_clean=grp([x for x in ec if x["n"] > 0 and not x["errs"]]),
        by_calls={b: grp([x for x in recs if lo <= x["n"] <= hi]) for b, (lo, hi) in
                  {"0": (0, 0), "1-3": (1, 3), "4-8": (4, 8), "9+": (9, 999)}.items()},
        by_difficulty={d: grp([x for x in recs if x["difficulty"] == d]) for d in ["simple", "moderate", "challenging"]},
        by_joins={k: grp([x for x in recs if (x["joins"] >= 2 if k == "2+" else x["joins"] == int(k))]) for k in ["0", "1", "2+"]},
        by_nei_category={c: grp([x for x in recs if x["category"] == c]) for c in ["OUT-OF-SCHEMA", "COUNTERFACTUAL", "SUBJECTIVE"]},
    )
    results[model] = res
    print(f"{model:22s} acc={res['acc']:.3f} F1={res['macro_f1']:.3f} NEI={res['pred_nei']:.2f} calls={res['calls_mean']:.1f} zero={res['zero_call']:.2f} "
          f"schema={res['schema_share']:.2f} err={res['err_share']:.2f} groundErrClaims={res['claims_with_grounding_err']:.2f} "
          f"EC: zero acc={res['ec_zero_calls']['acc']} nei={res['ec_zero_calls']['nei']} | gerr acc={res['ec_grounding_err']['acc']} nei={res['ec_grounding_err']['nei']} | clean acc={res['ec_clean']['acc']} nei={res['ec_clean']['nei']}")
json.dump(results, open(out, "w"), indent=1)
