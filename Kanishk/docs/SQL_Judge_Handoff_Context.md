# SQL-Judge Project: Complete Handoff Context

Prepared on 11 October 2026 from Kanishk's working session, for Kushagra Agnihotri and Navtej Singh Dua and for the Claude assistant each of them uses. Read Section 0 first. The appendices contain the raw source material (mentor messages, the full lecture transcript, the course template, the original brief and plan, and the literature review).

---

## 0. Instructions for the Claude reading this document (read first)

You are helping either **Kushagra Agnihotri** or **Navtej Singh Dua**, two members of a three-person student research team at BITS Pilani. The team lead is **Kanishk Didwania**. This document gives you the full context of the project as of 11 October 2026, so you can work at the same level as the assistant that helped Kanishk.

Follow these rules for the whole conversation.

1. **Kanishk writes the mid-semester report.** Do not draft report sections, abstracts, introductions or paper text for your user. Your job is to help your user run one experiment correctly, understand it completely, and hand a clean results package to Kanishk.

2. **The experiments are already split.** For the mid-semester report the team runs three versions (called "conditions") of the same experiment. Kanishk has taken **Condition C** (the NL2SQL builder) and the builder-alone test. Your user must take **Condition A** (reproducing ClaimDB) or **Condition B** (giving the schema with the claim). Kushagra and Navtej take different ones. **Your first action: ask your user which condition they have chosen, and ask them to confirm with their teammate that the other person has the other one.** Then guide them step by step using Section 11 and the condition-specific notes.

3. **Your user must understand everything.** The course instructor said he will ask students to explain their work, and that a top journal found 70 to 80% of authors could not explain their own AI-assisted papers. Explain every command before your user runs it. Explain what every file and every number means. After each major step, check their understanding with a short question. Never do something silently. If you change anything, say what, why, and what effect it has.

4. **Keep the protocol fixed.** Do not change the judge model (`qwen3:8b`), the claim subset (`subset_210.jsonl`), the prompt, the 20-call limit, the 100-row cap, or the timeout without your user's explicit approval. If a change is unavoidable (for example, the GPU cannot run the model), your user must tell Kanishk immediately, because all three conditions must stay comparable.

5. **Deadline.** All three experiment results must be consolidated with Kanishk on **12 October 2026** (Kanishk will confirm the exact time). The report is due on **13 October 2026**. Plan backwards from that. If a full run of 210 claims cannot finish in time, run as many claims as possible in the file's order (the script resumes where it stopped) and report exactly how many finished.

6. **Be honest about results.** Report exactly what happened. Runs that crash count as wrong answers, following ClaimDB's convention. Never round, adjust or invent numbers. Never invent citations or paper details. If you are unsure of a fact, say so.

7. **Writing style for any notes your user produces.** Kanishk prefers no em dashes or en dashes, no semicolons joining clauses, short and simple sentences, and no defensive "X rather than Y" phrasing. These are also the course instructor's rules for the paper.

8. **Your user is probably on Windows** without Ollama or the BIRD databases installed yet. Start setup early, because downloads take time.

---

## 1. People, course and deadlines

* **Team:** Kanishk Didwania (lead; writes the report; runs Condition C), Kushagra Agnihotri, Navtej Singh Dua. All are B.E. Computer Science students at BITS Pilani. None of them had a prior ML research background when the project started.
* **Mentors:** Dr Krishna Garg (main mentor) and Chirag Chhablani. The course instructor ("Sir" in the lecture transcript) set the report rules. Dhruv Kumar and Abhiruk Singha are also in the project group chat.
* **Course:** an LLM course whose projects aim at conference or workshop papers.
* **Mid-semester report:** due **13 October 2026**, in LaTeX using the course Overleaf template (Appendix C), target length **4 pages** (6 at most). The instructor expects: a final methodology, a clear list of experiments, about **20%** of the planned experiments actually run, and **at least one interesting insight**. Details are in Section 5.
* **Final paper:** end of semester (early December 2026). Possible conference target: ACL 2027 through ACL Rolling Review (submission around January 2027). The mentors have not confirmed a venue yet.

---

## 2. The project in plain words

### 2.1 The problem

Companies increasingly use language models to write text about their own data: reports, summaries, and answers from database chat assistants. Before anyone trusts such text, each factual claim in it should be checked against the database it describes. A model that checks another model's output is called a **judge**.

Checking a claim like "Employee 12 spent $1,950 in March" requires looking at many rows in a database. A judge cannot do this by reading alone. So the judge is given a **tool**: it can write a SQL query, our code runs it on the database, and the judge reads the result before deciding.

Large models (for example gpt-5-mini) do this well. **Small open models**, which are cheap and can run on a company's own machines, do it badly. On the ClaimDB benchmark, open models of 8B parameters or fewer reach only **34 to 53%** accuracy, against **82.7%** for gpt-5-mini.

### 2.2 Our question

*Why* do small judges fail, and can we fix it by helping them find the right data, **without training them**?

### 2.3 The task format (from ClaimDB)

* **Input:** a claim in plain English, an "extra information" hint (a note from the BIRD dataset such as "most points refers to max(points)"), and a SQLite database.
* **Output:** one of three labels: **ENTAILED** (the database supports the claim), **CONTRADICTED** (the database refutes it), **NOT ENOUGH INFO** (NEI; the database cannot decide it).

### 2.4 The four conditions, with one real example

Example claim (ClaimDB claim 4652, true): *"Sebastian Vettel is the driver with the most points, totaling 397.0."* The `drivers` table's ID column is called `driverId`.

| Condition | What the small judge gets | What we expect | Proposed by |
|---|---|---|---|
| **A** | Only the claim and the hint. It must discover the tables itself and write its own SQL. This is exactly ClaimDB's setup. | In ClaimDB's real run, qwen3:8b guessed a column `drivers.id`, got "no such column" twice, and answered NOT ENOUGH INFO, which is wrong. | Dr Krishna Garg ("reproduce ClaimDB") |
| **B** | Same as A, plus the full schema (all `CREATE TABLE` statements) written into the input. | It can see that `driverId` exists, so it should stop guessing names. | Chirag Chhablani ("give schema of tables with the claims itself") |
| **C** | The judge asks a question in plain English, for example "Which driver has the most points?". A small specialist model (an **NL2SQL** or "SQL builder" model, here Arctic-Text2SQL-R1 7B) writes and runs the SQL and returns the SQL plus the result. | The specialist knows the schema and is good at SQL, so the judge only needs to ask the right question. | Dr Krishna Garg ("plug in an NL2SQL tool instead of LLM writing the query") |
| **CS** | C plus the schema given to the judge. | Lets us compare fairly with B. | Proposed by Kanishk's assistant, approved by Kanishk. Runs after the midsem. |

**Why CS exists:** in C the builder always sees the schema. If C beats A, we cannot tell whether the gain came from the builder or simply from schema access. Comparing **B with CS** isolates the builder's value, because both have the schema and only the SQL writer differs.

### 2.5 The one insight we already have

From ClaimDB's released logs (Section 8): small models mostly fail because they **guess table or column names that do not exist**, their query errors out, and they then answer NOT ENOUGH INFO. On claims that are actually true or false, small models are right **20.8%** of the time when this happens, against **43.8%** when all their queries work. Across 19 models, the share of failed SQL calls correlates with accuracy at **r = −0.88**. This points to *grounding* (finding the right data) as the main bottleneck, more than *judging* itself. Conditions B and C test this causally.

---

## 3. How the project got here (timeline)

1. **Project allocation (late August to early September 2026).** The team first wanted projects under Dhruv Kumar. Those were taken, so the team took an open project under Dr Krishna Garg titled "Beyond Answer Imitation: Knowledge Distillation Amplifies Reasoning Brittleness in Small Language Models".
2. **Three candidate directions** came from Dr Garg. The team chose "SLM judges equipped with a SQL-execution tool" (the Research Direction Brief, Appendix D).
3. **Execution plan** (Appendix E) arrived around 24 September. It proposed a synthetic expenses database, policy rules, and a with-tool vs without-tool test. **This plan has since been superseded** by the ClaimDB-based direction below.
4. **18 September task** from Dr Garg: "Literature Review and let's solidify the gap (SQL for LLM-as-a-judge): Task (i/p, o/p), Tools, Settings, Datasets, Models, Findings/Claims. Let's hear back in a few days." The literature review (Appendix F) found that **ClaimDB** (ACL 2026) and **Thucy** (AAAI 2026) already study LLM agents with a SQL tool for claim verification, which narrowed the gap.
5. **26 September: Dr Garg's new direction** (verbatim in Appendix A.1). He and Chirag Chhablani proposed using a **SQL builder** (an existing small NL-to-SQL model) as the judge's tool in place of a raw SQL executor. Next steps: reproduce ClaimDB, then run an existing NL-to-SQL tool on the same databases and compare.
6. **27 September: the team's reply** (Appendix A.2) proposed four research questions. **Dr Garg's answers** (Appendix A.3) were:
   * try smaller builders (FINER-SQL 3B, SLM-SQL 1.5B, Arctic-Text2SQL-R1 7B);
   * "Let's not worry about the training for now";
   * don't build our own NL2SQL model (keep an existing builder fixed and vary its strength);
   * an oracle-SQL comparison isn't needed ("Let's see the final accuracy and we will need to do some analysis on a small subset");
   * RL compute will be managed later.

   His to-dos: **(1) reproduce ClaimDB, (2) build a pipeline that plugs in an NL2SQL tool instead of the LLM writing the query**, divided among students and done quickly "to see whether there is some promise". **Chirag Chhablani** added: keep the setup close to ClaimDB, start with the simplest experiments, keep only the SQL tool, add tools only if they help, and give the schema with the claim.
7. **5 to 11 October:** midsems. No project work.
8. **11 October:**
   * Kanishk's assistant analysed ClaimDB's released logs (the diagnostic study, Section 8).
   * It built and tested the experiment code (Section 11 and the code package).
   * The team fixed the decisions in Section 9.

   The assistant also drafted a full report on its own, which **Kanishk rejected** because it was written without consulting him and broke the course rules. **That draft must not be used.** The report will be written by Kanishk following the course process (Section 5).

---

## 4. Mentor direction, summarised

* **Main direction:** a small judge plus a small NL-to-SQL "builder" tool, compared directly against ClaimDB's results.
* **Immediate to-dos:** reproduce ClaimDB (Condition A) and build the NL2SQL pipeline (Condition C), done in parallel and quickly.
* **Keep it simple and close to ClaimDB.** Only the SQL tool for now. Add other tools (calculator, schema explorer) only if they help.
* **Schema:** Chirag suggested giving the schema with the claim (Condition B).
* **Builders to try:** FINER-SQL 3B, SLM-SQL 1.5B, Arctic-Text2SQL-R1 7B.
* **No training for now.** Training (SFT, then possibly RL like TIR-Judge) is a later step, only if the builder shows promise.
* **Analysis:** look at final accuracy, then analyse a small subset by hand.

---

## 5. Course rules for the mid-semester report (from the lecture, full transcript in Appendix B)

* **Format.** LaTeX, the course Overleaf template (Appendix C). No Word, Markdown or Google Docs.
* **Length.** 4 to 6 pages. The instructor will push for **4 pages**: the bare minimum content that is really the team's contribution.
* **Experiments.** The methodology must be final, the list of experiments must be clear, and about **20%** of the planned work must be run. His example: "if you are planning six models, run one or two; if you are planning a thousand samples, cover two hundred". Zero experimentation is not acceptable.
* **Insight.** By 13 October the team must know whether the project is "going somewhere": **at least one interesting, novel finding**. Evaluation papers showing bad model performance are fine. Negative results for methods (for example a fine-tuning approach that does not help) are generally not publishable and may require a pivot.
* **Template sections.** Each experiment is a results subsection with an **Objective** and **Findings**.
* **Writing.**
  * Abstract and introduction must be understandable to someone with only an ML 101 course.
  * Academic language, full sentences, no fragment bullets (except a contributions list).
  * Break long sentences. Use simple words and define technical terms on first use.
  * No defensive "this is X, not Y" phrasing. **No em dashes or en dashes. No semicolons as connectors.**
* **Process.** Use AI, but iterate.
  1. Read the template and the instructor's prompt yourself.
  2. Generate a draft.
  3. Read it line by line and give feedback to the AI.
  4. **Team members review it and check whether they understand it.**
  5. Optionally, other teams and outside friends review it too.

  A harder option he recommends: write or dictate your own answers to the template's questions first, at least for the abstract and introduction.
* **References.**
  * Every BibTeX entry must be copied from the **original published source** (conference proceedings, ACL Anthology, OpenReview, DBLP, ACM). Do not use arXiv when a published version exists.
  * At most about 25 to 30% arXiv entries.
  * He checks authors, title, venue and year. A hallucinated reference is penalised, and he will run an automatic hallucination checker.
* **Explaining your work.** Every student must be able to explain the paper.

---

## 6. Background knowledge

### 6.1 Terms

* **SLM:** small language model, here roughly 1B to 14B parameters.
* **LLM-as-a-judge:** using a language model to grade or check other model outputs.
* **Tool calling / agent:** the model outputs a structured request (for example a SQL query). Our code executes it and feeds the result back. This repeats until the model gives a final answer.
* **SQL executor vs SQL builder:**
  * An **executor** runs SQL that the judge itself wrote (Conditions A, B).
  * A **builder** is a separate NL-to-SQL model that turns the judge's English question into SQL and runs it (Conditions C, CS).
* **NL2SQL / text-to-SQL:** turning a plain-English question into a SQL query.
* **Schema:** the list of tables and columns in a database (here, the `CREATE TABLE` statements).
* **Grounding error:** a SQL error caused by referring to a table or column that does not exist ("no such table", "no such column").
* **BIRD:** a well-known text-to-SQL benchmark of English questions paired with the correct SQL, over 95 real databases (33.4 GB in total). Its splits are train, dev, and a hidden test set.
* **Ollama:** a free program that runs open models locally on your GPU and exposes them through an OpenAI-compatible API at `http://localhost:11434/v1`.
* **Pydantic AI:** the Python agent library ClaimDB used. Version 1.44 is pinned in our code to match ClaimDB.
* **Accuracy:** the fraction of claims labelled correctly. This is the primary metric, as in ClaimDB.
* **Macro-F1:** the average of the F1 scores of the three labels. It rewards balanced performance.
* **Predicted NEI rate:** how often the judge answers NOT ENOUGH INFO. The true rate in the test set is about 33%.
* **Bootstrap 95% CI:** a range in which the true accuracy likely lies, estimated by resampling claims.
* **McNemar's test:** checks whether two conditions differ on the *same* claims more than chance would explain.

### 6.2 Key papers (verified facts)

* **ClaimDB** (Theologitis, Dammu, Shah, Suciu; University of Washington; ACL 2026; arXiv 2601.14698). A benchmark of 53,368 claims over 80 BIRD databases (average 11 tables and 4.6 million rows), with 30 models evaluated as SQL-tool agents (zero-shot, at most 20 tool calls). gpt-5-mini scores 0.827, and 0.367 with no tools. Small open models score 0.344 to 0.533. Small models over-predict NEI, sometimes skip the tool, and write poor SQL. The paper reports no training and no breakdown by claim type. Code and data: github.com/claimdb/claimdb, website claimdb.github.io.
* **Thucy** (Theologitis, Suciu; AAAI 2026; arXiv 2512.03278). A multi-agent claim verifier: a GPT-5 verifier coordinates helper agents, including a "SQL Expert". It reaches 94.3% on TabFact. Prompting only, large models.
* **TIR-Judge** (Xu et al.; Emory and Google; ICLR 2026; arXiv 2510.23038). Trains Qwen3 4B and 8B judges with RL to call a Python executor. An *untrained* Qwen3-8B got worse with the tool (61.1 to 56.7 average). After training it reached 70.3, and the 8B judge reaches 96% of Claude Opus 4 on RewardBench 2.
* **T1 / ToolV** (Kang, Jeong, Cho; ICLR 2026; arXiv 2504.04718). Small verifiers (0.36B to 1B) with code or retrieval tools, distilled with LoRA. A 1B model with a tool beats an 8B model without one on MATH500. Small models fail at verifying sums as the number of terms grows.
* **Evergreen** (Lee et al.; Brown University and Snowflake; arXiv 2604.26180, April 2026). Verifies LLM summaries of a table by compiling each claim upfront into a declarative query. Large models only (Claude 4.x, Qwen3 80B/235B).
* **AggChecker** (Jo, Trummer et al.; SIGMOD 2019). Checks claims in articles against relational data by generating many candidate SQL queries. No LLM.
* **FinGround** (Guo, Wu, Yiu; listed at ACL 2026; arXiv 2604.23588). Financial hallucination detection with a distilled Llama-3-8B and retrieval, no SQL. 56% of its pilot misses were retrieval failures for the numbers a calculation needed.
* **Findeis et al.** (Apple; ACL 2025; arXiv 2507.17015). Prompted tools help LLM judges "in many but not all cases".
* **Themis / Tool-Augmented Reward Modeling** (Li et al.; ICLR 2024 spotlight; arXiv 2310.01045).
* **TableMind** (Jiang et al.; WSDM 2026). An RL-trained Python agent over tables given in the prompt. Not SQL, not a judge.
* **NL2SQL builders:**
  * Arctic-Text2SQL-R1 (Snowflake; arXiv 2505.20315): 7B scores 68.9% on BIRD dev. Trained on BIRD train, Spider and synthetic data with GRPO on 64 H100 GPUs.
  * OmniSQL-7B: 63.9% on BIRD dev.
  * FINER-SQL (arXiv 2605.03465; code says ICDE 2026): 3B scores 67.8% on BIRD dev. Weights are on Hugging Face under griffith-bigdata.
  * SLM-SQL (IJCNLP-AACL 2025 Findings; arXiv 2507.22478): 1.5B scores 67.08% on BIRD dev. Headline numbers use self-consistency or voting, so single-shot accuracy will be lower.
* **"What Stops a Small Language Model From Driving a Database Agent"** (Kaya et al.; arXiv 2609.21341, September 2026). In general database-agent work, small models fail mainly at the interface and mechanics, not reasoning. It supports our hypothesis and is a different task.

**Novelty statement (careful wording):** to our knowledge, no prior work (1) diagnoses why small judges fail on ClaimDB, (2) tests schema access versus a specialised small NL-to-SQL builder as remedies in a controlled comparison, or (3) uses small specialist NL2SQL models as tools for a small claim-verification judge. Always say "to our knowledge". The field moves fast.

**Important for references:** the venue and author details above were collected during research. **Every BibTeX entry must still be copied from the official source and checked by a human before it goes into the report.**

---

