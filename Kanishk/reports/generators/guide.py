from common import CSS, SEC1, AUC, ROUTE_A, bars

G_CSS = CSS + """
@page{size:A4;margin:16mm 16mm 18mm}
body{font-size:10.6pt;line-height:1.5}
h1{font-size:22pt;color:var(--navy);font-weight:800;margin:0 0 4px}
h2{font-size:14.5pt;color:var(--navy);font-weight:700;margin:18px 0 6px;padding-top:4px;border-top:2px solid var(--navy)}
h3{font-size:11.5pt;color:var(--teal);font-weight:700;margin:12px 0 4px}
p{margin:5px 0}
ul,ol{margin:4px 0 6px 20px}li{margin:2px 0}
table{font-size:9.4pt;margin:6px 0 4px}tr{page-break-inside:avoid}table.keep{page-break-inside:avoid}h2,h3{page-break-after:avoid}td,th{padding:4px 7px}
.note{font-size:8.8pt;color:var(--mute)}
.card{background:var(--soft);border-radius:8px;padding:8px 12px;margin:8px 0;page-break-inside:avoid}
.take{border-left:4px solid var(--teal);background:var(--soft2);padding:6px 11px;border-radius:0 6px 6px 0;margin:8px 0;page-break-inside:avoid}
.warn{border-left:4px solid var(--amber);background:#fff7ed;padding:6px 11px;border-radius:0 6px 6px 0;margin:8px 0;page-break-inside:avoid}
.flow{margin:8px 0;flex-wrap:wrap;gap:4px}.box{font-size:9pt;padding:5px 9px}
.qa{margin:7px 0;page-break-inside:avoid}.qa b{color:var(--navy)}
.pb{page-break-before:always}
.cover{border-bottom:3px solid var(--teal);padding-bottom:8px;margin-bottom:6px}
.two{display:flex;gap:14px}.two>div{flex:1;min-width:0}
"""

def flow(*items):
    out = []
    for i, (t, cls) in enumerate(items):
        if i:
            out.append('<span class="arrow">→</span>')
        out.append(f'<div class="box {cls}">{t}</div>')
    return f'<div class="flow">{"".join(out)}</div>'

OBS = '<span class="tag t-obs">observed</span>'
INT = '<span class="tag t-int">interpretation</span>'
HYP = '<span class="tag t-hyp">hypothesis</span>'

