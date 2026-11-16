from common import CSS, SEC1, AUC, ROUTE_A, bars

PAGE_CSS = CSS + """
@page{size:13.333in 7.5in;margin:0}
.page{width:13.333in;height:7.5in;padding:.42in .6in .5in;page-break-after:always;position:relative;overflow:hidden}
.page:last-child{page-break-after:auto}

.kicker{font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--teal)}
h1{font-size:31px;font-weight:800;color:var(--navy);margin:2px 0 14px;letter-spacing:-.01em}
h2{font-size:17px;font-weight:700;color:var(--navy);margin:0 0 8px}
p,li{font-size:15px;line-height:1.42}
ul{padding-left:20px}li{margin:3px 0}
.foot{position:absolute;bottom:.2in;left:.6in;right:.6in;display:flex;justify-content:space-between;font-size:11px;color:var(--mute);border-top:1px solid var(--line);padding-top:5px}
.cols{display:flex;gap:26px}.col{flex:1;min-width:0}
.card{background:var(--soft);border-radius:12px;padding:14px 16px}
.card.t{background:var(--soft2)}
.big{font-size:30px;font-weight:800;color:var(--teal);line-height:1}
.bigs{font-size:13px;color:var(--mute);margin-top:3px}
table{font-size:14px}td,th{padding:6px 9px}
.small{font-size:12.5px;color:var(--mute)}
.take{border-left:4px solid var(--teal);background:var(--soft2);padding:9px 14px;border-radius:0 8px 8px 0;font-size:15px;margin-top:10px}
.warn{border-left:4px solid var(--amber);background:#fff7ed;padding:9px 14px;border-radius:0 8px 8px 0;font-size:14px;margin-top:10px}
.lane{display:flex;align-items:center;gap:6px;margin:8px 0}
.lane .lbl{width:42px;height:42px;border-radius:10px;background:var(--navy);color:#fff;font-weight:800;font-size:20px;display:flex;align-items:center;justify-content:center;flex:none}
.box.c{border-color:var(--teal);background:var(--soft2)}.box.o{border-color:var(--amber);background:#fff7ed}
.box{font-size:13.5px}
"""

def page(n, total, kicker, title, body, zoom=1.3):
    return (f'<section class="page"><div class="inner" style="zoom:{zoom}"><div class="kicker">{kicker}</div><h1>{title}</h1>{body}</div>'
            f'<div class="foot"><span>SQL Judge project · Kanishk, Kushagra, Navtej · Intro to LLMs · 16 Nov 2026</span><span>{n} / {total}</span></div></section>')

T = 9
pages = []

# 1 overview
pages.append(page(1, T, "Where we are", "Small LLM judges checking claims against a database", f"""
<div class="flow" style="margin:6px 0 22px">
 <div class="box">Claim<br><span class="mute" style="font-weight:400;font-size:12px">"69 superheroes are taller than 200 cm"</span></div><span class="arrow">→</span>
 <div class="box">Judge (small LLM)</div><span class="arrow">⇄</span>
 <div class="box c">Database tool<br><span class="mute" style="font-weight:400;font-size:12px">A, C or S (next page)</span></div><span class="arrow">→</span>
 <div class="box">Verdict<br><span style="font-weight:400;font-size:12px">ENTAILED · CONTRADICTED · NOT ENOUGH INFO</span></div>
</div>
<div class="cols">
 <div class="col card"><h2>Benchmark</h2><ul>
  <li>ClaimDB public test: <b>1,000 claims</b> over 11 BIRD databases</li>
  <li>Same harness as ClaimDB: Ollama, 16k context, 20 tool calls</li>
  <li>Three labels; NEI = the database cannot decide the claim</li></ul></div>
 <div class="col card t"><h2>Done since the last meet</h2><ul>
  <li>Section 1: C with Arctic for 6 judges (14B on Colab)</li>
  <li>Section 3: OmniSQL builder cells on Colab</li>
  <li>Our own A baseline for all 5 PC judges</li>
  <li>Pathway #3 router: complexity and non-answerable (NEI)</li>
  <li>New cheap path S (Python lookup tool)</li></ul></div>
 <div class="col card"><h2>Question for #3</h2>
  <p style="font-size:16px">Can we choose, claim by claim, between a <b>cheap path</b> and the <b>expert builder path C</b> without losing accuracy?</p></div>
</div>
<div class="cols" style="margin-top:16px">
 <div class="col card"><div class="big">+13 to 20</div><div class="bigs">points: C (Arctic builder) over A, every judge</div></div>
 <div class="col card"><div class="big">76.5 / 76.0</div><div class="bigs">best C: qwen3:14b / qwen3:8b (ClaimDB release 53.1 / 52.1)</div></div>
 <div class="col card"><div class="big">0.95</div><div class="bigs">AUC of the non-answerable (NEI) router (complexity: 0.72 at best)</div></div>
 <div class="col card"><div class="big" style="color:var(--amber)">+0 to 2.6</div><div class="bigs">points from routing vs always C (only qwen3:4b significant)</div></div>
</div>""", zoom=1.14))

