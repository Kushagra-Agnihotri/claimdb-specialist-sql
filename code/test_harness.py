"""Plumbing test without any LLM: scripted models drive the real tools on a toy database."""
import sys, json, asyncio, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from pydantic_ai.models.function import FunctionModel, AgentInfo
from pydantic_ai.messages import ModelResponse, ToolCallPart, ToolReturnPart
import run_judge, common

DB_ROOT = Path(sys.argv[1])
claim = {"claim_id": 1, "db_name": "toy_db", "label": "ENTAILED", "claim": "Sebastian Vettel has the most points, 397.0.",
         "extra_info": "most points refers to max(points)"}

def scripted(sql_or_question, tool_suffix):
    def fn(messages, info: AgentInfo):
        returns = [p for m in messages for p in getattr(m, "parts", []) if isinstance(p, ToolReturnPart)]
        tool = next(t for t in info.function_tools if t.name.endswith(tool_suffix))
        if len(returns) == 0:
            arg = list(tool.parameters_json_schema["properties"])[0]
            return ModelResponse(parts=[ToolCallPart(tool.name, {arg: sql_or_question})])
        if len(returns) == 1:
            arg = list(tool.parameters_json_schema["properties"])[0]
            return ModelResponse(parts=[ToolCallPart(tool.name, {arg: "SELECT nosuchcol FROM drivers" if tool_suffix == "execute_sql" else "bad"})])
        out = info.output_tools[0]
        return ModelResponse(parts=[ToolCallPart(out.name, {"verdict": "ENTAILED", "justification": "max points is Vettel 397"})])
    return fn

class FakeBuilder:
    def sql_for(self, schema, question, evidence):
        assert "CREATE TABLE" in schema and "max(points)" in evidence
        return ("SELECT forename, surname, MAX(points) FROM drivers" if question != "bad" else "SELECT * FROM nope"), "raw"

async def go():
    for cond, q, suffix in [("A", "SELECT forename, surname, points FROM drivers ORDER BY points DESC LIMIT 1", "execute_sql"),
                            ("B", "SELECT * FROM drivers", "execute_sql"),
                            ("C", "Who has the most points?", "ask_database"), ("CS", "Who has the most points?", "ask_database")]:
        args = types.SimpleNamespace(db_root=DB_ROOT, condition=cond, sql_timeout=5, max_rows=100, max_calls=20,
                                     model="fake", builder="fake" if cond in ("C", "CS") else None)
        r = await run_judge.judge_one(claim, args, FunctionModel(scripted(q, suffix)), FakeBuilder())
        prompt = common.judge_prompt(cond)
        print(cond, "verdict:", r["verdict"], "| error:", r["error"], "| tool log:", [(t.get("sql") or t.get("question"))[:40] + " -> " + str(t.get("error") or t.get("n_rows")) for t in r["tool_log"]])
        user = r["all_messages"][0]["parts"][0]["content"]
        print("   schema in input:", "CREATE TABLE" in user, "| prompt has schema-query line:", "always start by querying" in prompt,
              "| builder wording:", "NL-to-SQL" in prompt)
        assert r["verdict"] == "ENTAILED" and len(r["tool_log"]) == 2
        assert r["tool_log"][1]["error"] and "no such" in r["tool_log"][1]["error"]
    # truncation note
    rows, err = common.execute_sql(DB_ROOT / "toy_db/toy_db.sqlite", "SELECT * FROM drivers", 5, 100)
    txt = common.rows_to_text(rows, 100); assert "truncated" in txt and len(json.loads(txt.split("\n")[0])) == 100
    # verbatim prompt check for A
    assert common.judge_prompt("A").startswith("\nYou are a fact-checking assistant")
    print("ALL TESTS PASSED")
asyncio.run(go())
