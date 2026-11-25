from figlib import *

# ---------------- Figure 5: Part 2 pipeline with router and setup S ----------------
css5 = """
.grid{display:grid;grid-template-columns:190px 40px 210px 40px 1fr;align-items:center;row-gap:16px}
.lanebox{border-radius:14px;padding:12px 14px;display:flex;align-items:center;gap:10px}
.small{font-size:13px;color:#6B7280}
"""
fig5 = f"""
<div class='title'>Part 2: can some claims skip the specialist?</div>
<div class='sub'>A router reads only the claim text and sends it to setup S or to setup C. Setup C is unchanged from Part 1.</div>
<div class='grid'>
 <div class='box' style='grid-row:1/3'>Claim + hint</div>
 <div class='arrow' style='grid-row:1/3;text-align:center'>→</div>
 <div class='box' style='grid-row:1/3;border-color:#7c3aed;background:#f5f3ff'>Router<small>logistic regression on a text embedding of the claim</small></div>
 <div class='arrow' style='text-align:center'>↗</div>
 <div class='lanebox' style='background:#ecf8f6;border:2px solid {S_COL}'>
   <span class='pill' style='background:{S_COL}'>"yes"</span>
   <div class='box'>Judge</div><span class='arrow'>→</span>
   <div class='box' style='border-color:{S_COL}'>fills a lookup form<small>table, filters, count / sum / avg / min / max</small></div><span class='arrow'>→</span>
   <div class='box' style='border-color:{S_COL}'>Python lookup tool<small>checks names, writes the SQL</small></div>
   <div class='small' style='margin-left:6px'><b style='color:{S_COL}'>Setup S</b><br>no second model</div>
 </div>
 <div class='arrow' style='text-align:center'>↘</div>
 <div class='lanebox' style='background:#eef3fb;border:2px solid {C_COL}'>
   <span class='pill' style='background:{C_COL}'>"no"</span>
   <div class='box'>Judge</div><span class='arrow'>→</span>
   <div class='box' style='border-color:{C_COL}'>asks in plain English</div><span class='arrow'>→</span>
   <div class='box' style='border-color:{C_COL}'>SQL specialist<small>Arctic 7B</small></div>
   <div class='small' style='margin-left:6px'><b style='color:{C_COL}'>Setup C</b><br>as in Part 1</div>
 </div>
</div>
<div class='note' style='margin-top:12px'>We trained three routers. Each one asks a different yes or no question about the claim, and "yes" sends the claim to S.</div>
"""
render(fig5, "fig/fig5_router_S_C.png", css=css5, width=1320)

# ---------------- Figure 6: how the lookup tool handles one call ----------------
css6 = """
.row{display:flex;gap:14px;align-items:stretch}
.card{flex:1;border-radius:12px;background:#f7f8fa;padding:12px 14px}
.card h4{font-size:15px;margin-bottom:6px}
.code{font-family:'DejaVu Sans Mono',monospace;font-size:12.5px;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;white-space:pre-wrap}
.n{display:inline-flex;width:24px;height:24px;border-radius:50%;background:#2A9D8F;color:#fff;font-weight:800;align-items:center;justify-content:center;margin-right:6px;font-size:13px}
"""
fig6 = f"""
<div class='title'>Inside setup S: what the Python lookup tool does with one call</div>
<div class='sub'>The judge never writes SQL. It fills fixed fields, and about 250 lines of Python do the rest.</div>
<div class='row'>
 <div class='card' style='flex:1.1'><h4>The judge fills the lookup form</h4>
 <div class='code'>lookup(
  table   = "League",
  filters = [
    name = "Scotland Premier League" ],
  aggregate = "none",
  columns = [ "id" ] )</div>
 <div class='note' style='margin-top:8px'>Allowed filters: = != &gt; &gt;= &lt; &lt;= contains, starts with, is empty, is not empty. Aggregates: count, count distinct, sum, average, minimum, maximum.</div></div>
 <div class='card' style='flex:1.5'><h4>Python, step by step</h4>
 <div style='font-size:14px;line-height:1.55'>
 <div><span class='n'>1</span><b>Check every name</b> against the real database. A wrong name gets the closest real names back: "superheroes" → superhero, superpower.</div>
 <div><span class='n'>2</span><b>Write the SQL itself</b>, with values passed separately. Text matching ignores capital letters and extra spaces.</div>
 <div class='code' style='margin:5px 0'>SELECT "id" FROM "League" WHERE TRIM("name") = ? COLLATE NOCASE</div>
 <div><span class='n'>3</span><b>Run it read only</b>, with a 30 second limit and at most 100 rows.</div>
 <div><span class='n'>4</span><b>Reply</b> with the rows and how many rows matched. If nothing matched, say whether the value exists at all: "Marvel" → stored as "Marvel Comics".</div>
 </div></div>
 <div class='card' style='flex:.8'><h4>The judge reads the reply</h4>
 <div class='code'>{{"rows_matching_filters": 1,
 "result": [{{"id": 19694}}]}}</div>
 <div class='note' style='margin-top:8px'>Then it fills a second form on the Match table with league_id = 19694 and season = "2015/2016", and gets 228.</div></div>
</div>"""
render(fig6, "fig/fig6_lookup_tool.png", css=css6, width=1320)

