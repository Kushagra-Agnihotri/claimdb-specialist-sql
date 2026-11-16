from common import CSS
import brief as _b  # reuse page CSS
PAGE_CSS = _b.PAGE_CSS + """
.trace{font-size:12px;line-height:1.35}
.trace .code{font-size:11px;display:block;margin:3px 0}
.ret{font-family:'DejaVu Sans Mono',monospace;font-size:10.5px;color:#374151;background:#fff;border-left:3px solid #cbd5e1;padding:2px 7px;margin:2px 0 6px;white-space:pre-wrap}
.err{border-left-color:#b91c1c;color:#b91c1c}
.verdict{margin-top:6px;padding:6px 9px;border-radius:7px;font-weight:700;font-size:13px}
.v-ok{background:#dcfce7;color:#166534}.v-bad{background:#fee2e2;color:#991b1b}
.claimbar{background:var(--navy);color:#fff;border-radius:10px;padding:9px 14px;margin-bottom:10px;font-size:15px}
.claimbar .mute{color:#cbd5e1}
.colhead{font-weight:800;font-size:15px;margin-bottom:4px}
"""

def page(n, total, kicker, title, body, zoom=1.0):
    return (f'<section class="page"><div class="inner" style="zoom:{zoom}"><div class="kicker">{kicker}</div><h1>{title}</h1>{body}</div>'
            f'<div class="foot"><span>SQL Judge project · walkthrough of A, C and S on two real claims (qwen3:8b, test set) · 16 Nov 2026</span><span>{n} / {total}</span></div></section>')

T = 5
P = []

P.append(page(1, T, "Answerable vs non-answerable", "What is answerable, what is not", """
<div class="cols"><div class="col card">
<h2>Definition</h2>
<p>A claim is <b>answerable</b> if the database stores the facts needed to check it. Then the answer is ENTAILED (data agrees) or CONTRADICTED (data disagrees).</p>
<p style="margin-top:6px">A claim is <b>not answerable</b> if no query on this database can settle it. Its gold label is <b>NOT ENOUGH INFO (NEI)</b>. NEI is not "false": false needs evidence against the claim; NEI means the evidence cannot exist in this database.</p>
<p style="margin-top:6px"><b>Router label:</b> positive = <b>non-answerable</b> (gold label is NEI, 33.6% of the test set); negative = answerable (ENTAILED or CONTRADICTED). It is a property of the claim and the database, the same for every judge.</p>
</div><div class="col" style="flex:1.25">
<table><tr><th>ClaimDB test (1,000)</th><th class="n">Claims</th><th>Real example from the test set</th></tr>
<tr><td>ENTAILED</td><td class="n">333</td><td>"The Scotland Premier League featured 228 matches in the 2015/2016 season."</td></tr>
<tr><td>CONTRADICTED</td><td class="n">331</td><td>"The School of Applied Sciences ... offers exactly 28 majors."</td></tr>
<tr class="hl"><td>NEI: out of schema</td><td class="n">111</td><td>"The junior credit card held by client 13539 is issued on the Mastercard network." (no network column)</td></tr>
<tr class="hl"><td>NEI: counterfactual</td><td class="n">113</td><td>"If audience popularity polls were considered, blond haired superheroes would rank top three."</td></tr>
<tr class="hl"><td>NEI: subjective</td><td class="n">112</td><td>"Ariel Borysiuk has the most aesthetically pleasing crossing technique."</td></tr></table>
<div class="take">Why it matters for routing: the builder always returns some SQL and some rows, so on NEI claims the judge is tempted to decide. The next two pages show this on real traces.</div>
</div></div>""", zoom=1.12))

def col(name, color, calls, verdict, ok, note):
    body = "".join(calls)
    return (f'<div class="col card trace" style="border-top:5px solid {color}"><div class="colhead" style="color:{color}">{name}</div>{body}'
            f'<div class="verdict {"v-ok" if ok else "v-bad"}">{verdict}</div><div class="small" style="margin-top:4px">{note}</div></div>')

def call(label, text, ret, err=False):
    return f'<div><b>{label}</b><span class="code">{text}</span>' + (f'<div class="ret{" err" if err else ""}">{ret}</div>' if ret else "") + "</div>"

A1 = col("A · judge writes SQL", "#475569", [
    call("Call 1", "SELECT COUNT(*) AS match_count FROM matches WHERE league = 'Scotland Premier League' AND season = '2015/2016';", "no such table: matches", True),
    call("Call 2", "SELECT name FROM sqlite_master WHERE type='table';", "Player_Attributes, Player, League, Country, Team, Team_Attributes, Match"),
    call("Call 3", "PRAGMA table_info(Match);", "id, country_id, league_id, season, ... (no league name in Match)")],
    "NOT ENOUGH INFO ✗", False, "Guessed a table name, then never found that the league name sits in League, linked by league_id. Gave up. 29.9 s.")