s = []
s.append(f"""
<div class="cover"><div style="font-size:9pt;font-weight:700;letter-spacing:.12em;color:var(--teal);text-transform:uppercase">Personal study guide · not for screen sharing</div>
<h1>SQL Judge project: what we ran this week and how to defend it</h1>
<p class="note">Kanishk Didwania · Intro to LLMs project with Kushagra Agnihotri and Navtej Sai Singh Dua · prepared 16 Nov 2026 from the result files on the PC (sqljudge/results, sqljudge/router).</p></div>
<p>This guide covers the work since the last meet: the Section 1 and Section 3 runs (PC and Colab), our own A baselines, the pathway #3 router (complexity and non-answerable (NEI), logistic regression and MLPs), the new simple path S, and the proposal for #4. Every number below comes from the result files. Labels used throughout: {OBS} measured in our runs, {INT} our reading of the measurements, {HYP} not tested yet.</p>

<h2>1. The week at a glance</h2>
<table><tr><th>When</th><th>What ran</th><th>Where</th><th>Status</th></tr>
<tr><td>3 to 12 Nov</td><td>Section 1: C (judge + Arctic builder) for qwen3 1.7B, 4B, 8B, llama3.2 3B, llama3.1 8B</td><td>PC</td><td>done, 1,000 claims each</td></tr>
<tr><td>10 to 14 Nov</td><td>Section 1: qwen3:14b with Arctic</td><td>Colab (L4, then A100); first 59 on PC</td><td>done (1 failed claim)</td></tr>
<tr><td>12 to 14 Nov</td><td>Section 3: qwen3:4b and llama3.1:8b with OmniSQL 7B</td><td>Colab A100</td><td>done</td></tr>
<tr><td>12 to 14 Nov</td><td>Section 3: qwen3:4b with SLM SQL 1.5B, Qwen2.5 Coder 7B</td><td>PC and Colab</td><td>partial (676 and 63 claims)</td></tr>
<tr><td>12 to 15 Nov</td><td>Our own A baseline for the 5 PC judges</td><td>PC</td><td>done</td></tr>
<tr><td>14 to 15 Nov</td><td>#3 router: labels, embeddings, 9 classifiers, offline routing evaluation</td><td>PC</td><td>done</td></tr>
<tr><td>15 Nov</td><td>Simple path S built; qwen3:8b S on 1,000 claims</td><td>PC</td><td>done</td></tr>
<tr><td>15 Nov onward</td><td>S for qwen3:4b, then llama3.1:8b, qwen3:1.7b, llama3.2:3b</td><td>PC</td><td><b>running</b> (qwen3:4b 107/1,000 at 21:47)</td></tr></table>

<h2>2. Terms, and what each one does in our project</h2>
<table><tr><th style="width:21%">Term</th><th style="width:24%">Full form</th><th>Role in this project</th></tr>
<tr><td>LLM / SLM</td><td>Large / Small Language Model</td><td>Our judges are SLMs (1.7B to 14B parameters) served locally by Ollama.</td></tr>
<tr><td>Judge</td><td></td><td>The SLM that reads the claim, gathers evidence with a tool and outputs a verdict plus a one line justification.</td></tr>
<tr><td>NL2SQL, builder</td><td>Natural Language to SQL</td><td>A model that turns an English question into SQL. In C the judge asks it questions. It never gives verdicts.</td></tr>
<tr><td>Arctic</td><td>Arctic Text2SQL R1 7B (Snowflake), GGUF Q8_0</td><td>Our main builder. OmniSQL 7B, SLM SQL 1.5B, Qwen2.5 Coder 7B are the alternatives in Section 3.</td></tr>
<tr><td>SQL</td><td>Structured Query Language</td><td>How the database is queried. A writes it; C gets it from Arctic; S never sees it (Python writes it).</td></tr>
<tr><td>BIRD</td><td>a text to SQL benchmark of real databases</td><td>ClaimDB claims are generated from BIRD questions, each with a reference SQL query.</td></tr>
<tr><td>ClaimDB</td><td></td><td>The benchmark: claims over BIRD databases labelled ENTAILED, CONTRADICTED or NOT ENOUGH INFO. Public test = 1,000 claims, 11 databases; train split = 46,486 claims.</td></tr>
<tr><td>Gold SQL</td><td></td><td>BIRD's correct query behind each claim (file BIRD-source.jsonl). We read its structure to make router labels.</td></tr>
<tr><td>Embedding</td><td></td><td>768 numbers summarising a claim's meaning, from <span class="code">nomic-embed-text</span> via Ollama.</td></tr>
<tr><td>Frozen</td><td></td><td>The embedding model is used as is; we never train it. Only the small classifier on top is trained.</td></tr>
<tr><td>Classifier / router</td><td></td><td>Decides per claim: cheap path (A or S) or C.</td></tr>
<tr><td>Logistic regression</td><td></td><td>One weight per embedding number, weighted sum, sigmoid to a probability. Our best router.</td></tr>
<tr><td>MLP</td><td>Multi Layer Perceptron</td><td>Small neural network: MLP 2 has one hidden layer of 256, MLP 3 has 256 then 128.</td></tr>
<tr><td>ROC, AUC</td><td>Receiver Operating Characteristic; Area Under the (ROC) Curve</td><td>How well the router's scores separate the two classes over all thresholds. 0.5 chance, 1.0 perfect. Not accuracy.</td></tr>
<tr><td>McNemar test</td><td></td><td>Paired test on the same claims: compares how often only method 1 is right with how often only method 2 is right.</td></tr>
<tr><td>p value</td><td></td><td>Chance of a difference at least this large if the two methods were equally good. Below 0.05 = significant.</td></tr>
<tr><td>Oracle router</td><td></td><td>Imaginary router that always picks the path that turned out right. Upper bound only; it needs the answer.</td></tr>
<tr><td>LoRA</td><td>Low Rank Adaptation</td><td>Cheap fine tuning method proposed for #4 (section 12).</td></tr></table>
""")

s.append(f"""
<h2>3. The task and the three setups</h2>
<p>The judge gets a claim plus ClaimDB's hint ("Extra Information") and must output one verdict:</p>
<ul><li><b>ENTAILED:</b> the data supports the claim.</li><li><b>CONTRADICTED:</b> the data shows the claim is false.</li>
<li><b>NOT ENOUGH INFO (NEI):</b> the database cannot settle it (the needed fact is not stored, the claim is subjective, or it is counterfactual). NEI is not "false": CONTRADICTED needs evidence against the claim, NEI means no evidence either way can exist in this database.</li></ul>
<div class="card"><b>Illustrative example</b> (superhero database, not experimental data). "69 superheroes are taller than 200 cm": ENTAILED if the count is 69, CONTRADICTED if it is 70. "Hulk's costume is the most iconic of the 2000s": NEI, the database stores heights and powers, not opinions.</div>

<h3>Setup A: judge writes its own SQL (ClaimDB's original setup)</h3>
{flow(("Judge", ""), ("writes SQL", ""), ("SQLite runs it", ""), ("rows or SQL error back", ""))}
<p>No schema is given; the prompt tells the judge to query the schema first. Small judges make many naming errors ("no such column"); in October, 34% of qwen3:8b's A queries failed. Advantage: no extra model. Limitation: the judge must be good at SQL.</p>
<h3>Setup C: judge asks the builder (our main contribution)</h3>
{flow(("Judge", ""), ("English question", ""), ("Arctic writes SQL from the schema", "c"), ("SQL + rows back", ""))}
<p>The judge never writes SQL; Arctic sees the schema and the hint. Advantage: far fewer grounding errors. Limitation: a second 7B model per call, and Arctic always returns some query and rows, even for questions the database cannot answer.</p>
<h3>Setup S: simple path, judge + Python lookup tool (built 15 Nov)</h3>
{flow(("Judge", ""), ("fills lookup form", ""), ("Python checks names, builds parameterised SQL, runs read only", "o"), ("rows + match count back", ""))}
<p>Two tools per database: <span class="code">describe_tables(table)</span> lists tables and columns (with example values and links between tables), and <span class="code">lookup(table, filters, aggregate, column, columns, group_by, order_by, descending, limit)</span> queries one table. Filters use =, !=, &gt;, &gt;=, &lt;, &lt;=, contains, starts_with, is_null, not_null; aggregates are count, count_distinct, sum, avg, min, max. Names are matched exactly, then ignoring case, then ignoring spaces and underscores; a wrong name returns the closest real names. When a text filter matches nothing, the tool shows stored values that look similar ("Marvel" returns "Marvel Comics"). Prompt, output format and the 20 call limit are the same as A and C. Code: <span class="code">code/simple_tools.py</span>, condition S in <span class="code">run_judge.py</span>.</p>
""")