# ---------------- Figure 7 animation: claim 1005 through S and C ----------------
anim_css = """
.claim{background:#13233f;color:#fff;border-radius:12px;padding:12px 16px;font-size:16px;margin-bottom:14px}
.claim span{color:#cbd5e1;font-size:13px}
.cols{display:flex;gap:18px}
.col{flex:1;border-radius:14px;padding:14px 16px;background:#f7f8fa;min-height:360px}
.head{font-weight:800;font-size:17px;margin-bottom:10px}
.step{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:8px 11px;margin:7px 0;font-size:14px}
.step .mono{display:block;margin-top:4px;color:#334155}
.err{border-left:4px solid #B91C1C}.okk{border-left:4px solid #15803D}.neu{border-left:4px solid #94a3b8}
.hid{visibility:hidden}
.verdict{font-weight:800;font-size:16px;padding:8px 12px;border-radius:10px;margin-top:10px}
.vok{background:#dcfce7;color:#166534}.vbad{background:#fee2e2;color:#991b1b}
"""
S_steps = [("neu", "Call 1: lists the tables", "describe_tables()", "→ card(card_id, disp_id, type, issued), disp(disp_id, client_id, ...): no network column anywhere"),
           ("neu", "Call 2: finds the client's account link", "lookup(table = disp, filters = [client_id = 13539], columns = [disp_id])", "→ disp_id 13231"),
           ("okk", "Call 3: finds the card", "lookup(table = card, filters = [disp_id = 13231], columns = [type])", "→ type 'junior'. The card exists, but the network is not stored.")]
C_steps = [("neu", "Call 1: asks the specialist", "\"What is the network of the junior credit card held by client ID 13539?\"", ""),
           ("err", "The specialist answers a different question", "SELECT c.type FROM card c JOIN disp d ON c.disp_id = d.disp_id WHERE d.client_id = 13539 AND c.type = 'credit'", "→ empty result. The judge reads it as evidence against the claim.")]
def frame(ns, nc, vs, vc):
    def col(title, color, steps, n, v):
        s = f"<div class='col'><div class='head' style='color:{color}'>{title}</div>"
        for i, (k, t, code, res) in enumerate(steps):
            s += f"<div class='step {k} {'hid' if i >= n else ''}'><b>{t}</b><span class='mono'>{code}</span><span class='mono' style='color:#0f172a'><b>{res}</b></span></div>"
        return s + v + "</div>"
    vS = "<div class='verdict vok'>Verdict: NOT ENOUGH INFO ✓ (23.5 s)</div>" if vs else "<div class='verdict hid'>.</div>"
    vC = "<div class='verdict vbad'>Verdict: CONTRADICTED ✗ (30.4 s)</div>" if vc else "<div class='verdict hid'>.</div>"
    return ("<div class='claim'>Claim 1005 (gold: NOT ENOUGH INFO): “The junior credit card held by client ID 13539 is issued on the Mastercard network.”"
            "<br><span>The database stores the card type and issue date. It does not store the card network, so the claim is unanswerable.</span></div>"
            f"<div class='cols'>{col('Setup S: the judge fills lookup forms', S_COL, S_steps, ns, vS)}{col('Setup C: the judge asks the specialist', C_COL, C_steps, nc, vC)}</div>")
