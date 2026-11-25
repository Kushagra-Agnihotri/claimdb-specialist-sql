"""Convert blog.html into Substack's ProseMirror draft JSON. Images use placeholders IMG:<file> that the page swaps for uploaded URLs."""
import json, re
from bs4 import BeautifulSoup, NavigableString

URLS = {"r1": "https://aclanthology.org/2026.acl-long.1589/", "r2": "https://arxiv.org/abs/2512.03278",
        "r3": "https://openreview.net/forum?id=rkeJRhNYDH",
        "r4": "https://proceedings.neurips.cc/paper_files/paper/2023/hash/83fc8fab1710363050bbd1d4b8cc0021-Abstract-Datasets_and_Benchmarks.html",
        "r5": "https://aclanthology.org/2026.findings-acl.1345/", "r6": "https://www.vldb.org/pvldb/vol18/p4695-li.pdf",
        "r7": "https://openreview.net/forum?id=WE_vluYUL-X", "r8": "https://arxiv.org/abs/2505.09388",
        "r9": "https://arxiv.org/abs/2407.21783"}


def link(href):
    return {"type": "link", "attrs": {"href": href, "target": "_blank", "rel": "noopener noreferrer nofollow", "class": None}}


def inline(node, marks=()):
    out = []
    for ch in node.children:
        if isinstance(ch, NavigableString):
            t = re.sub(r"\s+", " ", str(ch))
            if t:
                d = {"type": "text", "text": t}
                if marks:
                    d["marks"] = [dict(m) for m in marks]
                out.append(d)
            continue
        m = list(marks)
        if ch.name in ("b", "strong"):
            m.append({"type": "strong"})
        elif ch.name in ("i", "em"):
            m.append({"type": "em"})
        elif ch.name == "code":
            m.append({"type": "code"})
        elif ch.name == "a":
            href = ch.get("href", "")
            href = URLS.get(href[1:], href) if href.startswith("#") else href
            m.append(link(href))
        out += inline(ch, tuple(m))
    # trim outer whitespace
    if out and out[0]["type"] == "text":
        out[0]["text"] = out[0]["text"].lstrip()
    if out and out[-1]["type"] == "text":
        out[-1]["text"] = out[-1]["text"].rstrip()
    return [o for o in out if o.get("text", "x") != ""]


def para(node):
    c = inline(node)
    p = {"type": "paragraph", "attrs": {"textAlign": None}}
    if c:
        p["content"] = c
    return p


def heading(text_or_node, level):
    c = inline(text_or_node) if not isinstance(text_or_node, str) else [{"type": "text", "text": text_or_node}]
    return {"type": "heading", "attrs": {"textAlign": None, "level": level}, "content": c}


def lst(node, ordered):
    items = [{"type": "list_item", "content": [para(li)]} for li in node.find_all("li", recursive=False)]
    if ordered:
        return {"type": "ordered_list", "attrs": {"start": 1, "type": None, "order": 1}, "content": items}
    return {"type": "bullet_list", "content": items}


def figure(node):
    src = node.find("img")["src"].split("/")[-1]
    img = {"type": "image2", "attrs": {"src": "IMG:" + src, "srcNoWatermark": None, "fullscreen": None, "imageSize": None,
                                       "height": None, "width": None, "resizeWidth": None, "bytes": None, "alt": None,
                                       "title": None, "type": None, "href": None, "belowTheFold": False, "topImage": False,
                                       "internalRedirect": None, "isProcessing": False, "align": None, "offset": False}}
    cap = node.find("figcaption")
    return {"type": "captionedImage", "content": [img, {"type": "caption", "content": inline(cap)}]}


soup = BeautifulSoup(open("/home/claude/blog/blog.html", encoding="utf-8").read(), "html.parser")
body = soup.body
title = body.find("h1").get_text(" ", strip=True)
subtitle = body.find(class_="subtitle").get_text(" ", strip=True)
doc = []
for el in body.find_all(recursive=False):
    cls = el.get("class") or []
    if el.name == "h1" or "subtitle" in cls:
        continue
    if "byline" in cls:
        doc.append({"type": "paragraph", "attrs": {"textAlign": None}, "content": inline(el, ({"type": "em"},))})
    elif "tldr" in cls or "rq" in cls:
        doc.append({"type": "blockquote", "content": [para(el)]})
    elif "part" in cls:
        doc.append(heading(el.get_text(" ", strip=True), 1))
    elif el.name == "h2":
        doc.append(heading(el, 2))
    elif el.name == "h3":
        doc.append(heading(el, 3))
    elif el.name == "p":
        doc.append(para(el))
    elif el.name == "ul":
        doc.append(lst(el, False))
    elif el.name == "ol":
        # references: add a link on each entry
        items = []
        for li in el.find_all("li", recursive=False):
            p = para(li)
            u = URLS.get(li.get("id", ""))
            if u:
                p["content"] += [{"type": "text", "text": " "}, {"type": "text", "marks": [link(u)], "text": u}]
            items.append({"type": "list_item", "content": [p]})
        doc.append({"type": "ordered_list", "attrs": {"start": 1, "type": None, "order": 1}, "content": items})
    elif el.name == "figure":
        doc.append(figure(el))
    else:
        raise SystemExit(f"unhandled {el.name} {cls}")

out = {"title": title, "subtitle": subtitle, "body": {"type": "doc", "content": doc}}
json.dump(out, open("/home/claude/blog/substack_draft.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(json.dumps(out)), "chars,", len(doc), "blocks,", sum(1 for d in doc if d["type"] == "captionedImage"), "figures")
print(title, "|", subtitle[:80])