# 2 setups
pages.append(page(2, T, "Three ways the judge reaches the data", "A, C and S", """
<div class="lane"><div class="lbl">A</div><div class="box">Judge</div><span class="arrow">→</span><div class="box">writes SQL itself</div><span class="arrow">→</span><div class="box">SQLite</div><span class="arrow">→</span><div class="box">rows back to judge</div>
 <span style="margin-left:14px;font-size:14px">ClaimDB's original setup. Small judges make many naming and syntax errors.</span></div>
<div class="lane"><div class="lbl" style="background:var(--teal)">C</div><div class="box">Judge</div><span class="arrow">→</span><div class="box">asks in English</div><span class="arrow">→</span><div class="box c">Arctic 7B builder<br>writes SQL</div><span class="arrow">→</span><div class="box">SQL + rows back</div>
 <span style="margin-left:14px;font-size:14px">Arctic is an NL2SQL model, not a judge. Main result of the project.</span></div>
<div class="lane"><div class="lbl" style="background:var(--amber)">S</div><div class="box">Judge</div><span class="arrow">→</span><div class="box">fills a lookup form<br><span style="font-weight:400;font-size:11.5px">table, filters, count/sum/avg/min/max</span></div><span class="arrow">→</span><div class="box o">Python builds and<br>runs the query</div><span class="arrow">→</span><div class="box">rows back</div>
 <span style="margin-left:14px;font-size:14px">Built 15 Nov for #3. No SQL, no builder. Wrong names get closest real names back.</span></div>
<div class="card" style="margin-top:10px;padding:10px 14px"><h2 style="font-size:14px;margin-bottom:6px">Same claim, three ways <span class="mute" style="font-weight:400">(illustrative: "69 superheroes are taller than 200 cm")</span></h2>
<div class="cols" style="gap:14px">
<div class="col"><b>A</b> <span class="code">SELECT COUNT(*) FROM superhero WHERE height_cm &gt; 200</span></div>
<div class="col"><b>C</b> <span class="code">ask_database("How many superheroes are taller than 200 cm?")</span></div>
<div class="col"><b>S</b> <span class="code">lookup(table="superhero", filters=[height_cm &gt; 200], aggregate="count")</span></div>
</div></div>
<div class="cols" style="margin-top:12px">
 <div class="col take"><b>C beats A by 13 to 20 points for every judge</b> (all p &lt; 1e-10): qwen3:8b 76.0 vs 56.0, qwen3:4b 68.3 vs 54.3, qwen3:1.7b 54.7 vs 35.9, llama3.1:8b 54.7 vs 35.7, llama3.2:3b 45.2 vs 32.1.</div>
 <div class="col take" style="border-color:var(--amber);background:#fff7ed">So C is the strong default. #3 asks whether some claims can skip the builder: S (or A) as the cheap path.</div>
</div>""", zoom=1.15))

