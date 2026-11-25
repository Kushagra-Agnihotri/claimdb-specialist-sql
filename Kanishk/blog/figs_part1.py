from figlib import *

# ---------------- Figure 1: setup A vs setup C ----------------
lane_css = """
.lane{display:flex;align-items:center;gap:10px;margin:12px 0}
.tag{width:120px;flex:none;border-radius:12px;color:#fff;font-weight:800;padding:12px 10px;text-align:center;font-size:17px}
.tag small{display:block;font-weight:500;font-size:12px;opacity:.9}
.stat{margin-left:auto;font-size:14px;color:#374151;width:150px;text-align:right;flex:none}
.lane .box{white-space:nowrap}
.stat b{font-size:20px;display:block}
"""
fig1 = f"""
<div class='title'>Part 1: who writes the SQL?</div>
<div class='sub'>Same judge, same prompt, same answer format, same cap of 20 tool calls per claim. Only the tool changes.</div>
<div class='lane'><div class='tag' style='background:{A_COL}'>Setup A<small>baseline (ClaimDB)</small></div>
 <div class='box'>Claim + hint</div><span class='arrow'>→</span>
 <div class='box'>Judge<small>small LLM</small></div><span class='arrow'>→</span>
 <div class='box' style='border-color:{A_COL}'>writes SQL itself<small>must discover the tables</small></div><span class='arrow'>→</span>
 <div class='box'>SQLite database</div>
 <div class='stat'><b>2.7 calls</b>per claim</div></div>
<div class='lane'><div class='tag' style='background:{C_COL}'>Setup C<small>ours</small></div>
 <div class='box'>Claim + hint</div><span class='arrow'>→</span>
 <div class='box'>Judge<small>small LLM</small></div><span class='arrow'>→</span>
 <div class='box' style='border-color:{C_COL}'>asks in plain English<small>"How many matches...?"</small></div><span class='arrow'>→</span>
 <div class='box' style='border-color:{C_COL};background:#eef3fb'>SQL specialist<small>Arctic 7B, sees the schema</small></div><span class='arrow'>→</span>
 <div class='box'>SQLite database</div>
 <div class='stat'><b>1.0 call</b>per claim</div></div>
<div class='note' style='margin-top:8px'>In both setups the judge gets the query result back and decides: ENTAILED, CONTRADICTED or NOT ENOUGH INFO. Tool calls are averages for the Qwen3 8B judge over the 1,000 ClaimDB test claims.</div>
"""
render(fig1, "fig/fig1_setups_A_C.png", css=lane_css, width=1320)

