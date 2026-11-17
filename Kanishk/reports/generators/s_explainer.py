import brief as _b
PAGE_CSS = _b.PAGE_CSS + """
.step{display:flex;gap:12px;align-items:flex-start;margin:7px 0}
.num{flex:none;width:30px;height:30px;border-radius:50%;background:var(--teal);color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:15px}
.ex{font-family:'DejaVu Sans Mono',monospace;font-size:11.5px;background:#fff;border:1px solid var(--line);border-left:3px solid var(--teal);border-radius:4px;padding:4px 8px;margin:3px 0;white-space:pre-wrap}
.ex.bad{border-left-color:#b91c1c}
td.code2{font-family:'DejaVu Sans Mono',monospace;font-size:12px}
"""

def page(n, total, kicker, title, body, zoom=1.0):
    return (f'<section class="page"><div class="inner" style="zoom:{zoom}"><div class="kicker">{kicker}</div><h1>{title}</h1>{body}</div>'
            f'<div class="foot"><span>SQL Judge project · the simple path S (Python lookup tool) · code/simple_tools.py · 17 Nov 2026</span><span>{n} / {total}</span></div></section>')

T = 4
P = []

P.append(page(1, T, "The simple path S", "The judge asks for data by filling a form; Python writes the SQL", """
<div class="flow" style="margin:6px 0 16px">
 <div class="box">Claim the router sent to S</div><span class="arrow">→</span>
 <div class="box">Judge (small LLM)</div><span class="arrow">→</span>
 <div class="box">fills a lookup form<br><span style="font-weight:400;font-size:12px">table, filters, count / sum / avg / min / max</span></div><span class="arrow">→</span>
 <div class="box o">Python checks the form,<br>writes the SQL, runs it</div><span class="arrow">→</span>
 <div class="box">rows + number of matching rows</div><span class="arrow">→</span>
 <div class="box">verdict</div>
</div>
<div class="cols">
 <div class="col card"><h2>Why we built it</h2><ul>
 <li>In A the judge writes SQL itself. 34% of qwen3:8b's queries failed, mostly wrong table or column names.</li>
 <li>In C a second 7B model (Arctic) writes the SQL. Accurate, but it is a second model on every claim.</li>
 <li>S removes SQL writing from the judge <b>without</b> a second model: plain Python code does it.</li></ul></div>
 <div class="col card t"><h2>What is the same as A and C</h2><ul>
 <li>Same judge models, same ClaimDB prompt, same answer format</li>
 <li>Same limit: at most 20 tool calls per claim</li>
 <li>Only change in the prompt: the sentence describing the tools ("You do not need to write SQL")</li></ul></div>
 <div class="col card"><h2>Which claims use S</h2><ul>
 <li>The claims the router says "yes" to (cheap path)</li>
 <li>Strict router: claims it thinks need 1 table</li>
 <li>Non-answerable router: claims it thinks the database cannot settle</li>
 <li>All other claims go to C</li></ul></div>
</div>""", zoom=1.12))

P.append(page(2, T, "What the judge can do", "Two tools, nothing else", """
<div class="cols"><div class="col" style="flex:.85">
<div class="card"><h2>Tool 1: describe_tables</h2>
<p>No table name: lists every table and its columns.</p>
<div class="ex">League(id, country_id, name)
Match(id, country_id, league_id, season, ...)</div>
<p style="margin-top:6px">With a table name: also 3 example values per column and which columns link to other tables.</p>
<div class="ex">Table hero_power:
  hero_id INTEGER  e.g. 1, 2, 3
  power_id INTEGER  e.g. 1, 18, 26
Links: power_id -> superpower.id; hero_id -> superhero.id</div></div>
</div><div class="col" style="flex:1.15">
<div class="card t"><h2>Tool 2: lookup (one table per call)</h2>
<table style="font-size:13px"><tr><th>Field</th><th>Meaning</th><th>Example</th></tr>
<tr><td class="code2">table</td><td>which table to search</td><td class="code2">Match</td></tr>
<tr><td class="code2">filters</td><td>conditions, all must hold. Allowed: = != &gt; &gt;= &lt; &lt;= contains starts_with is_null not_null</td><td class="code2">season = '2015/2016'</td></tr>
<tr><td class="code2">aggregate</td><td>none (return rows), count, count_distinct, sum, avg, min, max</td><td class="code2">count</td></tr>
<tr><td class="code2">column</td><td>the column to count / sum / average</td><td class="code2">height_cm</td></tr>
<tr><td class="code2">columns</td><td>which columns to show when returning rows</td><td class="code2">[id]</td></tr>
<tr><td class="code2">group_by</td><td>one result per value of this column</td><td class="code2">publisher_id</td></tr>
<tr><td class="code2">order_by, descending</td><td>sort by a column, or by the result ("value")</td><td class="code2">value, true</td></tr>
<tr><td class="code2">limit</td><td>how many rows to return (max 100)</td><td class="code2">20</td></tr></table>
</div></div></div>
<div class="take">The judge never types SQL. It only fills these fields. Anything the form cannot express (joins in one call, maths across columns, date functions) the judge has to do in several lookups or cannot do.</div>""", zoom=1.2))

