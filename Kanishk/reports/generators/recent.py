import brief as _b
from common import bars
PAGE_CSS = _b.PAGE_CSS + """
.ex{font-family:'DejaVu Sans Mono',monospace;font-size:11px;background:#fff;border:1px solid var(--line);border-left:3px solid var(--teal);border-radius:4px;padding:4px 8px;margin:3px 0;white-space:pre-wrap}
td.g{color:var(--green);font-weight:700}td.r{color:var(--red);font-weight:700}
"""

def page(n, total, kicker, title, body, zoom=1.0):
    return (f'<section class="page"><div class="inner" style="zoom:{zoom}"><div class="kicker">{kicker}</div><h1>{title}</h1>{body}</div>'
            f'<div class="foot"><span>SQL Judge project · subset_210 results and the simple path S · 22 Nov 2026</span><span>{n} / {total}</span></div></section>')

T = 7
P = []

# 1 what we ran
P.append(page(1, T, "What we ran (Sir's 15 Nov note: subset only, plan first)", "Results on the 210 claim subset", """
<div class="cols"><div class="col card">
<h2>The subset</h2>
<p><b>subset_210</b>: 70 ENTAILED, 70 CONTRADICTED, 70 NOT ENOUGH INFO, from all 11 test databases (seed 13, the same 210 as the midsem pilot).</p>
<table style="margin-top:8px;font-size:13.5px"><tr><th>Inside the 210</th><th class="n">Claims</th></tr>
<tr><td>gold SQL uses 1 table</td><td class="n">41</td></tr>
<tr><td>gold SQL uses 2 tables</td><td class="n">99</td></tr>
<tr><td>3+ tables or nested</td><td class="n">70</td></tr>
<tr><td>non-answerable (gold NEI)</td><td class="n">70</td></tr></table>
<p class="small">The first three rows add to 210. The last row is a separate question about the same claims.</p>
</div><div class="col card t">
<h2>What was run, what was reused</h2><ul>
<li><b>Reused, no rerun:</b> A and C for all 5 judges (already on all 1,000 claims); S for qwen3:8b (already on all 1,000)</li>
<li><b>New runs (21 to 22 Nov):</b> S on the 210 for qwen3:4b, qwen3:1.7b, llama3.1:8b, llama3.2:3b. About 3.5 h on the PC</li>
<li><b>Routers:</b> no runs needed. A router only decides which claims take S's verdict and which take C's, so all three routers are scored from the same result files</li></ul>
</div><div class="col card">
<h2>The three setups</h2><ul>
<li><b>A:</b> judge writes SQL itself</li>
<li><b>C:</b> judge asks Arctic (a 7B SQL model) in English</li>
<li><b>S:</b> judge fills a lookup form; Python writes and runs the SQL (page 6)</li></ul>
<p class="small" style="margin-top:8px">Same prompt, answer format and 20 tool call limit in all three. Router = logistic regression on frozen nomic embeddings, threshold tuned on held out databases.</p>
</div></div>""", zoom=1.25))

# 2 A S C
chart = bars(["qwen3:8b", "qwen3:4b", "qwen3:1.7b", "llama3.1:8b", "llama3.2:3b"],
             [("A", [59.0, 51.4, 34.8, 39.0, 35.2]), ("S", [59.0, 62.4, 36.2, 23.3, 15.2]), ("C", [74.3, 67.6, 55.7, 53.3, 44.3])],
             ["#94a3b8", "#b45309", "#0f766e"], width=520, height=270, vmax=100, fmt="{:.0f}", ylabel="accuracy %")