C1 = col("C · judge asks Arctic", "#0f766e", [
    call("Judge asks", "How many matches were played in the Scotland Premier League during the 2015/2016 season?", ""),
    call("Arctic writes and runs", "SELECT COUNT(*) FROM Match INNER JOIN League ON Match.league_id = League.id WHERE League.name = 'Scotland Premier League' AND Match.season = '2015/2016'", "[{\"COUNT(*)\": 228}]")],
    "ENTAILED ✓", True, "One call. Arctic sees the schema, so it finds the join itself. 22.6 s.")
S1 = col("S · judge fills lookup forms", "#b45309", [
    call("Call 1", "describe_tables()", "... League(id, country_id, name) ... Match(id, country_id, league_id, season, ...)"),
    call("Call 2", "lookup(table=League, filters=[name = 'Scotland Premier League'], columns=[id])", "rows_matching_filters: 1 · result: id = 19694"),
    call("Call 3", "lookup(table=Match, filters=[league_id = 19694, season = '2015/2016'], aggregate=count)", "rows_matching_filters: 228 · value: 228")],
    "ENTAILED ✓", True, "No SQL written. The judge does the join itself in two one table lookups. 29.0 s.")
P.append(page(2, T, "Example 1 · answerable claim (gold: ENTAILED)", "Same claim through A, C and S", f"""
<div class="claimbar"><b>Claim 5584</b> (european_football_2): "The Scotland Premier League featured 228 matches in the 2015/2016 season." <span class="mute">Hint: Scotland Premier League refers to League.name = 'Scotland Premier League'</span></div>
<div class="cols" style="gap:14px">{A1}{C1}{S1}</div>""", zoom=1.0))

A2 = col("A · judge writes SQL", "#475569", [
    call("Call 1", "SELECT name FROM sqlite_master WHERE type='table';", "account, card, client, disp, district, loan, order, trans"),
    call("Call 2", "SELECT * FROM card WHERE client_id = 13539;", "no such column: client_id", True),
    call("Call 3", "SELECT * FROM card LIMIT 1;", "card_id 1, disp_id 9, type 'gold', issued 1998-10-16")],
    "NOT ENOUGH INFO ✓", True, "Right answer, partly by luck: it could not link client to card and gave up; there is also no network column. 26.0 s.")
C2 = col("C · judge asks Arctic", "#0f766e", [
    call("Judge asks", "What is the network of the junior credit card held by client ID 13539?", ""),
    call("Arctic writes and runs", "SELECT c.type FROM card c JOIN disp d ON c.disp_id = d.disp_id WHERE d.client_id = 13539 AND c.type = 'credit'", "[]  (empty)")],
    "CONTRADICTED ✗", False, "No network column exists, so Arctic answered a different question (filtered type = 'credit'). The empty result looked like evidence against the claim. 30.4 s.")
S2 = col("S · judge fills lookup forms", "#b45309", [
    call("Call 1", "describe_tables()", "card(card_id, disp_id, type, issued) ... no network column anywhere"),
    call("Call 2", "lookup(table=disp, filters=[client_id = 13539], columns=[disp_id])", "rows_matching_filters: 1 · disp_id = 13231"),
    call("Call 3", "lookup(table=card, filters=[disp_id = 13231], columns=[type])", "rows_matching_filters: 1 · type = 'junior'")],
    "NOT ENOUGH INFO ✓", True, "Confirmed the junior card exists, saw that no column holds the network, so NEI for the right reason. 23.5 s.")
P.append(page(3, T, "Example 2 · not answerable claim (gold: NEI, out of schema)", "Where the builder misleads the judge", f"""
<div class="claimbar"><b>Claim 1005</b> (financial): "The junior credit card held by client ID 13539 is issued on the Mastercard network." <span class="mute">The database stores card type and issue date, not the card network.</span></div>
<div class="cols" style="gap:14px">{A2}{C2}{S2}</div>
<div class="take" style="margin-top:8px">This is the pattern behind non-answerable routing: for qwen3:8b, 83 claims are right only with A, and 51 of them are NEI like this one. Send predicted NEI claims to the cheap path, the rest to C.</div>""", zoom=0.97))