rows = ""
for j in ["qwen3:14b", "qwen3:8b", "qwen3:4b", "qwen3:1.7b", "llama3.1:8b", "llama3.2:3b"]:
    cdb, a, c, ci, where, sa, sc, oa, oc, p = SEC1[j]
    rows += (f"<tr><td><b>{j}</b></td><td class='n'>{cdb}</td><td class='n'>{a if a is not None else 'not run'}</td><td class='n'><b>{c}</b></td>"
             f"<td class='n'>{ci}</td><td class='n'>{'+%.1f' % (c-a) if a is not None else ''}</td><td class='n'>{f'{oa} / {oc}' if oa else ''}</td><td class='n'>{p or ''}</td>"
             f"<td class='n'>{sa if sa else ''}</td><td class='n'>{sc}</td></tr>")
s.append(f"""
<h2>4. Results: Section 1 and Section 3</h2>
<h3>Section 1: each judge with Arctic (C) against the judge alone (A), all 1,000 claims {OBS}</h3>
<table><tr><th>Judge</th><th class="n">ClaimDB release</th><th class="n">Our A</th><th class="n">Our C</th><th class="n">C 95% CI</th><th class="n">C vs A</th><th class="n">only A right / only C right</th><th class="n">McNemar p</th><th class="n">A s/claim</th><th class="n">C s/claim</th></tr>{rows}</table>
<p class="note">ClaimDB release = ClaimDB's published per claim runs for the same model, rescored by us on the same 1,000 claims (their full test numbers match their paper). qwen3:14b C ran on Colab (first 59 claims on the PC); its time is not comparable with PC times. All other runs on the PC (RTX 4070 Super).</p>
<div class="take"><b>Main result:</b> the builder adds 13.1 to 20.0 points over our own A for every judge, all p below 1e-10. Our harness alone is close to ClaimDB (A within 4 points for 4 of 5 judges; llama3.2:3b is 6.6 lower and had 130 failed runs from broken output format). qwen3:14b with Arctic (76.5) is no better than qwen3:8b (76.0): {INT} beyond 8B the builder, not the judge, limits accuracy.</div>
<h3>Where C wins and where it loses (qwen3:8b, accuracy per gold label) {OBS}</h3>
<table><tr><th>Gold label</th><th class="n">A</th><th class="n">C</th><th class="n">S</th></tr>
<tr><td>ENTAILED</td><td class="n">31.5</td><td class="n"><b>64.9</b></td><td class="n">41.7</td></tr>
<tr><td>CONTRADICTED</td><td class="n">39.3</td><td class="n"><b>80.1</b></td><td class="n">49.5</td></tr>
<tr><td>NOT ENOUGH INFO</td><td class="n"><b>96.7</b></td><td class="n">83.0</td><td class="n">93.8</td></tr></table>
<p>Share of NEI verdicts given: A 69.9%, S 59.8%, C 36.1% (true share 33.6%). {INT} A and S say NEI too often, which helps on NEI claims and hurts everywhere else; C's builder gives the judge evidence, which fixes ENTAILED and CONTRADICTED but sometimes pushes the judge to decide claims that should stay NEI. This is the seed of the non-answerable (NEI) routing idea (section 7).</p>
<h3>Section 3: other builders {OBS}</h3>
<table><tr><th>Judge</th><th>Builder</th><th class="n">Claims</th><th class="n">Accuracy</th><th>Ran on</th></tr>
<tr><td>qwen3:4b</td><td>Arctic 7B</td><td class="n">1000</td><td class="n">68.3</td><td>PC</td></tr>
<tr><td>qwen3:4b</td><td>OmniSQL 7B</td><td class="n">1000</td><td class="n">65.5</td><td>Colab A100</td></tr>
<tr><td>qwen3:4b</td><td>SLM SQL 1.5B</td><td class="n">676</td><td class="n">54.1</td><td>PC, partial</td></tr>
<tr><td>qwen3:4b</td><td>Qwen2.5 Coder 7B</td><td class="n">63</td><td class="n">42.9</td><td>Colab, partial</td></tr>
<tr><td>llama3.1:8b</td><td>Arctic 7B</td><td class="n">1000</td><td class="n">54.7</td><td>PC</td></tr>
<tr><td>llama3.1:8b</td><td>OmniSQL 7B</td><td class="n">1000</td><td class="n">54.0</td><td>Colab A100</td></tr></table>
<p>OmniSQL is 2.8 (qwen3:4b) and 0.7 (llama3.1:8b) points below Arctic. The partial cells are early claims only and should not be quoted as final. Not in our results folder yet: Navtej's ministral judges, Kushagra's Section 2 builders for qwen3:8b, llama3.1:8b + SLM SQL. Compute: Colab Pro units are used up, the L4 was slower than the PC GPU (memory bandwidth), and RKIC access has been requested.</p>
""")