render_frames([frame(0, 0, 0, 0), frame(1, 0, 0, 0), frame(2, 0, 0, 0), frame(3, 0, 1, 0), frame(3, 1, 1, 0), frame(3, 2, 1, 0), frame(3, 2, 1, 1)],
              "fig/fig7_claim1005_S_vs_C.gif", css=anim_css, durations=[2200, 2400, 2400, 2800, 2600, 3200, 5000])

# ---------------- Figure 8: router labels and classifier quality ----------------
fig8 = f"""
<div class='title'>Three routers, three different questions</div>
<div class='sub'>Each router is trained on 40,652 labelled ClaimDB training claims and tested on the 1,000 test claims, whose 11 databases it never saw.</div>
<div style='display:flex;gap:26px'>
<div style='flex:1.1'>
<table>
<tr><th>Router</th><th>Says "yes" (send to S) when it predicts that...</th><th class='n'>True "yes" in test</th></tr>
<tr><td><b>Strict</b></td><td>the claim needs exactly one table (no nested query)</td><td class='n'>215</td></tr>
<tr><td><b>Loose</b></td><td>the claim needs at most two tables</td><td class='n'>692</td></tr>
<tr><td><b>Unanswerable</b></td><td>the database cannot settle the claim (gold label NOT ENOUGH INFO)</td><td class='n'>336</td></tr>
</table>
<div class='note' style='margin-top:8px'>Training labels come from the reference SQL behind each claim and from its gold label. At test time a router sees only the claim and its hint.</div>
</div>
<div style='flex:1'>
{legend([("Logistic regression", "#13233f"), ("Neural network, 1 hidden layer", "#7c8db0"), ("2 hidden layers", "#c7cfdf")])}
{gbars(["Strict", "Loose", "Unanswerable"], [("LR", [0.72, 0.64, 0.95]), ("M2", [0.68, 0.61, 0.95]), ("M3", [0.67, 0.61, 0.94])], ["#13233f", "#7c8db0", "#c7cfdf"], width=560, height=300, vmax=1, fmt="{:.2f}", ylab="AUC (0.5 = chance, 1 = perfect)")}
</div></div>"""
render(fig8, "fig/fig8_routers_auc.png", width=1260)
print("part 2a done")

# ---------------- Figure 9: S vs A vs C on the 210 subset, all judges ----------------
groups = ["Qwen3 8B", "Qwen3 4B", "Qwen3 1.7B", "Llama 3.1 8B", "Llama 3.2 3B"]
fig9 = ("<div class='title'>Setup S on its own: level with or above A for the Qwen judges, far below for Llama</div>"
        "<div class='sub'>Accuracy on the balanced 210 claim subset (70 per label). Every claim goes through each setup, with no router.</div>"
        + legend([("Setup A (judge writes SQL)", A_COL), ("Setup S (lookup tool)", S_COL), ("Setup C (specialist)", C_COL)])
        + gbars(groups, [("A", [59.0, 51.4, 34.8, 39.0, 35.2]), ("S", [59.0, 62.4, 36.2, 23.3, 15.2]), ("C", [74.3, 67.6, 55.7, 53.3, 44.3])],
                [A_COL, S_COL, C_COL], width=1130, height=390, fmt="{:.1f}",
                annot={(3, 1): "81|no verdict", (4, 1): "104|no verdict"})
        + "<div class='note' style='margin-top:6px'>\"No verdict\" means the claim ended without an answer (out of 210). Most of these runs stopped because the judge sent a malformed lookup form twice in a row. The Qwen judges had 0 to 2 such claims.</div>")
render(fig9, "fig/fig9_S_on_subset.png")