P.append(page(4, T, "How we built S", "The Python lookup tool", """
<div class="cols"><div class="col card">
<h2>Design goal</h2>
<p>A's failures were mostly <b>grounding errors</b> (wrong table or column names, 34% of qwen3:8b's A queries failed) and values written differently. S removes SQL writing and repairs names, without a second model.</p>
<h2 style="margin-top:10px">Two tools given to the judge</h2>
<ul><li><span class="code">describe_tables(table)</span>: all tables and columns; for one table, 3 example values per column and links to other tables (foreign keys)</li>
<li><span class="code">lookup(table, filters, aggregate, column, columns, group_by, order_by, descending, limit)</span>: one table per call. Filters: = != &gt; &gt;= &lt; &lt;= contains starts_with is_null not_null. Aggregates: count, count_distinct, sum, avg, min, max</li></ul>
<p class="small">Same ClaimDB prompt, output format and 20 call limit as A and C; only the tool description sentence changes.</p>
</div><div class="col card t">
<h2>What Python does on each lookup</h2>
<ol style="padding-left:20px">
<li><b>Resolve names</b> against the real schema: exact, then ignoring case, then ignoring spaces and underscores. Unknown name → reply with closest real names (e.g. "no table 'superheroes'; closest: superhero, superpower")</li>
<li><b>Build the SQL itself</b>, parameterised (values never pasted into the query); text "=" ignores case and spaces; numbers compared as numbers</li>
<li><b>Run read only</b> with a 30 s timeout and a 100 row cap</li>
<li><b>Return</b> rows + how many rows matched. If nothing matched: say which searched value does not exist and show similar stored values ("Marvel" → "Marvel Comics")</li></ol>
<p class="small" style="margin-top:6px">About 250 lines of Python (code/simple_tools.py) plus condition S in run_judge.py. Tested on real databases and a 30 claim pilot before the full run.</p>
<div class="take"><b>qwen3:8b, 1,000 claims:</b> S 61.8 vs A 56.0 (p = 0.0003) vs C 76.0. 1,136 lookups, 98 returned an error message instead of crashing (wrong names get the closest real names). Time 27.2 s vs C 29.0 s.</div>
</div></div>""", zoom=1.08))

P.append(page(5, T, "Sir's check (Nov 15, point 4)", "Python tool vs C on the claims the router marks non-answerable", """
<div class="cols"><div class="col" style="flex:1.3">
<table><tr><th>qwen3:8b · 340 claims the router marks non-answerable</th><th class="n">Claims</th><th class="n">S (Python tool)</th><th class="n">C (Arctic)</th><th class="n">A</th></tr>
<tr class="hl"><td><b>All 340 routed claims</b></td><td class="n">340</td><td class="n"><b>84.4</b></td><td class="n"><b>82.9</b></td><td class="n">82.9</td></tr>
<tr><td>of which gold NEI (router right)</td><td class="n">282</td><td class="n">94.0</td><td class="n">85.1</td><td class="n">96.8</td></tr>
<tr><td>of which gold ENTAILED (router wrong)</td><td class="n">30</td><td class="n">33.3</td><td class="n">70.0</td><td class="n">13.3</td></tr>
<tr><td>of which gold CONTRADICTED (router wrong)</td><td class="n">28</td><td class="n">42.9</td><td class="n">75.0</td><td class="n">17.9</td></tr>
<tr><td>Seconds per claim (all 340)</td><td></td><td class="n">19.1</td><td class="n">27.8</td><td></td></tr></table>
<p class="small" style="margin-top:6px">Router = logistic regression on frozen embeddings, threshold tuned on held out databases (not on test). McNemar S vs C on the 340: only S right 39, only C right 34, p = 0.64. Both runs already existed; no new run was needed.</p>
</div><div class="col">
<div class="take"><b>On the routed 33%, the Python tool is as good as C</b> (84.4 vs 82.9, no significant difference) and <b>31% faster</b> (19.1 vs 27.8 s).</div>
<div class="card" style="margin-top:8px"><ul>
<li>S is much better on the truly non-answerable claims (94.0 vs 85.1): C's builder returns rows and the judge over commits</li>
<li>S is much worse on the 58 answerable claims the router sent by mistake (they need the builder)</li>
<li>Answering NEI directly on these 340 would also score 282/340 = 82.9</li></ul></div>
<div class="warn"><b>Coverage:</b> full S exists for qwen3:8b only. qwen3:4b: 70 routed claims so far, S 78.6 vs C 72.9 (p = 0.48).</div>
</div></div>""", zoom=1.1))

html = f"<!doctype html><html><head><meta charset='utf-8'><title>A, C and S walkthrough</title><style>{PAGE_CSS}</style></head><body>{''.join(P)}</body></html>"
open("walk.html", "w").write(html)
print("ok")
