"""Figure 1 for the short blog (v4): the three setups side by side."""
from diagrams import png, A, S, C

css = """
.cols{display:flex;gap:12px}
.col{flex:1;border-radius:16px;padding:12px 12px 14px;display:flex;flex-direction:column}
.col .tag{align-self:flex-start;margin-bottom:4px}
.what{font-size:14.5px;font-weight:700;margin-bottom:10px;min-height:38px;line-height:1.3}
.col .box{font-size:15px;padding:8px 8px}
.col .box small{font-size:13px}
.ghost{border-style:dashed !important;background:transparent !important;color:#94A3B8}
.stat{margin-top:auto;padding-top:12px;text-align:center;font-size:14px;color:#334155;line-height:1.3}
.stat b{font-size:28px;display:block;line-height:1.1}
"""
def col(tag, color, bg, what, tool, tool_small, helper, helper_small, ghost, acc, calls):
    hb = f"<div class='box{' ghost' if ghost else ''}' style='{'' if ghost else f'border-color:{color};background:#fff'}'>{helper}<small>{helper_small}</small></div>"
    return (f"<div class='col' style='background:{bg}'><span class='tag' style='background:{color}'>{tag}</span><div class='what'>{what}</div>"
            f"<div class='box'>Claim + hint</div><div class='down'>↓</div><div class='box'>Judge<small>Qwen3 8B</small></div><div class='down'>↓</div>"
            f"<div class='box' style='border-color:{color}'>{tool}<small>{tool_small}</small></div><div class='down'>↓</div>{hb}<div class='down'>↓</div>"
            f"<div class='box'>Database</div><div class='stat'><b style='color:{color}'>{acc}</b>accuracy<br>{calls}</div></div>")

body = ("<div class='title'>Three ways to let a small model check a claim</div>"
        "<div class='sub'>Same judge, same prompt, same answers to choose from. Only the tool changes.</div><div class='cols'>"
        + col("Setup A", A, "#FDF3EC", "The judge writes SQL itself", "Writes SQL", "has to guess the names", "No helper", "SQL goes straight in", True, "56.0%", "2.7 tool calls per claim")
        + col("Setup C", C, "#EEF3FB", "The judge asks a SQL specialist", "Asks in English", "“How many matches...?”", "SQL specialist", "Arctic 7B, sees the schema", False, "76.0%", "1.0 tool call per claim")
        + col("Setup S", S, "#EAF6F4", "The judge fills a lookup form", "Fills a form", "one table, filters, count", "Python tool", "checks names, writes SQL", False, "61.8%", "2.0 tool calls per claim")
        + "</div><div class='note'>Accuracy on the 1,000 ClaimDB test claims with Qwen3 8B as the judge.</div>")
png(body, "fig1_three_setups.png", css)
print("fig1 three done")