s.append(f"""
<h2>5. Pathway #3: the router</h2>
<p><b>Sir's idea:</b> not every claim needs the expensive builder. A router reads the claim and sends it to a cheap path or to C. If the router is right, we keep C's accuracy at lower cost.</p>
<h3>Step 1: labels from gold SQL (training time only)</h3>
{flow(("Claim", ""), ("its BIRD gold SQL", ""), ("parse with sqlglot: tables, nesting", "c"), ("label", ""))}
{flow(("New test claim text", ""), ("embedding", ""), ("trained classifier", "c"), ("predicted label → route", "o"))}
<p>Gold SQL exists because every ClaimDB claim was generated from a BIRD question that has a reference query. We use it only to <b>create training labels</b> automatically for 47,486 claims (hand labelling that many is impossible). At test time the router sees only the claim and hint text; it never sees gold SQL, the database or any verdict. This does not defeat the purpose: the router learns to predict from text what the gold SQL would look like.</p>
<h3>The exact label rules (from <span class="code">router/make_labels.py</span>)</h3>
<table><tr><th>Label</th><th>Positive (route to cheap path) when</th><th class="n">Train</th><th class="n">Tune</th><th class="n">Test</th></tr>
<tr><td>Strict complexity</td><td>gold SQL uses at most <b>1 table</b> AND has no nested SELECT, no UNION / INTERSECT / EXCEPT, no window function</td><td class="n">19.8%</td><td class="n">18.2%</td><td class="n">21.5%</td></tr>
<tr><td>Loose complexity</td><td>at most <b>2 tables</b> (one join) with the same other conditions</td><td class="n">67.3%</td><td class="n">63.3%</td><td class="n">69.2%</td></tr>
<tr><td>Non-answerable (NEI)</td><td>ClaimDB label is NOT ENOUGH INFO</td><td class="n">45.0%</td><td class="n">45.7%</td><td class="n">33.6%</td></tr></table>
<p class="note">Claims whose gold SQL could not be parsed were skipped. Percentages are the positive share in each split.</p>
<div class="card"><b>Illustrative SQL</b> (superhero database):<br>
<span class="code">SELECT COUNT(*) FROM superhero WHERE height_cm &gt; 200</span> → one table, not nested: strict positive, loose positive.<br>
<span class="code">SELECT COUNT(*) FROM superhero s JOIN publisher p ON s.publisher_id = p.id WHERE p.publisher_name = 'Marvel Comics'</span> → two tables: strict negative, loose positive.<br>
<span class="code">SELECT superhero_name FROM superhero WHERE height_cm = (SELECT MAX(height_cm) FROM superhero)</span> → one table but nested: negative for both.</div>
<h3>Step 2: split by database</h3>
<table><tr><th>Split</th><th class="n">Claims</th><th class="n">Databases</th><th>Use</th></tr>
<tr><td>Train</td><td class="n">40,652</td><td class="n">62</td><td>fit the classifiers (ClaimDB train split, BIRD train databases)</td></tr>
<tr><td>Tune</td><td class="n">5,834</td><td class="n">7</td><td>pick the decision threshold (held out databases)</td></tr>
<tr><td>Test</td><td class="n">1,000</td><td class="n">11</td><td>ClaimDB public test; none of these databases seen in training</td></tr></table>
<p>Whole databases are held out, not random claims, so the router cannot memorise table names or a database's topic. This tests what we need in practice: routing claims about a database it has never seen.</p>
<h3>Step 3: embeddings and classifiers</h3>
<p><span class="code">nomic-embed-text</span> (run in Ollama) turns "classification: " + claim + hint into 768 numbers. Claims with similar meaning get nearby vectors, e.g. "Over 60 heroes are above 2 m" and "69 superheroes are taller than 200 cm" land close together. The numbers are standardised (StandardScaler, fitted on train).</p>
<ul><li><b>Logistic regression:</b> probability = sigmoid(w1·x1 + ... + w768·x768 + b). Class weights balance positives and negatives.</li>
<li><b>MLP 2:</b> 768 → 256 ReLU units → output. <b>MLP 3:</b> 768 → 256 → 128 → output. Both: L2 penalty 0.001, batch 256, early stopping on 10% of train, the smaller class oversampled to balance.</li>
<li><b>Threshold:</b> the probability cutoff that maximises balanced accuracy on the 7 tuning databases.</li></ul>
<p>Nine routers in total: 3 label types × 3 classifiers. Predictions are judge independent (one prediction per claim, reused for every judge).</p>
<h3>Step 4: offline evaluation</h3>
<p>We already have every claim's verdict under A, C and (for qwen3:8b) S. For a router, each claim takes the verdict from the path it would be sent to; accuracy and mean seconds are computed on that mix. Comparisons: always C, always cheap path, a random router sending the same share of claims, the true label router, and the oracle. Script: <span class="code">router/eval_routing.py</span> (<span class="code">--cheap S</span> for S).</p>
""")