# ---------------- Figure 2: animation, claim 5584 through A and C ----------------
anim_css = """
.claim{background:#13233f;color:#fff;border-radius:12px;padding:12px 16px;font-size:16px;margin-bottom:14px}
.claim span{color:#cbd5e1;font-size:13px}
.cols{display:flex;gap:18px}
.col{flex:1;border-radius:14px;padding:14px 16px;background:#f7f8fa;min-height:345px}
.head{font-weight:800;font-size:17px;margin-bottom:10px}
.step{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:8px 11px;margin:7px 0;font-size:14px}
.step .mono{display:block;margin-top:4px;color:#334155}
.err{border-left:4px solid #B91C1C}.okk{border-left:4px solid #15803D}.neu{border-left:4px solid #94a3b8}
.hid{visibility:hidden}
.verdict{font-weight:800;font-size:16px;padding:8px 12px;border-radius:10px;margin-top:10px}
.vok{background:#dcfce7;color:#166534}.vbad{background:#fee2e2;color:#991b1b}
"""
A_steps = [
    ("err", "Call 1: guesses a table name", "SELECT COUNT(*) FROM matches WHERE league = 'Scotland Premier League' ...", "→ error: no such table: matches"),
    ("neu", "Call 2: lists the tables", "SELECT name FROM sqlite_master WHERE type = 'table'", "→ Player, League, Country, Team, Match, ..."),
    ("neu", "Call 3: looks inside Match", "PRAGMA table_info(Match)", "→ league_id, season, ... but no league name"),
]
C_steps = [
    ("neu", "Call 1: asks the specialist in plain English", "\"How many matches were played in the Scotland Premier League during the 2015/2016 season?\"", ""),
    ("okk", "The specialist sees the schema and writes the join", "SELECT COUNT(*) FROM Match JOIN League ON Match.league_id = League.id WHERE League.name = 'Scotland Premier League' AND Match.season = '2015/2016'", "→ 228"),
]
def anim_frame(na, nc, va, vc):
    def col(title, color, steps, n, verdict):
        s = f"<div class='col'><div class='head' style='color:{color}'>{title}</div>"
        for i, (k, t, code, res) in enumerate(steps):
            s += f"<div class='step {k} {'hid' if i >= n else ''}'><b>{t}</b><span class='mono'>{code}</span><span class='mono' style='color:#0f172a'><b>{res}</b></span></div>"
        if verdict:
            s += verdict
        return s + "</div>"
    vA = "<div class='verdict vbad'>Verdict: NOT ENOUGH INFO ✗ (gives up, 3 calls)</div>" if va else "<div class='verdict hid'>.</div>"
    vC = "<div class='verdict vok'>Verdict: ENTAILED ✓ (1 call, 22.6 s)</div>" if vc else "<div class='verdict hid'>.</div>"
    return ("<div class='claim'>Claim 5584 (gold: ENTAILED): “The Scotland Premier League featured 228 matches in the 2015/2016 season.”"
            "<br><span>The answer needs two tables: League holds the league name, Match holds the matches and a league_id.</span></div>"
            f"<div class='cols'>{col('Setup A: the judge writes SQL', A_COL, A_steps, na, vA)}{col('Setup C: the judge asks the specialist', C_COL, C_steps, nc, vC)}</div>")
frames = [anim_frame(0, 0, 0, 0), anim_frame(1, 0, 0, 0), anim_frame(2, 0, 0, 0), anim_frame(3, 0, 1, 0),
          anim_frame(3, 1, 1, 0), anim_frame(3, 2, 1, 0), anim_frame(3, 2, 1, 1)]
render_frames(frames, "fig/fig2_claim5584_A_vs_C.gif", css=anim_css, durations=[2200, 2400, 2400, 2800, 2600, 3000, 5000])

# ---------------- Figure 3: our judge vs models reported by ClaimDB ----------------
rows = [("Claude Haiku 4.5", 80.9, GREY, 0), ("Gemini 2.5 Flash", 79.3, GREY, 0), ("GPT 5 nano", 78.7, GREY, 0),
        ("Qwen3 14B + specialist (ours, C)", 76.5, C_COL, 1), ("Qwen3 8B + specialist (ours, C)", 76.0, C_COL, 1),
        ("gpt oss 20B", 74.0, GREY, 0), ("Qwen3 32B", 57.4, GREY, 0), ("Qwen3 8B alone (ours, A)", 56.0, A_COL, 1),
        ("Qwen3 14B", 53.1, GREY, 0), ("Qwen3 8B", 52.1, GREY, 0)]
fig3 = ("<div class='title'>A small judge with a SQL specialist lands next to commercial models</div>"
        "<div class='sub'>Accuracy on the 1,000 ClaimDB test claims</div>"
        + legend([("Ours with the specialist (setup C)", C_COL), ("Ours alone (setup A)", A_COL), ("Reported in the ClaimDB paper", GREY)])
        + hbars(rows, width=1130, label_w=330)
        + "<div class='note' style='margin-top:4px'>Grey bars are copied from the ClaimDB paper. Our own harness scores 3.9 points above ClaimDB's run for the same Qwen3 8B model (56.0 vs 52.1), so close comparisons across the two harnesses should be read with care.</div>")
render(fig3, "fig/fig3_vs_claimdb.png")