P.append(page(2, T, "All five judges on the 210 claims", "A vs S vs C", f"""
<div class="cols"><div class="col" style="flex:1.2">
<table><tr><th>Judge</th><th class="n">A</th><th class="n">S</th><th class="n">C</th><th class="n">S failed</th><th class="n">Seconds A / S / C</th><th class="n">Tool calls A / S / C</th></tr>
<tr><td><b>qwen3:8b</b></td><td class="n">59.0</td><td class="n">59.0</td><td class="n"><b>74.3</b></td><td class="n">2</td><td class="n">25.5 / 26.0 / 29.5</td><td class="n">2.95 / 2.05 / 1.00</td></tr>
<tr><td><b>qwen3:4b</b></td><td class="n">51.4</td><td class="n">62.4</td><td class="n"><b>67.6</b></td><td class="n">0</td><td class="n">36.5 / 47.9 / 42.5</td><td class="n">1.28 / 1.53 / 0.77</td></tr>
<tr><td><b>qwen3:1.7b</b></td><td class="n">34.8</td><td class="n">36.2</td><td class="n"><b>55.7</b></td><td class="n">1</td><td class="n">2.7 / 4.2 / 8.2</td><td class="n">0.47 / 0.34 / 0.40</td></tr>
<tr><td><b>llama3.1:8b</b></td><td class="n">39.0</td><td class="n r">23.3</td><td class="n"><b>53.3</b></td><td class="n r">81</td><td class="n">4.4 / 10.6 / 19.5</td><td class="n">1.71 / 1.27 / 1.04</td></tr>
<tr><td><b>llama3.2:3b</b></td><td class="n">35.2</td><td class="n r">15.2</td><td class="n"><b>44.3</b></td><td class="n r">104</td><td class="n">3.3 / 5.3 / 11.7</td><td class="n">3.49 / 2.10 / 0.68</td></tr></table>
<p class="small" style="margin-top:6px">Accuracy in %, 210 claims each. "S failed" = claims with no verdict. Tool calls per claim answers Sir's point 6 (NL2SQL vs SQL writing, × n calls).</p>
<ul style="margin-top:8px"><li>C is best for every judge; with C the judge needs about 1 call per claim</li>
<li>S beats A for the qwen judges (qwen3:4b 62.4 vs 51.4)</li>
<li><b>The llamas cannot fill the lookup form:</b> 81 and 104 of 210 claims failed on malformed lookup calls (one retry allowed, same rule as A)</li></ul>
</div><div class="col">{chart}</div></div>""", zoom=1.15))

# 3 three routers end to end
P.append(page(3, T, "Three routers, scored from the same runs", "Routing on the 210: router says yes → S, otherwise → C", """
<table><tr><th>Judge</th><th class="n">Always C</th><th class="n">Strict router<br>(1 table) → S</th><th class="n">Loose router<br>(≤2 tables) → S</th><th class="n">Non-answerable<br>router → S</th><th class="n">Non-answerable router →<br>answer NEI, no judge</th></tr>
<tr><td><b>qwen3:8b</b></td><td class="n"><b>74.3</b></td><td class="n">70.5</td><td class="n r">61.9</td><td class="n">73.3</td><td class="n">73.3</td></tr>
<tr><td><b>qwen3:4b</b></td><td class="n"><b>67.6</b></td><td class="n">65.2</td><td class="n">60.0</td><td class="n">71.9</td><td class="n">71.9</td></tr>
<tr><td><b>qwen3:1.7b</b></td><td class="n"><b>55.7</b></td><td class="n r">50.0</td><td class="n r">44.3</td><td class="n">53.3</td><td class="n">53.3</td></tr>
<tr><td><b>llama3.1:8b</b></td><td class="n"><b>53.3</b></td><td class="n r">40.5</td><td class="n r">34.8</td><td class="n">47.6</td><td class="n">59.0</td></tr>
<tr><td><b>llama3.2:3b</b></td><td class="n"><b>44.3</b></td><td class="n r">33.8</td><td class="n r">22.9</td><td class="n r">34.8</td><td class="n g">53.8</td></tr>
<tr><td class="mute">Claims sent to S</td><td></td><td class="n mute">75</td><td class="n mute">145</td><td class="n mute">71</td><td class="n mute">71 (answered NEI)</td></tr></table>
<p class="small" style="margin-top:6px">Red = significantly worse than always C, green = significantly better (McNemar p &lt; 0.05). Everything else: no significant difference.</p>
<div class="cols" style="margin-top:8px">
<div class="col take" style="border-color:var(--red);background:#fef2f2"><b>Loose</b> is the worst: it sends about 70% of claims to S, including two table claims that need a join.</div>
<div class="col take" style="border-color:var(--amber);background:#fff7ed"><b>Strict</b> never helps: the router sends 75 claims, but only 41 truly need one table.</div>
<div class="col take"><b>Non-answerable</b> is the only router that keeps the qwen judges at C's level, and qwen3:4b goes up (71.9 vs 67.6, not significant on 210 claims).</div></div>""", zoom=1.25))