# 3 section 1 results
rows = ""
for j in ["qwen3:14b", "qwen3:8b", "qwen3:4b", "qwen3:1.7b", "llama3.1:8b", "llama3.2:3b"]:
    cdb, a, c, ci, where, sa, sc, oa, oc, p = SEC1[j]
    rows += (f"<tr><td><b>{j}</b></td><td class='n'>{cdb}</td><td class='n'>{a if a is not None else '<span class=mute>not run</span>'}</td>"
             f"<td class='n'><b>{c}</b></td><td class='n good'>+{c-cdb:.1f}</td><td class='n'>{'+%.1f' % (c-a) if a is not None else ''}</td><td>{where}</td></tr>")
chart = bars(["14B", "q8B", "q4B", "q1.7B", "L8B", "L3B"],
             [("ClaimDB release", [53.1, 52.1, 51.1, 36.6, 34.4, 38.7]), ("Our A", [None, 56.0, 54.3, 35.9, 35.7, 32.1]), ("Our C (Arctic)", [76.5, 76.0, 68.3, 54.7, 54.7, 45.2])],
             ["#cbd5e1", "#94a3b8", "#0f766e"], width=470, height=290, vmax=100, fmt="{:.0f}", ylabel="accuracy %")
pages.append(page(3, T, "Section 1 results · all 1,000 claims", "Arctic builder (C) vs judge alone (A)", f"""
<div class="cols"><div class="col" style="flex:1.35">
<table><tr><th>Judge</th><th class="n">ClaimDB</th><th class="n">Our A</th><th class="n">Our C</th><th class="n">C vs ClaimDB</th><th class="n">C vs our A</th><th>C run on</th></tr>{rows}</table>
<p class="small" style="margin-top:6px">ClaimDB column = ClaimDB's released per claim runs, re scored by us on the same claims. A runs: PC, 15 Nov. *qwen3:14b C: first 59 claims on PC, rest on Colab (L4, then A100); A not run.</p>
<div class="take">Our harness alone adds little (our A is within 4 points of ClaimDB for 4 of 5 judges; llama3.2:3b is 6.6 lower with 130 failed runs); <b>the builder adds 13 to 20 points.</b> 14B (76.5) ≈ 8B (76.0): with Arctic, scale stops helping after 8B.</div>
</div><div class="col">{chart}
<div class="warn"><b>Trade off:</b> A is better on NEI claims (qwen3:8b NEI accuracy A 96.7 vs C 83.0) but far worse on ENTAILED (31.5 vs 64.9) and CONTRADICTED (39.3 vs 80.1).</div></div></div>""", zoom=1.15))

# 4 section 3 / builders
pages.append(page(4, T, "Section 3 · other builders (Colab and PC)", "Builder grid so far", """
<div class="cols"><div class="col" style="flex:1.3">
<table><tr><th>Judge</th><th>Builder</th><th class="n">Claims</th><th class="n">Accuracy</th><th>Ran on</th></tr>
<tr><td>qwen3:4b</td><td>Arctic 7B (reference)</td><td class="n">1000</td><td class="n"><b>68.3</b></td><td>PC</td></tr>
<tr><td>qwen3:4b</td><td>OmniSQL 7B</td><td class="n">1000</td><td class="n"><b>65.5</b></td><td>Colab A100</td></tr>
<tr><td>qwen3:4b</td><td>SLM SQL 1.5B</td><td class="n">676</td><td class="n">54.1</td><td>PC (partial)</td></tr>
<tr><td>qwen3:4b</td><td>Qwen2.5 Coder 7B</td><td class="n">63</td><td class="n">42.9</td><td>Colab (partial)</td></tr>
<tr><td>llama3.1:8b</td><td>Arctic 7B (reference)</td><td class="n">1000</td><td class="n"><b>54.7</b></td><td>PC</td></tr>
<tr><td>llama3.1:8b</td><td>OmniSQL 7B</td><td class="n">1000</td><td class="n"><b>54.0</b></td><td>Colab A100</td></tr>
<tr><td>llama3.1:8b</td><td>SLM SQL 1.5B</td><td class="n">0</td><td class="n mute">pending</td><td></td></tr>
<tr><td>qwen3:14b</td><td>Arctic 7B</td><td class="n">1000</td><td class="n"><b>76.5</b></td><td>Colab (L4, A100)</td></tr>
</table>
<p class="small" style="margin-top:6px">Ministral judges (Navtej) and Section 2 builders for qwen3:8b (Kushagra) are not in this results folder yet.</p>
</div><div class="col">
<div class="card"><h2>Reading</h2><ul>
<li>SQL specialised 7B builders are close: OmniSQL is 0.7 to 2.8 below Arctic</li>
<li>Small or general builders do worse on the claims run so far (SLM SQL 54.1, Coder 42.9; partial)</li>
<li>The builder looks like the bottleneck: 14B judge gains nothing over 8B</li></ul></div>
<div class="warn"><b>Compute:</b> Colab Pro units used up; L4 was slower than the PC GPU. Remaining cells wait for RKIC access or PC time.</div>
</div></div>"""))

