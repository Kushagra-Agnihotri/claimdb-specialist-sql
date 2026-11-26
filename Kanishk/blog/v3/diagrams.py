"""Blog v3 diagrams, tables and animations (HTML rendered with Playwright). Designed at 760 px, the width of a Substack column."""
import io
from playwright.sync_api import sync_playwright
from PIL import Image

A, S, C, PUR, INK, MUTE = "#E07B39", "#2A9D8F", "#2B5DA8", "#7C3AED", "#0F172A", "#64748B"
OK, BAD = "#15803D", "#B91C1C"
OUT = "/home/claude/blog/v3/fig/"
W = 760
BASE = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Inter,sans-serif;color:{INK};background:#fff;font-size:16px}}
.wrap{{padding:26px 28px 24px;width:{W}px;background:#fff}}
.title{{font-size:23px;font-weight:800;letter-spacing:-.01em;margin-bottom:4px}}
.sub{{font-size:15px;color:{MUTE};margin-bottom:18px;line-height:1.4}}
.mono{{font-family:'DejaVu Sans Mono',monospace}}
.box{{border:2px solid #CBD5E1;border-radius:12px;padding:8px 12px;text-align:center;background:#fff;font-weight:700;font-size:16px}}
.box small{{display:block;font-weight:500;font-size:14px;color:{MUTE};margin-top:2px}}
.down{{text-align:center;color:#94A3B8;font-size:20px;line-height:1;margin:3px 0}}
.tag{{display:inline-block;color:#fff;font-weight:800;font-size:14px;border-radius:999px;padding:4px 12px}}
table{{border-collapse:collapse;width:100%}}
th{{font-size:14px;text-align:left;color:{MUTE};font-weight:700;padding:8px 8px;border-bottom:2px solid #0F172A}}
td{{font-size:15.5px;padding:10px 8px;border-bottom:1px solid #E5E7EB;vertical-align:top}}
.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
.note{{font-size:13.5px;color:{MUTE};margin-top:10px;line-height:1.45}}
"""


def page(body, css=""):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}{css}</style></head><body><div class='wrap'>{body}</div></body></html>"


def png(body, name, css="", scale=2.5):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": 400}, device_scale_factor=scale)
        pg.set_content(page(body, css)); pg.wait_for_timeout(200)
        pg.query_selector(".wrap").screenshot(path=OUT + name); b.close()


def gif(bodies, name, css="", durations=None, scale=1.5):
    frames = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": 400}, device_scale_factor=scale)
        for body in bodies:
            pg.set_content(page(body, css)); pg.wait_for_timeout(120)
            frames.append(Image.open(io.BytesIO(pg.query_selector(".wrap").screenshot())).convert("RGB"))
        b.close()
    h = max(f.height for f in frames)
    fr = []
    for f in frames:
        if f.height < h:
            c = Image.new("RGB", (f.width, h), "white"); c.paste(f, (0, 0)); f = c
        fr.append(f)
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=96) for f in fr]
    pal[0].save(OUT + name, save_all=True, append_images=pal[1:], duration=durations, loop=0, optimize=True)
    fr[-1].save(OUT + name.replace(".gif", "_last.png"))


# ---------------- Figure 1: setup A and setup C ----------------
css1 = """
.cols{display:flex;gap:18px}
.col{flex:1;border-radius:16px;padding:14px 16px 16px;display:flex;flex-direction:column}
.col .head{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.col .head b{font-size:17px}
.stat{margin-top:auto;padding-top:14px;text-align:center;font-size:15px;color:#334155}
.stat b{font-size:26px;display:block;line-height:1.1}
.spacer{height:88px}
"""
fig1 = f"""
<div class='title'>Who writes the SQL?</div>
<div class='sub'>Same judge, same prompt, same answer format. Both setups allow up to 20 tool calls per claim. Only the tool changes.</div>
<div class='cols'>
 <div class='col' style='background:#FDF3EC'>
  <div class='head'><span class='tag' style='background:{A}'>Setup A</span><b>baseline from ClaimDB</b></div>
  <div class='box'>Claim + hint</div><div class='down'>↓</div>
  <div class='box'>Judge<small>Qwen3 8B</small></div><div class='down'>↓</div>
  <div class='box' style='border-color:{A}'>Writes SQL itself<small>has to guess the table and column names</small></div><div class='down'>↓</div>
  <div class='box' style='border-style:dashed;background:transparent;color:#94A3B8'>No specialist<small style='color:#94A3B8'>the judge's SQL goes straight to the database</small></div><div class='down'>↓</div>
  <div class='box'>Database</div>
  <div class='stat'><b style='color:{A}'>2.7</b>tool calls per claim</div>
 </div>
 <div class='col' style='background:#EEF3FB'>
  <div class='head'><span class='tag' style='background:{C}'>Setup C</span><b>ours</b></div>
  <div class='box'>Claim + hint</div><div class='down'>↓</div>
  <div class='box'>Judge<small>Qwen3 8B</small></div><div class='down'>↓</div>
  <div class='box' style='border-color:{C}'>Asks in plain English<small>"How many matches did this league play?"</small></div><div class='down'>↓</div>
  <div class='box' style='border-color:{C};background:#DCE7F7'>SQL specialist<small>Arctic 7B, sees the full schema</small></div><div class='down'>↓</div>
  <div class='box'>Database</div>
  <div class='stat'><b style='color:{C}'>1.0</b>tool call per claim</div>
 </div>
</div>"""
png(fig1, "fig1_setups_A_C.png", css1)

# ---------------- shared animation style ----------------
anim_css = """
.claim{background:#0F172A;color:#fff;border-radius:14px;padding:13px 16px;font-size:16px;line-height:1.4;margin-bottom:14px}
.claim .k{display:block;color:#94A3B8;font-size:13px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;margin-bottom:4px}
.claim .h{display:block;color:#CBD5E1;font-size:14px;margin-top:6px}
.cols{display:flex;gap:14px}
.col{flex:1;border-radius:14px;padding:12px 12px 14px;min-height:470px;display:flex;flex-direction:column}
.chead{display:flex;align-items:center;gap:8px;margin-bottom:8px;font-weight:800;font-size:15.5px}
.step{background:#fff;border-radius:10px;padding:9px 11px;margin-bottom:9px;font-size:14.5px;line-height:1.35;border-left:5px solid #CBD5E1}
.step .code{display:block;font-family:'DejaVu Sans Mono',monospace;font-size:12.5px;color:#334155;margin-top:5px;line-height:1.4}
.step .res{display:block;font-weight:700;margin-top:5px}
.bad{border-left-color:#DC2626}.good{border-left-color:#16A34A}
.hid{visibility:hidden}
.verdict{margin-top:auto;border-radius:10px;padding:10px 12px;font-weight:800;font-size:15.5px}
.vg{background:#DCFCE7;color:#166534}.vb{background:#FEE2E2;color:#991B1B}
"""


def anim(claim_html, left, right, steps_order, out, durations):
    """left/right = (tag, color, bg, title, steps, verdict_html). steps_order = list of (n_left, n_right, show_vl, show_vr)."""
    def col(spec, n, show_v):
        tag, color, bg, title, steps, vhtml = spec
        h = f"<div class='col' style='background:{bg}'><div class='chead'><span class='tag' style='background:{color}'>{tag}</span>{title}</div>"
        for i, (kind, t, code, res) in enumerate(steps):
            h += (f"<div class='step {kind} {'hid' if i >= n else ''}'><b>{t}</b>"
                  + (f"<span class='code'>{code}</span>" if code else "") + (f"<span class='res'>{res}</span>" if res else "") + "</div>")
        return h + (vhtml if show_v else vhtml.replace("class='verdict", "class='verdict hid")) + "</div>"
    frames = [claim_html + f"<div class='cols'>{col(left, a, va)}{col(right, b, vb)}</div>" for a, b, va, vb in steps_order]
    gif(frames, out, anim_css, durations)


# ---------------- Figure 2: claim 5584 in A and C ----------------
claim2 = ("<div class='claim'><span class='k'>Claim 5584 · true answer: ENTAILED</span>"
          "“The Scotland Premier League featured 228 matches in the 2015/2016 season.”"
          "<span class='h'>The league name lives in the League table. The matches live in the Match table.</span></div>")
A_steps = [("bad", "Call 1: guesses a table name", "SELECT COUNT(*) FROM matches WHERE ...", "error: no such table: matches"),
           ("", "Call 2: lists all tables", "SELECT name FROM sqlite_master", "Player, League, Team, Match, ..."),
           ("", "Call 3: looks inside Match", "PRAGMA table_info(Match)", "league_id, season, ... but no league names")]
C_steps = [("", "Call 1: asks the specialist", None, "“How many matches did the Scotland Premier League play in 2015/2016?”"),
           ("good", "The specialist sees the schema and joins the two tables",
            "SELECT COUNT(*) FROM Match JOIN League ON Match.league_id = League.id WHERE League.name = 'Scotland Premier League' AND season = '2015/2016'", "228")]
anim(claim2,
     ("Setup A", A, "#FDF3EC", "the judge writes SQL", A_steps, "<div class='verdict vb'>Gives up: NOT ENOUGH INFO ✗</div>"),
     ("Setup C", C, "#EEF3FB", "the judge asks the specialist", C_steps, "<div class='verdict vg'>ENTAILED ✓ after one call</div>"),
     [(0, 0, 0, 0), (1, 0, 0, 0), (2, 0, 0, 0), (3, 0, 0, 0), (3, 0, 1, 0), (3, 1, 1, 0), (3, 2, 1, 0), (3, 2, 1, 1)],
     "fig2_claim5584_A_vs_C.gif", [2000, 2600, 2600, 2600, 2400, 2800, 3200, 6000])

# ---------------- Figure 7: claim 1005 in S and C ----------------
claim7 = ("<div class='claim'><span class='k'>Claim 1005 · true answer: NOT ENOUGH INFO</span>"
          "“The junior credit card held by client 13539 is issued on the Mastercard network.”"
          "<span class='h'>The database stores each card's type and issue date. It never stores the network.</span></div>")
S_steps = [("", "Call 1: lists the tables", "describe_tables()", "card has: card_id, disp_id, type, issued"),
           ("", "Call 2: finds the client's link to the card", "lookup(table = disp, client_id = 13539)", "disp_id 13231"),
           ("good", "Call 3: finds the card", "lookup(table = card, disp_id = 13231)", "a junior card, but no network column")]
C_steps7 = [("", "Call 1: asks the specialist", None, "“What network is the junior credit card of client 13539 on?”"),
            ("bad", "The specialist answers a different question",
             "SELECT c.type FROM card c JOIN disp d ON c.disp_id = d.disp_id WHERE d.client_id = 13539 AND c.type = 'credit'", "empty result")]
anim(claim7,
     ("Setup S", S, "#EAF6F4", "the judge fills lookup forms", S_steps, "<div class='verdict vg'>NOT ENOUGH INFO ✓</div>"),
     ("Setup C", C, "#EEF3FB", "the judge asks the specialist", C_steps7, "<div class='verdict vb'>Reads the empty result as a no: CONTRADICTED ✗</div>"),
     [(0, 0, 0, 0), (1, 0, 0, 0), (2, 0, 0, 0), (3, 0, 0, 0), (3, 0, 1, 0), (3, 1, 1, 0), (3, 2, 1, 0), (3, 2, 1, 1)],
     "fig7_claim1005_S_vs_C.gif", [2000, 2600, 2600, 2600, 2400, 2800, 3200, 6000])

# ---------------- Table 1 ----------------
def v(text, color):
    return f"<span style='color:{color};font-weight:700'>{text}</span>"
t1rows = [("Schema in the judge's prompt (setup B)", "Qwen3 8B judge, 210 claims", "61.0", "59.0 (A)", v("no real gain", BAD), "p = 0.70"),
          ("Example values shown to the specialist", "Qwen3 8B judge, 210 claims", "78.1", "74.3 (C)", v("small, not significant", MUTE), "p = 0.23"),
          ("OmniSQL 7B as the specialist", "Qwen3 4B judge, 1,000 claims", "65.5", "68.3 (Arctic)", v("about the same", MUTE), "p = 0.10"),
          ("OmniSQL 7B as the specialist", "Llama 3.1 8B judge, 1,000 claims", "54.0", "54.7 (Arctic)", v("about the same", MUTE), "p = 0.73"),
          ("SLM SQL 1.5B as the specialist", "Qwen3 4B judge, 676 claims *", "54.1", "67.8 (Arctic)", v("much worse", BAD), "p &lt; 0.001"),
          ("Qwen2.5 Coder 7B as the specialist", "Qwen3 4B judge, 63 claims *", "42.9", "77.8 (Arctic)", v("much worse", BAD), "p &lt; 0.001"),
          ("A bigger judge: Qwen3 14B", "with Arctic, 1,000 claims", "76.5", "76.0 (8B)", v("no gain", MUTE), "p = 0.76")]
t1 = ("<div class='title'>What else we tried in Part 1</div>"
      "<div class='sub'>Each row changes one thing and compares with the matching run on the same claims. Accuracy in %.</div>"
      "<table><tr><th>What we changed</th><th class='n'>Result</th><th class='n'>Compared with</th><th>Outcome</th></tr>"
      + "".join(f"<tr><td><b>{a}</b><br><span style='font-size:13.5px;color:{MUTE}'>{b}</span></td><td class='n'><b>{c}</b></td>"
                f"<td class='n'>{d}</td><td>{e}<br><span style='font-size:13.5px;color:{MUTE}'>{f}</span></td></tr>" for a, b, c, d, e, f in t1rows)
      + "</table><div class='note'>* Partial runs, stopped when our cloud credits ran out. Arctic is scored on the same claims.</div>")
png(t1, "table1_part1_variants.png")

# ---------------- Figure 5: the Part 2 pipeline ----------------
css5 = css1 + """
.top{display:flex;align-items:center;justify-content:center;gap:12px}
.split{display:flex;justify-content:space-around;margin:8px 0 6px;font-weight:700;font-size:15px}
"""
fig5 = f"""
<div class='title'>Part 2: can easy claims skip the specialist?</div>
<div class='sub'>A router reads only the claim and its hint. "Yes" sends the claim to the cheap path S. "No" sends it to setup C, unchanged from Part 1.</div>
<div class='top'><div class='box' style='width:190px'>Claim + hint</div><span style='font-size:22px;color:#94A3B8'>→</span>
<div class='box' style='width:300px;border-color:{PUR};background:#F5F3FF'>Router<small>a small classifier on the claim text</small></div></div>
<div class='split'><span style='color:{S}'>↙ "yes"</span><span style='color:{C}'>"no" ↘</span></div>
<div class='cols'>
 <div class='col' style='background:#EAF6F4'>
  <div class='head'><span class='tag' style='background:{S}'>Setup S</span><b>cheap path</b></div>
  <div class='box'>Judge<small>Qwen3 8B</small></div><div class='down'>↓</div>
  <div class='box' style='border-color:{S}'>Fills a lookup form<small>one table, filters, count or sum</small></div><div class='down'>↓</div>
  <div class='box' style='border-color:{S};background:#D5EEEA'>Python lookup tool<small>checks names, writes the SQL</small></div><div class='down'>↓</div>
  <div class='box'>Database</div>
 </div>
 <div class='col' style='background:#EEF3FB'>
  <div class='head'><span class='tag' style='background:{C}'>Setup C</span><b>as in Part 1</b></div>
  <div class='box'>Judge<small>Qwen3 8B</small></div><div class='down'>↓</div>
  <div class='box' style='border-color:{C}'>Asks in plain English<small>any question</small></div><div class='down'>↓</div>
  <div class='box' style='border-color:{C};background:#DCE7F7'>SQL specialist<small>Arctic 7B, a second model</small></div><div class='down'>↓</div>
  <div class='box'>Database</div>
 </div>
</div>"""
png(fig5, "fig5_router_S_C.png", css5)

# ---------------- Figure 6: one lookup call ----------------
css6 = """
.sec{border-radius:14px;padding:14px 16px;margin-bottom:12px}
.sec h4{font-size:16.5px;margin-bottom:9px;display:flex;align-items:center;gap:9px}
.num{display:inline-flex;width:26px;height:26px;border-radius:50%;background:#2A9D8F;color:#fff;font-size:14px;font-weight:800;align-items:center;justify-content:center;flex:none}
.code{font-family:'DejaVu Sans Mono',monospace;font-size:14px;background:#fff;border:1px solid #D9E2EC;border-radius:10px;padding:10px 12px;line-height:1.5;white-space:pre}
.st{display:flex;gap:10px;margin:8px 0;font-size:15.5px;line-height:1.4}
.st .num{background:#0F172A;width:24px;height:24px;font-size:13px;margin-top:1px}
"""
fig6 = f"""
<div class='title'>One call to the lookup tool</div>
<div class='sub'>The judge never writes SQL. It fills in a form, and about 250 lines of Python do the rest.</div>
<div class='sec' style='background:#EAF6F4'><h4><span class='num'>1</span>The judge fills in the form</h4>
<div class='code'>lookup(table   = "League",
       filters = [ name = "Scotland Premier League" ],
       columns = [ "id" ])</div></div>
<div class='sec' style='background:#F1F5F9'><h4><span class='num'>2</span>Python does the rest</h4>
<div class='st'><span class='num'>a</span><div><b>Checks every name</b> against the database. A wrong name gets the closest real ones back: "superheroes" → superhero, superpower.</div></div>
<div class='st'><span class='num'>b</span><div><b>Writes the SQL itself</b> and passes the values separately, so nothing the judge types can break the query.</div></div>
<div class='st'><span class='num'>c</span><div><b>Runs it read only</b>, with a 30 second limit and at most 100 rows.</div></div>
<div class='st'><span class='num'>d</span><div><b>If nothing matches</b>, shows similar stored values: "Marvel" → "Marvel Comics".</div></div></div>
<div class='sec' style='background:#EAF6F4;margin-bottom:0'><h4><span class='num'>3</span>The judge reads the reply</h4>
<div class='code'>{{ "rows_matching_filters": 1, "result": [ {{ "id": 19694 }} ] }}</div>
<div style='font-size:14.5px;color:#334155;margin-top:8px'>Next it looks up the Match table with league_id = 19694 and season = "2015/2016", and gets 228.</div></div>"""
png(fig6, "fig6_lookup_tool.png", css6)

# ---------------- Table 2: routing on the 210 subset ----------------
def cell(val, base, p):
    col = OK if (p < 0.05 and val > base) else (BAD if (p < 0.05 and val < base) else INK)
    bg = "#DCFCE7" if col == OK else ("#FEE2E2" if col == BAD else "transparent")
    return f"<td class='n'><span style='color:{col};background:{bg};border-radius:6px;padding:2px 6px;font-weight:{700 if col != INK else 500}'>{val:.1f}</span></td>"
rows = [("Qwen3 8B", 74.3, [(70.5, .24), (61.9, .00069), (73.3, .83), (73.3, .84)]),
        ("Qwen3 4B", 67.6, [(65.2, .5), (60.0, .056), (71.9, .11), (71.9, .093)]),
        ("Qwen3 1.7B", 55.7, [(50.0, .017), (44.3, .00012), (53.3, .23), (53.3, .18)]),
        ("Llama 3.1 8B", 53.3, [(40.5, 3.5e-6), (34.8, 7.5e-7), (47.6, .065), (59.0, .05)]),
        ("Llama 3.2 3B", 44.3, [(33.8, .00011), (22.9, 1.2e-8), (34.8, .0012), (53.8, .0017)])]
t2 = ("<div class='title'>No router beats always using the specialist</div>"
      "<div class='sub'>Accuracy (%) on the 210 claim subset. The router's \"yes\" claims go to S and the rest go to C. "
      f"<span style='color:{OK};font-weight:700'>Green</span>: significantly better than always C. <span style='color:{BAD};font-weight:700'>Red</span>: significantly worse.</div>"
      "<table><tr><th>Judge</th><th class='n'>Always C</th><th class='n'>One table<br>router</th><th class='n'>Two tables<br>router</th><th class='n'>Unanswerable<br>router</th><th class='n'>Unanswerable<br>router, NEI direct</th></tr>"
      + "".join(f"<tr><td><b>{j}</b></td><td class='n'><b>{b:.1f}</b></td>" + "".join(cell(x, b, p) for x, p in r) + "</tr>" for j, b, r in rows)
      + f"<tr><td style='color:{MUTE};font-size:14px'>Claims sent away from C</td><td></td>" + "".join(f"<td class='n' style='color:{MUTE};font-size:14px'>{k}</td>" for k in (75, 145, 71, 71)) + "</tr></table>"
      "<div class='note'>In the last column the flagged claims skip the judge and get NOT ENOUGH INFO (NEI) straight away.</div>")
png(t2, "table2_routing.png")

# ---------------- Figure 12: roadmap ----------------
css12 = """
.ph{border-radius:14px;padding:14px 16px}
.ph h3{font-size:18px;margin:6px 0 6px}
.ph li{font-size:15px;margin:5px 0 5px 20px;line-height:1.4}
"""
fig12 = f"""
<div class='title'>Where we go from here</div>
<div class='sub'>Setup C stays as it is. First we make S reliable on its own. Then we teach the router to send it the right claims.</div>
<div class='ph' style='background:#EAF6F4;border:2px solid {S}'><span class='tag' style='background:{S}'>Phase 1 · now</span>
<h3>Get S to 90% on one table claims</h3><ul>
<li>No router yet. S only sees claims that truly need one table.</li>
<li>Today: 74.9% with Qwen3 8B.</li>
<li>Fixes: a year filter, a percentage option, example values for each column, and a rule to look before answering NEI.</li>
<li>Tune on 8,053 training claims, then score once on the 215 test claims.</li></ul></div>
<div class='down' style='font-size:26px;margin:8px 0'>↓</div>
<div class='ph' style='background:#F5F3FF;border:2px solid {PUR}'><span class='tag' style='background:{PUR}'>Phase 2 · next</span>
<h3>A router that can see the schema</h3><ul>
<li>Today the one table router sends 75 claims to S, and only 23 of them need one table.</li>
<li>Fine tune a small language model on 46,486 labelled claims, with the schema as extra input.</li></ul></div>
<div class='down' style='font-size:26px;margin:8px 0'>↓</div>
<div class='ph' style='background:#EEF3FB;border:2px solid {C}'><span class='tag' style='background:{C}'>Unchanged</span>
<h3>Setup C handles everything else</h3><ul><li>Joins, nested queries and harder claims keep going to the specialist (76.0% overall).</li></ul></div>"""
png(fig12, "fig12_roadmap.png", css12)
print("diagrams done")