## 7. ClaimDB in detail (read from its code and data)

### 7.1 Data files (in the repository's `final-benchmark/` folder, also in our code package under `code/subsets/`)

* **`test-public.jsonl`:** 1,000 claims (333 ENTAILED, 331 CONTRADICTED, 336 NEI). They come from the **11 BIRD dev databases**: formula_1 130, superhero 120, thrombosis_prediction 109, codebase_community 101, financial 100, european_football_2 92, student_club 82, toxicology 78, california_schools 68, card_games 68, debit_card_specializing 52. The NEI claims split into OUT-OF-SCHEMA 111, COUNTERFACTUAL 113 and SUBJECTIVE 112.
* **Fields per claim:** `claim_id`, `bird_id`, `db_name`, `label`, `claim`, `extra_info`, and for NEI claims also `category`.
* **`test-private.jsonl`:** 999 claims with hidden labels.
* **`train.jsonl`:** 51,369 claims (23,312 NEI, 15,868 CONTRADICTED, 12,189 ENTAILED) over 80 databases. **Warning:** 4,883 of them come from the same 11 dev databases as the test sets, and **607 of the 609 BIRD questions behind the public test claims also appear in train**. Train and test are therefore *not* database-disjoint. Any future training must remove those claims.
* **`BIRD-source.jsonl`:** maps each `bird_id` to the original BIRD question, `evidence`, gold `SQL`, gold `result`, `difficulty`, `split` and a text schema. Example: claim 4652 has `bird_id` 892. Question 892 is "State the driver with the most points scored. Find his full name with that points." Its gold SQL joins `races`, `driverStandings` and `drivers` and orders by points, and the result is Sebastian Vettel, 397.0. So for every claim the correct verifying query is known. The team had told Dr Garg this was not available. **That was wrong and is being corrected.**

### 7.2 ClaimDB's exact agent setup (from `claimdb/experiments.py` and `claimdb/experiments_pydantic_ollama.py`)

* **Input to the judge:** `"Claim: <claim>\nExtra Information: <extra_info>"`. **No schema is given.**
* **System prompt (`FACT_CHECKER_PROMPT_3SHOT`):** a fact-checking assistant over structured data, with the three labels defined. It says to use the tools to query the database before deciding and not to ask for clarification. It ends: "You should always start by querying the database for the schema (tables and columns)." It is followed by the JSON output schema `{verdict, justification}` and three output examples. Our `common.py` copies this text verbatim.
* **Tool:** one per database, named `<db_name>_execute_sql`, served by Google's MCP Toolbox for Databases. Errors are returned to the model as text, for example "error while invoking tool: unable to execute query: SQL logic error: no such column: drivers.id (1)".
* **Open models:** run through **Ollama** with **Pydantic AI 1.44**, `UsageLimits(tool_calls_limit=20)` and `output_retries=20`. If a run exceeds the limits or crashes, the verdict is empty and counts as wrong.
* **Released transcripts:** `experiments/public/<model>.jsonl`, one line per claim with the full message history, stored with Git LFS. They can be downloaded from `https://media.githubusercontent.com/media/claimdb/claimdb/main/experiments/public/<model>.jsonl`, for example `.../qwen3:8b.jsonl`. **On Windows, save the file without the colon**, for example `qwen3_8b_release.jsonl`.

---

## 8. What has already been done

### 8.1 Diagnostic study of ClaimDB's released logs (Experiment 1, complete)

**Method.** We downloaded the released public-test transcripts for 19 models and parsed every message. Per claim we counted:

* SQL calls (the final-answer tool call is excluded);
* schema-lookup calls (queries containing `sqlite_master`, `PRAGMA` or `information_schema`);
* tool results that are errors, classified as no such table, no such column, syntax error, timeout, or other;
* the final verdict.

The accuracies we computed **match the published ClaimDB table exactly**, for example qwen3:8b 0.521, llama3.1:8b 0.344 and gpt-5-mini 0.827. Scripts: `analysis/diagnose_claimdb.py` and `analysis/plots.py`. Results: `analysis/diagnostics.json`.

**Table 1. All 19 models.** All columns are percentages except Params and Calls.

| Model | Params | Accuracy | Macro-F1 | Predicted NEI | SQL calls per claim | Claims with no call | Calls that are schema lookups | Calls that failed | Claims with a grounding error |
|---|---|---|---|---|---|---|---|---|---|
| gpt-5-mini | n/a | 82.7 | 82.8 | 27 | 5.2 | 1 | 49 | 7 | 32 |
| claude-haiku-4.5 | n/a | 80.9 | 81.1 | 23 | 8.2 | 1 | 46 | 1 | 4 |
| gpt-5-nano | n/a | 78.7 | 78.7 | 28 | 6.3 | 0 | 57 | 2 | 9 |
| gpt-oss | 20B | 74.0 | 73.9 | 43 | 5.7 | 0 | 62 | 3 | 12 |
| qwen3-coder | 30B | 67.2 | 67.2 | 36 | 7.8 | 0 | 50 | 2 | 11 |
| nemotron-3-nano | 30B | 66.7 | 67.1 | 41 | 7.3 | 2 | 60 | 7 | 11 |
| ministral-3 | 14B | 62.3 | 62.3 | 37 | 11.0 | 0 | 45 | 32 | 30 |
| qwen3 | 32B | 57.4 | 56.1 | 59 | 2.8 | 6 | 47 | 35 | 50 |
| ministral-3 | 8B | 53.3 | 52.0 | 55 | 8.0 | 0 | 55 | 27 | 66 |
| qwen3 | 14B | 53.1 | 50.2 | 72 | 2.9 | 6 | 50 | 34 | 60 |
| qwen3 | 8B | 52.1 | 48.8 | 70 | 2.8 | 10 | 48 | 31 | 48 |
| qwen3 | 4B | 51.1 | 47.5 | 59 | 1.2 | 51 | 63 | 25 | 17 |
| gpt-4o-mini | n/a | 44.5 | 50.3 | 5 | 5.2 | 37 | 19 | 24 | 54 |
| cogito | 14B | 43.5 | 36.0 | 85 | 4.4 | 0 | 27 | 54 | 92 |
| ministral-3 | 3B | 42.2 | 37.8 | 71 | 9.7 | 1 | 41 | 47 | 74 |
| llama3.2 | 3B | 38.7 | 34.5 | 63 | 2.7 | 18 | 8 | 86 | 55 |
| mistral-nemo | 12B | 38.7 | 37.1 | 50 | 2.4 | 4 | 31 | 64 | 68 |
| qwen3 | 1.7B | 36.6 | 23.9 | 94 | 0.7 | 49 | 5 | 88 | 46 |
| llama3.1 | 8B | 34.4 | 28.8 | 72 | 2.1 | 29 | 17 | 80 | 62 |