# ---------------- Figure 10: S vs C on the claims each router sends to S (Qwen3 8B, 1,000 claims) ----------------
groups = ["Router says\nunanswerable", "Truly\nunanswerable", "Answerable,\nsent by mistake", "Truly\none table", "Strict router\nsays one table"]
svg = gbars(["Router: unanswerable (340)", "of which truly unanswerable (282)", "of which answerable (58)", "Truly one table (215)", "Strict router: one table (371)"],
            [("S", [84.4, 94.0, 37.9, 74.9, 59.0]), ("C", [82.9, 85.1, 72.4, 76.7, 70.1])], [S_COL, C_COL], width=1180, height=380, fmt="{:.1f}")
fig10 = ("<div class='title'>Where the lookup tool is as good as the specialist, and where it is not</div>"
         "<div class='sub'>Qwen3 8B judge, accuracy of S and of C on the same groups of the 1,000 test claims</div>"
         + legend([("Setup S (lookup tool)", S_COL), ("Setup C (specialist)", C_COL)]) + svg.replace('font-size="15" font-weight="700" fill="#1F2937" text-anchor="middle">', 'font-size="12.5" font-weight="700" fill="#1F2937" text-anchor="middle">')
         + "<div style='display:flex;gap:26px;margin-top:6px;font-size:14px'><span>All 340 routed: no real difference (p = 0.64), S 31% faster</span><span>Truly unanswerable: S better (p &lt; 0.001)</span><span>Sent by mistake: C better (p &lt; 0.001)</span><span>Truly one table: tie (p = 0.64)</span></div>")
render(fig10, "fig/fig10_S_vs_C_groups.png", width=1250)

# ---------------- Figure 11: routing results table on the 210 subset ----------------
def cell(v, base, p):
    col = OK if (p < 0.05 and v > base) else (BAD if (p < 0.05 and v < base) else INK)
    return f"<td class='n' style='color:{col};font-weight:{700 if col != INK else 500}'>{v:.1f}</td>"
rows = [("Qwen3 8B", 74.3, [(70.5, .24), (61.9, .00069), (73.3, .83), (73.3, .84)]),
        ("Qwen3 4B", 67.6, [(65.2, .5), (60.0, .056), (71.9, .11), (71.9, .093)]),
        ("Qwen3 1.7B", 55.7, [(50.0, .017), (44.3, .00012), (53.3, .23), (53.3, .18)]),
        ("Llama 3.1 8B", 53.3, [(40.5, 3.5e-6), (34.8, 7.5e-7), (47.6, .065), (59.0, .05)]),
        ("Llama 3.2 3B", 44.3, [(33.8, .00011), (22.9, 1.2e-8), (34.8, .0012), (53.8, .0017)])]
body = "".join(f"<tr><td><b>{j}</b></td><td class='n'><b>{b:.1f}</b></td>" + "".join(cell(v, b, p) for v, p in r) + "</tr>" for j, b, r in rows)
fig11 = f"""
<div class='title'>Routing on the 210 claim subset: no router beats always using the specialist</div>
<div class='sub'>Accuracy when the router's "yes" claims go to S and the rest go to C. Green: significantly better than always C. Red: significantly worse (McNemar p &lt; 0.05).</div>
<table>
<tr><th>Judge</th><th class='n'>Always C</th><th class='n'>Strict router → S</th><th class='n'>Loose router → S</th><th class='n'>Unanswerable router → S</th><th class='n'>Unanswerable router → answer<br>NOT ENOUGH INFO, no judge</th></tr>
{body}
<tr><td style='color:{MUTE}'>Claims sent away from C</td><td></td><td class='n' style='color:{MUTE}'>75</td><td class='n' style='color:{MUTE}'>145</td><td class='n' style='color:{MUTE}'>71</td><td class='n' style='color:{MUTE}'>71</td></tr>
</table>
<div class='note' style='margin-top:8px'>Only 41 of the 75 claims the strict router sends to S truly need one table. The last column skips the judge entirely for the 71 flagged claims and answers NOT ENOUGH INFO.</div>"""
render(fig11, "fig/fig11_routing_table.png")

# ---------------- Figure 12: why S fails on one table claims ----------------
rows = [("Fetched data, wrong ENTAILED or CONTRADICTED call", 30, "#b45309", 1), ("Never made a lookup, said NOT ENOUGH INFO", 9, "#94a3b8", 0),
        ("Got 0 rows (value written differently), gave up", 8, "#94a3b8", 0), ("Got rows back, still said NOT ENOUGH INFO", 5, "#94a3b8", 0),
        ("Lookup errors or no verdict", 2, "#94a3b8", 0)]
