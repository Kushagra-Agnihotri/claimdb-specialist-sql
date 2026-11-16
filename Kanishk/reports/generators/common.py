"""Shared data and helpers for the two meeting PDFs. All numbers come from the PC results files (15 Nov 2026)."""

JUDGES = ["qwen3:14b", "qwen3:8b", "qwen3:4b", "qwen3:1.7b", "llama3.1:8b", "llama3.2:3b"]

# ClaimDB released runs re scored on the same claims, our A, our C with Arctic (all 1,000 claims)
SEC1 = {  # judge: (claimdb, ourA, ourC, c_ci, where_C_ran, secA, secC, onlyA, onlyC, p_AC)
    "qwen3:14b":  (53.1, None, 76.5, "", "Colab*", None, 21.1, None, None, None),
    "qwen3:8b":   (52.1, 56.0, 76.0, "73.3 to 78.4", "PC", 23.4, 29.0, 83, 283, "1e-26"),
    "qwen3:4b":   (51.1, 54.3, 68.3, "65.5 to 71.2", "PC", 36.7, 40.2, 121, 261, "6e-13"),
    "qwen3:1.7b": (36.6, 35.9, 54.7, "51.8 to 57.8", "PC", 2.5, 7.8, 30, 218, "2e-36"),
    "llama3.1:8b": (34.4, 35.7, 54.7, "51.7 to 57.8", "PC", 4.9, 18.9, 121, 311, "2e-20"),
    "llama3.2:3b": (38.7, 32.1, 45.2, "42.3 to 48.3", "PC", 3.3, 11.8, 132, 263, "4e-11"),
}

AUC = {  # task: (linear, mlp2, mlp3)
    "Strict complexity": (0.72, 0.68, 0.67),
    "Loose complexity": (0.64, 0.61, 0.61),
    "Answerability (NEI)": (0.95, 0.95, 0.94),
}

# routing with A as the cheap path, linear router unless stated (from router/routing_results.md)
ROUTE_A = {  # judge: (alwaysA, alwaysC, oracle, strict_true, strict_lin, loose_true, loose_lin, ans_true, ans_lin, ans_lin_p)
    "qwen3:8b":   (56.0, 76.0, 84.3, 74.1, 69.8, 61.9, 61.1, 80.6, 76.0, "1"),
    "qwen3:4b":   (54.3, 68.3, 80.4, 66.9, 62.6, 58.6, 57.5, 74.3, 70.9, "0.007"),
    "qwen3:1.7b": (35.9, 54.7, 57.7, 50.9, 48.9, 41.9, 42.2, 56.0, 53.8, "0.15"),
    "llama3.1:8b": (35.7, 54.7, 66.8, 51.3, 46.5, 41.5, 42.3, 57.6, 55.3, "0.66"),
    "llama3.2:3b": (32.1, 45.2, 58.4, 43.9, 41.4, 36.7, 36.5, 46.9, 45.3, "1"),
}

CSS = """
:root{--navy:#1d3557;--teal:#0f766e;--teal2:#14b8a6;--amber:#b45309;--red:#b91c1c;--green:#15803d;
--ink:#1f2937;--mute:#6b7280;--line:#e5e7eb;--soft:#f3f6fa;--soft2:#eef7f6;}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,'DejaVu Sans',sans-serif;color:var(--ink);background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}
table{border-collapse:collapse;width:100%}
th{background:var(--navy);color:#fff;font-weight:600;text-align:left}
td,th{border-bottom:1px solid var(--line)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
tr.hl td{background:#fff7e6}
.good{color:var(--green);font-weight:700}.bad{color:var(--red);font-weight:700}.mute{color:var(--mute)}
.tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:.78em;font-weight:600}
.t-obs{background:#dcfce7;color:#166534}.t-int{background:#e0e7ff;color:#3730a3}.t-hyp{background:#fef3c7;color:#92400e}
.box{border:1.5px solid var(--navy);border-radius:10px;padding:8px 12px;background:#fff;text-align:center;font-weight:600}
.arrow{color:var(--mute);font-size:1.4em;font-weight:700;padding:0 6px}
.flow{display:flex;align-items:center;justify-content:center;flex-wrap:nowrap}
.code{font-family:'DejaVu Sans Mono',monospace;font-size:.85em;background:#f6f8fa;border:1px solid var(--line);border-radius:6px;padding:6px 9px;white-space:pre-wrap}
"""


def bars(groups, series, colors, width=560, height=230, vmax=1.0, fmt="{:.2f}", ylabel="", baseline=None):
    """Grouped bar chart as inline SVG. groups: [label], series: [(name, [values])]."""
    left, bottom, top = 44, 40, 14
    plot_w, plot_h = width - left - 10, height - bottom - top
    n_g, n_s = len(groups), len(series)
    gw = plot_w / n_g
    bw = gw * 0.78 / n_s
    out = [f'<svg width="100%" viewBox="0 0 {width} {height}" style="max-width:{width*1.25:.0f}px;display:block" xmlns="http://www.w3.org/2000/svg" font-family="Inter,DejaVu Sans,sans-serif">']
    for k in range(6):
        v = vmax * k / 5
        y = top + plot_h - plot_h * v / vmax
        out.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-10}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        out.append(f'<text x="{left-6}" y="{y+4:.1f}" font-size="10" text-anchor="end" fill="#6b7280">{fmt.format(v) if vmax<=1 else int(v)}</text>')
    if baseline is not None:
        y = top + plot_h - plot_h * baseline / vmax
        out.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-10}" y2="{y:.1f}" stroke="#9ca3af" stroke-dasharray="4 3"/>')
    for gi, g in enumerate(groups):
        x0 = left + gi * gw + gw * 0.11
        for si, (name, vals) in enumerate(series):
            v = vals[gi]
            if v is None:
                continue
            h = plot_h * v / vmax
            x = x0 + si * bw
            y = top + plot_h - h
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw-2:.1f}" height="{h:.1f}" rx="2" fill="{colors[si]}"/>')
            out.append(f'<text x="{x+(bw-2)/2:.1f}" y="{y-3:.1f}" font-size="9.5" text-anchor="middle" fill="#1f2937" font-weight="600">{fmt.format(v)}</text>')
        out.append(f'<text x="{left+gi*gw+gw/2:.1f}" y="{height-bottom+16}" font-size="11" text-anchor="middle" fill="#1f2937" font-weight="600">{g}</text>')
    lx = left
    for si, (name, _) in enumerate(series):
        out.append(f'<rect x="{lx}" y="{height-14}" width="10" height="10" rx="2" fill="{colors[si]}"/>'
                   f'<text x="{lx+14}" y="{height-5}" font-size="10.5" fill="#374151">{name}</text>')
        lx += 18 + 7 * len(name)
    if ylabel:
        out.append(f'<text x="10" y="{top+plot_h/2}" font-size="10" fill="#6b7280" transform="rotate(-90 10 {top+plot_h/2})" text-anchor="middle">{ylabel}</text>')
    out.append("</svg>")
    return "".join(out)