# ---------------- Figure 4: every small judge, A vs C (1,000 claims) ----------------
groups = ["Qwen3 8B", "Qwen3 4B", "Qwen3 1.7B", "Llama 3.1 8B", "Llama 3.2 3B"]
fig4 = ("<div class='title'>The specialist helps every small judge we tried</div>"
        "<div class='sub'>Accuracy on the 1,000 ClaimDB test claims. Every gain from A to C is significant (McNemar p below 1e-10).</div>"
        + legend([("ClaimDB paper (their harness)", GREY), ("Setup A (judge writes SQL)", A_COL), ("Setup C (judge asks the specialist)", C_COL)])
        + gbars(groups, [("ClaimDB", [52.1, 51.1, 36.6, 34.4, 38.7]), ("A", [56.0, 54.3, 35.9, 35.7, 32.1]), ("C", [76.0, 68.3, 54.7, 54.7, 45.2])],
                [GREY, A_COL, C_COL], width=1130, height=400, fmt="{:.1f}")
        + "<div style='display:flex;gap:30px;margin-top:6px;font-size:14px'><span><b>+13 to +20 points</b> from A to C for every judge</span>"
          "<span><b>Qwen3 14B + specialist: 76.5</b>, no better than 8B (76.0)</span></div>")
render(fig4, "fig/fig4_judges_A_vs_C.png")

# ---------------- Table 1: what else we tried in Part 1 ----------------
t1 = f"""
<div class='title'>What else we tried in Part 1</div>
<div class='sub'>Each row changes one thing and compares with the matching run. p is the exact McNemar test (below 0.05 means a real difference).</div>
<table>
<tr><th>Change</th><th>Judge</th><th class='n'>Claims</th><th class='n'>Result</th><th class='n'>Compared with</th><th>Outcome</th></tr>
<tr><td>Give the judge the full schema in the prompt (setup B)</td><td>Qwen3 8B</td><td class='n'>210</td><td class='n'>61.0</td><td class='n'>A: 59.0</td><td style='color:{BAD};font-weight:700'>no real gain (p = 0.70)</td></tr>
<tr><td>Show the specialist 3 example values per column</td><td>Qwen3 8B</td><td class='n'>210</td><td class='n'>78.1</td><td class='n'>C: 74.3</td><td style='color:{MUTE};font-weight:700'>small, not significant (p = 0.23)</td></tr>
<tr><td>Other specialist: OmniSQL 7B</td><td>Qwen3 4B</td><td class='n'>1,000</td><td class='n'>65.5</td><td class='n'>Arctic: 68.3</td><td style='color:{MUTE};font-weight:700'>close (p = 0.10)</td></tr>
<tr><td>Other specialist: OmniSQL 7B</td><td>Llama 3.1 8B</td><td class='n'>1,000</td><td class='n'>54.0</td><td class='n'>Arctic: 54.7</td><td style='color:{MUTE};font-weight:700'>close (p = 0.73)</td></tr>
<tr><td>Smaller specialist: SLM SQL 1.5B</td><td>Qwen3 4B</td><td class='n'>676 *</td><td class='n'>54.1</td><td class='n'>Arctic: 67.8</td><td style='color:{BAD};font-weight:700'>much lower (p &lt; 0.001)</td></tr>
<tr><td>General coder: Qwen2.5 Coder 7B</td><td>Qwen3 4B</td><td class='n'>63 *</td><td class='n'>42.9</td><td class='n'>Arctic: 77.8</td><td style='color:{BAD};font-weight:700'>much lower (p &lt; 0.001)</td></tr>
<tr><td>Bigger judge: Qwen3 14B</td><td>Qwen3 14B</td><td class='n'>1,000</td><td class='n'>76.5</td><td class='n'>8B: 76.0</td><td style='color:{MUTE};font-weight:700'>no gain from scale (p = 0.76)</td></tr>
</table>
<div class='note' style='margin-top:8px'>* Partial runs, stopped when our cloud compute ran out. For these rows Arctic is scored on the same claims. The OmniSQL and Qwen3 14B runs used a cloud GPU. All other rows ran on our own GPU.</div>
"""
render(t1, "fig/table1_part1_variants.png")
print("part 1 figures done")
