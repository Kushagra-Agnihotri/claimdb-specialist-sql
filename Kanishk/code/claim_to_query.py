"""Sir's idea (Nov): can a small LLM turn a simple (one table) claim into a "queryable" form?

Queryable form used here = the same lookup form as the simple path S, plus the number or text the claim states:
  {"table": ..., "filters": [{"column","op","value"}], "aggregate": none|count|count_distinct|sum|avg|min|max,
   "column": ..., "claimed_value": ..., "comparison": "=" | ">" | ">=" | "<" | "<="}
One model call per claim (no tool loop). Python then runs the form with simple_tools.LookupEngine (no SQL written by the
model), compares the result with claimed_value, and gives a verdict. The gold SQL and its result are shown next to it.

  python claim_to_query.py --model qwen3:8b --n 5 --seed 7
Claims: random strict simple test claims (gold SQL uses 1 table, not nested) labelled ENTAILED or CONTRADICTED.
Output: ..\\results\\claim_to_query__<model>.jsonl and .md
"""
import argparse, json, random, time, urllib.request
from pathlib import Path
from common import load_jsonl, db_path, schema_ddl, execute_sql
from simple_tools import LookupEngine

HERE = Path(__file__).resolve().parent
FORM = {
    "type": "object",
    "properties": {
        "table": {"type": "string"},
        "filters": {"type": "array", "items": {"type": "object", "properties": {
            "column": {"type": "string"},
            "op": {"type": "string", "enum": ["=", "!=", ">", ">=", "<", "<=", "contains", "starts_with", "is_null", "not_null"]},
            "value": {"type": ["string", "number", "null"]}}, "required": ["column", "op"]}},
        "aggregate": {"type": "string", "enum": ["none", "count", "count_distinct", "sum", "avg", "min", "max"]},
        "column": {"type": "string"},
        "claimed_value": {"type": ["string", "number"]},
        "comparison": {"type": "string", "enum": ["=", ">", ">=", "<", "<="]}},
    "required": ["table", "filters", "aggregate", "column", "claimed_value", "comparison"]}

PROMPT = """You turn a factual claim about a SQLite database into a query form that a program will run.
The claim can be checked with ONE table. Fill in:
- table: the one table that holds the facts
- filters: conditions on that table's columns (op is one of = != > >= < <= contains starts_with is_null not_null)
- aggregate: count, count_distinct, sum, avg, min, max, or none (none returns the value of `column` from the matching row)
- column: the column to aggregate or return (for count of rows use "")
- claimed_value: the number or text the claim states
- comparison: how the claim relates the true result to claimed_value (= for "exactly", > for "more than", etc.)
Use only table and column names that appear in the schema. Use the Extra Information to pick columns and values.
Answer with the JSON object only.

Database schema:
{schema}

Claim: {claim}
Extra Information: {hint}"""


def ask(model, prompt, url):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False,
                       "format": FORM, "think": False, "options": {"temperature": 0}}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["message"]["content"]


def as_num(v):
    try:
        return float(str(v).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def compare(true, claimed, op):
    a, b = as_num(true), as_num(claimed)
    if a is None or b is None:
        ok = str(true).strip().lower() == str(claimed).strip().lower()
        return ok if op == "=" else None
    if op == "=":
        return abs(a - b) <= 0.01 * max(1.0, abs(b))          # 1% tolerance for rounding in the claim
    return {">": a > b, ">=": a >= b, "<": a < b, "<=": a <= b}[op]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3:8b"); ap.add_argument("--n", type=int, default=5); ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--db-root", default=str(HERE.parent / "data" / "dev_databases" / "dev_databases"))
    ap.add_argument("--url", default="http://localhost:11434/api/chat")
    a = ap.parse_args()
    labels = {json.loads(l)["claim_id"]: json.loads(l) for l in open(HERE.parent / "router" / "labels.jsonl", encoding="utf-8")}
    claims = load_jsonl(HERE / "subsets" / "test-public.jsonl")
    src = {}
    for l in open(HERE / "subsets" / "BIRD-source.jsonl", encoding="utf-8"):
        d = json.loads(l); src[d["bird_id"]] = d
    pool = [c for c in claims if labels.get(c["claim_id"], {}).get("simple_strict") == 1 and c["label"] != "NOT ENOUGH INFO"]
    pick = random.Random(a.seed).sample(pool, a.n)
    out_base = HERE.parent / "results" / f"claim_to_query__{a.model.replace(':', '_')}"
    rows, md = [], [f"# Claim to query form: {a.model}, {a.n} random strict simple claims (seed {a.seed})", ""]
    for c in pick:
        dbf = db_path(Path(a.db_root), c["db_name"])
        t0 = time.time()
        raw = ask(a.model, PROMPT.format(schema=schema_ddl(dbf), claim=c["claim"], hint=c.get("extra_info", "")), a.url)
        secs = round(time.time() - t0, 1)
        try:
            form = json.loads(raw)
        except json.JSONDecodeError:
            form = None
        result_text, true_val, verdict, sql = "", None, "FAILED (no valid form)", None
        if form:
            text, info = LookupEngine(dbf).lookup(table=form.get("table", ""), filters=form.get("filters") or [],
                                                  aggregate=form.get("aggregate", "none"), column=form.get("column", ""),
                                                  columns=[form["column"]] if form.get("aggregate", "none") == "none" and form.get("column") else None,
                                                  limit=5)
            result_text, sql = text, info.get("sql")
            if not info.get("error"):
                res = json.loads(text.split("\n")[0]).get("result") or []
                if res:
                    true_val = res[0].get("value", next(iter(res[0].values())))
                    ok = compare(true_val, form.get("claimed_value"), form.get("comparison", "="))
                    verdict = "UNDECIDED" if ok is None else ("ENTAILED" if ok else "CONTRADICTED")
                else:
                    verdict = "NO ROWS"
            else:
                verdict = "FAILED (form error)"
        g = src[c["bird_id"]]
        gold_rows, gerr = execute_sql(dbf, g["SQL"], 30, 5)
        r = {"claim_id": c["claim_id"], "db": c["db_name"], "claim": c["claim"], "hint": c.get("extra_info", ""), "gold_label": c["label"],
             "form": form, "raw": raw, "python_sql": sql, "result": result_text[:500], "true_value": true_val, "verdict": verdict,
             "correct": verdict == c["label"], "seconds": secs, "gold_sql": g["SQL"], "gold_result": gold_rows if not gerr else gerr}
        rows.append(r)
        md += [f"## Claim {c['claim_id']} ({c['db_name']}), gold {c['label']}", "", f"Claim: {c['claim']}", f"Hint: {c.get('extra_info', '')}", "",
               "Query form from the model:", "```json", json.dumps(form, indent=1) if form else raw, "```",
               f"Python ran: `{sql}`", f"Result: {result_text[:300]}", "",
               f"Verdict from the form: **{verdict}** ({'correct' if r['correct'] else 'wrong'}), {secs} s", "",
               f"Gold SQL: `{g['SQL']}`", f"Gold result: {r['gold_result']}", ""]
    md.insert(2, f"Correct verdicts: {sum(r['correct'] for r in rows)} of {len(rows)}\n")
    with open(f"{out_base}.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    open(f"{out_base}.md", "w", encoding="utf-8").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