chart = bars(["Strict complexity", "Loose complexity", "Non-answerable (NEI)"],
             [("Logistic regression", [v[0] for v in AUC.values()]), ("MLP 2", [v[1] for v in AUC.values()]), ("MLP 3", [v[2] for v in AUC.values()])],
             ["#1d3557", "#14b8a6", "#94a3b8"], width=520, height=220, vmax=1.0, baseline=0.5, ylabel="test AUC")
s.append(f"""
<h2>6. Classifier results {OBS}</h2>
<div class="two"><div>
<table><tr><th>Task</th><th class="n">Logistic regression</th><th class="n">MLP 2</th><th class="n">MLP 3</th></tr>
<tr><td>Strict complexity</td><td class="n"><b>0.72</b></td><td class="n">0.68</td><td class="n">0.67</td></tr>
<tr><td>Loose complexity</td><td class="n"><b>0.64</b></td><td class="n">0.61</td><td class="n">0.61</td></tr>
<tr><td>Non-answerable (NEI)</td><td class="n"><b>0.95</b></td><td class="n"><b>0.95</b></td><td class="n">0.94</td></tr></table>
<p class="note">Test AUC on the 1,000 public test claims. Balanced accuracy at the tuned threshold: strict 0.65 / 0.62 / 0.61; loose 0.60 / 0.57 / 0.54; non-answerable 0.88 / 0.88 / 0.88. Predicted positive share (test): strict 37 / 36 / 26% (true 21.5%), non-answerable 34 / 36 / 38% (true 33.6%).</p>
</div><div>{chart}</div></div>
<h3>How to read AUC</h3>
<p>Sort all test claims by the router's score. AUC is the chance that a random positive claim gets a higher score than a random negative one. 0.5 = no better than a coin; 1.0 = every positive above every negative. It ignores the threshold, so it is <b>not accuracy</b>: a 0.95 AUC router still makes mistakes once a single cutoff is chosen (balanced accuracy 0.88 here).</p>
<h3>What it means {INT}</h3>
<ul><li><b>Non-answerable claims are easy to spot from text.</b> ClaimDB's NEI claims come in recognisable categories (out of schema, counterfactual "If ... had ...", subjective "widely regarded as"). The wording gives them away.</li>
<li><b>Complexity is hard from text.</b> How many tables a query needs depends on how the database is organised, which the router never sees.</li>
<li><b>Bigger networks did not help.</b> Logistic regression is best or tied everywhere. When the input lacks the needed information (the schema), extra layers can only fit noise; with 40k examples and frozen 768 dim inputs a linear boundary already captures what is there.</li></ul>
""")

rows = ""
for j in ["qwen3:8b", "qwen3:4b", "qwen3:1.7b", "llama3.1:8b", "llama3.2:3b"]:
    aA, aC, orc, st, sl, lt, ll, at, al, ap = ROUTE_A[j]
    rows += f"<tr><td><b>{j}</b></td><td class='n'>{aA}</td><td class='n'><b>{aC}</b></td><td class='n'>{st}</td><td class='n'>{sl}</td><td class='n'>{lt}</td><td class='n'>{ll}</td><td class='n'>{at}</td><td class='n'>{al}</td><td class='n'>{ap}</td><td class='n'>{orc}</td></tr>"
s.append(f"""
<h2>7. Routing results with A as the cheap path (all 5 judges) {OBS}</h2>
<table><tr><th>Judge</th><th class="n">Always A</th><th class="n">Always C</th><th class="n">Strict true</th><th class="n">Strict LR</th><th class="n">Loose true</th><th class="n">Loose LR</th><th class="n">Answ. true</th><th class="n">Answ. LR</th><th class="n">p (Answ. LR vs C)</th><th class="n">Oracle</th></tr>{rows}</table>
<p class="note">LR = logistic regression router. "True" = routing with the real label (a perfect classifier for that label). MLP routers are similar or worse, e.g. non-answerable routing for qwen3:4b: MLP 2 70.1 (p 0.089), MLP 3 70.7 (p 0.032). Random router with the same share as the non-answerable LR router: qwen3:8b 69.2, qwen3:4b 63.4.</p>
<h3>Why complexity routing fails</h3>
<p>Three different things are easy to mix up: (1) how hard the SQL is to write, (2) whether the cheap path finds useful evidence, (3) whether the final verdict is right. Sir's idea assumes (1) predicts (3). Our numbers say it does not: even with <b>perfect</b> strict labels qwen3:8b scores 74.1 against 76.0 for always C, and every judge loses with every complexity router. {INT} C is better than A even on one table claims, so sending them to A costs accuracy; this is a limit of the routing signal, not just of the classifier. Loose routing sends about 70% of claims to A and loses 8.5 to 14.1 points even with true labels.</p>
<div class="card"><b>Same sentence, different SQL</b> (illustrative). "Marvel has more than 300 heroes." If publisher name is stored in the hero table: one table. If heroes store a publisher_id pointing to a publisher table (as in BIRD's superhero database): a join. The text is identical; only the schema decides.</div>
<h3>Why route non-answerable (NEI) claims</h3>
<p>For qwen3:8b, 83 claims are right only under A and 283 only under C; 51 of those 83 are NEI. Other judges: qwen3:4b 121 (70 NEI), qwen3:1.7b 30 (17), llama3.1:8b 121 (78), llama3.2:3b 132 (91). So the claims where the cheap path wins are mostly NEI. {INT} Arctic always produces some query and rows; the judge, seeing numbers, tends to commit to ENTAILED or CONTRADICTED on claims the database cannot settle. Routing rule: predicted NEI → cheap path; otherwise → C. This was tested as a strategy; it does not guarantee the cheap path is right on every NEI claim.</p>
<div class="take"><b>Result:</b> non-answerable routing beats always C significantly only for qwen3:4b (70.9 vs 68.3, p = 0.007). For qwen3:8b it ties (76.0), for llama3.1:8b and llama3.2:3b it is within 0.6 points (not significant), and for qwen3:1.7b it is 0.9 lower. With true labels the gain would be 1.3 to 6.0 points, so the router's errors eat most of it.</div>
""")