fig12 = (f"<div class='title'>Why setup S gets 54 of the 215 one table claims wrong</div>"
         f"<div class='sub'>Qwen3 8B judge. S is right on 161 of 215 one table test claims (74.9%). We read every wrong case.</div>"
         + hbars(rows, width=1130, label_w=470, vmax=35, fmt="{:.0f}").replace(">20<", ">20<")
         + f"""<div style='display:flex;gap:14px;margin-top:10px'>
<div style='flex:1;background:#fff7ed;border-radius:12px;padding:10px 14px;font-size:14px'><b>No date functions.</b> "236 users created their accounts after 2013." The form compares the whole date with 2013, so S counted 3,278 users.</div>
<div style='flex:1;background:#fff7ed;border-radius:12px;padding:10px 14px;font-size:14px'><b>No percentages.</b> "About 0.0485% of compounds have a triple bond." The form cannot divide two counts, and the judge's own arithmetic went wrong.</div>
<div style='flex:1;background:#fff7ed;border-radius:12px;padding:10px 14px;font-size:14px'><b>Wrong column.</b> The judge counted <span class='mono'>types</span> instead of <span class='mono'>type</span>, and <span class='mono'>GSoffered</span> instead of <span class='mono'>GSserved</span>.</div>
</div>""")
fig12 = fig12.replace("range(0, 101, 20)", "")
render(fig12, "fig/fig12_S_failures.png")
print("part 2b done")

# ---------------- Figure 13: roadmap ----------------
css13 = """
.ph{flex:1;border-radius:14px;padding:14px 16px}
.ph h3{font-size:18px;margin-bottom:6px}
.ph li{font-size:14px;margin:4px 0 4px 18px;line-height:1.4}
.badge{display:inline-block;font-size:12px;font-weight:800;border-radius:999px;padding:2px 10px;color:#fff;margin-bottom:6px}
"""
fig13 = f"""
<div class='title'>What we are doing now</div>
<div class='sub'>C stays as it is. We first make S reliable on its own, then teach the router to send it the right claims.</div>
<div style='display:flex;gap:16px;align-items:stretch'>
<div class='ph' style='background:#ecf8f6;border:2px solid {S_COL}'><span class='badge' style='background:{S_COL}'>Phase 1 · in progress</span>
<h3>Make S reach 90% on one table claims</h3><ul>
<li>No router. Only claims that truly need one table go to S.</li>
<li>Improve the lookup tool using one table claims from the ClaimDB training split (8,053 available), then score once on the 215 test claims.</li>
<li>Planned fixes: a year filter, a percentage option, columns with example values, a rule to always look before answering NOT ENOUGH INFO.</li>
<li>Starting point: 74.9% (Qwen3 8B).</li></ul></div>
<div style='display:flex;align-items:center;font-size:30px;color:#64748b'>→</div>
<div class='ph' style='background:#f5f3ff;border:2px solid #7c3aed'><span class='badge' style='background:#7c3aed'>Phase 2 · planned</span>
<h3>A router that sends S the right claims</h3><ul>
<li>Today the strict router sends 75 claims of the 210 subset to S, and only 41 of them need one table.</li>
<li>Fine tune a small language model on the 46,486 labelled training claims, with the database schema as extra input.</li>
<li>Goal: S receives the one table claims, so it gets both its speed and its accuracy.</li></ul></div>
<div style='display:flex;align-items:center;font-size:30px;color:#64748b'>→</div>
<div class='ph' style='background:#eef3fb;border:2px solid {C_COL}'><span class='badge' style='background:{C_COL}'>Unchanged</span>
<h3>C handles everything else</h3><ul>
<li>Joins, nested queries and harder claims keep going to the SQL specialist.</li>
<li>76.0% on all 1,000 claims with Qwen3 8B.</li></ul></div>
</div>"""
render(fig13, "fig/fig13_roadmap.png", css=css13, width=1320)
print("roadmap done")