# 5 router build
pages.append(page(5, T, "Pathway #3 · how the router was built", "A router that picks the path per claim", """
<div class="flow" style="margin:2px 0 16px">
 <div class="box">Claim + hint text</div><span class="arrow">→</span>
 <div class="box">nomic embed text<br><span style="font-weight:400;font-size:12px">frozen, 768 numbers</span></div><span class="arrow">→</span>
 <div class="box c">Classifier<br><span style="font-weight:400;font-size:12px">logistic regression · MLP 2 · MLP 3</span></div><span class="arrow">→</span>
 <div class="box o">positive: cheap path (A or S)</div><span style="padding:0 8px;font-weight:700">or</span><div class="box c">negative: C</div>
</div>
<div class="cols">
 <div class="col card"><h2>Three label types (one router per type)</h2>
 <table style="font-size:13.5px"><tr><th>Label</th><th>Positive when</th><th class="n">Test share</th></tr>
 <tr><td>Strict complexity</td><td>gold SQL uses <b>1 table</b>, no nested SELECT, set operation or window</td><td class="n">21.5%</td></tr>
 <tr><td>Loose complexity</td><td><b>at most 2 tables</b>, same other conditions</td><td class="n">69.2%</td></tr>
 <tr><td>Non-answerable (NEI)</td><td>claim label is <b>NOT ENOUGH INFO</b></td><td class="n">33.6%</td></tr></table>
 <p class="small" style="margin-top:6px">Gold SQL = BIRD's reference query behind each claim. Used <b>only to make training labels</b>; the router at test time sees only the claim text.</p></div>
 <div class="col card t"><h2>Data split (by database)</h2>
 <table style="font-size:13.5px"><tr><th>Split</th><th class="n">Claims</th><th class="n">Databases</th></tr>
 <tr><td>Train (ClaimDB train split)</td><td class="n">40,652</td><td class="n">62</td></tr>
 <tr><td>Tune threshold (held out DBs)</td><td class="n">5,834</td><td class="n">7</td></tr>
 <tr><td>Test (public test)</td><td class="n">1,000</td><td class="n">11 unseen</td></tr></table>
 <p class="small" style="margin-top:6px">Threshold = best balanced accuracy on the 7 tuning DBs. MLPs: 256 and 256+128 hidden units, oversampling for balance. Evaluation is offline: we already have every claim's A, S and C verdicts.</p></div>
</div>"""))

# 6 AUC
groups = list(AUC)
chart = bars(["Strict complexity", "Loose complexity", "Non-answerable (NEI)"],
             [("Logistic regression", [v[0] for v in AUC.values()]), ("MLP 2 layer", [v[1] for v in AUC.values()]), ("MLP 3 layer", [v[2] for v in AUC.values()])],
             ["#1d3557", "#14b8a6", "#94a3b8"], width=560, height=300, vmax=1.0, baseline=0.5, ylabel="test AUC")
