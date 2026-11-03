import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for f in fm.findSystemFonts():
    if "Carlito" in f: fm.fontManager.addfont(f)
plt.rcParams.update({"font.family": "Carlito", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#8a8984", "axes.labelcolor": "#0b0b0b", "xtick.color": "#52514e", "ytick.color": "#52514e"})
B, O, A = "#2a78d6", "#eb6834", "#1baf7a"
R = json.load(open("diagnostics.json"))
small = [m for m, r in R.items() if r["size_b"] and r["size_b"] <= 14]
# pooled groups
groups = [("ec_clean", "All queries ran"), ("ec_grounding_err", "Hit a missing table/\ncolumn error"), ("ec_zero_calls", "Never queried")]
vals = []
for k, lab in groups:
    n = sum(R[m][k]["n"] for m in small)
    acc = sum(R[m][k]["acc"] * R[m][k]["n"] for m in small if R[m][k]["n"]) / n
    nei = sum(R[m][k]["nei"] * R[m][k]["n"] for m in small if R[m][k]["n"]) / n
    vals.append((lab, n, acc, nei))
fig, ax = plt.subplots(figsize=(4.6, 2.9))
x = range(len(vals)); w = 0.36
b1 = ax.bar([i - w/2 - 0.01 for i in x], [v[2]*100 for v in vals], w, color=B, label="Accuracy")
b2 = ax.bar([i + w/2 + 0.01 for i in x], [v[3]*100 for v in vals], w, color=O, label='Predicted "Not Enough Info"')
for bars in (b1, b2):
    for r in bars:
        ax.text(r.get_x() + r.get_width()/2, r.get_height() + 1.2, f"{r.get_height():.0f}%", ha="center", va="bottom", fontsize=8.5, color="#0b0b0b")
ax.set_xticks(list(x)); ax.set_xticklabels([f"{v[0]}\n(n={v[1]:,})" for v in vals], fontsize=8.8)
ax.set_ylim(0, 85); ax.set_ylabel("% of ENTAILED/CONTRADICTED claims")
ax.yaxis.grid(True, color="#e6e5e1", lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=8.5, loc="upper left", ncol=1)
plt.tight_layout(); plt.savefig("fig_grounding_vs_outcome.pdf"); plt.savefig("fig_grounding_vs_outcome.png", dpi=200)

fig, ax = plt.subplots(figsize=(4.6, 3.0))
prop = {"gpt-5-mini", "gpt-5-nano", "gpt-4o-mini", "claude-haiku-4-5"}
cats = [("Open, 14B or less", lambda m: m not in prop and (R[m]["size_b"] or 99) <= 14, B),
        ("Open, 20B to 32B", lambda m: m not in prop and (R[m]["size_b"] or 0) > 14, A),
        ("Proprietary API", lambda m: m in prop, O)]
for lab, fn, c in cats:
    ms = [m for m in R if fn(m)]
    ax.scatter([R[m]["err_share"]*100 for m in ms], [R[m]["acc"]*100 for m in ms], s=34, color=c, label=lab,
               edgecolors="white", linewidths=1.2, zorder=3)
offs = {"qwen3:8b": (6, -10), "llama3.1:8b": (-8, -12), "gpt-5-mini": (6, 2), "qwen3:1.7b": (2, -13), "gpt-4o-mini": (6, -3)}
for m, o in offs.items():
    ax.annotate(m, (R[m]["err_share"]*100, R[m]["acc"]*100), textcoords="offset points", xytext=o, fontsize=7.8, color="#52514e",
                ha=("right" if o[0] < 0 else "left"))
ax.set_xlabel("SQL calls that returned an error (%)"); ax.set_ylabel("Accuracy (%)")
ax.set_xlim(-3, 95); ax.set_ylim(25, 90)
ax.yaxis.grid(True, color="#e6e5e1", lw=0.6); ax.xaxis.grid(True, color="#e6e5e1", lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=8, loc="upper right")
plt.tight_layout(); plt.savefig("fig_error_vs_accuracy.pdf"); plt.savefig("fig_error_vs_accuracy.png", dpi=200)
print(vals)
