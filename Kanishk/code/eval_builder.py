"""Builder on its own: run it on the BIRD questions behind the subset's claims and compare with gold SQL results.
  python eval_builder.py --claims subsets/subset_150.jsonl --source BIRD-source.jsonl --db-root D:\\bird\\dev_databases --builder hf.co/mradermacher/Arctic-Text2SQL-R1-7B-GGUF:Q4_K_M
Execution accuracy uses BIRD's convention: the predicted and gold result sets are equal as sets of rows."""
import argparse, json, time
from pathlib import Path
from common import load_jsonl, db_path, schema_ddl, schema_ddl_with_values, execute_sql, safe_name, load_results_repair
from builder import Builder

ap = argparse.ArgumentParser()
ap.add_argument("--claims", required=True); ap.add_argument("--source", required=True)
ap.add_argument("--db-root", required=True, type=Path); ap.add_argument("--builder", required=True)
ap.add_argument("--builder-backend", default="openai", choices=["openai", "hf"])
ap.add_argument("--builder-template", default="omnisql", choices=["omnisql", "finer"])
ap.add_argument("--builder-url", default="http://localhost:11434/v1"); ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--builder-values", type=int, default=0, help="N>0: show N example values per column in the schema")
a = ap.parse_args()
src = {s["bird_id"]: s for s in load_jsonl(a.source)}
bird_ids = []
for c in load_jsonl(a.claims):
    if c["bird_id"] not in bird_ids: bird_ids.append(c["bird_id"])
if a.limit: bird_ids = bird_ids[:a.limit]
b = Builder(a.builder, backend=a.builder_backend, template=a.builder_template, base_url=a.builder_url)
out = Path(__file__).resolve().parent.parent / "results" / f"builder_eval__{safe_name(a.builder)}{f'__vals{a.builder_values}' if a.builder_values else ''}.jsonl"
out.parent.mkdir(exist_ok=True)
prev = {r["bird_id"]: r for r in load_results_repair(out)}   # resume: skip questions already done
correct = sum(r["correct"] for r in prev.values() if r["bird_id"] in bird_ids)
for i, bid in enumerate(bird_ids, 1):
    if bid in prev: continue
    s = src[bid]; f = db_path(a.db_root, s["db_id"]); t = time.time()
    try:
        sql, raw = b.sql_for(schema_ddl_with_values(f, a.builder_values) if a.builder_values else schema_ddl(f), s["question"], s.get("evidence", ""))
    except Exception as e:  # builder server problem: record it as a miss and keep going
        sql, raw = "", f"builder failure: {e}"
    pred, err = execute_sql(f, sql, 30, None) if sql else (None, "no SQL returned")
    gold, gerr = execute_sql(f, s["SQL"], 60, None)
    ok = err is None and gerr is None and set(map(lambda r: tuple(r.values()), pred)) == set(map(lambda r: tuple(r.values()), gold))
    correct += ok
    with open(out, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"bird_id": bid, "db": s["db_id"], "question": s["question"], "pred_sql": sql, "gold_sql": s["SQL"],
                             "correct": ok, "error": err, "seconds": round(time.time() - t, 1)}) + "\n")
    print(f"[{i}/{len(bird_ids)}] {'OK ' if ok else '-- '}{s['db_id']}  running EX = {correct / i:.3f}")
print(f"\nExecution accuracy: {correct}/{len(bird_ids)} = {correct / len(bird_ids):.3f}")