pages.append(page(6, T, "Classifier quality on the 1,000 test claims", "Non-answerable claims are easy to spot, complexity is not", f"""
<div class="cols"><div class="col">
<table><tr><th>Task</th><th class="n">Logistic regression</th><th class="n">MLP 2 layer</th><th class="n">MLP 3 layer</th></tr>
<tr><td>Strict complexity</td><td class="n"><b>0.72</b></td><td class="n">0.68</td><td class="n">0.67</td></tr>
<tr><td>Loose complexity</td><td class="n"><b>0.64</b></td><td class="n">0.61</td><td class="n">0.61</td></tr>
<tr><td>Non-answerable (NEI)</td><td class="n"><b>0.95</b></td><td class="n"><b>0.95</b></td><td class="n">0.94</td></tr></table>
<p class="small" style="margin-top:6px">Test AUC (0.5 = chance, 1.0 = perfect separation). Not accuracy. Non-answerable router balanced accuracy ≈ 0.88.</p>
<ul style="margin-top:12px">
<li>Deeper MLPs <b>never beat</b> logistic regression</li>
<li>Complexity from text alone is weak (0.61 to 0.72)</li>
<li>NEI claims have a recognisable style (counterfactual, subjective, out of schema), so text predicts them well</li></ul>
</div><div class="col">{chart}</div></div>"""))

# 7 routing
r = ROUTE_A
rows = ""
for j in ["qwen3:8b", "qwen3:4b", "qwen3:1.7b", "llama3.1:8b", "llama3.2:3b"]:
    aA, aC, orc, st, sl, lt, ll, at, al, ap = r[j]
    cls = lambda v: "good" if v > aC + 0.05 else ("bad" if v < aC - 0.05 else "")
    rows += (f"<tr><td><b>{j}</b></td><td class='n'>{aA}</td><td class='n'><b>{aC}</b></td>"
             f"<td class='n {cls(st)}'>{st}</td><td class='n {cls(sl)}'>{sl}</td><td class='n {cls(lt)}'>{lt}</td>"
             f"<td class='n {cls(at)}'>{at}</td><td class='n {cls(al)}'>{al}</td><td class='n'>{ap}</td><td class='n mute'>{orc}</td></tr>")
pages.append(page(7, T, "End to end accuracy · cheap path = A · all 5 judges", "Complexity routing hurts; non-answerable routing helps a little", f"""
<table><tr><th>Judge</th><th class="n">Always A</th><th class="n">Always C</th><th class="n">Strict, true labels</th><th class="n">Strict, router</th><th class="n">Loose, true labels</th><th class="n">Non-answerable, true labels</th><th class="n">Non-answerable, router</th><th class="n">p vs C</th><th class="n">Oracle</th></tr>{rows}</table>
<p class="small" style="margin-top:6px">Router = logistic regression (MLPs are similar or worse). "True labels" = perfect classifier for that label. Oracle = picks whichever of A or C is right per claim: an upper bound, not a model. p = McNemar vs always C.</p>
<div class="cols" style="margin-top:6px">
 <div class="col take" style="border-color:var(--red);background:#fef2f2"><b>Complexity:</b> even perfect labels lose to always C for every judge (qwen3:8b 74.1 vs 76.0). The cheap path is not better on one table claims, so "simple" is the wrong signal.</div>
 <div class="col take"><b>Non-answerable routing:</b> for qwen3:8b, 83 claims are right only with A, and 51 of them are NEI. Routing NEI to A gives <b>qwen3:4b 70.9 vs 68.3 (p = 0.007)</b>, the only significant gain. Others: ±1 point, not significant.</div>
</div>"""))

# 8 simple path S
chart = bars(["Accuracy %", "Seconds per claim"], [("A", [56.0, 23.4]), ("S", [61.8, 27.2]), ("C", [76.0, 29.0])],
             ["#94a3b8", "#b45309", "#0f766e"], width=420, height=250, vmax=80, fmt="{:.1f}")
