# ClaimDB: exact setup and diagnostic analysis of released runs (updated 11 Oct 2026)

Source: github.com/claimdb/claimdb (code, final-benchmark/, experiments/public/ transcripts).

## Exact ClaimDB setup (claimdb/experiments.py, experiments_pydantic_ollama.py)
- Judge input: "Claim: <claim>\nExtra Information: <extra_info>". Schema NOT given; prompt says "always start by querying the database for the schema".
- One SQL tool per database (Google MCP Toolbox, SQLite). Open models via Ollama + Pydantic AI 1.44; tool_calls_limit=20, output_retries=20.
- Output JSON {verdict, justification}; 3-shot output examples.
- Splits: train 51,369 claims (80 DBs, incl. 4,883 claims from the 11 BIRD dev DBs), test-public 1,000 (11 BIRD dev DBs, 333/331/336), test-private 999.
- Each claim has bird_id; BIRD-source.jsonl maps it to BIRD question, evidence, gold SQL, gold result, schema text, difficulty. Oracle SQL IS available.
- CORRECTION: train and test are NOT database-disjoint. 607 of the 609 BIRD questions behind public-test claims also appear in train. Any training must drop train claims from the 11 dev DBs (keeps 46,486 claims on 69 BIRD train DBs).

## Diagnostic results (19 models, public test)
- Failed-call share vs accuracy: r = -0.88; share of claims with a grounding error vs accuracy: r = -0.77.
- Pooled 11 open models <=14B, on ENTAILED/CONTRADICTED claims:
  - all queries succeeded: n=1,207, acc 43.8%, predicted NEI 41%
  - at least one "no such table/column" error: n=4,346, acc 20.8%, predicted NEI 68%
  - no SQL call: n=956, acc 21.9%, predicted NEI 59%
- Pattern holds for 9 of 11 small models (exceptions qwen3:4b, llama3.2:3b). gpt-5-mini hits grounding errors on 32% of claims but still 89% accurate on those E/C claims.
- Error types: llama3.1:8b 1,456 of 1,658 failed calls are no such table/column; qwen3:8b 826 of 850.
- Examples: qwen3:8b claim 4652 (queried drivers.id, column is driverId, answered NEI on a true claim); llama3.1:8b claim 5588 (invented table "fixture").

## ClaimDB release accuracy on our balanced subsets (seed 13, nested)
- subset_60: qwen3:4b 40.0, qwen3:8b 51.7, llama3.1:8b 31.7, gpt-5-mini 76.7
- subset_150: qwen3:4b 47.3, qwen3:8b 49.3, llama3.1:8b 33.3, gpt-5-mini 80.7

## Conditions (harness built, tested with scripted models)
A ClaimDB exact; B schema given (CREATE TABLE); C NL2SQL builder via ask_database (returns SQL + rows); CS builder + schema. B vs CS isolates builder value beyond schema. Rows capped at 100 in all conditions.