# 4 Sir's check
P.append(page(4, T, "Sir's check (15 Nov, point 4)", "On the claims sent to S: is S as good as C?", """
<div class="cols"><div class="col" style="flex:1.25">
<table><tr><th>Judge</th><th class="n">Non-answerable router<br>71 claims: S / C</th><th class="n">p</th><th class="n">Strict router<br>75 claims: S / C</th><th class="n">Loose router<br>145 claims: S / C</th></tr>
<tr><td><b>qwen3:8b</b></td><td class="n"><b>78.9 / 81.7</b></td><td class="n">0.83</td><td class="n">59 / 69</td><td class="n">58 / 76</td></tr>
<tr><td><b>qwen3:4b</b></td><td class="n"><b>78.9 / 66.2</b></td><td class="n">0.11</td><td class="n">60 / 67</td><td class="n">59 / 70</td></tr>
<tr><td><b>qwen3:1.7b</b></td><td class="n"><b>78.9 / 85.9</b></td><td class="n">0.23</td><td class="n">31 / 47</td><td class="n">35 / 52</td></tr>
<tr><td><b>llama3.1:8b</b></td><td class="n">45.1 / 62.0</td><td class="n">0.07</td><td class="n">17 / 53</td><td class="n">23 / 50</td></tr>
<tr><td><b>llama3.2:3b</b></td><td class="n r">22.5 / 50.7</td><td class="n">0.001</td><td class="n">19 / 48</td><td class="n">15 / 46</td></tr></table>
<p class="small" style="margin-top:6px">Accuracy (%) of S and of C on exactly the claims that router sends to S.</p>
<h2 style="margin-top:12px">Inside the 71 non-answerable routed claims</h2>
<table style="font-size:13px"><tr><th>Judge</th><th class="n">56 truly NEI: S / C</th><th class="n">15 answerable, sent by mistake: S / C</th></tr>
<tr><td>qwen3:8b</td><td class="n">92.9 / 80.4</td><td class="n">26.7 / 86.7</td></tr>
<tr><td>qwen3:4b</td><td class="n g">92.9 / 71.4</td><td class="n">26.7 / 46.7</td></tr>
<tr><td>qwen3:1.7b</td><td class="n">98.2 / 96.4</td><td class="n">6.7 / 46.7</td></tr></table>
</div><div class="col">
<div class="take"><b>Answer to Sir:</b> for the three qwen judges, the claims the non-answerable router sends to S get the same accuracy as with C (no significant difference), with no 7B builder involved.</div>
<div class="card" style="margin-top:8px"><ul>
<li>On truly unanswerable claims S is often better (qwen3:4b 92.9 vs 71.4, p = 0.008): C's rows push the judge into a wrong yes or no</li>
<li>S is much worse on the answerable claims the router sends there by mistake</li>
<li>With perfect NEI labels, routing would beat always C: qwen3:8b 79.0 vs 74.3 (p = 0.03), qwen3:4b 76.2 vs 67.6 (p = 0.0003)</li>
<li>Strict and loose: S loses on the claims they send</li>
<li>Llamas: S fails because of the form errors (page 2)</li></ul></div>
</div></div>""", zoom=1.08))