pages.append(page(8, T, "Pathway #3 with the real cheap path", "Simple path S (judge + Python lookup tool)", f"""
<div class="cols"><div class="col" style="flex:1.25">
<table><tr><th>qwen3:8b, 1,000 claims</th><th class="n">Accuracy</th><th class="n">Seconds / claim</th></tr>
<tr><td>A (judge writes SQL)</td><td class="n">56.0</td><td class="n">23.4</td></tr>
<tr><td>S (Python lookup tool)</td><td class="n"><b>61.8</b></td><td class="n">27.2</td></tr>
<tr><td>C (Arctic builder)</td><td class="n"><b>76.0</b></td><td class="n">29.0</td></tr>
<tr class="hl"><td>Strict complexity, true labels → S</td><td class="n">75.6</td><td class="n">26.9</td></tr>
<tr><td>Strict complexity, router → S</td><td class="n bad">71.9</td><td class="n">28.0</td></tr>
<tr class="hl"><td>Non-answerable, true labels → S</td><td class="n">79.6</td><td class="n">25.2</td></tr>
<tr><td>Non-answerable, router → S</td><td class="n">76.5 <span class="mute">(p = 0.64)</span></td><td class="n">26.1</td></tr>
<tr><td>Oracle (S or C per claim)</td><td class="n mute">85.4</td><td class="n"></td></tr></table>
<p class="small" style="margin-top:6px">S beats A (p = 0.0003) but trails C (p = 3e-15). 8 S claims failed (bad tool arguments).</p>
</div><div class="col">{chart}
<div class="warn"><b>Cost:</b> S is only 1.8 s faster than C. Judge reasoning, not the builder, dominates time, so the "cheap" path is not much cheaper.</div>
<div class="warn"><b>In progress:</b> S for qwen3:4b is running (107/1,000 so far, 66.4%, 47.6 s per claim); llama3.1:8b, qwen3:1.7b, llama3.2:3b queued.</div>
</div></div>"""))

# 9 limitations + #4
pages.append(page(9, T, "Takeaways and next step", "What #3 shows, and pathway #4", """
<div class="cols"><div class="col card"><h2>What we can claim</h2><ul>
<li><span class="tag t-obs">observed</span> C beats A by 13 to 20 points for 5 judges</li>
<li><span class="tag t-obs">observed</span> Complexity routing loses to always C, even with true labels</li>
<li><span class="tag t-obs">observed</span> Non-answerable (NEI) router AUC 0.95; significant gain only for qwen3:4b with A</li>
<li><span class="tag t-obs">observed</span> Large untapped gap: oracle 84 to 85 vs always C 76 (qwen3:8b)</li>
<li><span class="tag t-int">interpretation</span> The builder hurts on NEI claims because it always returns some rows</li></ul>
<h2 style="margin-top:10px">Limits</h2><ul style="font-size:14px">
<li>Router sees claim text only; complexity depends on the schema</li>
<li>NEI prediction may lean on ClaimDB's wording of NEI claims</li>
<li>S results so far for qwen3:8b only</li></ul></div>
<div class="col card t"><h2>Proposed #4 <span class="tag t-hyp">not run yet</span></h2>
<div class="flow" style="justify-content:flex-start;margin:6px 0"><div class="box" style="font-size:12.5px">#3: claim</div><span class="arrow">→</span><div class="box" style="font-size:12.5px">frozen embedding</div><span class="arrow">→</span><div class="box" style="font-size:12.5px">classifier</div></div>
<div class="flow" style="justify-content:flex-start;margin:6px 0 10px"><div class="box c" style="font-size:12.5px">#4: claim + table names</div><span class="arrow">→</span><div class="box c" style="font-size:12.5px">Qwen3 0.6B fine tuned (LoRA)</div><span class="arrow">→</span><div class="box c" style="font-size:12.5px">route</div></div>
<ul><li>Same labels, splits, A/S/C results and evaluation script; only the predictions change</li>
<li>Seeing the schema is the point: complexity depends on it</li>
<li>Second idea: skip the judge when the router is very confident a claim is NEI (real time saving) <span class="tag t-hyp">hypothesis</span></li></ul>
<div class="take" style="margin-top:12px"><b>Question for Sir:</b> go ahead with #4 (schema aware SLM router), the confident NEI shortcut, or both?</div></div></div>"""))

html = f"<!doctype html><html><head><meta charset='utf-8'><title>Research Project Meeting Brief</title><style>{PAGE_CSS}</style></head><body>{''.join(pages)}</body></html>"
open("brief.html", "w").write(html)
print("pages", len(pages))
