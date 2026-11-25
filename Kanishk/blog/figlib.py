"""Shared helpers for the blog figures: HTML templates rendered to PNG with Playwright, plus simple SVG charts."""
from playwright.sync_api import sync_playwright

A_COL, S_COL, C_COL, GREY, INK, MUTE = "#E07B39", "#2A9D8F", "#2B5DA8", "#CBD5E1", "#1F2937", "#6B7280"
OK, BAD = "#15803D", "#B91C1C"

BASE_CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Inter,'DejaVu Sans',sans-serif;color:{INK};background:#fff}}
.wrap{{padding:28px 34px;width:1200px}}
.title{{font-size:24px;font-weight:800;color:#13233f;margin-bottom:4px}}
.sub{{font-size:15px;color:{MUTE};margin-bottom:18px}}
.box{{border:2px solid #13233f;border-radius:14px;padding:12px 16px;background:#fff;text-align:center;font-weight:700;font-size:16px}}
.box small{{display:block;font-weight:500;font-size:13px;color:{MUTE};margin-top:3px}}
.mono{{font-family:'DejaVu Sans Mono',monospace;font-size:13px}}
.pill{{display:inline-block;border-radius:999px;padding:3px 11px;font-size:13px;font-weight:700;color:#fff}}
.arrow{{font-size:26px;color:#64748b;font-weight:700}}
.note{{font-size:13px;color:{MUTE}}}
table{{border-collapse:collapse;width:100%;font-size:15px}}
th{{background:#13233f;color:#fff;text-align:left;padding:9px 12px;font-weight:700}}
td{{padding:9px 12px;border-bottom:1px solid #e5e7eb}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
"""


def render(html_body, out, width=1200, css="", scale=2):
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE_CSS}{css}</style></head><body><div class='wrap' style='width:{width}px'>{html_body}</div></body></html>"
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": width, "height": 400}, device_scale_factor=scale)
        pg.set_content(html)
        pg.wait_for_timeout(150)
        el = pg.query_selector(".wrap")
        el.screenshot(path=out)
        b.close()


def render_frames(bodies, out_gif, width=1200, css="", durations=None, scale=1):
    """Render several HTML states with identical size and assemble an animated GIF."""
    from PIL import Image
    import io
    frames = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": width, "height": 400}, device_scale_factor=scale)
        for body in bodies:
            html = f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE_CSS}{css}</style></head><body><div class='wrap' style='width:{width}px'>{body}</div></body></html>"
            pg.set_content(html)
            pg.wait_for_timeout(100)
            frames.append(Image.open(io.BytesIO(pg.query_selector(".wrap").screenshot())).convert("RGB"))
        b.close()
    h = max(f.height for f in frames)
    frames = [f if f.height == h else _pad(f, h) for f in frames]
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in frames]
    pal[0].save(out_gif, save_all=True, append_images=pal[1:], duration=durations or 2200, loop=0, optimize=True)
    frames[-1].save(out_gif.replace(".gif", "_last.png"))


def _pad(img, h):
    from PIL import Image
    c = Image.new("RGB", (img.width, h), "white"); c.paste(img, (0, 0)); return c


def hbars(rows, width=1000, bar_h=34, gap=12, vmax=100, label_w=270, fmt="{:.1f}"):
    """rows: [(label, value, color, bold)] -> horizontal bar chart SVG."""
    plot_w = width - label_w - 70
    h = len(rows) * (bar_h + gap) + 40
    s = [f'<svg width="{width}" height="{h}" xmlns="http://www.w3.org/2000/svg" font-family="Inter,DejaVu Sans,sans-serif">']
    step = 20 if vmax >= 60 else (10 if vmax >= 20 else 5)
    for k in range(0, int(vmax) + 1, step):
        x = label_w + plot_w * k / vmax
        s.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h-30}" stroke="#eef0f3"/><text x="{x}" y="{h-10}" font-size="13" fill="{MUTE}" text-anchor="middle">{k}</text>')
    for i, (lab, v, col, bold) in enumerate(rows):
        y = i * (bar_h + gap) + 4
        w = plot_w * v / vmax
        fw = "800" if bold else "500"
        s.append(f'<text x="{label_w-12}" y="{y+bar_h/2+5}" font-size="15" font-weight="{fw}" fill="{INK}" text-anchor="end">{lab}</text>')
        s.append(f'<rect x="{label_w}" y="{y}" width="{w}" height="{bar_h}" rx="4" fill="{col}"/>')
        s.append(f'<text x="{label_w+w+8}" y="{y+bar_h/2+5}" font-size="15" font-weight="{fw}" fill="{INK}">{fmt.format(v)}</text>')
    s.append("</svg>")
    return "".join(s)


def gbars(groups, series, colors, width=1100, height=380, vmax=100, fmt="{:.0f}", ylab="Accuracy (%)", annot=None):
    """Grouped vertical bars. series: [(name, [values or None])]. annot: {(group_index, series_index): text}."""
    left, bottom, top = 60, 50, 20
    pw, ph = width - left - 20, height - bottom - top
    gw = pw / len(groups); bw = gw * 0.8 / len(series)
    s = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" font-family="Inter,DejaVu Sans,sans-serif">']
    for t in range(6):
        k = vmax * t / 5
        y = top + ph - ph * k / vmax
        lab = f"{k:.1f}" if vmax <= 1 else f"{k:.0f}"
        s.append(f'<line x1="{left}" y1="{y}" x2="{width-20}" y2="{y}" stroke="#eef0f3"/><text x="{left-8}" y="{y+5}" font-size="13" fill="{MUTE}" text-anchor="end">{lab}</text>')
    s.append(f'<text x="16" y="{top+ph/2}" font-size="13" fill="{MUTE}" transform="rotate(-90 16 {top+ph/2})" text-anchor="middle">{ylab}</text>')
    for gi, g in enumerate(groups):
        x0 = left + gi * gw + gw * 0.1
        for si, (_, vals) in enumerate(series):
            v = vals[gi]
            if v is None:
                continue
            hh = ph * v / vmax; x = x0 + si * bw; y = top + ph - hh
            s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw-4:.1f}" height="{hh:.1f}" rx="3" fill="{colors[si]}"/>')
            s.append(f'<text x="{x+(bw-4)/2:.1f}" y="{y-6:.1f}" font-size="14" font-weight="700" fill="{INK}" text-anchor="middle">{fmt.format(v)}</text>')
            if annot and (gi, si) in annot:
                lines = annot[(gi, si)].split("|")
                for li, ln in enumerate(lines):
                    yy = top + ph - 8 - (len(lines) - 1 - li) * 13
                    s.append(f'<text x="{x+(bw-4)/2:.1f}" y="{yy:.1f}" font-size="10.5" font-weight="700" fill="#fff" text-anchor="middle">{ln}</text>')
        s.append(f'<text x="{left+gi*gw+gw/2:.1f}" y="{height-bottom+24}" font-size="15" font-weight="700" fill="{INK}" text-anchor="middle">{g}</text>')
    s.append("</svg>")
    return "".join(s)


def legend(items):
    return "<div style='display:flex;gap:22px;margin:6px 0 10px'>" + "".join(
        f"<span style='display:flex;align-items:center;gap:7px;font-size:14px'><span style='width:14px;height:14px;border-radius:3px;background:{c};display:inline-block'></span>{n}</span>" for n, c in items) + "</div>"