s.append(f"""
<h2>8. The simple path S, end to end (qwen3:8b) {OBS}</h2>
<table class="keep"><tr><th>qwen3:8b, 1,000 claims</th><th class="n">Accuracy</th><th class="n">Seconds per claim</th><th>Note</th></tr>
<tr><td>Always A</td><td class="n">56.0</td><td class="n">23.4</td><td></td></tr>
<tr><td>Always S</td><td class="n">61.8</td><td class="n">27.2</td><td>8 failed (malformed tool arguments twice)</td></tr>
<tr><td>Always C</td><td class="n">76.0</td><td class="n">29.0</td><td></td></tr>
<tr><td>Strict, true labels → S</td><td class="n">75.6</td><td class="n">26.9</td><td>22% to S</td></tr>
<tr><td>Strict, LR router → S</td><td class="n">71.9</td><td class="n">28.0</td><td>p = 0.0002 vs C (worse)</td></tr>
<tr><td>Non-answerable, true labels → S</td><td class="n">79.6</td><td class="n">25.2</td><td>34% to S</td></tr>
<tr><td>Non-answerable, LR router → S</td><td class="n">76.5</td><td class="n">26.1</td><td>p = 0.64 vs C (no real difference)</td></tr>
<tr><td>Oracle, S or C per claim</td><td class="n">85.4</td><td class="n"></td><td>upper bound only</td></tr></table>
<ul><li>S beats A: 156 claims only S right vs 98 only A right, p = 0.0003. It trails C: 94 vs 236, p = 3e-15.</li>
<li>Tool use: 1,136 lookups (98 returned a name or argument error, each with the closest real names), 903 describe calls; on 163 claims the judge answered without any tool call.</li>
<li>30 claim pilot before the full run: S 19, A 20, C 26 correct.</li></ul>
<h3>Runtime</h3>
<p>S was meant to be cheap because it drops the 7B builder. Measured: S 27.2 s vs C 29.0 s, a saving of 1.8 s (6%). {INT} Most time is the judge's own reasoning tokens (qwen3 thinks before each tool call), not the builder, so removing the builder saves little. With A as the cheap path the picture is the same (23.4 vs 29.0 s). An idea that would save real time {HYP}: when the non-answerable router is very confident a claim is NEI, skip the judge and answer NEI directly. Not tested yet.</p>
<div class="warn"><b>Coverage caveat:</b> S has been run on all 1,000 claims for qwen3:8b only. qwen3:4b S was at 107/1,000 (66.4%, 47.6 s per claim) at the last check; llama3.1:8b, qwen3:1.7b and llama3.2:3b are queued. A and C cover all five judges.</div>

<h2>9. Statistics used</h2>
<h3>McNemar test</h3>
<p>Both methods are scored on the same 1,000 claims, so we compare paired outcomes. Claims where both are right or both wrong say nothing about which is better. Only the disagreements count: b = only method 1 right, c = only method 2 right. If the methods were equal, each disagreement would be a coin flip, so we ask how unlikely a split as uneven as b vs c is (exact binomial, two sided). Example: qwen3:8b A vs C has 83 vs 283 disagreements, p ≈ 1e-26. Non-answerable LR routing vs C for qwen3:8b with S: the two differ on few claims and split almost evenly, p = 0.64.</p>
<h3>Significance vs size</h3>
<p>p &lt; 0.05 says a difference is unlikely to be chance; it says nothing about size. +2.6 points (qwen3:4b) is significant but small; +0.5 (qwen3:8b with S) is neither. Section 1 gains (13 to 20 points, p below 1e-10) are both large and certain.</p>
<h3>Oracle</h3>
<p>For each claim, take the path that was right. qwen3:8b: 84.3 (A or C) and 85.4 (S or C) vs 76.0 always C. It shows how much a perfect router could gain, about 9 points. It is not deployable: it needs the correct verdict to choose.</p>
""")