(llama3.2 1B was skipped because ClaimDB's released file contains only 146 of the 1,000 claims.)

**Correlations across the 19 models:**

* share of failed calls vs accuracy: r = −0.88;
* share of claims with a grounding error vs accuracy: r = −0.77;
* predicted NEI rate vs accuracy: r = −0.65.

**Error types:**

* **llama3.1 8B:** 1,658 failed calls. 853 were "no such table", 603 "no such column", 168 syntax and 34 other. So 1,456 of 1,658 are grounding errors.
* **qwen3 8B:** 850 failed calls. 663 were "no such column", 163 "no such table", 14 syntax and 10 other. So 826 of 850 are grounding errors.

**Table 2. Grounding errors and wrong abstention.** This uses only claims whose true label is ENTAILED or CONTRADICTED (664 per model), for the 11 open models of 14B or fewer. Each run is put into one of three groups:

* **All queries worked:** at least one call, and no call returned an error.
* **Hit a grounding error:** at least one "no such table" or "no such column" error.
* **Never queried:** zero calls.

Each cell is n / accuracy / share answering NEI.

| Model | All queries worked | Hit a grounding error | Never queried |
|---|---|---|---|
| qwen3 1.7B | 37 / 57% / 24% | 366 / 1% / 98% | 249 / 5% / 92% |
| llama3.2 3B | 70 / 20% / 67% | 384 / 17% / 71% | 120 / 38% / 36% |
| ministral-3 3B | 34 / 53% / 29% | 505 / 18% / 71% | 8 / 12% / 38% |
| qwen3 4B | 183 / 35% / 47% | 143 / 41% / 41% | 331 / 30% / 45% |
| llama3.1 8B | 39 / 49% / 31% | 423 / 10% / 84% | 180 / 21% / 53% |
| ministral-3 8B | 170 / 51% / 30% | 426 / 35% / 49% | 1 / 0% / 0% |
| qwen3 8B | 241 / 40% / 48% | 388 / 27% / 62% | 30 / 3% / 97% |
| mistral-nemo 12B | 160 / 38% / 44% | 447 / 25% / 51% | 28 / 50% / 21% |
| cogito 14B | 44 / 59% / 32% | 610 / 13% / 83% | 1 / 0% / 100% |
| ministral-3 14B | 56 / 73% / 12% | 176 / 45% / 31% | 4 / 0% / 50% |
| qwen3 14B | 173 / 49% / 44% | 478 / 26% / 68% | 4 / 0% / 100% |
| **All 11 pooled** | **1,207 / 43.8% / 41.3%** | **4,346 / 20.8% / 68.2%** | **956 / 21.9% / 58.7%** |

**Notes on Table 2:**

* About 795 of the 7,304 runs had only *other* errors (syntax, timeout) and are in none of the three groups.
* The pattern holds for 9 of the 11 models. The exceptions are qwen3 4B, which barely queries, and llama3.2 3B, which is poor in every group.
* Strong models recover from grounding errors. gpt-5-mini hits one on 32% of claims but is still 89% accurate on those true or false claims.
* **This is correlation, not causation.** Claims that cause errors may also simply be harder. Conditions B and C test causation.
* Even when every query works, small models reach only 44%, so judging ability also matters.

**Real failure examples (from ClaimDB's logs):**

* **qwen3 8B, claim 4652 (true):** it queried `drivers.id` and got "no such column: drivers.id" twice (the column is `driverId`). It answered NEI, saying "The database schema appears to lack a clear driver identifier column".
* **qwen3 8B, claim 16409 (true), "At 16:25:00 on 2012-08-24, the customer paid in CZK":** it queried `transactions_1k.currency` and got "no such column: currency" (currency is in the `customers` table). It answered NEI.
* **llama3.1 8B, claim 5588 (false), about Scotland Premier League fixtures:** it queried a non-existent table `fixture`, got "no such table", and answered NEI.
* **llama3.1 8B, claim 6640 (false):** it queried a non-existent table `thrombosis_predictions` and answered NEI.

**Figures:** `analysis/fig_grounding_vs_outcome.png` (Table 2's pooled row as bars) and `analysis/fig_error_vs_accuracy.png` (failed-call share vs accuracy, one point per model).

### 8.2 Experiment code (built and tested; in `sqljudge_experiments.zip`)

| File | What it does |
|---|---|
| `code/common.py` | ClaimDB's prompt (verbatim) and the per-condition prompt edits; the input format; schema extraction (`CREATE TABLE` statements from `sqlite_master`); read-only SQL execution with a 30-second timeout and ClaimDB-style error messages; the 100-row cap with a "truncated" note. |
| `code/run_judge.py` | Runs one judge on a claims file under condition A, B, C or CS using Pydantic AI 1.44 and Ollama, with the same 20-call limit and 20 output retries as ClaimDB. Writes one line per claim to `results/<model>__<condition>.jsonl` with the verdict, the full transcript (`all_messages`), a `tool_log` of every SQL query or builder call, and timing. **It resumes automatically** if stopped. |
| `code/builder.py` | The NL2SQL builder for Conditions C and CS. It uses an OmniSQL/Arctic-style prompt (or FINER-SQL's), passes schema plus evidence plus question, extracts the SQL and returns it. |
| `code/eval_builder.py` | Tests a builder on its own on the BIRD questions behind a claims file, measuring execution accuracy against the gold SQL results. |
| `code/score.py` | Accuracy with a 95% bootstrap CI, macro-F1, per-label recall, predicted NEI rate, tool-call statistics and error types. It runs a McNemar test between two result files and a reproduction check against ClaimDB's released file (`--claimdb-release`). |
| `code/make_subset.py` | Builds label-balanced subsets with seed 13. Smaller subsets are nested inside larger ones. |
| `code/subsets/` | `subset_210.jsonl` (70 per label, **used for the midsem**), `subset_150.jsonl`, `subset_60.jsonl`, `test-public.jsonl`, `BIRD-source.jsonl`. |
| `tests/test_harness.py` | A plumbing test with scripted fake models on a toy database. All four conditions passed. |
| `code/README.md` | Windows setup and run commands. |

**Deliberate deviation from ClaimDB, applied equally to all conditions:** query results are capped at 100 rows, with a note telling the model to aggregate. Without a cap, one huge result can overflow a local model's context window and silently corrupt the run. Our tool descriptions are our own, because ClaimDB's MCP Toolbox description text was not published. The tool argument is named `sql_query`, as in ClaimDB's Ollama code.

**Reference numbers for the 210-claim subset**, from ClaimDB's released runs restricted to the same claims:

| Model | Accuracy | Predicted NEI |
|---|---|---|
| qwen3:8b | **48.6%** | 73% |
| qwen3:4b | 47.1% | 62% |
| llama3.1:8b | 32.9% | 70% |
| gpt-5-mini | 83.8% | 27% |

---

## 9. Decisions log (approved by Kanishk on 11 October 2026)

| # | Decision | Status |
|---|---|---|
| D1 | **Scope of the paper:** diagnose why small judges fail, then test fixes (schema; NL2SQL builder) without training. Training is future work, revisited after the full evaluation and only if the builder shows promise. | Approved |
| D2 | **Conditions:** A (ClaimDB exact), B (schema given), C (NL2SQL builder), CS (builder plus schema). | Approved |
| D3 | **Judges for the full paper:** qwen3:4b, qwen3:8b, llama3.1:8b. All three appear in ClaimDB's table, so reproduction can be checked. | Approved |
| D4 | **Builders:** SLM-SQL 1.5B, FINER-SQL 3B, Arctic-Text2SQL-R1 7B (Dr Garg's list). Kept frozen. | Approved |
| D5 | **Metrics:** accuracy (primary); macro-F1, predicted NEI rate, calls per claim and error types (secondary); bootstrap CI and McNemar for comparisons. | Approved |
| D6 | **100-row cap** in all conditions, as an equal deviation from ClaimDB. | Approved |
| D7 | **Midsem slice:** judge qwen3:8b on `subset_210.jsonl` (70 per label, about 20% of the test set) under **A, B and C**, plus the builder-alone test. CS waits until after the midsem. Diagnostic study complete. | Approved |
| D8 | **Who runs what:** Kanishk runs C and the builder test. Kushagra and Navtej each run one of A or B (they choose and confirm with each other). | Approved |
| D9 | **Report process:** Kanishk writes the report following the course process. Every line is agreed before writing. Teammates review the draft and must be able to explain it. References come from official sources and are verified by hand. Target 4 pages. | Approved |

---

## 10. The plan

### 10.1 Full paper (whole semester)

| Experiment | What | When |
|---|---|---|
| Diagnosis | ClaimDB's released logs, 19 models (Section 8) | Done |
| Main evaluation | 3 judges × A, B, C, CS × all 1,000 public-test claims | After midsem |
| Builder strength | SLM-SQL 1.5B, FINER-SQL 3B, Arctic 7B in C/CS with one judge | After midsem |
| Error analysis | Hand-check about 100 failures (wrong question, wrong builder SQL, misread result, giving up early), plus each builder alone on the BIRD questions | After midsem (a first slice for the midsem from Kanishk's builder test) |
| Generalisation (optional) | A database outside BIRD | If time permits |
| Training (conditional) | SFT, then possibly RL, to teach the judge to use the builder | Only if C/CS clearly help |

**What makes it a paper:** the diagnosis as the insight, plus a positive result from B and/or C (they clearly beat A for small judges). If neither helps, the team discusses a partial pivot with the mentors.

### 10.2 Midsem slice (by 12 October, report on 13 October)

| Run | Who | Claims | Notes |
|---|---|---|---|
| Condition A, qwen3:8b | Kushagra or Navtej | `subset_210.jsonl` | Expect close to 48.6% if the reproduction is faithful |
| Condition B, qwen3:8b | the other one | `subset_210.jsonl` | The first test of the grounding hypothesis |
| Condition C, qwen3:8b + Arctic-Text2SQL-R1-7B | Kanishk | `subset_210.jsonl` | If time is short, at least the first claims in file order |
| Builder alone (Arctic 7B) | Kanishk | the 189 BIRD questions behind the 210 claims | Separates builder errors from judge errors |

---

## 11. Step-by-step guide for running Condition A or B

**Claude: walk your user through these steps one at a time, explaining each.**

### 11.1 One-time setup (Windows)

1. **Python 3.11** from python.org. During installation tick "Add python.exe to PATH". Check with `python --version`.
2. **Ollama for Windows** from ollama.com. It installs as a normal app and uses an NVIDIA GPU automatically.
3. **Set a larger context window**, then fully quit Ollama from the system tray and reopen it:
   ```
   setx OLLAMA_CONTEXT_LENGTH 16384
   ```
   This lets the model hold the prompt, the schema (in B) and several query results at once. Record the value you used.
4. **Pull the judge model:** `ollama pull qwen3:8b`. This is the same tag ClaimDB used, about 5 GB, 4-bit quantised. Check that it runs with `ollama run qwen3:8b "hello"` and, while it runs, `ollama ps`, which should show the GPU in use.
5. **BIRD dev databases.** Go to bird-bench.github.io, download the dev set and unzip it. Inside, unzip `dev_databases.zip`. You need the folder containing 11 subfolders (california_schools, card_games, codebase_community, debit_card_specializing, european_football_2, financial, formula_1, student_club, superhero, thrombosis_prediction, toxicology), each with a `.sqlite` file. Below, this folder is `C:\bird\dev_databases`.
6. **Unzip `sqljudge_experiments.zip`**, open a terminal in its `code` folder, and run `pip install -r requirements.txt`.
7. **Optional sanity test:** `python ..\tests\test_harness.py C:\path\to\a\folder\containing\toy_db`. This needs a toy database, so it is optional. The plumbing was already tested.

### 11.2 Run

**Condition A:**
```
python run_judge.py --claims subsets\subset_210.jsonl --db-root C:\bird\dev_databases --model qwen3:8b --condition A
```
**Condition B:**
```
python run_judge.py --claims subsets\subset_210.jsonl --db-root C:\bird\dev_databases --model qwen3:8b --condition B
```

* **What you see:** each line prints the claim ID, the gold label, the prediction, the number of tool calls and the seconds taken.
* **Estimate the total time** from the first 10 claims. A rough guess is 20 to 60 seconds per claim, so 210 claims take about 1.5 to 3.5 hours.
* **If the run stops,** run the same command again. It skips the claims already done.
* **Output:** `results\qwen3_8b__A.jsonl` or `results\qwen3_8b__B.jsonl`.

### 11.3 Score

```
python score.py results\qwen3_8b__A.jsonl
```

**For A, also check the reproduction.** Download ClaimDB's released qwen3:8b file (save it without the colon):
```
curl -L -o qwen3_8b_release.jsonl "https://media.githubusercontent.com/media/claimdb/claimdb/main/experiments/public/qwen3:8b.jsonl"
python score.py results\qwen3_8b__A.jsonl --claimdb-release qwen3_8b_release.jsonl
```
This prints the per-claim agreement with ClaimDB's run and both accuracies on the same claims.

**When A and B are both done** (share files with your teammate), compare them:
```
python score.py results\qwen3_8b__A.jsonl results\qwen3_8b__B.jsonl
```

### 11.4 Condition-specific guidance

**Condition A (reproduction):**

* **What it shows.** Our harness reproduces ClaimDB's result for qwen3:8b. Expected accuracy on the subset is around **48.6%**, with a predicted NEI rate around 73%.
* **What can make it differ:** sampling randomness (Ollama's default temperature), a different Ollama version or context length, our 100-row cap, and our tool description text. A difference of a few points is normal. **A large difference (more than about 8 points) must be investigated and reported**: look at a few transcripts, check for crashes (empty verdicts) and check the context length.
* **What to look at:** failed-call share, error types, the share of schema-lookup calls and the predicted NEI rate. These should resemble ClaimDB's qwen3:8b row in Section 8.

**Condition B (schema given):**

* **What changes.**
  * The input starts with "Database schema:" followed by all `CREATE TABLE` statements of that database, then the usual "Claim: ... Extra Information: ...".
  * The prompt's last sentence, "You should always start by querying the database for the schema (tables and columns).", is replaced with "The database schema (tables and columns) is provided together with the claim."
  * Everything else is identical to A.
* **What to expect if our hypothesis holds:**
  * fewer "no such table/column" errors;
  * fewer schema-lookup calls;
  * fewer NEI answers on true or false claims;
  * higher accuracy than A.
* **What could go wrong:**
  * Some BIRD schemas are long. If runs fail or get slow, check the context length (16,384) and report it.
  * If B does *not* beat A, that is still informative: grounding may not be the only bottleneck. Report it honestly.
* **What to look at:** the same statistics as A. Compare with A once both are available, using the McNemar test.

### 11.5 Troubleshooting

* **Model too slow or out of GPU memory.** Check `ollama ps`. If the GPU has less than about 8 GB, try `setx OLLAMA_CONTEXT_LENGTH 8192` and tell Kanishk, because it is a deviation.
* **No usable GPU at all.** Tell Kanishk immediately. A fallback is running qwen3-8b through a hosted API (`--provider openai --base-url <provider URL> --api-key <key>`). That changes the setup (not the same quantisation), so it must be recorded and approved.
* **Database not found.** Check that `--db-root` points to the folder whose subfolders are named after the databases, each containing `<name>.sqlite`.
* **Pydantic AI version errors.** Keep version 1.44.0 exactly, as pinned.

---

## 12. What to hand to Kanishk by 12 October

1. **The results file:** `results\qwen3_8b__A.jsonl` or `__B.jsonl`, even if incomplete. Say how many claims finished.
2. **The full printed output of `score.py`**, saved as a text file. For A, include the `--claimdb-release` reproduction check.
3. **Run details:**
   * GPU model and memory;
   * Ollama version (`ollama --version`);
   * the `OLLAMA_CONTEXT_LENGTH` used;
   * start and end time, average seconds per claim;
   * any crashes, restarts or deviations.
4. **Short notes in plain sentences:** three example claims from your run (one correct, one wrong after a SQL error, one wrong NEI) with what happened, plus anything surprising.
5. **Confirmation that you can explain** your condition and your numbers (Section 13).

---

## 13. Understanding checklist (your user should be able to answer all of these)

1. What is a claim, an "extra information" hint and a label in ClaimDB? Give an example.
2. What is ClaimDB, how was it built from BIRD, and what did it find about small models?
3. What exactly does your condition change compared with the others, and why does that test our hypothesis?
4. Walk through `run_judge.py` for one claim: what goes to the model, what a tool call is, what happens when SQL errors, and when the run ends.
5. Why the 20-call limit, the 30-second timeout and the 100-row cap?
6. How was `subset_210.jsonl` made (balanced, seed 13, 70 per label), and why not use all 1,000 claims for the midsem?
7. Why qwen3:8b?
8. What do accuracy, macro-F1, predicted NEI rate, the bootstrap CI and McNemar's test mean? What do your numbers say?
9. What is the diagnostic insight (Section 8), and why is it correlation and not causation?
10. If your result differs from the expected number, what are the possible reasons?

---

## 14. After the midsem

* Full evaluation: 3 judges × A, B, C, CS × 1,000 claims.
* Builder sizes: SLM-SQL 1.5B, FINER-SQL 3B, Arctic 7B.
* Error analysis on about 100 failures.
* Optionally, a database outside BIRD.
* Training only if C/CS clearly help.
* Write a 4-page paper. The venue is to be confirmed with the mentors.

---

## 15. Open issues and risks

* **Corrections to send Dr Garg:**
  * ClaimDB *does* link claims to their BIRD source SQL.
  * ClaimDB's train and test sets overlap at the database and question level.
* **Contamination:** the NL2SQL builders were trained on BIRD train, and BIRD dev (where the test databases come from) is a standard development benchmark for them. So builder accuracy here may be optimistic.
* **Builder setup:** FINER-SQL and SLM-SQL may need the Hugging Face `transformers` backend (`--builder-backend hf`) if no Ollama build exists. Their prompt formats should be checked against the model cards.
* **References** for the report must be rebuilt from official sources and verified by a human.
* **Kanishk's Claude found during setup:**
  * Hugging Face and the BIRD website were blocked from its cloud workspace, so all model and database downloads must happen on the students' own machines.
  * The ClaimDB transcript files are stored with Git LFS. Use the media.githubusercontent.com links above.

---

## 16. Messages drafted for Dr Garg (Kanishk sends these; status not confirmed)

**Status update (drafted 11 October):**

> Hello sir, now that midsems are over, I have been working on research again and wanted to share where we stand before the mid-semester report.
>
> First, we analysed the logs that the ClaimDB authors released for all 19 models on their 1,000-claim public test set. We found a clear pattern. Small models mostly fail because they guess table or column names that do not exist in the database, their query returns an error, and they then answer "Not Enough Info". On claims that are actually true or false, small models are right only about 21% of the time when this happens, compared with about 44% when all their queries work. Across all 19 models, the share of failed queries is strongly linked to lower accuracy. This suggests the main problem for small models is finding the right data in the database, not judging the claim itself.
>
> Based on this, we have built a pipeline that keeps ClaimDB's exact setup and tests three versions of the same small judge on the same claims: (1) ClaimDB's original setup, where the judge writes its own SQL (our reproduction); (2) the same setup, but with the database schema given along with the claim, as Chirag sir suggested; (3) the judge asks questions in plain English, and an NL2SQL model (Arctic-Text2SQL-R1 7B) writes and runs the SQL.
>
> For the mid-semester report, we are running these three versions with Qwen3-8B on a balanced set of 210 claims. After that, we plan to extend this to all 1,000 claims, two more judge models, the smaller NL2SQL models you suggested (FINER-SQL 3B and SLM-SQL 1.5B), and a manual analysis of the remaining errors. If the NL2SQL tool shows promise, training the judge to use it could be a later step.
>
> One correction to my earlier message: ClaimDB does link each claim to its original BIRD question and SQL, so an oracle comparison is possible if needed.
>
> Please let me know if you would like any changes to this direction.

**Plan after the midsem (drafted 11 October):**

> Hello sir, I also wanted to share our plan for after the mid-semester report.
>
> 1. **Full evaluation:** run all three versions of the judge on the full 1,000-claim ClaimDB public test set with three small judges (Qwen3-4B, Qwen3-8B and Llama-3.1-8B). We will also add a fourth version, where the judge uses the NL2SQL model and is also given the schema. Comparing this with the "schema given" version tells us whether the NL2SQL model helps beyond simply knowing the schema.
> 2. **NL2SQL model size:** compare SLM-SQL 1.5B, FINER-SQL 3B and Arctic-Text2SQL-R1 7B as the NL2SQL tool, to see how much the size and quality of this tool matter.
> 3. **Error analysis:** manually check around 100 remaining wrong answers to see whether the judge asked the wrong question, the NL2SQL model wrote wrong SQL, the judge misread a correct result, or it gave up too early. We will also test each NL2SQL model on its own on the original BIRD questions behind these claims.
> 4. **Generalisation:** if time permits, test the best setup on one database that does not come from BIRD.
> 5. **Training:** only if the NL2SQL version shows a clear improvement, we would then consider training the judge to use it better.
>
> We plan to write this up as a four-page paper following the course template. We would appreciate your suggestions on which conference to target.

---

## Appendices

* **Appendix A.** Mentor messages and the team's message, as received.
* **Appendix B.** The course instructor's lecture on the mid-semester report (full transcript).
* **Appendix C.** The course paper template (text extracted from the PDF).
* **Appendix D.** The original Research Direction Brief.
* **Appendix E.** The original Execution Plan (superseded by the ClaimDB direction, kept for context).
* **Appendix F.** The literature review notes of 18 to 25 September. They are partly superseded: their gap statement predates the ClaimDB-based direction and the corrections in Sections 7 and 15.


---

# Appendix A. Mentor messages and the team's message (as received, transcribed from screenshots)

## A.0 Dr Krishna Garg, 18 September 2026 (task note)

> Sep 18
> - Literature Review and let's solidify the gap (SQL for LLM-as-a-judge)
>   - Task (i/p, o/p), Tools, Settings, Datasets, Models, Findings/ Claims
> - Let's hear back in a few days

## A.1 Dr Krishna Garg, 26 September 2026, 9:52 PM (new direction)

> Hi Kanishk and Team,
> Both Chirag Sir and myself discussed a very concrete direction for the same problem.
>
> ClaimDB showed that small open-source models (under 30B parameters) are terrible at verifying claims against databases — most score below 55%, barely above random guessing. The main reason is that these small models fail at the *mechanics* of database interaction: they often skip querying the database entirely, write broken SQL when they do try, and either ask too few questions (1–2 queries) or spiral into too many (15–20) when the sweet spot is 4–8. Meanwhile, TIR-Judge showed that you can train a small model via reinforcement learning to learn *when and how* to call an external tool (a code executor), and this dramatically improves its judgment ability.
>
> **Research Direction:**
> We would train an SLM judge to query a SQL builder tool, and the SQL builder tool could be an existing SLM-based training model. Another angle would be to train the SLM judges on when to execute this SQL builder tool. The novelty comes from using these SQL builder tools, not just SQL executor tools, which the DB paper showed.
>
> (9:53 PM) Could you people meet at 7 pm IST tomorrow if you have confusion about the idea of the next steps? My understanding is that the next steps would be to reproduce the claim DB paper and finally execute an existing NL-to-SQL tool over the same database, compare directly the results with the claim DB paper.

## A.2 The team's message to Dr Garg (27 September 2026, as Kanishk shared it)

> We plan to investigate four questions:
> 1. Does using a separate SQL builder help compared with the judge writing SQL itself? We will test both untrained and trained judges in both settings.
> 2. Does stronger builder quality improve the overall system? We will compare OmniSQL-7B, Arctic-7B, larger Arctic models, and a strong API model.
> 3. How much does training improve the judge? We will compare untrained, SFT, and SFT+RL judges.
> 4. Do the results generalize beyond BIRD-derived databases?
>
> We will start by reproducing ClaimDB's results on its public test set, and train on the ClaimDB training set, whose databases are separate from those in the test set.
>
> A few points on which we would appreciate your view:
> - We do not plan to build our own NL-to-SQL model initially. We would keep an existing builder fixed and vary its strength instead.
> - Thucy already uses a prompted SQL helper with large models, so our proposed distinction is the use of a small trained judge with a specialized NL-to-SQL builder.
> - ClaimDB does not directly provide the source SQL corresponding to each claim, so a direct oracle-SQL comparison may not be feasible. We are considering an oracle-evidence condition or using a strong API model as the builder instead.
> - The RL stage is likely to require substantially more GPU memory than our local hardware. We would appreciate your guidance on the compute requirements.
>
> (The message also mentioned that the judge would have access to a schema explorer, a Python calculator, and plain-text reasoning.)

**Two statements in this message were later found to be wrong** (see main document Sections 7 and 15): ClaimDB's train and test databases are *not* separate, and ClaimDB *does* link each claim to its source SQL.

## A.3 Dr Krishna Garg's replies, 27 September 2026 (5:58 PM to 5:59 PM)

> \>> "The judge would also have access to a schema explorer, a Python calculator, and plain-text reasoning for claims that do not require database evidence."
> @Chirag Chhablani do we want this also?
>
> \>> "2. Does stronger builder quality improve the overall system* We will compare OmniSQL-7B, Arctic-7B, larger Arctic models, and a strong API model."
> For NL2SQL tools, I would like to try out even **smaller SLMs** like FINER-SQL 3B, SLM-SQL 1.5B, or Arctic-Text2SQL-R1 7B.
>
> \>> "After that, we will train the judge, starting with SFT and then exploring RL along the lines of TIR-Judge."
> Let's not worry about the training for now.
>
> \* We do not plan to build our own NL-to-SQL model initially. We would keep an existing builder fixed and vary its strength instead.
> Correct
>
> \* Thucy already uses a prompted SQL helper with large models, so our proposed distinction is the use of a small trained judge with a specialized NL-to-SQL builder.
> What is Thucy?
>
> \* ClaimDB does not directly provide the source SQL corresponding to each claim, so a direct oracle-SQL comparison may not be feasible. We are considering an oracle-evidence condition or using a strong API model as the builder instead.
> If ClaimDB do not provide the intermediate SQL, it's okay. Let's see the final accuracy and we will need to do some analysis on a small subset.
>
> \* The RL stage is likely to require substantially more GPU memory than our local hardware. We would appreciate your guidance on the compute requirements
> We will try to manage it. We don't know as of now whether we need to go for RL training or not.
>
> ToDos:
> 1. Reproduce ClaimDB paper
> 2. Build a pipeline to plug-in NL2SQL tool instead of LLM writing the query.
>
> The two things can/ should be divided among the students and can be worked parallely. Remember that we need to do this iteration faster since we need to see whether there is some promise in the overall research direction.

(Answer to "What is Thucy?", drafted for Kanishk: Thucy (Theologitis and Suciu, University of Washington, AAAI 2026) is a claim-verification system from the same group as ClaimDB. A GPT-5 "verifier" agent coordinates helper agents, one of which is a "SQL Expert" that writes and runs queries for it. It reaches 94.3% on TabFact. It is prompted only, uses large proprietary models and involves no training.)

## A.4 Chirag Chhablani, 27 September 2026, 7:19 PM

> @KANISHK DIDWANIA - Lets keep the setup closer to setup of claimDB paper since we are trying to beat performance on the claims they propose (atleast to some degree). Here is a thumb rule - Start with simplest experiments. Keep only SQL tool and add new tool only if it increases the performance of SLM in the task of claim verification. Also, what is schema explorer? I thought we will give schema of tables with the claims itself.

(Group chat members visible in the screenshot: Kanishk, Abhiruk Singha, Chirag Chhablani, Dhruv Kumar, Dr Krishna Garg, Kushagra Agnihotri, Navtej Singh Dua.)


---

# Appendix B. Course instructor's lecture on the mid-semester report (full transcript, as shared by Kanishk)

The instructor sent this video and asked students to watch it thoroughly. The transcript is reproduced as received (auto-transcribed, so some words are garbled, for example "latte" means LaTeX and "cloud" means Claude).

Okay. So, All right. So, some points which I think you should note in your notebook also uh for your mid-semester evaluation. First of all, there is no mid-semester exam, right? uh for your mid-semester report. Uh I think the format has already been shared with you, right? So So right so format has already been shared on over leaf. Uh you can essentially make a copy of this and start putting in your content. Uh so till now uh so till now or at least in the last semester we have been focusing on uh submission of eight page reports. Uh so for this semester I'm thinking uh uh we'll reduce it to four to six pages. All right. uh reason is majority of the projects uh which students do to uh the the amount of work is not sufficient enough for an eight-page uh conference track paper right and our goal uh for this for this course projects is that you should be able to sum you should be able to submit it into into a decent uh conference right uh there are workshops also which u which allow you to submit four pages, six pages or eight pages reports.

uh so workshop wise I think students are doing fine but we want to go beyond workshops and target main track conference and for that uh most of the teams are not able to do more not most maybe at least like you can say 50% of the students are not able to do that amount that much amount of work which is required for a main track conference right so uh so therefore we are reducing the requirement to four to six pages and this is uh interesting uh in today's era Because uh before AI uh length if we ask you to write long large high number of pages larger number of pages then it would you would require you you would have to put in lot of effort now it's the opposite you would have to put some effort reducing the length right uh as compared to uh just giving a free hand to AI to write an 8 page 10 page on 12page report right and second thing is uh conference and many of the conferences which we target have a short paper track uh so there you can submit a four-page paper.

So although I've written four to six I'll basically uh during the review mid-semester review and the end semester review I'll push you to bring it to four pages uh to just keep the bare minimum content uh which is actually required and which is really your contribution right we'll see on a case by case basis at some places I might say this work seems reasonable for an 8-page paper especially if you're working with an external collaborator and they feel that you should submit it as an 8-page paper absolutely fine some of you are working on existing projects uh uh there I think we'll have to check again we'll have to revisit it is not necessary that initially if the paper has been submitted as an 8-page paper we can we we have to submit it as an 8-page paper we can reduce the uh length as well uh the bottom line or the target is that we get acceptance as this at these conferences right uh so we want to maximize our chances of acceptance at these conferences and so on and the same draft can be submitted to workshops also so from your perspect perspective, you can submit to workshops also.

That's what students are generally doing these days. But from our perspective, we would like you to submit to conferences, right? And therefore, we want to target four-page papers and exceptions will always be there, right? Then uh then the format is basically already provided to you. So you need to use latte. So don't submit a word formatted file or a markdown file or a Google doc. Don't submit that. and uh so write it in latte. AI is good at writing in latte also. So should not be a problem. Uh right and the paper format is al also given. So in fact what we have given is what you should do is um so if you look at for example abstract right so abstract we have told you you have to basically have three four components problem statement research gap approach and methodology experimental setup and key result right similarly introduction also we have mentioned what all you should add in the introduction right so just give it a read I think uh in today's time I've been mentioning this emphasizing this again and again uh reading is becoming uh more and more scarce students or I will include myself also but at least I'm consciously trying to read something uh uh but unfortunately students are reading lesser and lesser and depending too much on AI uh in software engineering it works because let's say you're building a website you can just see the website and you don't need to look at the code it doesn't work in research uh for example let's say uh let's say you made change in the transformer architecture, right?

And you're proposing a new change in the transformer architecture and uh and then you're running some experiments on that uh you will it will be very difficult to basically make AI write test cases for verifying this transformer architecture and so on and then trusting the test cases and so on. So what I'm trying to say is that uh leaving everything to AI for verification and review uh is a risky process in the world of research. So if you want to do serious and sincere research, then you will have to put some manual effort. Uh we're not saying don't use AI, use AI as much as you want, but spend some manual time also in preparing the draft and doing experiments and so on. At least spend some time verifying what AI has written and so on. Okay. So uh what was I saying? Um I just lost track of what I wanted to say. So anyways uh so stick to the format which is provided for every section we have told you step by step what is required right and um there's some other important points yeah I'll start with like the huh so what is the expectation from the perspective of the mid-semester report so mid-semester report we're not expecting you to finish the project obviously uh what is expected is Okay.

Uh so for example a paper which is focusing on some kind of evaluation benchmarking you are expected to do you're expected to finalize your methodology or set of experiments which you want to perform. So your methodology should be final. If not final at least you should have a fair idea what you are planning to do and then uh you should have some some amount of experimentation. Now the sum amount of experimentation is slightly vague but it will vary from project to project. What I'm trying to emphasize is that it should not happen that you're just submitting a report which has zero experimentation or zero evaluation or zero uh uh results right it should not happen like that. You should not say sir we're still planning what we want to do still figuring out what we want to do. It should not happen uh like that. You should make sure that there is some evaluation some experimentation you have added in your paper. So experiments evaluation. So within this for example you should be clear what experiments you're planning to run. Even if you've not run all the experiments you should be clear uh the list of experiments should be clear.

In fact actually if you look at this template you will see that in the experimental section we have basically broken down the results and discussion part into um results and discussion part into um subsections and each subsection is basically an experiment right and for each experiment you have to write what is the objective right and then what is the finding and so on right So, so at least you should know what is the what are the set of objectives which you're trying to focus on in your research paper or in your project, right? That much should be clear. You should know how do you want to carry out these uh experiments and so on. And additionally, you should you should have performed or run at least, you know, 20% of what uh you're planning to do in your entire semester. Okay. The main takeaway or main objective of or or you know the main um goal of this mid-semester submission is that by the time you're submitting your mid-semester report and I think the date is mentioned what 7th or I think I think the date is wrong we'll give you 2 days after the last day of mid- semester exam so 13th of October so that way you will have some exclusive time for working on your project also uh so so the objective or the goal is that by the time you are submitting your co mid- semester report on October 13th you are clear in your head whether this project is actually going somewhere or not right because we don't want you to work on a project which is not going to lead us anywhere right we already reduced the requirement to eight from eight pages to four pages right and but we want you to work on these four that four-page report should be such that it is leading us to some at least a workshop paper or some kind of acceptance somewhere right we don't know what kind of acceptance but it should be leading us to something or in other words uh by the by October 13th you should be clear in your head that there is at least one interesting insight I'm going to show from my project at least one interesting insight that's all we are asking okay so not uh we're not asking too much but at least there should be one new thing which is coming out of a project one small uh novel finding which you are showing okay uh so other point additional point here is that some of the projects will have negative results in the sense that uh for example mechanistic interpretability right so evaluation papers which are showing very bad performance of large language models agents are fine that's absolutely fine but mechanistic interpretability papers which are showing negative results okay or a fine-tuning approach which is basically showing a negative result that is generally not publishable right so uh so then the next question would be of course if you're getting a negative result in your project then what to do.

So we'll give you more time. So for a for a mid- semester submission you would submit whatever you have and then youly discuss with us or your external mentor and make sure that you try to partially pivot or fully pivot to a problem statement where you can get some interesting insight. Okay. So generally speaking negative results are not interesting enough for the uh research community. Exceptions are always there. Not saying they're never interesting but exceptions are always there. most of the results most of the problems which we are going to work on we need some positive result okay uh right and one more concrete example which I can give is for example let's say you are there's someone who is looking at like an indic version of vending bench I don't recall the team now I mean there's a benchmark so you're looking at like indicing bench so there the expectation is uh so if essentially if you're trying out like let's say n models Right? N models and let's say X number of samples or scenarios or data points. Then your evaluation should cover at least 20% of these.

For example, let's say finally you're planning to do six models. So you should at least run your results on one or two models. If you're planning to cover like thousand samples, so you should at least cover 200 samples in your mid- semester report. So some bare minimum evaluation you need to do as I said so that by October 13th you are clear that this project is leading you somewhere if it is not leading we'll pivot to something else lots of projects are there which have potential and which have not been picked up by students right so don't worry about the availability of project there are many ideas which we have so that's on. All right. Now, the most important part uh most important part is uh how do you write your paper? How do you uh u uh so essentially how do you how do you write your paper? So, So this is assumed or this is known that all of these students are going to use AI. So first thing which you should do is you should read this template which we have given you end to end line by line yourselves.

You can give it to AI also. You can give it to AI. AI can explain you all of that is absolutely fine. But after you're done with all of this please spend 1 hour 2 hour reading this template line by line end to end so that you are clear what is expected out of your report. Right? So 90% I would say may not be 90% but easily 75% or more students what they generally do is they will just basically download this report put it into cloud and chat GPT and ask it to basically format the results in this format the whatever the report is asking and they will not even open the PDF and see even if they are opening they will just see whether it is looking fine or not they will not read even one line of the report and just submit it as is okay so that's what is happening in more than I'm not exaggerating numbers at all 7 more than 75% maybe 75% is lesser but at least 75%. 75 more than 75% of the students are doing this and uh so there is no problem in doing this also but the problem is uh I mean it doesn't matter how you're doing it I mean whether you're doing it or not the end result is that whatever paper you are submitting to a conference or a workshop it is completely you can say u incomprehensible right so why what do I mean by incomprehensible if you read the abstract introduction of any paper you will not understand what they are doing.

Basically AI unfortunately is writing in such complex language and such uses such complex jargon if you read the abstract introduction of even a very simple idea you will not be able to explain what the authors have done. This is not just this university it is happening glo globally and people are really very frustrated and angry with this kind of uh um these kind of papers and uh so it's happening at bits as well. So therefore I am very explicitly clearly telling you up front and it will just take me five minutes to figure out how much effort you have actually spent writing the paper. I uh by God's grace I have read many papers in the last 2 years. uh and um it will just literally I'm telling you it will just take me 5 minutes to figure out how much effort you have put in writing the abstracted introduction right and why because abstract and introduction are two sections of the paper which should be as easy right so abstract introduction should be as easy to understand as possible right as clear accessible By accessible I mean someone who is not an expert in this field should also be able to get some idea of what you're trying to do.

Okay. So for example anyone who has taken just you know machine learning 101 online or machine learning course of this university should be able to understand all of your abstract should be able to understand all of your introductions. that's the uh uh you can say uh criteria or goal which you want to achieve when you are writing these papers right and um so this is something which AI can also do but it doesn't do in the way students are generally using AI so as I said what students are doing doing is they are basically putting the entire thing dumping the entire thing in AI cla whatever you're using and asking it to do it they're essentially trying to zero shot or single shot the entire So it doesn't work. So one thing which you need to do and uh uh one thing which you need to definitely do is spend some time with AI. So we're not we're not saying don't use AI but spend some time with AI read what it has generated at least you should be able to explain for the 75% of the student which I'm saying now they are submitting the paper like that.

If we call them and try ask them to explain the paper they will not be able to explain the paper. In fact, it happened also. There is a very uh highly reputed journal TMLR transactions on machine learning research. I think I shared that link on the group also. Uh what they did was they were experiencing the same issue. So an editor of that uh journal uh invited the uh authors to a zoom call and asked them to explain the paper. Uh I think 70 to 80% of the authors were not able to explain the paper. So uh uh it's a very big problem which we are facing uh at this moment. uh AI is helping in many things but it's actually degrading the quality of paper writing and so on right so therefore I'm spending this full lecture on this writing part so you take it seriously I mean this is not a small thing which I'm talking about it's going to help you all throughout your career also right so if you are just used to using AI blindly it's not going to take you anywhere you need to spend some time manually if AI if you're singleotting everything oneshotting everything then what's the need of your your intelligence if you're not using it so your IQ your intelligence your brain if you're not using it at all then what's why should we even hire you right you can think it from that perspective also what are you contributing what are you bringing to the table okay as of now AI has not become good that it can write uh uh conference level papers at the moment we don't know what's going to happen in the future so that's the expectation from you that you are able to bring the paper to a stage where uh it is easy to understand clear accessible now the next question here which will come is many of you will say sir we have never written papers we have not really read many papers then how can we do a good job reading the paper so that's a fair argument so one exercise which clicked to me today morning while I was taking the same lecture for the agent course is uh what you should do is you should basically make it a goal of doing four iterations on your paper three to four iterations and what are these iterations so all of us are very you know good at step by step following the algorithm if we give you the algorithm.

So if you want to follow something, follow one algorithm sincerely. So follow this algorithm which I'm telling you. Okay. First of all, spend a couple of hours reading this template. Okay. Okay. Second, for your convenience, I've also kind of rewritten this template in the form of a prompt which you can give it to the AI. So read this prompt, right? Read this prompt line by line. yourself. So spend a couple of hours, three, four hours just reading okay so that you come to know what is expected what what AI has to do how otherwise how will you even verify what AI has done if you don't even know what is there in the prompt then how will you verify what AI has done so you should read the prompt what you are feeding to the model right okay this is just a one-time thing frankly speaking if you do this once then you're set for at least next 2 three years at least one year I don't know how AI will evolve beyond that but at least you're set for one Okay, then you can whatever AI tool you're using to write the paper, you can write feed it this prompt, give it your content, it will write something.

The other thing is u so maybe I'll come back to that thing later on. The other thing is uh once you have basically generated the initial content or written the initial draft u using this prompt and whatever whatever results etc you've got read it yourselves read it yourselves line by line patiently okay so read the paper read the draft yourselves Okay, for example, let's say Dlesh writes the paper and he will read it himself based on that. So read it yourselves and then see what parts of the prompt are actually for each section, abstract, introduction, related work, methodology, right? Which parts of the prompt or the template are actually present in your paper? which parts are not present or not uh actually uh or or the draft doesn't follow some parts of the prompt, doesn't follow some parts of the template. For example, these are actually very simple simple things. For example, write in academic research language. Use full complete sentences throughout. Do not use short noun phrases or fragment style bullets uh where pro is called for. Some bullets are fine, for example, a list of contributions, but do not default to bullets as a way to avoid writing full sentences.

Now this is plain English. There's nothing much to explain here, right? You know what we are trying to what we are asking the II to do. So you should check break long sentences up. So should you identify whether there are too many long sentences or not, right? And use simple language wherever possible. If a technical term is unavoidable, define it the first time it appears unless the term is already very common knowledge for the specific domain or community you're writing for. Right? So these are very simple instructions which you can also understand. Right? You're you're expected to understand. Other thing is do not write defensively. For example, you will often see AI is writing this means X not Y. This is A rather than B. So this negative defense or this defensive language is really really very um annoying and I would say so remove these highlight in your give this feedback to the uh model saying that why have you not removed these uh uh defensive uh style of writing when we actually asked you to do that in the initial prompt. Right? So the quality of the paper will improve only when you give some feedback to AI.

It will not do a good job at one shot because the problem is that some of you might be wondering why it cannot do a good job at one shot. Although it is now these models are very good at instruction following and all that. They are not able to do this in one shot because uh you're essentially asking them to you know change their very ingrained writing behavior. So that is something which very which is very difficult to uh you know change. In fact, uh I don't know how much you have read about these AI detectors and so on, right? Uh I had spent some time during the summer uh working on like can we actually force claude or chat GPT to not write like AI or to uh write like you know uh humans. So it was not able to do claude charge deputy they were not able to do. In fact, that's also an instruction. Now, it might it was at least surprising to me at that time that why, you know, it's a very simple instruction. Why can't you write like a human?

It cannot because they're like too too fine-tuned, too heavily trained on a very specific type of writing and behavior that you cannot change just by doing it single shot and you have to basically do it iteratively, repeatedly. Then also it's not going to write like human but at least it will fix these issues which are there in the writing. Right? So that's why you have to do it in multiple iterations. is not going to do in one shot. Right? For example, never use m dashes or n dashes connectors. Never use semicolons as connectors between clauses. Right? So all of these are very straightforward things. uh right for other thing is even for section by section I mentioned like uh what all details uh um are required right and uh so some of this content would be overlapping also you will see but you need to read this still okay u other part is references okay so this I'll come back to in a bit but still just finishing the prompt here uh to do not add any hallucinated reference hallucinated citation. So uh the so again actually I forgot so let's first finish this.

So you start with reading the template. Then you read the prompt. Spend a couple of hours 2 three hours reading this. I don't think it should take more than two three hours. Then you read the draft yourself. Once you have generated the AI paper using this uh I mean AI written draft uh using AI using this prompt. Then what you should do is for example Dlesh has uh generated or drafted the paper with AI and he has read also and and given some feedback to the AI to improve the paper right. So read the draft and then basically iteratively work with the AI. Iteratively work with AI to improve work with AI uh to polish the paper. Right? Then what should what you should do is you should repeat this exercise with your team members within your group. Dles has two three other I think Chetanya was part of the same group. Right? So you have two three group members. So then you give this draft to other team members. So so that way so then the question which Chetan has to answer is that is he actually able to understand what DH has written?

Because if Chetan is not able to understand what Dles has written, how am I supposed to understand or how am I how am how is any other reader supposed to understand if you yourself cannot understand what you are writing. Right? So fourth step is ask your team members to review and give feedback. Feedback is same. You have to basically point out like what part of the prompt, what part of the template it's not following and what part of the paragraph, what part of the text you are not able to understand what is mentioned right so this much is required for your mid-semester report you do this much I'm telling one or two more iterations for your uh ultimate submission at the end of the semester right so this will let's see I'm also doing this experiment hopefully trusting you guys that you at least some of you will follow this and we'll see how the results uh as I said it will just take me 5 7 minutes to figure out how much effort you have put in writing the paper. Okay. So I'm expecting some positive results if not all but at least some of you will follow this.

It's not too much of time taking frankly speaking the 2 hours of reading is here. Okay this anyway you have written the run the experiments right anyway you should read the paper otherwise what's the point of writing the paper if you can't read your own paper. This anyway you have to do All we are asking is just read the paper, give feedback to AI. That's all we are asking. We are asking bare minimum then anyway your team members are going to get the basically the credit for the same paper which you are writing. So why not just ask them to at least read the paper. Okay. This is like bare minimum we are asking. Then additional two steps which you can do is uh so this is not required for MIT because I understand you have other courses and all that also. If you can do other two steps well and good but if you can't do at least do this. The next step is so till now you have given your paper to I mean you you have yourself read the paper and you have asked your team members to read the paper.

Now you ask other teams to read the paper at least select two teams within the class. I for most of you will have some friends. Simple huh? So at least you will have one team right with which which you can request to read your paper and give feedback right so ask other teams okay so they will also give the same feedback paper in your paper I'm not able to understand abstract introduction at least this is the first feedback which I'm giving again for more than 75% of the papers after reading the abstract introduction not able to understand anything after reading abstract introduction. So maybe they will also say the same thing but at least they should come back saying sixth. So once you've done this again you will work with AI to fix the feedback whatever they have given ask some of your friends outside the course. So ask your friends outside the course at least one or two friends. Anyway you spend so much of time with your friends why not discuss something interesting which you have done as part of the course project.

Okay. Again this is not too much to ask. It is just going to take a couple of hours to read do to give a reading of the research paper and give feedback. Okay. So the point which you should take away from all of this discussion is that use AI as much as you want but work iteratively with AI. There is a more difficult option which many of the researchers are u uh suggesting which I'm not suggesting because I know most of you will not anyway do it. The difficult version is or the difficult path is you actually don't use AI for the first draft. You write it yourselves in whatever tutty footy English with as many mistakes, grammatical mistakes and all that without worrying about all that. Just write it yourselves. You can do this if anyone is sincere enough. You can do this right. So what you can do is we have already told you. So the entire paper is kind of you can say questions. Just write the answers in your own language. It can be in short also. Okay. You can do that.

actually you can try to do it at least for abstract introduction because if you do that now paper quality you will yourself also start feeling it's actually a much better quality so you can give it a try I mean you can at least do it for abstract introduction because if you do a good job at abstract introduction then you can do a good job at other sections also the most difficult sections to write in any research paper is abstract introduction okay so you can do that also if you want but uh at least do this what I'm saying. Let's see what results we get. But best is you essentially write the first draft in uh in in Hindi. You can write it in Hindi also. You can write it in English also. You can write it in whatever language you are comfortable with. You can even use just a you know nowadays these are dictating apps are becoming so popular. Just dictate answers to all of these questions, right? Transcribe and put it into AI. That is that will also do a good job. Okay, you can do that also.

So that's the style which uh researchers are suggesting. Uh but if you don't want to follow that at least follow uh this the other style which we just discussed. Okay. All right. Um there were other points also. Any questions till now? So the other part is uh so you are basically evaluated you are going to be evaluated on this you can say on based on this template how much you followed the template and based on this prompt how much you followed the prompt right again we're not asking you to follow it line by line broadly we will check it's not going to be like a line by line feedback that in this line you followed this step not followed this step section by section will give you some highle feedback any any questions so Is it making sense what we are discussing? Do you think this is reasonable? Okay, any questions or you're already um convinced that this is what you have to do? Okay. All right. The last part before we stop u um so um another major issue which we are facing in the world of research is uh people are essentially blindly using AI.

So what's happening is uh they are adding these references citations using AI and AI is basically fabricating or hallucinating citations references which don't even exist in real life. In fact, what has happened is even at top tier conferences like the the best conferences uh papers have been submitted withinated references and papers have been accepted with hallucinated references only at the time of camera ready submission the final submission which the authors have to do once the papers have been accept accepted the program chairs or the conference organizers are coming to know that there are hallucinated references in the paper right so uh so for some of these conferences what they did Because even if the paper was accepted, the paper was then rejected because it had these references which didn't even exist which was kind of indicating that the authors did not even you know proofread the paper draft. So then if that's the issue then there is you can't trust the authors with any other piece of information which they have presented in the paper right. So there was a very strong decision taken of rejecting all such papers and it's a very big thing.

Uh most of you will not understand this because uh but uh just to help you understand uh one conference acceptance main track full full page a full eightpage paper takes around like any anywhere between 8 months to one one year or more of effort in terms of doing experiments writing paper and all of that and after one one and a one year you are basically coming to know that your paper is getting rejected after it has been accepted. It's it's very discouraging, very disappointing, very discouraging and heartbreaking also, right? Because as PhD students, as researchers, I think uh everyone puts in a lot of effort getting uh submitting papers to these top conferences. So now it has become very strict uh right and people have become very strict and even if there is one hallucinated reference which is clear indication of irresponsibility on your on the author's side papers are getting rejected. This is what we are going to follow in this course also. So this is something which you can easily fix with again with additional one or two hours of effort. Right? So our recommendation here is that whatever citation, whatever reference you are adding, you add it manually.

Right? Add it manually. Don't use AI. Even if you want to use AI, at least verify what AI has added. Okay. The other thing is that for many of the papers, what AI will do is I think I had shared one example in the morning lecture also. What AI will do it do is for example this is one of our papers the same paper you will find on archive right and but this paper has already been accepted at a conference right so you will find it in the conference proceedings also so this is the conference proceeding all right the way to add citation is that you have to basically understand or learn uh so in generally in latte the way to add citations is you first of all maintain a database of all the papers from which you want to site a paper in your paper right so I'm calling it as a database but it is essentially a file a file where you have all these entries so each paper is basically one one such entry visible right now The problem is AI hallucinates or generate these entries on its own.

Right? So what you need to do is either you either AI automatically downloads it either from here. This is called as a BIP tech citation basically right either you download it from here and copy it here right manually or you download it from here right bip tag entry and copy it here. So what you are supposed to do it do is you're supposed to download it from the original source. So for 75 80% of your of the papers which you're citing in your report they will already be published or accepted somewhere. Okay. So for those papers you should basically add this bipek entry copy the bipek entry from the original source. Don't use the archive version. This you might have to do manually. AI also can do it uh if you want to rely on AI but you have to check it manually whether it is correct or not. Okay. So what we are going to evaluate is uh all the author names are correct, the title of the paper is correct, venue where it is published or accepted is correct and the year of publication.

These four things we are going to check. Essentially there should not be any piece of information which is incorrect. Okay. uh also uh so as I'm mentioning the same paper can be on archive same paper can be on maybe already published so you have to look at the original source the latest source in some sense basically okay not just the latest because sometimes what people do is the paper is already published but then on archive they have published one more recent version of the paper but we will still site the original source basically wherever the paper has been published conference journal or whatever okay the other thing is uh this there was just one more point which I wanted to mention uh for some of the papers you will not find you will not be able to find the original source okay so for those papers you can use archive but we generally speaking we don't expect you to use more than 25 or 30% of the papers so if your if your biblography or if your references have 30 papers then not more than six seven papers or eight papers at max at max 10 papers should be from archive rest 20 22 papers should be from original sources right uh the other point is you can again use AI or whatever you can so I've added this helloation checker prompt also you can give it to your codeex cloud code or whatever it can give you a nice report where it will basically mention where it will explain you for every reference what are the issues so you can use this also if you want we are going to use this skill to automatically check what are the issues And if there are very serious issues with your references, we will penalize you on that as well.

The focus is not on marks or grade or penalty. But we are doing this as part of the course. So we have to penalize you in some way to incentivize that you do a good job. Okay? So you can use this prompt as well. All right. And uh yeah, I think that's all from my side. Let me just check if there is anything else we want to discuss. Okay. So I think yeah that's all from my side in crux I think your job while writing the paper your focus while writing the paper should be to make it as simple and easy to understand as possible while following the academic research language that's like slight a small constraint because otherwise you can ask AI to make it as simple as possible but then it will not be uh it might compromise on the research paper language or research paper format research paper quality as well so we don't want you to do that Okay. So, any questions anyone otherwise we'll just stop for today and then we'll continue after the mid-semester exams. So, today's the last day of classes, right?

Uh huh. >> Huh. >> So, one is sufficient for the overall diagram. Other thing which you can do is if you have some time at least after mids you should do this. I have added some uh recordings here two three recordings. You can take a look. I think I'll add one or two more recordings here if you if required. it just go through these recordings in your free time. We have done a lot of discussion around what is acceptable, what is not acceptable, what is a good practice, what is not a good practice and so on. Okay. So all in all doing research, writing research paper, reading research paper, there are no these are not I mean uh nowadays nothing is rocket science because you have all the intelligence of the world with you at your laptop using claude and chat GPT but you just need to put in some time basically as long as you put ready to put in the time ready to spend some manual effort I think you'll do a good job. Okay. All right. Any other questions? Huh? So you can take feedback using AI.

We will also give you some feedback during the mid-semester review. But you can do this uh you can take feedback uh using AI also. In fact uh I have also added um I think review prompt I have not added here. There are some bits and pieces I've added. You can take a look at this if you want. And uh and there is a detailed prompt also which I prepared which I'll share later on. You can do that also. Okay. But you can check you can yeah basic consistency checks basic checks of the paper can be done by AI. You can ask like for example um have I actually done all the important experiments or not. So generally speaking AI will tell you 80% of the experiments but 20% is remaining. You have to then use your own brain to see whether it is actually important or not. Okay. General practice is general rule of thumb is if an experiment is feasible and it's not very challenging add it. Okay. Uh because generally reviewers and reviewers they like more and large number of experiments in your paper.

Okay. >> Missing what? >> Yes. Yes. Yes. So that's the missing experiment, right? That's the missing experiment. So even with this also I mean so you can use AI to get some feedback and identify what data sets you should run on, what models you should try out, what experiments, what ablations etc you need to run. Uh but beyond that that always happens in reviews. Uh you will get some new experiment request from the reviewer which you have to satisfy. So that happens anyways. So we're not going to penalize you on that until unless it is very very obvious. Okay. Okay. All right then. Thank you.


---

# Appendix C. Course paper template (text extracted from the PDF; the real template is on Overleaf)

```text
            [Your Paper Title Here: Concise, Descriptive, and Keyword-Rich]


                                            Anonymous ACL submission




001                        Abstract                              a new benchmark, or a new evaluation framework?         042
                                                                 Explain at a conceptual level how your approach         043
002       [PROBLEM STATEMENT:] [1–2 sentences
003       on the core problem you are solving and why            bridges the gap above. (??).]                           044

004       it is important or practically relevant.] [RE-            [Briefly describe your experimental setup:           045
005       SEARCH GAP:] [1–2 sentences on what ex-                datasets, models, and what you measured. Sum-           046
006       isting work has failed to address and what un-         marize your headline result in 1–2 sentences, e.g.,     047
007       explored angle this paper focuses on.] [AP-            “Our method achieves X% improvement over the            048
008       PROACH & METHODOLOGY:] [1–2 sen-                       strongest baseline on [Dataset], demonstrating that     049
009       tences describing your proposed approach at
                                                                 [key insight].” (??).]                                  050
010       a high level — the key idea or innovation
011       behind your method.] [EXPERIMENTAL                     Contributions.     Our main contributions are as        051
012       SETUP & KEY RESULT:] [1–2 sentences
                                                                 follows:                                                052
013       on the datasets and models used, and the single
014       most important result or takeaway from your
015       experiments.]                                              • [Contribution 1]: [e.g., We introduce             053
                                                                       M ETHOD NAME, a novel framework for [task]        054
016   1   Introduction                                                 that addresses [limitation] by [key mecha-        055
                                                                       nism].]                                           056
017   [Begin with a broad overview of the research do-
018   main — e.g., natural language processing, infor-
                                                                     • [Contribution 2]: [e.g., We construct             057
019   mation retrieval, multilingual understanding, etc.
                                                                       DATASET NAME, a benchmark of N samples            058
020   Establish why this area is important and currently
                                                                       spanning K domains/languages — the first to       059
021   active. Introduce the real-world or scientific con-
                                                                       cover [property].]                                060
022   text that makes the problem worth studying. This
023   paragraph should be accessible to a reader who is              • [Contribution 3]: [e.g., Through extensive        061
024   not a specialist in your sub-area. (???).]                       experiments across N models and M datasets,       062
025      [Narrow down from the broad domain to your                    we show that [finding], providing new insights    063
026   specific problem. Define the task clearly: what are              into [phenomenon].]                               064
027   the inputs, outputs, and constraints? Explain why
028   this problem is difficult or non-trivial. Highlight            • [Contribution 4 — optional]: [e.g., We            065
029   challenges such as ambiguity, scale, domain diver-               release all code, data, and model check-          066
030   sity, or lack of supervision. Make explicit what                 points at https://github.com/[yourrepo]           067
031   “solving” this problem would mean. (??).]                        to support reproducibility.]                      068
032      [Survey the most relevant prior work. What
033   methods, benchmarks, or datasets currently exist?          2    Related Work                                       069
034   Then critically identify what is still missing — the
035   gap(s) your paper addresses. Be specific: is the           2.1 [Category 1 — e.g., Task-Specific Models /          070

036   gap missing multilingual coverage, an unexplored               Foundational Methods]                               071

037   domain, a missing evaluation dimension, or an ar-          [Describe the body of work in this category. What       072
038   chitectural limitation? (?????).]                          problems did these papers address? What meth-           073
039      [Introduce your approach without going into im-         ods, architectures, or training regimes did they use?   074
040   plementation details. What is the key idea? Is it a        What did they achieve, and where do they fall short     075
041   new model architecture, a novel prompting strategy,        with respect to your problem? (?????).]                 076


                                                             1
                                                                         annotation process. If this is a model/system pa-      116
      Figure 1: Overview of [Your System / Method Name].
                                                                         per: describe the input representation or the first    117
      [Describe the block diagram here: label each compo-
      nent, describe the flow of information between them,               processing stage. Explain the rationale for your       118

      and highlight the key novelty. e.g., “Our pipeline con-            design choices.]                                       119
      sists of three stages: (1) [Stage 1 description], (2) [Stage
      2 description], and (3) [Stage 3 description]. Colors              3.3     [Component 2 — e.g., Core Model /              120
      denote different functional modules.”]                                     Algorithm / Approach]                          121

                                                                         [Describe the main technical contribution — the        122

077   Gap addressed by this paper: [1–2 sentences                        model architecture, algorithm, prompting strategy,     123

078   explicitly stating what remains unsolved in this                   retrieval mechanism, etc. Use equations if helpful.    124

079   category and how your work fills that gap.]                        For example, the core prediction is:                   125


080   2.2    [Category 2 — e.g., Benchmarks &                                               ŷ = fθ (x; C),              (1)    126
081          Evaluation Frameworks]
                                                                         where x is the input, C is [context / context set],    127
082   [Describe existing datasets, benchmarks, or evalu-
                                                                         and fθ denotes [your model]. Explain how this          128
083   ation protocols relevant to your task. Cover their
                                                                         component directly addresses the research gap.]        129
084   scope, annotation schemes, languages, domains,
085   and known limitations such as limited diversity,                   3.3.1    [Sub-component 2a — e.g., Encoding            130
086   annotation noise, or lack of adversarial examples.                          Module]                                       131
087   (????).]
                                                                         [Describe sub-component 2a here.]                      132
088   Gap addressed by this paper: [1–2 sentences on
089   what your benchmark or evaluation setup adds over                  3.3.2    [Sub-component 2b — e.g., Decoding /          133
090   existing ones.]                                                             Inference Module]                             134

091   2.3    [Category 3 — e.g., Large Language                          [Describe sub-component 2b here.]                      135

092          Models / Prompting / Agents]
                                                                         3.4     [Component 3 — e.g., Output Generation         136
093   [Describe the third major category — this could be                         / Reasoning Module / Post-Processing]          137
094   LLMs applied to your domain, prompting or fine-
                                                                         [Describe the final stage of your pipeline. How are    138
095   tuning strategies, retrieval-augmented generation,
                                                                         outputs generated, predictions made, or results ag-    139
096   agent-based systems, or any other theme central to
                                                                         gregated? Explain any scoring, ranking, or decision    140
097   your paper. What have these works demonstrated?
                                                                         logic used here.]                                      141
098   Which settings have they not explored that you do?
099   (????).]                                                           3.5     Design Choices and Justification               142
100   Gap addressed by this paper: [1–2 sentences on
101   the specific novelty your paper brings relative to                 [Justify key design decisions. Why this architec-      143

102   this body of literature.]                                          ture over alternatives? Why these components and       144
                                                                         not others? This helps reviewers evaluate the va-      145
103   3     Methodology                                                  lidity of your approach and strengthens the paper’s    146
                                                                         narrative.]                                            147
104   3.1    Overview
105   [Provide a 2–3 sentence summary of the overall                     4     Experimental Setup                               148
106   approach. Reference Figure 1 here, e.g., “Figure 1
                                                                         4.1     Datasets                                       149
107   illustrates the end-to-end pipeline of our proposed
108   system.” Describe the high-level flow: what goes                   [Introduce the datasets used in your experiments.      150
109   in, what processing stages occur, and what comes                   For each dataset describe its source, domain, size,    151
110   out.]                                                              language(s), and why it was selected. Table 1 sum-     152
                                                                         marises key statistics.]                               153
111   3.2    [Component 1 — e.g., Data Collection &                         [2–3 sentences of commentary on Table 1. Ex-        154
112          Preprocessing / Input Representation]                       plain why this combination of datasets was chosen      155
113   [Describe the first major component of your sys-                   and what each one contributes to the evaluation,       156
114   tem. If this is a dataset paper: describe your data                e.g., domain diversity, language coverage, or diffi-   157
115   collection protocol, sources, filtering criteria, and              culty level.]                                          158


                                                                     2
                             Dataset       Domain     #Train     #Test    Ref.
                             [Dataset 1]   [Domain]      [N]       [N]    (?) Dataset 2>Dataset 2
                                           [Domain]      [N]       [N]    (?) Dataset 3>Dataset 3
                                           [Domain]      [N]       [N]    (?)

                                  Table 1: Summary of datasets used in our experiments.


159   4.2    Models
                                                                 Figure 2: [Caption for this figure, e.g., “Performance of
160   [Describe each model used for evaluation, fine-            all systems on [Dataset] across three metrics. Our full
161   tuning, or as a backbone. State the architecture           system (blue) consistently outperforms all baselines.”]
162   family, approximate parameter count, and usage
163   mode (zero-shot, few-shot, or fine-tuned). See Ta-
164   ble 2.]                                                    Figure 3: [Caption, e.g., “Heatmap of F1 scores per
165      [2–3 sentences of commentary on Table 2. Ex-            domain for all evaluated systems. Darker cells indicate
                                                                 higher performance.”]
166   plain why this mix of models was selected — e.g.,
167   to study the effect of scale, to compare open-weight
168   vs. proprietary systems, or to assess resource-            Findings. [Discuss what Table 5 shows. Which                200
169   constrained settings.]                                     system performs best overall? By how much?                  201

170   4.3    Evaluation Metrics                                  Are the gains consistent across datasets and met-           202
                                                                 rics? Provide an intuitive explanation for why your         203
171   [Describe each evaluation metric and why it is ap-         method outperforms the baselines. Flag any sur-             204
172   propriate for your task. Specify computation de-           prising or counterintuitive results and hypothesize         205
173   tails — e.g., macro vs. micro F1, BLEU order, or           why they occur.]                                            206
174   significance threshold. See Table 3.]
175      [Commentary on Table 3: identify which metric
                                                                 5.2     [Experiment 2: Ablation Study]                      207
176   is primary and why. Mention any known limita-
177   tions of the chosen metrics and how you address            Objective. [E.g., “To quantify the contribution             208
178   them.]                                                     of each component of our system, we remove one              209
                                                                 component at a time and measure the resulting               210
179   4.4    Baselines                                           performance degradation.”]                                  211
180   [Describe all systems compared, including external
181   baselines from prior work and ablations/variants of        Findings. [Which component contributes the                  212
182   your own system. Table 4 provides an overview.]            most? Which the least? Does removing any com-               213
183      [Commentary on Table 4: explain the rationale           ponent hurt performance more than expected? Pro-            214
184   for each baseline — what claim does it test? What          vide mechanistic explanations where possible —              215
185   does each ablation isolate?]                               e.g., “Removing Component A causes the largest              216
                                                                 drop because it handles [function]; without it the          217
186   4.5    Implementation Details                              model must resort to [fallback].”]                          218
187   [Describe high-level implementation details rele-
188   vant to reproducibility: hardware (e.g., 4×A100            5.3     [Experiment 3: Analysis by Domain /                 219
189   GPUs), training duration, batch size, learning rate                Language / Model Size]                              220
190   schedule, random seeds, and hyperparameter selec-
191   tion strategy. Avoid low-level code details. State         Objective. [E.g., “To understand how perfor-                221

192   whether code and data will be publicly released.]          mance varies across domains, languages, or model            222
                                                                 scales, we break down results along these dimen-            223
193   5     Results and Discussion                               sions.”]                                                    224

194   5.1    [Experiment 1: Main Results — Overall               Findings. [Where does your system improve the               225
195          Performance]                                        most? Where does it struggle? What do these pat-            226
196   Objective. [What question does this experiment             terns tell you about the strengths and limitations of       227
197   answer? e.g., “Does our proposed method outper-            your approach? e.g., “Our method gains the most             228
198   form existing baselines on the primary evaluation          on [Subset 1], likely because [reason], but under-          229
199   benchmarks?”]                                              performs on [Subset 3], suggesting [limitation].”]          230


                                                             3
                                 Model         Architecture       Params     Mode
                                 [Model 1]     [Decoder-only]        [7B]    Fine-tuned Model 2>Model 2
                                               [Enc-Dec]             [3B]    Fine-tuned Model 3>Model 3
                                               [GPT-based]         [175B]    Zero-shot Model 4>Model 4
                                               [Enc-Dec]          [250M]     Few-shot

                                 Table 2: Models used in our experiments with references (????).

              Metric                 Measures                     Higher = Better?
              [Metric 1, e.g., F1]   [Precision/recall balance]   Yes Metric 2, e.g., BLEU>Metric 2, e.g., BLEU
                                     [N-gram overlap]             Yes Metric 3, e.g., BERTScore>Metric 3, e.g., BERTScore
                                     [Semantic similarity]        Yes Metric 4, e.g., Latency>Metric 4, e.g., Latency
                                     [Inference time (ms)]        No

                                             Table 3: Evaluation metrics used in our study.


231   5.4    [Experiment 4 — Qualitative / Error                         X% improvement over the strongest baseline on           266
232          Analysis (Optional)]                                        [benchmark].”]                                          267

233   Objective. [E.g., “To gain deeper insight into                        [PARAGRAPH 2 — Broader impact & take-                268

234   model behavior, we perform a qualitative error anal-               aways: What should the reader take away? What           269

235   ysis on a random sample of N outputs, categorising                 has this work established or made possible that did     270

236   errors into a taxonomy.”]                                          not exist before? Reinforce the significance of your    271
                                                                         contributions in the context of the field.]             272
237   Findings. [What are the most common failure                           [PARAGRAPH 3 — Future work: What are the             273
238   modes? Are there systematic patterns? Provide 2–                   natural next steps? What would you pursue with          274
239   3 concrete input/output examples illustrating both                 more time, data, or compute? What open questions        275
240   success and failure cases. What do these patterns                  remain? e.g., “Future work will explore [direction      276
241   suggest about future improvements?]                                1], [direction 2], and the application of [method] to   277
                                                                         [new setting].”]                                        278
242   5.5    Discussion
243   [PARAGRAPH 1 — Synthesis: What is the sin-                         Limitations                                             279
244   gle most important takeaway from all your experi-
245   ments? How do the individual results fit together                     • Dataset limitations: [The datasets used may        280

246   into a coherent story?]                                                 not fully represent all languages, dialects, or    281

247      [PARAGRAPH 2 — Implications: What do your                            demographic groups. Annotation quality may         282

248   findings mean for the broader research community?                       vary across sources, and dataset size may be       283

249   Does your work challenge any prevailing assump-                         insufficient for fine-grained sub-group analy-     284

250   tions or open new research directions?]                                 sis.]                                              285

251      [PARAGRAPH 3 — Comparison to related
252   work: How do your results compare to the prior                        • Methodological limitations: [Our approach          286

253   work discussed in Section 2? Do your findings                           assumes [assumption], which may not hold in        287

254   confirm, contradict, or extend their conclusions?]                      all real-world settings. The method requires       288
                                                                              [input type] that may not always be available      289
255      [PARAGRAPH 4 — Practical relevance (op-
                                                                              in practice.]                                      290
256   tional): Are there direct real-world applications
257   of your findings? Who would benefit from using
                                                                            • Model limitations: [We evaluated models up         291
258   your system, dataset, or method?]
                                                                              to [X]B parameters; behaviour at larger scales     292

259   6     Conclusion                                                        is unknown. Proprietary models are accessed        293
                                                                              via API without access to weights or logits,       294
260   [PARAGRAPH 1 — Summary: Restate the prob-                               limiting interpretability.]                        295
261   lem, your approach, and your key results with
262   specific details. e.g., “In this paper we intro-                      • Computational limitations: [Full fine-tuning       296
263   duced M ETHOD NAME, a [description] approach                            experiments were constrained by GPU avail-         297
264   for [task]. Evaluating across N datasets and M                          ability. Some configurations were tested only      298
265   models, we demonstrated [key finding], achieving                        at smaller scale due to cost constraints.]         299


                                                                     4
                       System           Type       Description
                       [Baseline 1]     External   [Fine-tuned X on task Y (?)] Baseline 2>Baseline 2
                                        External   [GPT-4 zero-shot (?)] Baseline 3>Baseline 3
                                        External   [SOTA from ACL 2024 (?)] Ours w/o A>Ours w/o A
                                        Ablation   [Full system minus Component A] Ours w/o B>Ours w/o B
                                        Ablation   [Full system minus Component B]
                       Ours (Full)      Proposed   [Complete system]

                                         Table 4: Systems compared in our experiments.

                              System           [Metric 1]   [Metric 2]          [Metric 3]
                              [Baseline 1]       XX.X         XX.X       XX.X Baseline 2>Baseline 2
                                                 XX.X         XX.X       XX.X Baseline 3>Baseline 3
                                                 XX.X         XX.X                XX.X
                              Ours (w/o A)       XX.X         XX.X                XX.X
                              Ours (Full)       XX.X†        XX.X†               XX.X†

      Table 5: Main results on [Dataset Name(s)]. Best results in bold; second-best underlined. † indicates significance
      over the best baseline (p < 0.05, bootstrap resampling).


       Variant             [Metric 1]     [Metric 2]   ∆ [M1]        System: You are a helpful assistant.                     324
       Full System           XX.X           XX.X         —
       w/o Component A       XX.X           XX.X       −X.X          User: Given the following [INPUT TYPE]:                  325
       w/o Component B       XX.X           XX.X       −X.X          ---                                                      326
       w/o Component C       XX.X           XX.X       −X.X          {input}                                                  327

      Table 6: Ablation study results. ∆ shows the change            ---                                                      328

      relative to the full system.                                   Please [TASK DESCRIPTION].                               329
                                                                     Output format: [SPECIFY FORMAT].                         330

300       • Generalizability: [Results may not gener-                   [Add one block per distinct prompt type used          331
301         alise to low-resource languages, highly spe-             in your experiments. Label each clearly with its         332
302         cialised domains, or task formulations signifi-          purpose — e.g., zero-shot prompt, few-shot prompt,       333
303         cantly different from those evaluated here.]             chain-of-thought prompt, etc.]                           334

304   Acknowledgements                                               B   Additional Experimental Results                      335

305   [This research was supported by [Funding Agency],
                                                                     [Tables or figures that support the main results but     336
306   Grant No. [XXXX]. We thank [Name(s)] for in-
                                                                     were omitted from the main paper for space. Each         337
307   sightful discussions and feedback on earlier drafts.
                                                                     table and figure must have a caption.]                   338
308   We are grateful to [Institution / Platform] for pro-
309   viding computational resources. We also thank the
                                                                     C    Dataset Construction Details                        339
310   anonymous reviewers for their constructive com-
311   ments.]                                                        [For benchmark or dataset papers: full annota-           340
312   AI Use Statement. The authors are responsible for              tion guidelines, quality control procedures, inter-      341
313   all content, facts, and claims presented in this paper.        annotator agreement (IAA) scores, and annotator          342
314   Any use of AI-assisted writing tools was limited               demographics if applicable. e.g., “Three trained         343
315   to [grammar checking / brainstorming / none]. All              annotators labelled each instance independently.         344
316   scientific content, analysis, results, and conclusions         Cohen’s κ = X.XX, indicating [level of] agree-           345
317   are entirely the authors’ own.                                 ment.” Describe any adjudication process used to         346
                                                                     resolve disagreements.]                                  347

318   References
                                                                     D    Statistical Significance Tests                      348

319   A    Full Prompt Templates
                                                                     [Report the statistical test used (e.g., bootstrap re-   349
320   [If your method uses prompting, include the exact              sampling, paired t-test, Wilcoxon signed-rank), the      350
321   prompt templates here so that reviewers can verify             significance threshold (p < 0.05), and which com-        351
322   and reproduce your work. Use verbatim or a code-               parisons are significant. A full pairwise signifi-       352
323   listing environment:]                                          cance table is recommended here.]                        353


                                                                 5
                                 [Dimension]     Best Baseline     Ours            Improv.
                                 [Subset 1]         XX.X           XX.X      +X.X Subset 2>Subset 2
                                                    XX.X           XX.X      +X.X Subset 3>Subset 3
                                                    XX.X           XX.X      −X.X Subset 4>Subset 4
                                                    XX.X           XX.X             +X.X
                                 Overall            XX.X           XX.X             +X.X

                    Table 7: Performance breakdown by [Dimension — e.g., domain / language / model size].


       Error Type        Count                                %
       [Error Type 1]      [N]    [X%] Error Type 2>Error Type 2
                           [N]    [X%] Error Type 3>Error Type 3
                           [N]                             [X%]
       Total               [N]                             100%

      Table 8: Error taxonomy from manual analysis of N
      outputs.

       System         [DS 1]   [DS 2]   [DS 3]            Avg.
       [System 1]     XX.X     XX.X     XX.X     XX.X System 2>System 2
                      XX.X     XX.X     XX.X             XX.X

      Table 9: Full results across all datasets and all models.


354   E    Extended Qualitative Examples
355   [Additional input/output examples illustrating sys-
356   tem behaviour across diverse conditions, includ-
357   ing both success cases and failure modes. The
358   four-column table format below — Input, Gold La-
359   bel, Best Baseline Output, Your System Output —
360   works well for most NLP tasks.]                                        Comparison            [Metric 1]   [Metric 2]
                                                                             Ours vs. Baseline 1    <0.01 ✓      <0.05 ✓
                                                                             Ours vs. Baseline 2    <0.05 ✓       0.12
                                                                             Ours vs. Baseline 3    <0.01 ✓      <0.01 ✓

                                                                       Table 10: Pairwise statistical significance (p-values). ✓
                                                                       = p < 0.05.




                                                                   6
ID   Input                        Gold                         Best Baseline                     Ours
1    [Input 1]                    [Gold]                       [Output – incorrect]         [Output – correct]
2    [Input 2]                    [Gold]                       [Output – correct]           [Output – correct]
3    [Input 3 — failure case]     [Gold]                       [Output – incorrect]        [Output – incorrect]

                  Table 11: Extended qualitative examples showing success and failure cases.




                                                      7

```


---

# Appendix D. Original Research Direction Brief (received from Dr Garg)

```text
RESEARCH DIRECTION BRIEF
Small Language Models as Judges, Equipped with a SQL-Execution Tool
==========================================================================

NOTE ON THIS DOCUMENT
This is a starting point for a student research project, not a finished
literature review. Every claim about "what has/hasn't been done" reflects
a web-search pass at the time of writing (2026) and should be re-verified
before committing, since this area is moving quickly. Novelty claims in
fast-moving ML sub-fields are frequently narrower than they first appear
once searched more thoroughly -- treat every "gap" claim below as a
hypothesis to re-check at the time you start, not a settled fact.


1. THE PROBLEM, IN SIMPLE WORDS
--------------------------------
An AI "judge" is a model whose job is to look at something another AI
produced and decide if it's correct. Normally, a judge only gets to READ
what it's grading -- it can't go check anything for itself.

This project asks: what if a judge, instead of just reading, could
actually RUN A DATABASE QUERY to check a claim before deciding?

Example: an AI writes "Employee #47's March expenses total $1,950, which
is within the $2,000 monthly limit." A judge that can only read this
sentence has to guess whether it's true. A judge that can query the
actual expense database can add up employee #47's real March expenses
and know for certain -- catching it if the true total is actually
$2,150.

The specific question this project asks: does giving a SMALL, cheap AI
model this kind of database-query tool let it judge claims -- especially
claims that require adding up or cross-checking many rows -- as well as
a much bigger model, or even make things possible that no judge (big or
small) could do without the tool at all?


2. WHY THIS MATTERS
-----------------------
Some claims can ONLY be checked by looking at many pieces of data at
once (e.g., "did this person's total spending this month exceed the
limit?"). A judge that only sees one row of data, no matter how smart it
is, literally cannot verify a claim like that -- the information isn't
in front of it. Giving a judge a tool to go query for what it's missing
turns an impossible task into a checkable one. This applies anywhere an
AI generates a written explanation, summary, or claim about
structured/tabular data -- financial reports, business "why did this
change" explanations, HR summaries, customer account narratives, and
more.


3. RELATED WORK
-----------------
This project sits at the crossing of two different lines of work: (A)
judges that are given SOME kind of tool, and (B) work that uses SQL
execution for a DIFFERENT purpose (checking generated SQL code itself,
not checking an unrelated claim). Both are listed below so the
difference is clear.

--- 3.1 Judges given a tool (but never a SQL/database tool) ---

(a) "Incentivizing Agentic Reasoning in LLM Judges via Tool-Integrated
    Reinforcement Learning" (TIR-Judge)
    Ran Xu et al.
    Venue: ICLR 2026
    Link: https://arxiv.org/abs/2510.23038
    What it did: Trained judge models (4B and 8B parameters) that can
    call a Python code executor mid-judgment. Supports pointwise,
    pairwise, and listwise judging. The 8B version beats 32B text-only
    judges and reaches 96% of Claude-Opus-4's performance on listwise
    ranking (RewardBench 2). Trained via reinforcement learning
    (rejection-sampling SFT + RL cycles); a "Zero" variant is trained by
    RL alone, no distillation needed.
    What it does NOT do: The only tool is a Python code executor. No SQL
    or database tool. Domain is math, code, and instruction-following --
    not claims about structured/tabular business data.

(b) "T1: Tool-integrated Verification for Test-time Compute Scaling in
    Small Language Models" (also referred to as ToolV)
    Kang et al.
    Venue: arXiv preprint (arXiv:2504.04718) -- marked "under review" in
    the paper itself; venue not confirmed as of this writing.
    Link: https://arxiv.org/abs/2504.04718
    What it did: Explicitly small models -- LLaMA-3.2-1B-Instruct,
    Qwen-2.5-0.5B-Instruct, SmolLM2-360M-Instruct. Fine-tuned via LoRA,
    distilled from a GPT-4o-mini teacher. Its verifier uses a code
    interpreter (for math) and Wikipedia/BM25 retrieval (for factual
    claims on MMLU-Pro). Headline result: a 1B model with the tool beats
    an 8B model without it, on the MATH benchmark.
    What it does NOT do: No SQL/database tool. Domain is math word
    problems and closed-form factual QA (multiple choice), not open
    claims about a business's own data.

(c) "Scaling Medical Reasoning Verification via Tool-Integrated
    Reinforcement Learning" (Med-TIV)
    Venue: arXiv preprint (arXiv:2601.20221) -- posted January 2026;
    venue not confirmed.
    Link: https://arxiv.org/abs/2601.20221
    What it did: A judge for medical reasoning that retrieves real
    medical knowledge dynamically instead of relying on memorized
    (parametric) knowledge, to catch confidently-stated but incorrect
    medical claims. Trained via an iterative RL paradigm.
    What it does NOT do: No SQL/database tool; the tool is knowledge
    retrieval, and the domain is medical text, not tabular data.

(d) "Tool-Augmented Reward Modeling" (sometimes cited as "Themis" --
    note: this is a DIFFERENT paper from "Themis: A Reference-free NLG
    Evaluation Language Model," EMNLP 2024, which has no tool use; do
    not conflate the two when citing)
    Li et al.
    Venue: arXiv preprint (arXiv:2310.01045) -- venue not confirmed.
    Link: https://arxiv.org/abs/2310.01045
    What it did: An early (2023) tool-augmented reward model that can
    call a calculator, a search engine, and a knowledge base while
    scoring responses. Used as a baseline in later papers (e.g., T1
    reports outperforming it on MATH).
    What it does NOT do: No SQL/database-specific tool.

--- 3.2 SQL execution used to judge/reward SQL itself (a related but
different target -- read carefully, this is NOT the same task) ---

(e) "Reward-SQL: Boosting Text-to-SQL via Stepwise Execution-Aware
    Reasoning and Process-Supervised Rewards"
    Zhang, Fan, Fan, Yi, Luo, Li, Wu, Zhou.
    Venue: SIGMOD 2026 (Proc. ACM Manag. Data, Article 228)
    What it did: Uses SQL execution results as a process-level reward
    signal to train a text-to-SQL GENERATION model via RL.
    Key difference from this project: the thing being judged/rewarded
    IS the generated SQL query's correctness, not a natural-language
    claim about the data.

(f) "ToolSQL: A Tool-Assisted Agent for SQL Verification and
    Refinement"
    Venue: KDD 2026 (Proceedings of the 31st ACM SIGKDD Conference,
    V.2)
    What it did: An agent with a retriever and a detector tool to
    diagnose and correct SQL queries that mismatch the database schema.
    Key difference: verifies/repairs a SQL query, not a claim written in
    plain language.

(g) "PV-SQL: Synergizing Database Probing and Rule-based Verification
    for Text-to-SQL Agents"
    Venue: arXiv preprint (arXiv:2604.17653) -- venue not confirmed.
    Link: https://arxiv.org/abs/2604.17653
    What it did: An agent that generates its own "probing" SQL queries
    to discover database content and check whether a GENERATED SQL query
    satisfies the constraints implied by the question.
    Key difference: same as above -- the object under test is the SQL
    query, not a downstream natural-language claim.

(h) "Beyond Query-Level Comparison: Fine-Grained Reinforcement Learning
    for Text-to-SQL with Automated Interpretable Critiques" (RuCo-C)
    and "Graph-Reward-SQL: Execution-Free Reinforcement Learning for
    Text-to-SQL via Graph Matching and Stepwise Reward"
    Venues: both arXiv preprints (arXiv:2511.22258 and arXiv:2505.12380
    respectively) -- venues not confirmed.
    What they did: Both are generative judge/reward models for grading
    generated SQL queries during RL training, with more fine-grained
    feedback than a single pass/fail execution check.
    Key difference: same pattern as (e)-(g) -- SQL-quality judging, not
    claim-verification.

--- 3.3 Closest attempts at "judge a claim against real data/policy,"
without an active SQL tool ---

(i) "Detecting and Grounding Financial Hallucinations via Atomic Claim
    Verification" (FinGround)
    Venue: arXiv preprint (arXiv:2604.23588) -- venue not confirmed.
    Link: https://arxiv.org/abs/2604.23588
    What it did: A small, DISTILLED 8B model (from a GPT-4o teacher)
    that decomposes an AI-generated financial answer into individual
    claims and checks each against retrieved SEC filing text and tables,
    including recomputing arithmetic ("formula reconstruction").
    Reports 91.4% F1 and 18x faster inference than the teacher model.
    What it does NOT do: Retrieves from pre-chunked filing TEXT, not by
    running live SQL queries against a database. This matters
    specifically for claims that require aggregating many rows that
    would not all appear together in one retrieved text chunk.

(j) "Detecting Financial Regulatory Non-Compliance in LLM Interactions"
    (FinGuard)
    Venue: arXiv preprint (arXiv:2605.29427) -- venue not confirmed.
    Link: https://arxiv.org/abs/2605.29427
    What it did: An 8B model (Qwen3-8B based) trained via SFT plus
    self-play RL specifically to detect regulatory non-compliance in
    LLM conversations. Notably outperforms much larger general models
    (even a 397B model and GPT-5.1) at this task.
    What it does NOT do: Classifies conversational text, not database
    rows; regulation knowledge appears to be trained into the model's
    weights rather than given to it as a live document or database
    query at inference time (this specific point was not fully
    confirmed and should be re-checked against the full paper).

(k) "From Organizational Policies to Neuro-Symbolic Compliance Review
    Engines" (PolicyGuard)
    Venue: arXiv preprint (arXiv:2606.32004) -- venue not confirmed.
    Link: https://arxiv.org/abs/2606.32004
    What it did: Explicitly grounds compliance checking against a real,
    given policy document (not memorized knowledge) at review time,
    using retrieval plus a symbolic rule evaluator. Evaluated on
    NDA/contract review against organizational negotiation policies.
    What it does NOT do: Works over documents/contracts, not structured
    database rows, and has no SQL/live-query component.

--- 3.4 Foundational "judge" lineage (no tool; defines the evaluation
style this project should follow) ---

(l) "Prometheus: Inducing Fine-Grained Evaluation Capability in
    Language Models"
    Kim, Shin, Bae, et al.
    Venue: ICLR 2024
    Link: https://arxiv.org/abs/2310.08491
    Relevance: established that a fine-tuned, open, ~13B model can match
    GPT-4-level agreement with human judges on scoring a single response
    against a rubric -- the paper that motivates asking whether this
    still holds once tool use and harder verification tasks are added.

(m) "Agent-as-a-Judge: Evaluate Agents with Agents"
    Zhuge, Zhao, Ashley, et al.
    Venue: ICML 2025
    Link: https://arxiv.org/abs/2410.10934
    Relevance: introduced grading against a set of individually
    checkable, hierarchical requirements (365 requirements across 55
    tasks) rather than one holistic pass/fail label -- a design pattern
    worth reusing for this project's evaluation (see Section 7).

--- 3.5 Related work on ATTACKING judges (relevant only if you add a
robustness/adversarial module -- optional extension, not required) ---

(n) "Adversarial Attacks on LLM-as-a-Judge Systems: Insights from
    Prompt Injections"
    Venue: arXiv preprint (arXiv:2504.18333) -- venue not confirmed.
    Link: https://arxiv.org/abs/2504.18333
    What it did: Shows text-only judges can be manipulated into giving a
    fixed score via injected instructions in the content being judged.

(o) "Jagged Judges: Epistemic Stability Under Silence, Pressure, and
    Persistence"
    Zhao et al. (Meta Superintelligence Labs)
    Venue: Submitted to NeurIPS 2026 (under review at time of writing)
    Link: https://arxiv.org/abs/2608.12645
    What it did: Shows large, frontier judges flip their verdict 25-71%
    of the time under a single conversational challenge, mostly toward
    the wrong answer. Tests 9 frontier (large) models on static text
    tasks only -- no tool-using judges, no small models.
    IMPORTANT: if extending this project with an attack/robustness
    module, this is the paper to cite and explicitly differentiate from
    (different model class: small vs. frontier; different mechanism:
    tool-output poisoning vs. conversational pressure).

(p) An unnamed side-experiment referred to as "JudgeJacking
    (Rubric-Mimicry)" inside "MemoryGraft: Persistent Compromise of LLM
    Agents via Poisoned Experience Retrieval"
    Venue: arXiv preprint (arXiv:2512.16962) -- venue not confirmed.
    Link: https://arxiv.org/abs/2512.16962
    What it did: A small side-experiment (not the paper's main
    contribution) showing a validator can be fooled by a script that
    merely prints "all checks passed" without doing real computation.
    The authors themselves note this uses a narrow, artificial threat
    model. Closest existing example of "poisoning a tool's output to
    fool a judge/validator," but not a systematic study.


4. WHAT IT SEEMS PEOPLE HAVE DONE SO FAR (SUMMARY)
-----------------------------------------------------
- Giving a judge a tool (instead of just letting it read and reason in
  text) is an established, working idea -- proven for code execution
  (TIR-Judge), for Wikipedia/BM25 retrieval with small models
  specifically (T1/ToolV), and for medical-knowledge retrieval
  (Med-TIV).
- Every one of these tool-augmented judge papers found so far ALSO
  fine-tuned the model to use its tool well (via LoRA distillation, or
  RL) rather than just prompting an off-the-shelf model -- none of them
  report a purely zero-shot, untrained tool-using judge as their main
  result.
- Using SQL execution as a check is separately well-established, but
  ALWAYS to judge/reward whether a generated SQL query itself is
  correct (Reward-SQL, ToolSQL, PV-SQL, RuCo-C, Graph-Reward-SQL) -- not
  to judge some other, unrelated claim.
- Checking a claim against a real policy document (PolicyGuard) and
  doing small-model, tool-grounded arithmetic re-verification of
  financial claims (FinGround) both exist, but neither actively queries
  a live database -- both retrieve from pre-chunked text.


5. WHAT APPEARS TO STILL BE OPEN (THE GAP)
---------------------------------------------
HONESTY NOTE: No paper reviewed for this brief explicitly states "giving
a judge an active SQL-querying tool to verify claims about structured
data is an open problem." The gap below is INFERRED from surveying the
tool types and target types across the papers above -- it is not a gap
any of these papers themselves flagged as future work. Re-verify this
yourself (Section 6) before relying on it. Note also that the adjacent
application area of financial/compliance auditing with LLMs is already
fairly populated (see Section 3.3) -- the same could be true here once
searched more thoroughly closer to the project start date.

The inferred gap, stated precisely: no paper found gives a judge model
(small or large) an ACTIVE SQL-execution tool to independently verify a
CLAIM THAT IS NOT ITSELF A SQL QUERY (e.g., an explanatory or
descriptive natural-language statement about data), as opposed to using
SQL execution to check the correctness of a generated SQL query, or
retrieving from pre-chunked text/tables.

The specific reason this distinction is not just a technicality: some
claims (e.g., "this person's total spending this month exceeded $2,000")
require aggregating information across many rows that cannot all fit in
one retrieved text chunk the way FinGround's approach works -- they
structurally require an active query, not passive retrieval.


6. STEPS TO VERIFY THE GAP IS STILL REAL (DO THIS FIRST)
-------------------------------------------------------------
1. Search arXiv (last 3 months) for combinations of: "SQL" + "judge" or
   "verifier" + "reinforcement learning" or "tool-integrated"; also try
   "database" + "fact-checking" + "small language model."
2. Check whether FinGround's method has been extended to use live
   database queries instead of retrieval in any follow-up paper.
3. Check the Awesome-LLMs-as-Judges and Awesome-Agent-as-a-Judge GitHub
   lists for anything newly added matching this description.
4. Re-read FinGround and T1/ToolV closely -- confirm their exact
   retrieval/tool mechanisms so you can precisely state, in your
   related-work section, why an active SQL-query tool is mechanically
   different from what they do.
5. If a paper doing exactly this is found, check whether it leaves a
   narrower gap open (e.g., only tests one model size, only one type of
   rule, no robustness/attack angle) that you can still contribute to.


7. A POSSIBLE PLAN TO CLOSE THE GAP
---------------------------------------
Phase 1 -- Build the test data (no model training required yet):
  - Build a small synthetic database (SQLite is enough) -- e.g., an
    expense-report table: employee_id, amount, category, date.
  - Write a set of explicit rules yourself (10-20), modeled on how a
    real company policy reads. Deliberately include BOTH single-row
    rules (checkable from one row alone) AND aggregate/cross-row rules
    (e.g., a monthly total limit) -- the aggregate rules are the ones
    that specifically require a tool, and are the heart of this
    project's contribution.
  - Write your own script that computes the correct answer for every
    case mechanically (the same "programmatic ground truth" trick used
    by TIR-Judge and T1/ToolV with GSM8K/IFEval) -- this avoids needing
    human annotation.
  - Generate the claims to be judged the same way TIR-Judge and T1
    built their evaluation data: have a real AI model generate
    explanatory claims about your data (both correct and incorrect
    ones), rather than writing every example by hand. Deliberately
    include "near-miss" claims that sound right but are subtly wrong
    (e.g., a claimed total just under a threshold when the real total is
    just over) -- these are the cases that make the evaluation
    meaningful.

Phase 2 -- Build the judge and baselines:
  - Small open model(s) with function-calling support (e.g.,
    Qwen2.5-7B-Instruct, Llama-3.2-8B-Instruct) as your main judge.
  - Baselines: (a) same small model with no tool, just handed the row
    as text; (b) a strong large model with no tool, as an upper-bound
    reference; (c) optionally, a large model WITH the SQL tool.
  - A simple tool-calling loop: prompt with the claim + rule text + a
    "run_sql(query)" tool description, execute against SQLite, feed the
    result (or the error message, if the query fails) back, repeat
    until a final verdict.

Phase 3 -- Evaluate, following the design patterns used by the related
work above:
  - Grade against your mechanically-generated ground truth (as in
    Phase 1), the same style as TIR-Judge/T1's programmatic
    verification.
  - Break results down by rule type: single-row vs. aggregate/cross-row
    (this split is the paper's central finding -- expect the tool to
    matter little on single-row rules and matter a great deal, or be the
    only way to succeed at all, on aggregate rules).
  - Decompose grading into sub-checks rather than one pass/fail label,
    following Agent-as-a-Judge's approach: did it identify the right
    rule; did its query actually touch the needed rows; did its final
    verdict match ground truth; did it cite the right evidence.
  - Report tool-use efficiency (number of queries per case, following
    SWE-Eval's style of measuring more than just final correctness).

Phase 4 -- Close the gap between zero-shot and trained performance
(optional but recommended, since every related paper found did this):
  - Light fine-tuning (e.g., LoRA) of the small model on judge-style
    tool-use traces, following T1/ToolV's recipe: generate training
    traces from a stronger teacher model, then fine-tune the small
    model to imitate good tool-use behavior.

Phase 5 -- Optional stretch experiment (robustness/attack angle):
  - Tamper with the database or the SQL result the judge sees (a
    corrupted value, a manipulated read) and measure how often the
    judge's verdict flips, compared to a text-only judge given the same
    false claim with no way to check it. Frame this explicitly as
    extending the JudgeJacking side-experiment (item p, Section 3.5) and
    citing Jagged Judges (item o) for the broader "judge stability"
    framing -- and be upfront that this connects to the broader
    "reward hacking" problem only if the judge is actually used as a
    training signal, which this project's core design does not require.


8. RISK ASSESSMENT
----------------------
- Field speed and narrowing risk: adjacent application areas (e.g.,
  "compliance auditing with AI") are already fairly crowded -- FinGuard,
  FinGround, PolicyGuard, plus an entire deployed industry pattern of
  policy-plus-data compliance agents. The specific mechanism this
  project targets ("active SQL querying for claim verification") was
  not found anywhere during this review, but given how populated the
  neighboring space is, budget time to re-run Section 6's checks close
  to when you actually start, since the gap could narrow further by
  then.
- Avoid the compliance/regulatory framing as your primary motivation.
  Reason: of all the concrete applications this mechanism could be
  pointed at, compliance/regulatory auditing is the one found to already
  have the most direct occupants in this review -- FinGuard (an 8B
  model trained specifically for regulatory non-compliance detection,
  already outperforming much larger general models at that job),
  FinGround (financial-claim verification), and PolicyGuard
  (document-vs-policy compliance review), plus a documented, already
  deployed industry pattern of "policy agent + violation-detection
  agent" pipelines in banking and healthcare. Leading with compliance as
  the motivating example therefore invites a reviewer to immediately
  ask "isn't this FinGuard/PolicyGuard already?" -- a question that is
  answerable (the mechanism differs, see Section 5) but is better
  avoided than invited. Frame the contribution around the MECHANISM
  (active tool-querying vs. passive retrieval or memorized knowledge)
  and pick whichever concrete application is easiest to build clean
  data for; auditing a text-to-SQL system's own final answers (reusing
  existing text-to-SQL benchmark data) may be simpler to start with than
  a compliance scenario, and sidesteps the crowded framing entirely.
- Reviewer skepticism risk: a reviewer familiar with FinGround, T1/
  ToolV, or the text-to-SQL reward-model literature (Reward-SQL,
  ToolSQL, PV-SQL) may initially assume this is already done. The
  related-work section must clearly and immediately state the
  mechanical distinction (active database querying, not passive
  retrieval; verifying a claim, not verifying a SQL query) rather than
  leaving it for a reader to infer.
- Every tool-augmented judge paper found in this research fine-tuned
  its model rather than relying on zero-shot tool use alone -- budget
  for at least a light fine-tuning phase (Phase 4) if you want results
  competitive with this literature, rather than treating it as
  optional.
- Data risk: since no off-the-shelf benchmark exists for this exact
  task, the quality of the synthetic database and rules you construct
  (particularly the aggregate/cross-row rules and the "near-miss"
  claims) will determine whether the study has a real finding to report
  -- this is the single most important place to invest careful design
  time (see Phase 1 above).


10. ONE-PARAGRAPH SUMMARY TO REUSE IN A DRAFT INTRODUCTION
----------------------------------------------------------------
Judges equipped with a tool -- rather than only reading and reasoning in
text -- have been shown to work well for code-checkable tasks
(TIR-Judge), for small models specifically on knowledge-intensive
multiple-choice QA (T1/ToolV), and for medical-knowledge grounding
(Med-TIV). Separately, SQL execution is a mature tool for judging
whether a GENERATED SQL QUERY is correct (Reward-SQL, ToolSQL, PV-SQL),
and small, tool-grounded models have been shown to verify financial
claims against retrieved filing text and tables (FinGround). No existing
work gives a judge an ACTIVE SQL-querying tool to verify a
natural-language claim that is not itself a SQL query -- a distinction
that matters because some claims (particularly those requiring
aggregation across many rows) cannot be verified by passive retrieval
over pre-chunked text at all. This project tests whether a small model,
given this kind of tool, can verify such claims -- especially
aggregate/cross-row claims that no static-context judge, regardless of
size, could verify at all -- and reports accuracy, cost, and tool-use
behavior relative to text-only baselines of both sizes.
```


---

# Appendix E. Original Execution Plan (superseded by the ClaimDB direction; kept for context)

```text
EXECUTION PLAN: TESTING SLM-AS-JUDGE WITH A SQL TOOL
Fast, Iterative Plan for a Team of 3
==========================================================================

REQUIRED READING BEFORE ANYONE WRITES CODE
(do this first, ~half a day, can be split across the team)
--------------------------------------------------------------------------
- TIR-Judge ("Incentivizing Agentic Reasoning in LLM Judges via
  Tool-Integrated Reinforcement Learning," ICLR 2026, arXiv:2510.23038)
  -- read this for how a judge decides WHEN to call a tool versus answer
  directly, and how tool results get folded back into its reasoning
  before the final verdict.
- T1 / ToolV ("Tool-Integrated Verification for Test-Time Compute
  Scaling in Small Language Models," arXiv:2504.04718) -- read this one
  closely, since it's the closest precedent for SMALL models
  specifically. Pay attention to their exact recipe: how they format the
  tool call in the prompt, how they feed the tool's result back in, and
  how they fine-tuned via LoRA using a stronger teacher model's traces.

Nobody needs to reproduce their training pipeline -- the point is to
steal their FORMAT (how a tool call and its result look inside the
conversation) rather than reinvent it from scratch.


THE SQL TOOL ITSELF -- CONCRETE SPEC
--------------------------------------------------------------------------
Database: SQLite, single file, opened in read-only mode. No server
needed.

The one tool the model gets:
  run_sql(query: str) -> {"columns": [...], "rows": [...]}   on success
                       -> {"error": "<message>"}              on failure

How to actually wire this up -- two viable approaches, pick based on
which models you choose:
- Native tool-calling: Qwen2.5-Instruct and Llama-3.1+/3.2-Instruct
  models ship with built-in chat templates that support structured tool
  calls out of the box (via Hugging Face's transformers, using the
  model's tool-calling template). This is the cleanest option and
  matches how TIR-Judge and T1/ToolV structure things.
- Manual ReAct-style loop (fallback for any model, including ones
  without native tool support): prompt the model to output its SQL
  query inside a fixed marker (e.g., a fenced code block), parse it out
  with a regex, execute it, and append the result as the next message
  before letting the model continue. T1/ToolV effectively does a
  version of this for their code-interpreter tool -- same pattern, just
  a SQL executor instead of Python.
- If manual plumbing feels like too much setup for the time you have,
  Hugging Face's smolagents library handles this loop with very little
  code and is worth trying first before hand-rolling it.

Safety/sanity rules for the tool: reject anything that isn't a SELECT
(simple keyword check), cap returned rows (e.g., first 50), set a short
timeout. This isn't about security hardening -- it's just to stop one
bad query from breaking your test run.


THE TASK: WHAT YOU'RE ACTUALLY TESTING, AND HOW TO BUILD IT
--------------------------------------------------------------------------
This is the part that determines whether the whole experiment means
anything -- spend real care here, not just on the tool plumbing above.

1. BUILD A SMALL FAKE DATABASE.
   One table is enough to start. Example schema:
     expenses(employee_id, amount, category, date)
   Generate a few hundred rows of realistic fake data (Python's Faker
   library works fine for this) -- a handful of employees, a spread of
   categories (travel, meals, supplies), dates across a few months.

2. WRITE A SMALL SET OF RULES -- AND MAKE SURE SOME OF THEM REQUIRE
   ADDING ROWS TOGETHER, NOT JUST READING ONE ROW.
   Write 10-15 rules that read like a real company policy. Deliberately
   include BOTH kinds:
     - Single-row rules (checkable from one row alone), e.g.: "Any
       single meal expense over $75 requires prior approval."
     - Aggregate rules (require summing/grouping across several rows),
       e.g.: "An employee's total expenses in a calendar month may not
       exceed $2,000."
   The aggregate rules are the whole point of giving the judge a tool --
   a judge that only sees one row, no matter how good it is, literally
   cannot check these without going and looking at the other rows.

3. WRITE A GROUND-TRUTH CHECKER SCRIPT.
   Since you built the database and the rules yourselves, write a plain
   Python/SQL script that computes the CORRECT answer for any claim
   mechanically. This is your answer key -- no human labeling needed,
   and no ambiguity about what "correct" means.

4. CONSTRUCT THE CLAIMS THE JUDGE WILL BE ASKED TO VERIFY.
   For each rule, generate a mix of:
     - Clear violations (obviously breaks the rule).
     - Clear compliant cases (obviously fine).
     - NEAR-MISSES -- this is the most important category, and the one
       most teams under-build. Examples: a $74.99 meal (just under the
       single-row threshold), or an employee whose monthly total only
       crosses $2,000 once you add up three separate small purchases
       spread across different days (no single receipt looks
       suspicious on its own). These are the cases that actually
       require the tool -- if every test case is obvious, every
       condition will score near-perfectly and you'll learn nothing.
   Write the CLAIM as a natural-language sentence a person or another
   AI might say, e.g.: "Employee #12's March expenses totaled $1,950,
   which is within policy." Some claims should be true, some false --
   know which, from your ground-truth checker.
   You can generate these claims by hand for a first small batch (aim
   for 20-30 to start), or prompt an LLM to phrase them naturally once
   you already know the underlying facts and correct answer.

5. RUN EACH CLAIM THROUGH THE JUDGE TWO WAYS, AND COMPARE.
   - Condition A (NO TOOL): give the judge only the claim and the
     specific row(s) it would need if it already knew which ones
     mattered -- i.e., simulate what a text-only judge would see if
     handed a fixed excerpt of context, not the live database.
   - Condition B (WITH TOOL): give the judge only the claim and the
     table schema, and let it use run_sql to go find whatever it needs.
   For each claim, in each condition, record whether the judge's final
   verdict matches your ground-truth answer.

6. HOW TO TELL IF THE GAP IS REAL AND WORTH PURSUING FURTHER.
   Break your results into the two rule types from step 2 and compare
   accuracy across conditions:
     - Single-row rules: expect Condition A and B to perform similarly
       -- the tool shouldn't matter much here, since one row is enough.
     - Aggregate rules: this is the key comparison. If Condition B
       (with tool) clearly beats Condition A (no tool) here -- ideally
       by a wide margin, since Condition A is often structurally unable
       to get these right at all -- that is your core, addressable
       finding. If there's little to no difference even on the
       aggregate rules, the effect isn't showing up, and that's
       important to know before building anything bigger: either the
       test cases aren't hard enough (add harder near-misses), the
       model isn't using the tool well (check the transcripts -- is it
       even calling run_sql when it should?), or the idea needs
       rethinking for this setup.
   A simple table -- accuracy by (model x condition x rule-type) -- is
   enough to answer this at first pass. You don't need statistics
   beyond plain accuracy and case counts for this initial check.


MODEL CHOICES -- PICK 2-3 SMALL, PLUS 1 LARGE REFERENCE
--------------------------------------------------------------------------
Small judge (pick 2-3, all support tool calling):
  - Qwen2.5-7B-Instruct
  - Qwen2.5-3B-Instruct
  - Llama-3.1-8B-Instruct
  - Phi-4-mini-instruct
  - Mistral-7B-Instruct-v0.3

Large reference judge:
  - GPT-4o-mini or GPT-4o via API
  - or Qwen2.5-72B-Instruct / Llama-3.1-70B-Instruct if you want to stay
    fully open-weight

HOW TO ACCESS THE MODELS
If getting local GPU access set up eats into your available time,
consider running the small models through a cheap/free API provider
(Together.ai, Groq, Fireworks, OpenRouter all host these exact models)
instead of fighting with local inference setup -- for a fast first
iteration, API calls are usually faster to get working than a local GPU
pipeline.


SAVE EVERYTHING, IN ONE CONSISTENT FORMAT
--------------------------------------------------------------------------
Every single case run should get logged as one line in a JSONL file,
with at minimum: a case ID, the ground-truth answer, which condition it
was (tool vs. no-tool), which model ran it, the full transcript (every
tool call made and every result returned, in order), the model's final
verdict, and whether that verdict was correct. This is what lets you
actually analyze results afterward instead of just eyeballing a few
examples -- and it's what you'd need anyway if this turns into a real
paper later.


WHAT CAN RUN IN PARALLEL VS. WHAT HAS TO WAIT
--------------------------------------------------------------------------
Runs in parallel, starting immediately:
  - Building the synthetic database + policy rules + the claims +
    ground-truth-checking script, per the "THE TASK" section above
    (this doesn't depend on anything else).
  - Building the tool-calling harness itself -- getting one model wired
    up to call run_sql and getting a result back (this can be
    prototyped on a toy database while the real one is still being
    built).
  - Reading the two papers above and pulling out the exact format
    details to inform the harness.

Has to wait until both of the above are done:
  - Running the full test: feeding real cases from the database through
    the harness, for both the "no tool" and "with tool" conditions.

Runs in parallel once the harness works:
  - Running the second and third small models, plus the large reference
    model, once the pipeline is proven on the first one -- this is just
    re-running the same harness with a different model, no new build
    work needed.

Sequential, at the very end:
  - Pulling all the JSONL logs together into one results table
    (accuracy with vs. without the tool, broken down by single-row vs.
    aggregate-style rules) -- this has to wait until all the model runs
    are actually done.
```


---

# Appendix F. Literature review notes (18 to 25 September; partly superseded, see main document)

## Literature Review: SQL Tools for LLM-as-a-Judge (Sep 18 action item)

Project: Small language model judges equipped with a SQL-execution tool
Mentor: Dr Krishna Garg | Prepared: 25 Sep 2026

Each paper is summarised on the fields requested: Task (input, output), Tools, Settings, Datasets, Models, Findings/Claims, plus how it differs from our project.

## Headline: the gap has narrowed since the brief was written

The brief's gap ("no work gives a judge an active SQL tool to verify natural-language claims") no longer holds. Two University of Washington papers do exactly this with prompted agents: Thucy (AAAI 2026) and ClaimDB (ACL 2026). ClaimDB also shows small open models do poorly at it. The remaining, defensible gap is narrower and is stated at the end.

## A. Judges and verifiers given a tool (never SQL over a database)

### A1. TIR-Judge (Xu et al., Emory + Google, ICLR 2026, arXiv 2510.23038)
- Task: input is a user prompt plus 1, 2 or n candidate responses (no reference answer). Output is a score (pointwise), the preferred response (pairwise) or the best index (listwise).
- Tools: Python executor in a sandbox, at most 3 calls per judgment, errors truncated to the last line.
- Settings: trained with RL (DAPO, a GRPO variant). Reward = correctness + output format + error-free tool use. Two variants: Distill (SFT on about 10k Gemini-2.5-Flash tool trajectories, then RL) and Zero (iterative RL, rejection sampling, SFT; no teacher). 8x H100.
- Datasets: training about 26k preference pairs (HelpSteer3, UltraInteract, CodeRM, Tulu 3 IF, Safe-RLHF, MATH, DAPO-Math, WebInstruct, Loong). Evaluation on 7 benchmarks: PPE Correctness, IFBench, CodeJudgeBench, RewardBench, RM-Bench, JudgeBench, RewardBench 2.
- Models: Qwen3-8B, Qwen3-4B-Instruct-2507.
- Findings: up to +6.4% (pointwise) and +7.7% (pairwise) over text-only reasoning judges; the 8B model reaches 96% of Claude-Opus-4 on RewardBench 2 listwise (73.4 vs 76.5). Giving untrained Qwen3 the tool gave under 1% or negative gains (Qwen3-8B pointwise PPE average 61.1 without the tool, 56.7 with it). Zero matches or beats Distill. Tools help on reasoning and instruction following, slightly hurt on chat and safety.
- Versus us: Python not SQL; judges responses to prompts, not claims about stored data.

### A2. T1 / ToolV (Kang, Jeong, Cho; KAIST, UW-Madison, KRAFTON; ICLR 2026, arXiv 2504.04718)
- Task: input is a math problem plus N candidate solutions (up to 64). Output is the selected best solution (weighted best-of-N).
- Tools: Python interpreter (math); BM25 retrieval of 3 Wikipedia abstracts (MMLU-Pro knowledge claims).
- Settings: two stages. The tool verifier writes code that prints True/False and filters candidates, then a reward model (PRM or GenRM) scores survivors. Distilled with multi-LoRA (rank 64) from gpt-4o-mini; 4x A100.
- Datasets: MATH500, GSM8K, MMLU-Pro subset.
- Models: SmolLM2-360M, Qwen2.5-0.5B, Llama-3.2-1B (3B and 8B as comparisons).
- Findings: Llama-3.2-1B with the tool beats Llama-3.1-8B without it on MATH500. Concept experiment: a 1B verifier fails to check sums of N three-digit numbers as N grows, and code execution largely fixes this. Theory: tools remove the memorisation burden. Limitation: buggy generated code rejects correct answers (high precision, low recall); future work is integrating the tool into the reasoning itself.
- Versus us: no SQL; the tool is a one-shot filter, not called mid-reasoning; math, not data claims.

### A3. Themis, Tool-Augmented Reward Modeling (Li et al., Zhejiang + Baidu, ICLR 2024 spotlight, arXiv 2310.01045)
- Task: input is a question plus two responses. Output is a reward score with a Thought, Action, Observation, Rationale trace.
- Tools: calculator, code interpreter, translator, Google search, weather, calendar, Wikipedia search.
- Settings: trained with pairwise ranking loss plus language-modelling loss.
- Datasets: TARA, 13,604 train / 1,469 test, built with GPT-4.
- Models: Vicuna-7B/13B/33B.
- Findings: +17.7% over vanilla reward models across 8 tasks; beats Gopher 280B by 7.3% on TruthfulQA.
- Versus us: no SQL or database tool.

### A4. External validation tools for LLM-as-a-Judge (Findeis et al., Apple, ACL 2025, arXiv 2507.17015)
- Task: pairwise annotation of responses (long-form facts, math, code; RewardBench, AlpacaEval, LLMBar, RewardMath).
- Tools: web search and code execution, prompted agent (no training).
- Findings: tools help in many but not all cases; results are sensitive to simple choices such as the prompt.
- Versus us: supports the case that prompted tool use is unreliable and training matters.

### A5. Med-TIV (Zhang et al., arXiv 2601.20221, Jan 2026)
- Task: verify medical reasoning traces. Tool: iterative querying of medical corpora. Settings: iterative RL with trace-level supervision and adaptive curriculum.
- Findings: +23.5% (MedQA) and +32.0% (MedXpertQA) relative accuracy; 8x smaller sampling budget than prior reward models.
- Versus us: text retrieval, medical domain, no tables.

## B. Verifying natural-language claims against structured data (closest to us)

### B1. AggChecker (Jo, Trummer et al., Cornell + Google, SIGMOD 2019; arXiv 1804.07686)
- Task: input is a text document plus a relational dataset. Output is claims flagged with a probability of being wrong.
- Tools: translates each claim into many candidate SQL queries (tens to hundreds of thousands per document) and reasons with a probabilistic model. No LLM.
- Datasets: 53 articles, 392 claims.
- Findings: better precision and recall than natural-language-query and fact-checking baselines; users about 6x faster than with a SQL interface.
- Versus us: pre-LLM; not a judge; nothing learned about tool use.

### B2. Evergreen (Lee, Yeom, Han, Cetintemel, Sen, Datta; Brown + Snowflake; arXiv 2604.26180, Apr 2026)
- Task: input is an LLM-written summary of a relation plus the relation. Output is a true/false verdict per claim plus the minimal set of rows that justify it.
- Tools: the LLM splits text into claims and compiles each one upfront into a declarative query (relational plus semantic operators) that the engine executes. No decisions mid-reasoning.
- Settings: prompting only; the contribution is query optimisation (early stopping, estimation, operator fusion).
- Datasets: Yelp reviews and Twitter support dialogs (6 relations of about 1.2k to 3.2k rows), 32 claims.
- Models: Claude Opus 4.6, Sonnet 4.6, Haiku 4.5, Qwen3-VL 235B, Qwen3-Next 80B.
- Findings: F1 0.94 with Opus at 3.1x lower cost than unoptimised; with Qwen3-VL, F1 0.87 beats the best baseline (0.83) at 7x lower cost. Baselines include an LLM-as-judge that reads serialised rows.
- Versus us: compiled queries, not an agentic judge; large models only; no training.

### B3. Thucy (Theologitis, Suciu; Univ. of Washington; AAAI 2026; arXiv 2512.03278)
- Task: input is a natural-language claim plus one or more relational databases not known in advance. Output is a verdict (Verified, Partly Verified, Partly Inaccurate, Inaccurate) plus the SQL queries used as evidence.
- Tools: four prompted agents (Data Expert, Schema Expert, SQL Expert, Verifier) connected to databases through MCP Toolbox.
- Datasets: TabFact (about 2k test claims); a Seattle crime database (about 1.5M rows) as a case study.
- Models: GPT-5 verifier; GPT-5-mini or GPT-4o-mini experts.
- Findings: 94.3% on TabFact, 5.6 points above the previous best (AutoTQA, 88.7%); about 5 cents per claim.
- Versus us: large proprietary models; multi-agent; no training; not a judge study.

### B4. ClaimDB (Theologitis, Dammu, Shah, Suciu; Univ. of Washington; ACL 2026 long; arXiv 2601.14698)
- Task: input is a natural-language claim plus a BIRD database (average 11 tables, 4.6M rows). Output is Entailed, Contradicted or Not Enough Information.
- Tools: one tool that executes arbitrary SQL, up to 20 calls (exceeding counts as failure).
- Settings: prompting only, 30 models, no training.
- Datasets: 53,368 claims from 80 BIRD databases, generated from SQL queries involving aggregation, sorting, joins or window functions.
- Models and results (accuracy): gpt-5-mini 0.827, claude-haiku-4.5 0.809, gemini-3-flash 0.801, gpt-oss-20b 0.740, qwen3-32b 0.574; small models: ministral-3-8b 0.533, qwen3-8b 0.521, qwen3-4b 0.511, llama3.2-3b 0.387, qwen3-1.7b 0.366, llama3.1-8b 0.344. gpt-5-mini without tools: 0.367.
- Findings: 17 of 30 models score below 55%. Best runs use 4 to 8 SQL calls. Open models over-predict Not Enough Information, sometimes skip the tool entirely, write weaker SQL and compose queries poorly.
- Limitations stated: no breakdown by claim type; SQL-only; static snapshots; future work on other tools.
- Versus us: the closest paper. It already shows zero-shot small models with a SQL tool are weak. It does not train them, and does not isolate when the tool is necessary.

### B5. FinGround (Guo, Wu, Yiu; Univ. of Hong Kong; ACL 2026; arXiv 2604.23588)
- Task: input is a question, an LLM's financial answer and retrieved SEC filing evidence. Output is flagged hallucinated claims with citations, plus a regenerated answer.
- Tools: hybrid retrieval over structure-preserving chunks, cross-encoder alignment, formula reconstruction (47 templates). No SQL.
- Settings: distilled from GPT-4o into Llama-3-8B-Instruct (3,200 annotated examples).
- Datasets: FinQA, TAT-QA, FinanceBench (150), FinHalu (1,200 claims); transfer to ConvFinQA, MultiHiertt.
- Findings: 91.4% detection F1 (teacher 95.0%), 18x faster per claim, 15.7x cheaper. 56% of pilot misses were failures to retrieve the operands needed for computational claims.
- Versus us: passive retrieval; its own failure analysis is the aggregation problem our SQL tool targets.

## C. Trained small models reasoning over tables (tables in the prompt)

### C1. TableMind (Jiang et al., USTC, WSDM 2026, arXiv 2509.06278)
- Task: table plus question or claim in, answer or verdict out. Tool: Python in a sandbox over a table that is also in context. Settings: SFT on distilled trajectories, then RL (rank-aware policy optimisation).
- Datasets: train 8k (WikiTQ, TabMWP, TabFact); test also HiTab, FinQA. Models: Qwen3-8B (also 1.7B, 4B).
- Findings: TabFact 91.85% vs 88.93% prior best; gains on every benchmark.
- Versus us: small tables that fit in the prompt; Python not SQL; not a judge.

### C2. Reasoning-Table (Lei et al., arXiv 2506.01710, 2025)
- GRPO on Qwen2.5-7B across table QA, TabFact, text-to-SQL; tables in context, no tool; beats Claude-3.7-Sonnet by about 4 points on table QA.

## D. SQL execution used to judge SQL itself (from the brief, not re-verified)
Reward-SQL (SIGMOD 2026), ToolSQL (KDD 2026), PV-SQL, RuCo-C, Graph-Reward-SQL: execution is used to score or repair a generated SQL query. The object judged is the query, not a natural-language claim.
Related: Singh et al. (Oracle, arXiv 2510.23854) judge natural-language narrations of SQL result tables without executing SQL; accuracy falls 10 to 30% as result sets grow.

## Comparison matrix

| Work | Live SQL tool | Verifies NL claims | Small model (8B or less) | Trained | Controlled "when is the tool needed" study |
|---|---|---|---|---|---|
| TIR-Judge | No (Python) | No | Yes | Yes (RL) | Partial (tool vs text) |
| T1 / ToolV | No (Python, BM25) | Math solutions | Yes | Yes (LoRA) | Toy sum-of-N study |
| Themis | No | No | Yes (7B) | Yes | No |
| AggChecker | Yes (no LLM) | Yes | n/a | n/a | No |
| Evergreen | Compiled upfront | Yes | No (80B+) | No | By claim type only |
| Thucy | Yes | Yes | No (GPT-5) | No | No |
| ClaimDB | Yes | Yes | Evaluated, weak | No | No breakdown |
| FinGround | No (retrieval) | Yes | Yes (8B) | Yes | No |
| TableMind | No (Python, table in prompt) | Yes (TabFact) | Yes | Yes | No |
| Ours | Yes | Yes | Yes | Phase 2 | Yes |

## Solidified gap

Prompted LLM agents with a SQL tool can verify natural-language claims over databases (Thucy, ClaimDB, Evergreen), but these systems rely on large models, and ClaimDB shows open models of 8B or less reach only 34 to 53% accuracy against 83% for gpt-5-mini. Trained tool-integrated judges exist (TIR-Judge, T1, TableMind), but they use Python over inputs already in the prompt, never SQL over databases too large to read. No work (1) isolates when database access is necessary, by comparing the same small judge with no context, partial context, full context and SQL access, stratified by how many rows a claim aggregates, or (2) trains small judges to use a SQL tool for claim verification. This project does both.

## Implications for the execution plan
1. The zero-shot pilot is still the right first step, but it partly reproduces ClaimDB, so its value is the controlled design (A-partial, A-full, B; rows-needed axis), not novelty on its own.
2. Fine-tuning a small judge (LoRA distillation, then possibly RL) moves from optional to the core contribution.
3. Use ClaimDB as an external test set (BIRD-based, public, 30-model leaderboard) instead of building a second domain, if its release licence allows.
4. Set the SQL call budget to about 5 to 8 and log it; ClaimDB's best runs used 4 to 8 calls, so TIR-Judge's cap of 3 may be too tight.
5. Consider a third label (Not Enough Information), as in ClaimDB, since small models over-predict it.

## Corrections to the brief and earlier notes
- T1 is published at ICLR 2026 (brief: under review).
- Themis is ICLR 2024 spotlight (brief: venue not confirmed).
- AggChecker is SIGMOD 2019 (arXiv 2018), Cornell with Google.
- Evergreen's open models are 80B and 235B; it did not test llama3.1-8b (that model appears in ClaimDB).
- FinGround is listed as ACL 2026.
- The brief's core gap statement is superseded by Thucy and ClaimDB.