P.append(page(3, T, "What Python does with every lookup", "The rules (criteria) inside the tool", """
<div class="cols"><div class="col">
<div class="step"><div class="num">1</div><div><b>Check every table and column name against the real database.</b> Try in order: exact name, then ignoring capital letters, then ignoring spaces and underscores. If nothing matches, refuse and reply with the closest real names.
<div class="ex bad">table "superheroes" → error: no table called 'superheroes'. Closest names: superhero, superpower</div>
<div class="ex">column "Height CM" → accepted as height_cm</div></div></div>
<div class="step"><div class="num">2</div><div><b>Write the SQL itself.</b> Each filter becomes one condition, joined with AND. Values are passed separately (never pasted into the SQL text). Text "=" ignores capital letters and extra spaces; number columns compare as numbers; "contains" becomes LIKE '%value%'.
<div class="ex">lookup(Match, league_id = 19694, season = '2015/2016', count)
→ SELECT COUNT(*) AS value FROM "Match"
  WHERE "league_id" = ? AND TRIM("season") = ? COLLATE NOCASE   [19694, '2015/2016']</div></div></div>
</div><div class="col">
<div class="step"><div class="num">3</div><div><b>Run it safely.</b> Database opened read only (nothing can be changed), stopped after 30 seconds, at most 100 rows returned.</div></div>
<div class="step"><div class="num">4</div><div><b>Reply with the rows and how many rows matched.</b>
<div class="ex">{"rows_matching_filters": 228, "result": [{"value": 228}]}</div>
If more rows matched than were shown, it says so ("Showing 20 of 2,218 matching rows. Use an aggregate or more filters").</div></div>
<div class="step"><div class="num">5</div><div><b>If nothing matched, say why.</b> For each text filter, check whether the searched value exists in that column at all.
<div class="ex">publisher_name = 'Marvel' → value not found; similar stored values: ["Marvel Comics"]</div>
<div class="ex">both values exist but no row has both → "Each searched value exists, but no row matches all filters together"</div></div></div>
</div></div>""", zoom=1.18))

P.append(page(4, T, "How well it works (qwen3:8b, all 1,000 claims)", "Good on one table claims and on unanswerable claims, weak on joins", """
<div class="cols"><div class="col">
<table><tr><th>Claims</th><th class="n">Count</th><th class="n">S</th><th class="n">C</th><th class="n">p</th><th class="n">Seconds S / C</th></tr>
<tr><td>All claims</td><td class="n">1000</td><td class="n">61.8</td><td class="n">76.0</td><td class="n">3e-15</td><td class="n">27.2 / 29.0</td></tr>
<tr class="hl"><td>Truly 1 table (strict simple)</td><td class="n">215</td><td class="n"><b>74.9</b></td><td class="n"><b>76.7</b></td><td class="n">0.64</td><td class="n">19.8 / 29.9</td></tr>
<tr class="hl"><td>Router says non-answerable</td><td class="n">340</td><td class="n"><b>84.4</b></td><td class="n"><b>82.9</b></td><td class="n">0.64</td><td class="n">19.1 / 27.8</td></tr>
<tr><td>Truly 1 or 2 tables (loose simple)</td><td class="n">692</td><td class="n">61.6</td><td class="n">76.6</td><td class="n">4e-12</td><td class="n">25.9 / 29.0</td></tr>
<tr><td>Strict router says simple</td><td class="n">371</td><td class="n">59.0</td><td class="n">70.1</td><td class="n">0.0002</td><td class="n">26.5 / 29.4</td></tr></table>
<p class="small" style="margin-top:6px">p = McNemar test, S vs C on the same claims; p above 0.05 means no real difference. Also: S beats A overall (61.8 vs 56.0, p = 0.0003).</p>
</div><div class="col">
<div class="card"><h2>Where S is as good as C</h2><ul>
<li><b>1 table claims</b>: same accuracy, a third faster (no second model)</li>
<li><b>Unanswerable claims</b>: S finds nothing and says NOT ENOUGH INFO, which is correct; C's rows often push the judge into a wrong yes/no</li></ul></div>
<div class="card" style="margin-top:8px"><h2>Where S fails</h2><ul>
<li><b>Claims needing a join</b>: the judge must look up an id in one table, then use it in another. It often does not (claim 7019: gave up, said NEI)</li>
<li><b>Bad routing</b>: when the router sends join claims to S, accuracy drops (59.0 vs 70.1)</li></ul></div>
<div class="warn">Full S results exist only for qwen3:8b. 1,136 lookups: 98 got an error message back (wrong names, bad arguments); 8 claims failed.</div>
</div></div>""", zoom=1.18))

html = f"<!doctype html><html><head><meta charset='utf-8'><title>Simple Path S</title><style>{PAGE_CSS}</style></head><body>{''.join(P)}</body></html>"
open("s_explainer.html", "w").write(html)
print("ok")