s.append(f"""
<h2>10. Limitations and caveats</h2>
<ol><li><b>Router sees text only.</b> No schema, no database contents.</li>
<li><b>Complexity depends on the schema,</b> so text based complexity routers are capped.</li>
<li><b>The non-answerable router may be dataset specific.</b> ClaimDB's NEI claims have recognisable wording; on real world claims NEI may be harder to spot. Also, NEI is one of the three answers, so the router partly predicts the answer from style.</li>
<li><b>Good AUC does not mean good routing.</b> 0.95 AUC still gave no gain for 4 of 5 judges.</li>
<li><b>Each wrong route usually costs a correct verdict.</b> Routing NEI claims to A loses some, routing E/C claims to A loses many.</li>
<li><b>The cheap path is not much cheaper</b> in time for these judges (S 27.2 vs C 29.0 s).</li>
<li><b>S coverage:</b> qwen3:8b only so far.</li>
<li><b>Section 3 partial cells</b> (SLM SQL, Coder) are early claims only.</li>
<li><b>Train vs test label mix:</b> NEI share is 45% in train but 33.6% in test; the threshold is tuned on held out databases, which partly absorbs this.</li></ol>

<h2>11. What #3 established, in one table</h2>
<table><tr><th>Statement</th><th>Status</th></tr>
<tr><td>C beats A by 13 to 20 points for 5 judges</td><td>{OBS}</td></tr>
<tr><td>Complexity routing (any router, even true labels) loses to always C</td><td>{OBS}</td></tr>
<tr><td>Non-answerable (NEI) router AUC 0.95; significant gain only for qwen3:4b with A (+2.6)</td><td>{OBS}</td></tr>
<tr><td>Logistic regression ≥ MLPs on every task</td><td>{OBS}</td></tr>
<tr><td>S: 61.8 for qwen3:8b, between A and C, 1.8 s faster than C</td><td>{OBS}</td></tr>
<tr><td>The builder misleads the judge on NEI claims</td><td>{INT}</td></tr>
<tr><td>Schema access would make complexity routing work</td><td>{HYP} (#4)</td></tr>
<tr><td>Skipping the judge on confident NEI would save time</td><td>{HYP}</td></tr></table>

<h2>12. Proposed #4: a fine tuned small LM as the router {HYP}</h2>
<p><b>Fine tuning</b> means continuing to train a pretrained model on our task, so its weights adapt. Proposed: Qwen3 0.6B, trained on the same 40,652 training claims to output the route label.</p>
<p><b>LoRA (Low Rank Adaptation).</b> Intuition: instead of rewriting a whole book, add sticky notes in the margins. Technically: each large weight matrix W (d × d) stays frozen; we learn a small update ΔW = B·A where A is r × d and B is d × r with small rank r (e.g. 8 or 16). Only A and B are trained, a tiny fraction of the parameters, so it fits on the PC GPU.</p>
<table class="keep"><tr><th></th><th>#3 (done)</th><th>#4 (proposed)</th></tr>
<tr><td>Input</td><td>claim + hint text</td><td>claim + hint <b>+ database schema (table and column names)</b></td></tr>
<tr><td>Text understanding</td><td>frozen embedding, 768 numbers</td><td>the SLM reads the tokens itself, adapted by LoRA</td></tr>
<tr><td>Decision</td><td>logistic regression / MLP</td><td>fine tuned Qwen3 0.6B outputs the label</td></tr>
<tr><td>Labels, splits, A/S/C results, evaluation script</td><td colspan="2">unchanged; only the predictions file changes</td></tr></table>
<p><b>Why the schema matters:</b> whether a claim needs one table or a join is decided by the schema (section 7). The #3 router could never see it; #4 can. The non-answerable router is already at 0.95 AUC, so #4's main test is whether complexity routing can finally beat always C, and whether the router's errors on non-answerable claims shrink enough to capture more of the true label gain (+4.6 for qwen3:8b with A).</p>
""")