# 5 answerability
P.append(page(5, T, "Terms", "Answerable, non-answerable, and the three routers", """
<div class="cols"><div class="col card">
<h2>Non-answerable (NEI)</h2>
<p>The database cannot settle the claim, so the correct verdict is NOT ENOUGH INFO. ClaimDB has three kinds:</p>
<ul><li><b>Out of schema:</b> "The junior card of client 13539 is on the Mastercard network" (no network column)</li>
<li><b>Counterfactual:</b> "If popularity polls were considered, blond heroes would rank top three"</li>
<li><b>Subjective:</b> "Borysiuk has the most aesthetically pleasing crossing technique"</li></ul>
<p style="margin-top:6px"><b>Answerable</b> = the data can show the claim true (ENTAILED) or false (CONTRADICTED).</p>
</div><div class="col card t">
<h2>Three separate routers</h2>
<table style="font-size:13px"><tr><th>Router</th><th>Says "yes" (send to S) when it predicts</th></tr>
<tr><td>Strict</td><td>the claim's gold SQL uses 1 table, no nesting</td></tr>
<tr><td>Loose</td><td>the gold SQL uses at most 2 tables, no nesting</td></tr>
<tr><td>Non-answerable</td><td>the claim's gold label is NEI</td></tr></table>
<ul style="margin-top:8px"><li>Each router alone splits all claims into S or C; they are three separate experiments, never combined</li>
<li>Strict and loose are two definitions of "simple", not simple vs complex. Loose includes all strict simple claims</li>
<li>Gold SQL and gold labels make the <b>training labels</b> only. At test time the router sees only the claim text</li></ul>
</div><div class="col card">
<h2>Classifier quality (1,000 test claims, AUC)</h2>
<table style="font-size:13px"><tr><th>Router</th><th class="n">LR</th><th class="n">MLP 2</th><th class="n">MLP 3</th></tr>
<tr><td>Strict</td><td class="n">0.72</td><td class="n">0.68</td><td class="n">0.67</td></tr>
<tr><td>Loose</td><td class="n">0.64</td><td class="n">0.61</td><td class="n">0.61</td></tr>
<tr><td>Non-answerable</td><td class="n">0.95</td><td class="n">0.95</td><td class="n">0.94</td></tr></table>
<p class="small" style="margin-top:6px">AUC: 0.5 = chance, 1.0 = perfect. NEI claims are easy to spot from their wording; table counts depend on the database layout, which the router never sees.</p>
</div></div>""", zoom=1.15))

# 6 how S works
P.append(page(6, T, "How the simple path S works", "Tool calling, the lookup form, and what Python does", """
<div class="cols"><div class="col">
<div class="card"><h2>1. Tool calling (same mechanism in A, C and S)</h2>
<p>The judge can only write text. pydantic-ai gives it a list of tools, each with a <b>JSON schema</b> of allowed arguments. The judge replies with a JSON "call tool X with these arguments"; pydantic-ai checks it against the schema, runs the Python function, and sends the result back as the next message.</p>
<table style="font-size:12.5px;margin-top:6px"><tr><th>Setup</th><th>Argument the judge fills</th></tr>
<tr><td>A</td><td><span class="code">sql_query</span>: free text SQL</td></tr>
<tr><td>C</td><td><span class="code">question</span>: free text English</td></tr>
<tr><td>S</td><td>the <b>lookup form</b>: fixed fields with fixed choices</td></tr></table></div>
<div class="card" style="margin-top:8px"><h2>2. The lookup form = the function's arguments</h2>
<div class="ex">lookup(table, filters=[{column, op, value}],
       aggregate = none | count | count_distinct | sum | avg | min | max,
       column, columns, group_by, order_by, descending, limit)
op = "=" "!=" "&gt;" "&gt;=" "&lt;" "&lt;=" contains starts_with is_null not_null</div>
<p class="small">Plus <span class="code">describe_tables(table)</span> to list tables and columns. A wrongly filled form is rejected; one retry, then the claim fails.</p></div>
</div><div class="col">
<div class="card t"><h2>3. What Python does with a filled form</h2>
<ol style="padding-left:20px">
<li><b>Check names</b> against the real database: exact, then ignoring capitals, then ignoring spaces and underscores. Unknown name → reply with the closest real names ("superheroes" → superhero, superpower)</li>
<li><b>Write the SQL itself</b>: each filter becomes one condition joined with AND; values passed as parameters; text "=" ignores capitals and spaces; numbers compared as numbers</li>
<li><b>Run read only</b>, 30 s limit, at most 100 rows</li>
<li><b>Reply</b> with the rows and how many rows matched. No match: say whether the value exists at all and show similar stored values ("Marvel" → "Marvel Comics")</li></ol>
</div>
<div class="warn"><b>Limits:</b> one table per call, so a join needs several lookups chained by the judge; no maths across columns, no date functions, no nested queries.</div>
</div></div>""", zoom=1.15))

