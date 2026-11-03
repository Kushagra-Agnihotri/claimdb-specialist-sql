"""NL2SQL builder: question (+ evidence + schema) -> SQL -> execution result.

Two backends:
  openai : any OpenAI-compatible server (Ollama, LM Studio, vLLM). Default http://localhost:11434/v1
  hf     : Hugging Face transformers, loaded in this process (for models without a GGUF/Ollama build)
Two prompt templates:
  omnisql: the OmniSQL / Arctic-Text2SQL-R1 style prompt (also suits SLM-SQL, trained on SynSQL)
  finer  : FINER-SQL's system prompt. Check the model card and adjust if their README differs.
"""
import re

OMNISQL_TEMPLATE = """Task Overview:
You are a data science expert. Below, you are provided with a database schema and a natural language question. Your task is to understand the schema and generate a valid SQL query to answer the question.

Database Engine:
SQLite

Database Schema:
{schema}
This schema describes the database's structure, including tables, columns, primary keys, foreign keys, and any relevant relationships or constraints.

Question:
{evidence}
{question}

Instructions:
- Make sure you only output the information that is asked in the question. If the question asks for a specific column, make sure to only include that column in the SELECT clause, nothing more.
- The generated query should return all of the information asked in the question without any missing or extra information.
- Before generating the final SQL query, please think through the steps of how to write the query.

Output Format:
In your answer, please enclose the generated SQL query in a code block:
```sql
-- Your SQL query
```

Take a deep breath and think step by step to find the correct SQL query."""

FINER_SYSTEM = ("You are a meticulous SQL expert. Generate a single, correct SQL query for the user question "
                "and the provided database schema.")
FINER_USER = "Database schema:\n{schema}\n\nExternal knowledge: {evidence}\n\nQuestion: {question}\n\nReturn only the SQL query."

def build_messages(template: str, schema: str, question: str, evidence: str):
    if template == "finer":
        return [{"role": "system", "content": FINER_SYSTEM},
                {"role": "user", "content": FINER_USER.format(schema=schema, evidence=evidence or "", question=question)}]
    return [{"role": "user", "content": OMNISQL_TEMPLATE.format(schema=schema, evidence=evidence or "", question=question)}]

def extract_sql(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    blocks = re.findall(r"```(?:sql|sqlite)?\s*(.*?)```", text, flags=re.S | re.I)
    sql = blocks[-1] if blocks else text
    sql = "\n".join(l for l in sql.strip().splitlines() if not l.strip().startswith("--"))
    return sql.strip().rstrip(";").strip()

class Builder:
    def __init__(self, model: str, backend: str = "openai", template: str = "omnisql",
                 base_url: str = "http://localhost:11434/v1", max_new_tokens: int = 2048):
        self.model, self.backend, self.template, self.max_new_tokens = model, backend, template, max_new_tokens
        if backend == "openai":
            from openai import OpenAI
            self.client = OpenAI(base_url=base_url, api_key="ollama")
        elif backend == "hf":
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.tok = AutoTokenizer.from_pretrained(model)
            self.lm = AutoModelForCausalLM.from_pretrained(model, torch_dtype=torch.bfloat16, device_map="auto")
        else:
            raise ValueError(backend)

    def generate(self, schema: str, question: str, evidence: str) -> str:
        msgs = build_messages(self.template, schema, question, evidence)
        if self.backend == "openai":
            r = self.client.chat.completions.create(model=self.model, messages=msgs, temperature=0,
                                                    max_tokens=self.max_new_tokens)
            return r.choices[0].message.content or ""
        import torch
        ids = self.tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(self.lm.device)
        with torch.no_grad():
            out = self.lm.generate(ids, max_new_tokens=self.max_new_tokens, do_sample=False)
        return self.tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)

    def sql_for(self, schema: str, question: str, evidence: str) -> tuple[str, str]:
        raw = self.generate(schema, question, evidence)
        return extract_sql(raw), raw