qa = [
 ("Why use gold SQL if the aim is to avoid SQL generation?", "Gold SQL is used once, offline, to create training labels automatically. The deployed router never sees it; at test time it only reads the claim text. It is a labelling device, like using answer keys to grade practice questions."),
 ("What exactly are strict and loose complexity?", "Strict: gold SQL touches at most one table and has no nested SELECT, set operation or window function. Loose: at most two tables with the same other conditions. Implemented with sqlglot in router/make_labels.py. Test positive shares 21.5% and 69.2%."),
 ("Why doesn't a perfect complexity router improve accuracy?", "Because C is better than A (and S) even on one table claims. Sending those claims to the cheap path can only lose accuracy; qwen3:8b with perfect strict labels: 74.1 vs 76.0. The signal is wrong, not just the classifier."),
 ("Why are non-answerable claims easier to predict?", "ClaimDB's NEI claims are written in recognisable ways (out of schema facts, counterfactuals, subjective statements), so text alone separates them (AUC 0.95). Complexity depends on the schema, which the router does not see."),
 ("Why did logistic regression beat the MLPs?", "The limiting factor is the information in the input, not model capacity. With frozen embeddings and no schema, a linear boundary already uses what is there; extra layers add variance. Logistic regression also has class weights, the MLPs rely on oversampling."),
 ("Is 0.95 AUC the same as 95% accuracy?", "No. AUC measures ranking over all thresholds. At the chosen threshold balanced accuracy is about 0.88, and those errors are enough to remove most of the routing gain."),
 ("What does the oracle tell us?", "That a perfect per claim choice would reach about 84 to 85% for qwen3:8b vs 76.0 always C: the two paths are complementary. It is an upper bound that needs the answer, not a model."),
 ("Why is the +0.5 for qwen3:8b with S weak?", "The routed system and always C disagree on few claims and the disagreements split almost evenly; McNemar p = 0.64. It is indistinguishable from no change."),
 ("Is the qwen3:4b gain real?", "70.9 vs 68.3, McNemar p = 0.007 on 1,000 claims, and far above a random router with the same share (63.4). It is significant but small, and it is one judge out of five."),
 ("Why can the same claim need different SQL in different databases?", "SQL follows the schema. If a fact sits in the same table as the entity, one table suffices; if it sits in a linked table, a join is needed. The sentence does not change."),
 ("Why could a schema aware SLM do better (#4)?", "It sees the table and column names with the claim, so it can tell whether the needed facts are in one table. That is exactly what the #3 router lacks. This is a hypothesis to test."),
 ("Is non-answerable routing dataset dependent?", "Possibly. It exploits how ClaimDB phrases NEI claims. We have not tested on other claim sources, so we should not claim it generalises."),
 ("Why is S not much faster than C?", "Time is dominated by the judge's own reasoning tokens; the builder call is a small part. Removing the builder saved only 1.8 s per claim (27.2 vs 29.0)."),
 ("Why is S better than A?", "S removes SQL syntax errors and repairs wrong names with closest matches and similar stored values. qwen3:8b: 61.8 vs 56.0, p = 0.0003. It is still below C because the judge must plan multi table lookups itself."),
 ("Why did you split by database?", "So the router is tested on databases it has never seen, as in real use. A random split would let it memorise table names and topics."),
 ("Why route NEI claims to the cheap path and not simply answer NEI?", "Routing keeps the judge in the loop, so a wrong NEI prediction can still be corrected. Answering NEI directly would save far more time but risks errors; that is a separate hypothesis we have not tested."),
 ("Was the harness itself responsible for the C gain?", "No. Our A (same harness, no builder) is within 4 points of ClaimDB's runs for 4 of 5 judges; the 13 to 20 point jump comes from adding the builder."),
 ("Why not run qwen3:14b A?", "Compute: 14B ran on Colab, whose units are used up. We have its C result (76.5) only."),
 ("What would make #3 succeed?", "A routing signal that tracks where the cheap path is actually better (mostly NEI), predicted accurately enough that errors do not cancel the gain, and a cheap path that is actually cheaper. Right now only the first holds."),
]
qa_html = "".join(f'<div class="qa"><b>Q{i+1}. {q}</b><br>{a}</div>' for i, (q, a) in enumerate(qa))

s.append(f"""
<h2 class="pb">13. Meeting preparation</h2>
<h3>One minute version</h3>
<div class="card">Our main result is that a small judge with an NL2SQL builder (C) beats the same judge writing SQL (A) by 13 to 20 points for all five judges; qwen3:8b reaches 76.0 against ClaimDB's 52.1. For pathway #3 we trained routers that pick, per claim, between a cheap path and C. Complexity routers are weak (AUC up to 0.72) and complexity routing loses even with perfect labels. Non-answerable routing, which sends predicted NEI claims to the cheap path, uses a strong classifier (AUC 0.95) but gives a significant gain only for qwen3:4b (+2.6). We built the real cheap path S, a Python lookup tool: it beats A but trails C, and it is barely faster. Next is #4: a fine tuned small LM router that also sees the schema.</div>
<h3>Three minute version</h3>
<ol><li><b>Section 1:</b> all five PC judges with Arctic and without it; gains 13 to 20 points, p below 1e-10; qwen3:14b on Colab 76.5, same as 8B, so the builder is likely the bottleneck.</li>
<li><b>Section 3:</b> OmniSQL is close to Arctic (65.5 and 54.0 vs 68.3 and 54.7); smaller or general builders are behind on the claims run so far.</li>
<li><b>#3 router:</b> labels from gold SQL for 47,486 claims (strict, loose, non-answerable); frozen nomic embeddings; logistic regression, MLP 2, MLP 3; databases held out.</li>
<li><b>Classifiers:</b> non-answerable 0.95 AUC, complexity 0.64 to 0.72; MLPs never better.</li>
<li><b>Routing:</b> complexity hurts for every judge even with true labels; non-answerable routing helps significantly only for qwen3:4b; the oracle shows about 9 points of untapped room.</li>
<li><b>S:</b> 61.8 for qwen3:8b, between A and C, only 1.8 s faster than C; other judges running.</li>
<li><b>Ask:</b> #4 with schema input, the confident NEI shortcut, or both.</li></ol>
<h3>Questions Sir may ask</h3>
{qa_html}
<h3>Things I must NOT claim in the meeting</h3>
<ul><li>That #4 has been run, or that schema input will fix complexity routing (it is a hypothesis).</li>
<li>That the oracle is a model we built.</li>
<li>That AUC 0.95 means 95% accuracy.</li>
<li>That non-answerable routing improves accuracy in general (one significant case out of five).</li>
<li>That S is substantially cheaper than C (27.2 vs 29.0 s).</li>
<li>That S results hold for all judges (qwen3:8b only so far).</li>
<li>That the partial Section 3 cells (SLM SQL 676 claims, Coder 63 claims) are final numbers.</li>
<li>That the router uses gold SQL at test time.</li>
<li>That the MLPs beat logistic regression.</li></ul>
""")

html = f"<!doctype html><html><head><meta charset='utf-8'><title>Research Project Personal Study Guide</title><style>{G_CSS}</style></head><body>{''.join(s)}</body></html>"
open("guide.html", "w").write(html)
print("ok")