# 7 examples
P.append(page(7, T, "Two real traces (qwen3:8b, exact messages from the result file)", "S in action", """
<div class="cols"><div class="col card">
<h2>Claim 5584 (answerable, gold ENTAILED)</h2>
<p style="font-size:13.5px">"The Scotland Premier League featured 228 matches in the 2015/2016 season."</p>
<div class="ex">1 describe_tables("")  →  League(id, country_id, name) · Match(id, ..., league_id, season, ...)
2 lookup {"table":"League","filters":[{"column":"name","op":"=","value":"Scotland Premier League"}],"columns":["id"]}
  Python: SELECT "id" FROM "League" WHERE TRIM("name") = ? COLLATE NOCASE   ['Scotland Premier League']
  → {"rows_matching_filters":1,"result":[{"id":19694}]}
3 lookup {"table":"Match","filters":[{"column":"league_id","op":"=","value":19694},
                                   {"column":"season","op":"=","value":"2015/2016"}],"aggregate":"count"}
  Python: SELECT COUNT(*) FROM "Match" WHERE "league_id" = ? AND TRIM("season") = ? COLLATE NOCASE
  → {"rows_matching_filters":228,"result":[{"value":228}]}</div>
<p style="margin-top:4px"><b>ENTAILED ✓</b> in 29.0 s. The judge did the join itself in two lookups. A failed this claim (guessed a table that does not exist); C got it in one Arctic call.</p>
</div><div class="col card t">
<h2>Claim 1005 (non-answerable, out of schema)</h2>
<p style="font-size:13.5px">"The junior credit card held by client ID 13539 is issued on the Mastercard network."</p>
<div class="ex">1 describe_tables("")  →  card(card_id, disp_id, type, issued) · disp(disp_id, client_id, ...) · no network column
2 lookup {"table":"disp","filters":[{"column":"client_id","op":"=","value":13539}],"columns":["disp_id"]}
  Python: SELECT "disp_id" FROM "disp" WHERE "client_id" = ?   [13539]   →  disp_id 13231
3 lookup {"table":"card","filters":[{"column":"disp_id","op":"=","value":13231}],"columns":["type"]}
  Python: SELECT "type" FROM "card" WHERE "disp_id" = ?   [13231]   →  type 'junior'</div>
<p style="margin-top:4px"><b>NOT ENOUGH INFO ✓</b> in 23.5 s: card exists, network not stored. C got it wrong: Arctic filtered type = 'credit', got an empty result, and the judge said CONTRADICTED.</p>
</div></div>
<div class="take" style="margin-top:8px"><b>Next decision:</b> report the llama form failures as a finding (setups stay identical), or rerun llama S with more retries. Also open: #4 (a router that also sees the schema), to make strict routing work.</div>""", zoom=1.1))

html = f"<!doctype html><html><head><meta charset='utf-8'><title>Subset 210 Results</title><style>{PAGE_CSS}</style></head><body>{''.join(P)}</body></html>"
open("recent.html", "w").write(html)
print("ok")
