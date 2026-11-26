"""Blog v3 charts (matplotlib). Sized for a 728 px Substack column: 1900 px wide images, about 15 px text on screen."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import glob

for f in glob.glob("/usr/share/fonts/opentype/inter/Inter-*.otf"):
    fm.fontManager.addfont(f)
plt.rcParams.update({
    "font.family": "Inter", "font.size": 15, "axes.titlesize": 19, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.titlepad": 14, "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.edgecolor": "#CBD5E1", "axes.labelcolor": "#475569",
    "xtick.color": "#475569", "ytick.color": "#1F2937", "axes.grid": True, "grid.color": "#EEF0F3",
    "grid.linewidth": 1.2, "axes.axisbelow": True, "legend.frameon": False, "legend.fontsize": 14,
    "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.pad_inches": 0.25, "figure.facecolor": "white"})

A, S, C, GREY, INK, MUTE = "#E07B39", "#2A9D8F", "#2B5DA8", "#CBD5E1", "#1F2937", "#64748B"
OUT = "/home/claude/blog/v3/fig/"
W = 9.5




def finish(fig, ax, title, handles=None, ncol=3, fname=None, top_gap=0.0):
    """Left align the title and legend with the left edge of the tick labels, then save."""
    import matplotlib.transforms as mt
    ax.set_title("")
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    ext = [t.get_window_extent(r).x0 for t in ax.get_yticklabels() if t.get_text()] + [ax.get_window_extent(r).x0]
    if ax.yaxis.label.get_text():
        ext.append(ax.yaxis.label.get_window_extent(r).x0)
    x0 = min(ext)
    xf = x0 / fig.bbox.width
    tr = mt.blended_transform_factory(fig.transFigure, ax.transAxes)
    if handles:
        fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(xf - 0.008, 1.005 + top_gap), bbox_transform=tr, ncol=ncol,
                   handlelength=1, columnspacing=1.4, handletextpad=0.5, borderaxespad=0)
        ty = 1.11 + top_gap
    else:
        ty = 1.04 + top_gap
    fig.text(xf, ty, title, transform=tr, fontsize=19, fontweight="bold", color="#0F172A", va="bottom")
    fig.savefig(OUT + fname); plt.close(fig)


def subtitle(ax, text, y=1.02):
    ax.text(0, y, text, transform=ax.transAxes, fontsize=14, color=MUTE, va="bottom")


# ---------- Figure 3: our judge next to the ClaimDB models ----------
rows = [("GPT 5 mini", 82.7, GREY), ("Claude Haiku 4.5", 80.9, GREY), ("Gemini 3 Flash", 80.1, GREY), ("Gemini 2.5 Flash", 79.3, GREY), ("GPT 5 nano", 78.7, GREY),
        ("Qwen3 14B + specialist", 76.5, C), ("Qwen3 8B + specialist", 76.0, C), ("gpt oss 20B", 74.0, GREY),
        ("Qwen3 32B", 57.4, GREY), ("Qwen3 8B alone", 56.0, A), ("Qwen3 14B", 53.1, GREY), ("Qwen3 8B", 52.1, GREY)]
fig, ax = plt.subplots(figsize=(W, 7.4))
y = list(range(len(rows)))[::-1]
ax.barh(y, [r[1] for r in rows], color=[r[2] for r in rows], height=0.66)
ax.set_yticks(y, [r[0] for r in rows])
for yi, (lab, v, c) in zip(y, rows):
    bold = c != GREY
    ax.text(v + 0.8, yi, f"{v:.1f}", va="center", fontsize=15, fontweight="bold" if bold else "normal", color=INK)
    if bold:
        ax.get_yticklabels()[len(rows) - 1 - yi].set_fontweight("bold")
ax.set_xlim(0, 100); ax.grid(axis="y", visible=False); ax.tick_params(axis="y", length=0)
ax.set_xlabel("Accuracy on the 1,000 ClaimDB test claims (%)")
from matplotlib.patches import Patch
finish(fig, ax, "A small judge with a specialist lands close to commercial models",
       [Patch(color=C, label="Ours, with the specialist"), Patch(color=A, label="Ours, alone"), Patch(color=GREY, label="ClaimDB paper")], 3, "fig3_vs_claimdb.png", top_gap=-0.03)

# ---------- Figure 4: A to C for every small judge ----------
judges = [("Qwen3 8B", 56.0, 76.0), ("Qwen3 4B", 54.3, 68.3), ("Qwen3 1.7B", 35.9, 54.7), ("Llama 3.1 8B", 35.7, 54.7), ("Llama 3.2 3B", 32.1, 45.2)]
fig, ax = plt.subplots(figsize=(W, 5.2))
for i, (j, a, c) in enumerate(judges):
    yy = len(judges) - 1 - i
    ax.annotate("", xy=(c - 1.2, yy), xytext=(a + 1.2, yy), arrowprops=dict(arrowstyle="-|>", color="#94A3B8", lw=2.4, mutation_scale=18))
    ax.scatter([a], [yy], s=260, color=A, zorder=3); ax.scatter([c], [yy], s=260, color=C, zorder=3)
    ax.text(a - 2.2, yy, f"{a:.1f}", ha="right", va="center", fontsize=15, color=A, fontweight="bold")
    ax.text(c + 2.2, yy, f"{c:.1f}", ha="left", va="center", fontsize=15, color=C, fontweight="bold")
    ax.text(97, yy, f"+{c - a:.1f}", ha="right", va="center", fontsize=15, color=INK, fontweight="bold")
ax.set_yticks(range(len(judges)), [j[0] for j in judges][::-1]); ax.tick_params(axis="y", length=0)
ax.set_xlim(20, 98); ax.set_ylim(-0.6, len(judges) - 0.4); ax.grid(axis="y", visible=False)
ax.set_xlabel("Accuracy on the 1,000 ClaimDB test claims (%)")
H4 = [plt.Line2D([], [], marker="o", ls="", ms=12, color=A, label="Setup A (judge writes SQL)"),
      plt.Line2D([], [], marker="o", ls="", ms=12, color=C, label="Setup C (judge asks the specialist)")]
ax.text(97, len(judges) - 0.45, "gain", ha="right", va="bottom", fontsize=13, color=MUTE)
finish(fig, ax, "Adding the specialist helps every small judge", H4, 2, "fig4_judges_A_vs_C.png", top_gap=0.03)

# ---------- Figure 8: router AUC ----------
routers = [("Is the claim unanswerable?", 0.95, "#7C3AED"), ("Does it need exactly one table?", 0.72, "#A78BFA"), ("Does it need two tables or fewer?", 0.64, "#A78BFA")]
fig, ax = plt.subplots(figsize=(6.6, 3.4))
yy = [2, 1, 0]
ax.barh(yy, [r[1] for r in routers], color=[r[2] for r in routers], height=0.6)
ax.set_yticks(yy, [r[0] for r in routers]); ax.tick_params(axis="y", length=0)
for y_, (_, v, _) in zip(yy, routers):
    ax.text(v + 0.012, y_, f"{v:.2f}", va="center", fontsize=16, fontweight="bold", color=INK)
ax.axvline(0.5, color="#94A3B8", ls="--", lw=1.6)
ax.text(0.51, 2.42, "guessing", color=MUTE, fontsize=13, va="bottom"); ax.set_ylim(-0.5, 2.8)
ax.set_xlim(0, 1.0); ax.grid(axis="y", visible=False)
ax.set_xlabel("AUC on the 1,000 test claims (0.5 = guessing, 1.0 = perfect)")
finish(fig, ax, "Spotting unanswerable claims is easy.\nCounting tables is not.", None, 0, "fig8_routers_auc.png")

# ---------- Figure 9: A, S and C for every judge on the 210 subset ----------
import numpy as np
names = ["Qwen3 8B", "Qwen3 4B", "Qwen3 1.7B", "Llama 3.1 8B", "Llama 3.2 3B"]
vals = {"A": [59.0, 51.4, 34.8, 39.0, 35.2], "S": [59.0, 62.4, 36.2, 23.3, 15.2], "C": [74.3, 67.6, 55.7, 53.3, 44.3]}
fig, ax = plt.subplots(figsize=(W, 5.6))
x = np.arange(len(names)); w = 0.27
for k, (key, col, lab) in enumerate([("A", A, "A: judge writes SQL"), ("S", S, "S: Python lookup tool"), ("C", C, "C: SQL specialist")]):
    bars = ax.bar(x + (k - 1) * w, vals[key], w * 0.92, color=col, label=lab)
    for b, v in zip(bars, vals[key]):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.0f}", ha="center", fontsize=13.5, fontweight="bold" if key == "C" else "normal", color=INK)
ax.set_xticks(x, ["Qwen3 8B", "Qwen3 4B", "Qwen3 1.7B", "Llama 3.1 8B\n(81 no verdict)", "Llama 3.2 3B\n(104 no verdict)"], fontsize=13.5)
ax.tick_params(axis="x", length=0)
ax.set_ylim(0, 85); ax.set_yticks(range(0, 81, 20)); ax.set_ylabel("Accuracy (%)"); ax.grid(axis="x", visible=False)
finish(fig, ax, "The lookup tool helps the Qwen judges\nand trips up the Llama judges", ax.get_legend_handles_labels()[0], 3, "fig9_S_on_subset.png")

# ---------- Figure 10: S vs C on the same groups ----------
groups = ["All routed\n(340 claims)", "Truly unanswerable\n(282)", "Sent by mistake\n(58)", "Truly one table\n(215)"]
sv, cv = [84.4, 94.0, 37.9, 74.9], [82.9, 85.1, 72.4, 76.7]
fig, ax = plt.subplots(figsize=(W, 5.4))
x = np.arange(len(groups)); w = 0.36
for k, (vv, col, lab) in enumerate([(sv, S, "S: Python lookup tool"), (cv, C, "C: SQL specialist")]):
    bars = ax.bar(x + (k - 0.5) * w, vv, w * 0.92, color=col, label=lab)
    for b, v in zip(bars, vv):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.3, f"{v:.1f}", ha="center", fontsize=14.5, fontweight="bold", color=INK)
verdicts = ["about equal", "S better", "C better", "about equal"]
for xi, t in zip(x, verdicts):
    ax.text(xi, 104, t, ha="center", fontsize=13.5, color=MUTE, style="italic")
ax.set_xticks(x, groups, fontsize=13.5); ax.tick_params(axis="x", length=0)
ax.set_ylim(0, 110); ax.set_yticks(range(0, 101, 20)); ax.set_ylabel("Accuracy (%)"); ax.grid(axis="x", visible=False)
finish(fig, ax, "On truly unanswerable claims, the cheap path wins", ax.get_legend_handles_labels()[0], 2, "fig10_S_vs_C_groups.png")

# ---------- Figure 11: why S fails on one table claims ----------
fails = [("Fetched data, then made the wrong call", 30, "#C2410C"), ("Never looked anything up", 9, "#94A3B8"),
         ("Got 0 rows back and gave up", 8, "#94A3B8"), ("Got rows back, still said NEI", 5, "#94A3B8"), ("Errors or no verdict", 2, "#94A3B8")]
fig, ax = plt.subplots(figsize=(6.4, 4.0))
yy = list(range(len(fails)))[::-1]
ax.barh(yy, [f[1] for f in fails], color=[f[2] for f in fails], height=0.62)
ax.set_yticks(yy, [f[0] for f in fails]); ax.tick_params(axis="y", length=0)
for y_, (_, v, _) in zip(yy, fails):
    ax.text(v + 0.4, y_, str(v), va="center", fontsize=16, fontweight="bold", color=INK)
ax.set_xlim(0, 34); ax.grid(axis="y", visible=False); ax.set_xlabel("Number of claims (54 wrong out of 215)")
finish(fig, ax, "Most mistakes happen after the lookup,\nnot before it", None, 0, "fig11_S_failures.png")
print("charts done")
