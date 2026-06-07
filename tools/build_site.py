#!/usr/bin/env python3
"""Build the static OpenTikZ website from catalog.json + item files.

Reads catalog.json (root) and, for each item, its sibling .tex (code) and .svg
(preview). Emits a self-contained static site under site/:

  site/
    index.html              gallery (build-time cards) + Fuse.js search/filter
    item/<id>.html          per-item page: preview, copyable .tex, metadata
    previews/<id>.svg       copied preview
    assets/style.css        the stylesheet
    assets/app.js           search/filter + copy-to-clipboard
    .nojekyll               disable Jekyll on GitHub Pages

Stdlib only. The site needs no TeX to build — only catalog.json and the committed
.svg previews. Serve locally with:  python3 -m http.server -d site
"""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from _common import repo_root

TAGLINE = "A TikZ resource library for academic conceptual diagrams."
LEDE = ("Copyable icons, editable architecture templates, and AI-editable skills "
        "— so researchers produce paper figures fast without writing TikZ from scratch.")

TYPE_ORDER = {"icon": 0, "template": 1, "example": 2, "skill": 3}
TYPE_LABEL = {"icon": "icon", "template": "template", "example": "example", "skill": "skill"}


def find_tex(item_dir: Path) -> Path | None:
    texs = sorted(item_dir.glob("*.tex"))
    return texs[0] if texs else None


def _inline_md(s: str) -> str:
    """Inline markdown -> HTML on an already-plain string (escapes first)."""
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def md_to_html(md: str) -> str:
    """Minimal Markdown -> HTML for skill.md (headings, code fences, lists,
    blockquotes, bold, inline code, links). Not a general parser — covers the
    constructs the skills actually use."""
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    list_type: str | None = None
    i, n = 0, len(lines)

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    while i < n:
        line = lines[i]
        if line.startswith("```"):
            close_list()
            i += 1
            buf = []
            while i < n and not lines[i].startswith("```"):
                buf.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append('<pre class="md-code"><code>' + "\n".join(buf) + "</code></pre>")
            continue
        if not line.strip():
            close_list()
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            close_list()
            level = min(len(m.group(1)) + 1, 6)  # '#' -> h2 (page owns h1)
            out.append(f"<h{level}>{_inline_md(m.group(2))}</h{level}>")
            i += 1
            continue
        if line.startswith(">"):
            close_list()
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(_inline_md(lines[i].lstrip(">").strip()))
                i += 1
            out.append("<blockquote>" + "<br>".join(buf) + "</blockquote>")
            continue
        ml = re.match(r"^\s*([-*]|\d+\.)\s+(.*)$", line)
        if ml:
            ltype = "ol" if ml.group(1)[0].isdigit() else "ul"
            if list_type != ltype:
                close_list()
                out.append(f"<{ltype}>")
                list_type = ltype
            out.append("<li>" + _inline_md(ml.group(2)) + "</li>")
            i += 1
            continue
        close_list()
        buf = []
        while (i < n and lines[i].strip() and not lines[i].startswith("```")
               and not re.match(r"^#{1,6}\s", lines[i]) and not lines[i].startswith(">")
               and not re.match(r"^\s*([-*]|\d+\.)\s", lines[i])):
            buf.append(_inline_md(lines[i].strip()))
            i += 1
        out.append("<p>" + " ".join(buf) + "</p>")
    close_list()
    return "\n".join(out)


# --------------------------------------------------------------------------- #
#  HTML fragments
# --------------------------------------------------------------------------- #
def head(title: str, css_href: str, *, description: str = TAGLINE) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,900&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{css_href}">
</head>
<body>
<div class="grid-bg" aria-hidden="true"></div>
"""


REPO_URL = "https://github.com/opentikz/opentikz"


def navbar(home_href: str, anchor_base: str) -> str:
    """Sticky header. anchor_base='' on the index (in-page #icons), or
    '../index.html' on item pages (return to index.html#icons)."""
    return f"""<header class="navbar">
  <div class="nav-inner">
    <a class="wordmark" href="{home_href}">Open<span class="tik">TikZ</span><span class="caret">┃</span></a>
    <nav class="nav-links">
      <a href="{anchor_base}#icons" data-nav="icons">Icons</a>
      <a href="{anchor_base}#templates" data-nav="templates">Templates</a>
      <a href="{anchor_base}#examples" data-nav="examples">Examples</a>
      <a href="{REPO_URL}#readme">Docs</a>
      <a class="nav-gh" href="{REPO_URL}" target="_blank" rel="noopener">GitHub <span class="star">★</span></a>
    </nav>
  </div>
</header>
"""


def badge(t: str) -> str:
    return f'<span class="badge badge-{html.escape(t)}">{html.escape(TYPE_LABEL.get(t, t))}</span>'


def tag_list(tags: list[str], limit: int | None = None) -> str:
    if limit:
        tags = tags[:limit]
    return "".join(f'<span class="tag">{html.escape(x)}</span>' for x in tags)


def card(item: dict, preview_href: str, item_href: str, idx: int) -> str:
    name = html.escape(item["name"])
    domains = " · ".join(html.escape(d) for d in item.get("domain", []))
    return f"""  <a class="card" href="{item_href}" data-id="{html.escape(item['id'])}" data-type="{html.escape(item['type'])}" style="--i:{idx}">
    <div class="canvas"><img src="{preview_href}" alt="{name} preview" loading="lazy"></div>
    <div class="card-meta">
      {badge(item['type'])}
      <h3>{name}</h3>
      <p class="domains">{domains}</p>
    </div>
  </a>
"""


def metadata_table(item: dict) -> str:
    rows = []

    def row(k: str, v: str) -> str:
        return f"<tr><th>{html.escape(k)}</th><td>{v}</td></tr>"

    rows.append(row("id", f"<code>{html.escape(item['id'])}</code>"))
    rows.append(row("type", badge(item["type"])))
    rows.append(row("domain", ", ".join(html.escape(d) for d in item.get("domain", []))))
    if item.get("venue"):
        rows.append(row("venue", ", ".join(html.escape(v) for v in item["venue"])))
    if item.get("requires"):
        reqs = ", ".join(f"<code>{html.escape(r)}</code>" for r in item["requires"])
        rows.append(row("requires", reqs))
    rows.append(row("license", f"<code>{html.escape(item['license'])}</code>"))
    rows.append(row("author", html.escape(item.get("author", ""))))
    return "<table class=\"meta-table\">" + "".join(rows) + "</table>"


def item_page(item: dict, code: str, tex_name: str, skill_md: str | None, css_href: str) -> str:
    name = html.escape(item["name"])
    desc = html.escape(item.get("description", ""))
    preview = f"../previews/{item['id']}.svg"
    is_template = item["type"] == "template"
    skill_note = ""
    skill_section = ""
    if is_template and skill_md:
        skill_note = (
            '<p class="skill-note">This template ships a companion '
            '<strong>skill</strong> (<code>skill.md</code>) so an AI agent can edit it '
            'reliably — the full guide is below. Copy it together with the <code>.tex</code> '
            'into your AI assistant.</p>'
        )
        skill_section = f"""
  <section class="skill">
    <div class="skill-head">
      <h2>Companion skill <span>— edit this template with AI</span></h2>
      <button class="copy" data-target="skillsrc">Copy skill.md</button>
    </div>
    <details class="skill-body">
      <summary>Show the skill — structure · edit operations · constraints</summary>
      <div class="md">{md_to_html(skill_md)}</div>
    </details>
    <pre id="skillsrc" hidden>{html.escape(skill_md)}</pre>
  </section>
"""
    return (
        head(f"{item['name']} — OpenTikZ", css_href, description=item.get("description", TAGLINE))
        + navbar("../index.html", "../index.html")
        + f"""<main class="item">
  <a class="back" href="../index.html">← all resources</a>
  <div class="item-top">
    <div class="item-canvas"><img src="{preview}" alt="{name} preview"></div>
    <div class="item-head">
      {badge(item['type'])}
      <h1>{name}</h1>
      <p class="lede">{desc}</p>
      {skill_note}
      {metadata_table(item)}
      <p class="tags">{tag_list(item.get('tags', []))}</p>
    </div>
  </div>

  <section class="code-block">
    <div class="code-head">
      <span class="filename">{html.escape(tex_name)}</span>
      <button class="copy" data-target="src">Copy .tex</button>
    </div>
    <pre><code id="src">{html.escape(code)}</code></pre>
  </section>
{skill_section}
  <section class="usage">
    <h2>Use it</h2>
    <p>The file compiles on its own (<code>\\documentclass{{standalone}}</code>).
       Drop it into your project and <code>\\input</code> it, or copy the
       <code>tikzpicture</code> into your figure. Colours come from the shared
       palette defined in the preamble — edit those named colours, not raw hex.</p>
    <p class="license-note">Graphic content is <strong>CC0 1.0</strong> (public domain) — reuse freely, no attribution required.</p>
  </section>
</main>
"""
        + footer()
        + f'<script src="{css_href.replace("style.css", "app.js")}"></script>\n</body>\n</html>\n'
    )


def footer() -> str:
    return """<footer class="site-footer">
  <div>
    <span class="fw">OpenTikZ</span> — conceptual TikZ for papers.
  </div>
  <div class="licenses">
    Code <code>MIT</code> · Content <code>CC0 1.0</code>
  </div>
</footer>
"""


def index_page(items: list[dict], css_href: str) -> str:
    counts = {"icon": 0, "template": 0, "example": 0}
    for it in items:
        counts[it["type"]] = counts.get(it["type"], 0) + 1

    # One section per type: Icons / Templates / Examples.
    section_titles = {"icon": "Icons", "template": "Templates", "example": "Examples"}
    groups_html = ""
    idx = 0
    for t in ("icon", "template", "example"):
        members = [it for it in items if it["type"] == t]
        if not members:
            continue
        cards = ""
        for it in members:
            cards += card(it, f"previews/{it['id']}.svg", f"item/{it['id']}.html", idx)
            idx += 1
        groups_html += f"""  <section class="group" id="{t}s" data-group="{t}">
    <div class="group-head">
      <h2>{section_titles[t]}</h2>
      <span class="group-count" data-count>{len(members)}</span>
    </div>
    <div class="grid">
{cards}    </div>
  </section>
"""

    chips = ['<button class="chip active" data-type="all">all</button>']
    for t in ("icon", "template", "example"):
        if counts.get(t):
            chips.append(f'<button class="chip" data-type="{t}">{section_titles[t].lower()} · {counts[t]}</button>')
    chips_html = "\n      ".join(chips)

    search_index = json.dumps(
        [
            {
                "id": it["id"],
                "name": it["name"],
                "type": it["type"],
                "domain": it.get("domain", []),
                "tags": it.get("tags", []),
                "description": it.get("description", ""),
            }
            for it in items
        ],
        ensure_ascii=False,
    )

    return (
        head("OpenTikZ — TikZ for academic diagrams", css_href)
        + navbar("index.html", "")
        + f"""<section class="hero">
  <p class="eyebrow">{html.escape(TAGLINE)}</p>
  <p class="lede">{html.escape(LEDE)}</p>
  <div class="hero-search">
    <input id="search" type="search" placeholder="Search icons, templates, tags…    ( / )" autocomplete="off" aria-label="Search resources">
  </div>
  <div class="chips" id="chips">
      {chips_html}
  </div>
  <p class="result-count" id="count"></p>
</section>

<main id="gallery">
{groups_html}</main>
<p class="empty" id="empty" hidden>No resources match — try a different term.</p>
"""
        + footer()
        + f'<script id="catalog" type="application/json">{search_index}</script>\n'
        + ('<script src="https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js" '
           'integrity="sha384-PCSoOZTpbkikBEtd/+uV3WNdc676i9KUf01KOA8CnJotvlx8rRrETbDuwdjqTYvt" '
           'crossorigin="anonymous" referrerpolicy="no-referrer"></script>\n')
        + f'<script src="{css_href.replace("style.css", "app.js")}"></script>\n'
        + "</body>\n</html>\n"
    )


# --------------------------------------------------------------------------- #
def build(root: Path) -> int:
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    catalog = [it for it in catalog if it.get("type") in ("icon", "template", "example")]
    catalog.sort(key=lambda it: (TYPE_ORDER.get(it["type"], 9), it["name"].lower()))

    site = root / "site"
    if site.exists():
        shutil.rmtree(site)
    (site / "item").mkdir(parents=True)
    (site / "previews").mkdir(parents=True)
    (site / "assets").mkdir(parents=True)

    (site / "assets" / "style.css").write_text(STYLE_CSS, encoding="utf-8")
    (site / "assets" / "app.js").write_text(APP_JS, encoding="utf-8")
    (site / ".nojekyll").write_text("", encoding="utf-8")

    n_prev = 0
    for it in catalog:
        item_dir = root / it["path"]
        # copy preview
        svg = item_dir / it["preview"]
        if svg.exists():
            shutil.copyfile(svg, site / "previews" / f"{it['id']}.svg")
            n_prev += 1
        # per-item page
        tex = find_tex(item_dir)
        code = tex.read_text(encoding="utf-8") if tex else "% (source not found)"
        tex_name = tex.name if tex else ""
        skill_path = item_dir / "skill.md"
        skill_md = skill_path.read_text(encoding="utf-8") if skill_path.exists() else None
        (site / "item" / f"{it['id']}.html").write_text(
            item_page(it, code, tex_name, skill_md, "../assets/style.css"), encoding="utf-8"
        )

    (site / "index.html").write_text(index_page(catalog, "assets/style.css"), encoding="utf-8")

    print(f"built site/ — {len(catalog)} items, {n_prev} previews, "
          f"{len(catalog)+1} pages")
    return 0


# --------------------------------------------------------------------------- #
#  Assets (kept here so the script is the single source of truth)
# --------------------------------------------------------------------------- #
STYLE_CSS = r""":root{
  --paper:#FBFAF6; --ink:#1B1A16; --muted:#6F6C61; --line:#E6E3D8; --line-strong:#D6D2C4;
  --otblue:#0072B2; --otorange:#E69F00; --otteal:#009E73; --otpurple:#A85C86; --otgray:#5A5A5A;
  --grid:rgba(0,114,178,.05);
  --shadow:0 1px 0 var(--line-strong), 0 18px 40px -28px rgba(27,26,22,.45);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:16px; line-height:1.6;
  -webkit-font-smoothing:antialiased; position:relative; min-height:100vh;
}
/* TikZ-style coordinate grid background */
.grid-bg{
  position:fixed; inset:0; z-index:-1; pointer-events:none;
  background-image:
    linear-gradient(var(--grid) 1px,transparent 1px),
    linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:26px 26px;
  mask-image:radial-gradient(ellipse 120% 90% at 50% 0,#000 40%,transparent 100%);
}
a{color:inherit}
code{font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.86em;
  background:#F1EFE6; padding:.08em .35em; border-radius:3px; border:1px solid var(--line)}

/* ---------- sticky nav bar ---------- */
.navbar{position:sticky; top:0; z-index:50; background:rgba(251,250,246,.86);
  backdrop-filter:blur(8px); border-bottom:1px solid var(--line)}
.nav-inner{max-width:1180px; margin:0 auto; padding:11px 28px;
  display:flex; align-items:center; gap:16px; flex-wrap:wrap}
.wordmark{display:inline-block; text-decoration:none; font-family:"Fraunces",serif;
  font-weight:900; font-size:26px; letter-spacing:-.02em; line-height:1}
.wordmark .tik{color:var(--otblue)}
.wordmark .caret{color:var(--otorange); animation:blink 1.2s steps(1) infinite; margin-left:.04em}
@keyframes blink{50%{opacity:0}}
.nav-links{display:flex; align-items:center; gap:4px; margin-left:auto; flex-wrap:wrap}
.nav-links a{font-family:"IBM Plex Sans",sans-serif; font-size:.92rem; color:var(--muted);
  text-decoration:none; padding:7px 11px; border-radius:7px; white-space:nowrap;
  transition:color .15s, background .15s}
.nav-links a:hover{color:var(--ink); background:#F1EFE6}
.nav-links a.active{color:var(--otblue)}
.nav-gh{color:var(--ink); font-weight:500}
.nav-gh .star{color:var(--otorange)}

/* ---------- hero (elevated, centred search) ---------- */
.hero{max-width:760px; margin:0 auto; padding:54px 28px 12px; text-align:center}
.hero .eyebrow{margin:0 0 .4em; font-family:"IBM Plex Mono",monospace; font-size:.8rem;
  letter-spacing:.03em; color:var(--muted)}
.hero .lede{font-size:clamp(1.15rem,2.6vw,1.6rem); margin:0 auto .95em; max-width:30ch;
  font-family:"Fraunces",serif; font-weight:400; color:#34322b}
.hero-search{position:relative; max-width:640px; margin:0 auto}
#search{width:100%; padding:16px 18px 16px 48px; font:inherit; font-size:1.05rem; color:var(--ink);
  background:#fff; border:1.5px solid var(--line-strong); border-radius:13px; box-shadow:var(--shadow);
  transition:border-color .15s, box-shadow .15s}
#search::placeholder{color:#A6A294}
#search:focus{outline:none; border-color:var(--otblue); box-shadow:0 0 0 4px rgba(0,114,178,.14)}
.hero-search::before{content:"\2315"; position:absolute; left:17px; top:50%;
  transform:translateY(-50%) rotate(-12deg); color:#A6A294; font-size:1.3rem; pointer-events:none}
.chips{display:flex; flex-wrap:wrap; gap:8px; margin:14px 0 0; justify-content:center}
.chip{font:500 .85rem/1 "IBM Plex Mono",monospace; padding:7px 13px; cursor:pointer;
  background:#fff; color:var(--muted); border:1.5px solid var(--line-strong);
  border-radius:999px; transition:.15s}
.chip:hover{border-color:var(--otblue); color:var(--ink)}
.chip.active{background:var(--ink); color:var(--paper); border-color:var(--ink)}
.result-count{color:var(--muted); font-size:.82rem; margin:12px 0 0; text-align:center;
  font-family:"IBM Plex Mono",monospace}

/* ---------- gallery ---------- */
.grid{
  max-width:1180px; margin:6px auto 0; padding:14px 28px 60px;
  display:grid; grid-template-columns:repeat(auto-fill,minmax(232px,1fr)); gap:20px;
}
.card{
  display:flex; flex-direction:column; text-decoration:none; background:#fff;
  border:1px solid var(--line); border-radius:12px; overflow:hidden;
  box-shadow:var(--shadow); transition:transform .18s cubic-bezier(.2,.7,.2,1), box-shadow .18s, border-color .18s;
  animation:rise .5s both; animation-delay:calc(var(--i,0) * 32ms);
}
@keyframes rise{from{opacity:0; transform:translateY(12px)}to{opacity:1; transform:none}}
.card:hover{transform:translateY(-4px); border-color:var(--line-strong);
  box-shadow:0 1px 0 var(--line-strong),0 26px 50px -26px rgba(27,26,22,.55)}
.canvas{
  aspect-ratio:4/3; display:grid; place-items:center; padding:20px;
  background:
    linear-gradient(rgba(0,0,0,.028) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,0,0,.028) 1px,transparent 1px) #fcfcfa;
  background-size:18px 18px; border-bottom:1px solid var(--line);
}
.canvas img{max-width:100%; max-height:150px; width:auto; height:auto}
.card-meta{padding:13px 15px 16px}
.card-meta h3{margin:.35em 0 .15em; font-family:"Fraunces",serif; font-weight:600;
  font-size:1.12rem; letter-spacing:-.01em}
.domains{margin:0; color:var(--muted); font-size:.8rem;
  font-family:"IBM Plex Mono",monospace}
.empty{max-width:1180px; margin:0 auto; padding:0 28px 80px; color:var(--muted)}

/* ---------- badges ---------- */
.badge{display:inline-block; font:500 .68rem/1 "IBM Plex Mono",monospace;
  text-transform:uppercase; letter-spacing:.06em; padding:5px 8px; border-radius:5px;
  border:1px solid currentColor}
.badge-icon{color:var(--otteal)}
.badge-template{color:var(--otblue)}
.badge-example{color:var(--otpurple)}
.badge-skill{color:var(--otorange)}

/* ---------- item page ---------- */
.item{max-width:1000px; margin:0 auto; padding:8px 28px 70px}
.back{display:inline-block; margin:6px 0 22px; color:var(--muted);
  font-family:"IBM Plex Mono",monospace; font-size:.85rem; text-decoration:none}
.back:hover{color:var(--otblue)}
.item-top{display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.1fr); gap:34px; align-items:start}
.item-canvas{
  background:
    linear-gradient(rgba(0,0,0,.03) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,0,0,.03) 1px,transparent 1px) #fff;
  background-size:22px 22px; border:1px solid var(--line); border-radius:12px;
  padding:30px; display:grid; place-items:center; box-shadow:var(--shadow); min-height:240px;
}
.item-canvas img{max-width:100%; max-height:360px}
.item-head h1{font-family:"Fraunces",serif; font-weight:900; letter-spacing:-.02em;
  font-size:clamp(1.8rem,4vw,2.6rem); margin:.3em 0 .15em; line-height:1.05}
.item-head .lede{font-family:"Fraunces",serif; color:#34322b; margin:.2em 0 1em}
.skill-note{background:#FFF8EC; border:1px solid #F0DDB6; border-left:3px solid var(--otorange);
  padding:11px 14px; border-radius:7px; font-size:.9rem; color:#5b5341}
.meta-table{width:100%; border-collapse:collapse; margin:14px 0 4px; font-size:.9rem}
.meta-table th{text-align:left; width:96px; padding:7px 10px 7px 0; color:var(--muted);
  font-weight:500; vertical-align:top; font-family:"IBM Plex Mono",monospace; font-size:.82rem}
.meta-table td{padding:7px 0; border-bottom:1px solid var(--line)}
.tags{display:flex; flex-wrap:wrap; gap:6px; margin:14px 0 0}
.tag{font:.74rem/1 "IBM Plex Mono",monospace; color:var(--muted);
  background:#F1EFE6; border:1px solid var(--line); border-radius:999px; padding:5px 9px}

/* ---------- code block ---------- */
.code-block{margin:34px 0 0; border:1px solid var(--line-strong); border-radius:12px;
  overflow:hidden; box-shadow:var(--shadow); background:#1c1b1f}
.code-head{display:flex; align-items:center; justify-content:space-between;
  padding:10px 14px; background:#26242b; border-bottom:1px solid #34313b}
.filename{font-family:"IBM Plex Mono",monospace; font-size:.82rem; color:#cfc9d6}
.copy{font:500 .8rem "IBM Plex Mono",monospace; cursor:pointer; color:#1c1b1f;
  background:var(--otorange); border:none; padding:7px 13px; border-radius:6px; transition:.15s}
.copy:hover{filter:brightness(1.08)}
.copy.done{background:var(--otteal); color:#fff}
.code-block pre{margin:0; padding:18px 16px; overflow:auto; max-height:560px}
.code-block code{background:none; border:none; padding:0; color:#e9e6f0;
  font-family:"IBM Plex Mono",monospace; font-size:.82rem; line-height:1.65; white-space:pre}
.usage{margin:34px 0 0; max-width:70ch}
.usage h2{font-family:"Fraunces",serif; font-weight:600; font-size:1.4rem; margin:0 0 .4em}
.license-note{color:var(--muted); font-size:.92rem}

/* ---------- footer ---------- */
.site-footer{max-width:1180px; margin:40px auto 0; padding:24px 28px 50px;
  border-top:1px solid var(--line); display:flex; flex-wrap:wrap; gap:14px;
  justify-content:space-between; color:var(--muted); font-size:.86rem}
.site-footer .fw{font-family:"Fraunces",serif; font-weight:600; color:var(--ink)}

/* ---------- homepage sections (Icons / Templates / Examples) ---------- */
.group{max-width:1180px; margin:10px auto 0; padding:0 28px; scroll-margin-top:74px}
.group[hidden]{display:none}
.group-head{display:flex; align-items:baseline; gap:12px; padding:20px 0 10px;
  border-bottom:1px solid var(--line-strong)}
.group-head h2{margin:0; font-family:"Fraunces",serif; font-weight:600;
  font-size:1.55rem; letter-spacing:-.01em}
.group-count{font-family:"IBM Plex Mono",monospace; font-size:.82rem; color:var(--muted);
  background:#F1EFE6; border:1px solid var(--line); border-radius:999px; padding:3px 9px}
.group .grid{max-width:none; margin:0; padding:18px 0 6px}

/* ---------- companion skill (template pages) ---------- */
.skill{margin:36px 0 0}
.skill-head{display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:12px}
.skill-head h2{margin:0; font-family:"Fraunces",serif; font-weight:600; font-size:1.4rem}
.skill-head h2 span{font-family:"IBM Plex Sans",sans-serif; font-weight:400;
  font-size:.82rem; color:var(--muted)}
.skill-body{background:#fff; border:1px solid var(--line-strong); border-radius:12px;
  box-shadow:var(--shadow)}
.skill-body>summary{cursor:pointer; padding:14px 16px; list-style:none;
  font-family:"IBM Plex Mono",monospace; font-size:.86rem; color:var(--otblue)}
.skill-body>summary::-webkit-details-marker{display:none}
.skill-body>summary::before{content:"▸ "; color:var(--otorange)}
.skill-body[open]>summary{border-bottom:1px solid var(--line)}
.skill-body[open]>summary::before{content:"▾ "}
.md{padding:8px 22px 22px; max-width:74ch}
.md h2,.md h3,.md h4{font-family:"Fraunces",serif; font-weight:600; letter-spacing:-.01em;
  margin:1.1em 0 .35em}
.md h2{font-size:1.25rem} .md h3{font-size:1.08rem} .md h4{font-size:.98rem}
.md p{margin:.5em 0}
.md ul,.md ol{padding-left:1.3em; margin:.5em 0}
.md li{margin:.2em 0}
.md a{color:var(--otblue)}
.md blockquote{border-left:3px solid var(--otorange); background:#FFF8EC;
  margin:.8em 0; padding:9px 13px; border-radius:6px; color:#5b5341; font-size:.92rem}
.md pre.md-code{background:#1c1b1f; border-radius:8px; padding:13px 14px; overflow:auto; margin:.7em 0}
.md pre.md-code code{background:none; border:none; padding:0; color:#e9e6f0;
  font-family:"IBM Plex Mono",monospace; font-size:.8rem; line-height:1.6; white-space:pre}

@media(max-width:720px){
  .item-top{grid-template-columns:1fr; gap:22px}
  .group{padding:0 18px}
  .nav-inner{padding:10px 18px; gap:10px}
  .nav-links{margin-left:0; width:100%; gap:2px; overflow-x:auto; -webkit-overflow-scrolling:touch}
  .nav-links a{padding:6px 9px; font-size:.86rem}
  .hero{padding:34px 20px 8px}
}
"""

APP_JS = r"""(function () {
  // ---- search + filter (index page) ----
  var catalogEl = document.getElementById('catalog');
  var gallery = document.getElementById('gallery');
  if (catalogEl && gallery) {
    var data = JSON.parse(catalogEl.textContent);
    var cards = Array.prototype.slice.call(gallery.querySelectorAll('.card'));
    var groups = Array.prototype.slice.call(gallery.querySelectorAll('.group'));
    var byId = {};
    cards.forEach(function (c) { byId[c.getAttribute('data-id')] = c; });
    var searchEl = document.getElementById('search');
    var countEl = document.getElementById('count');
    var emptyEl = document.getElementById('empty');
    var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
    var activeType = 'all';

    var fuse = window.Fuse ? new window.Fuse(data, {
      includeScore: true, threshold: 0.38, ignoreLocation: true,
      keys: [
        { name: 'name', weight: 3 }, { name: 'tags', weight: 2 },
        { name: 'domain', weight: 1.5 }, { name: 'id', weight: 1 },
        { name: 'description', weight: 1 }
      ]
    }) : null;

    function apply() {
      var q = (searchEl.value || '').trim();
      var rank = {};
      var matched = null;          // null = no query (show all)
      if (q && fuse) {
        matched = {};
        fuse.search(q).forEach(function (r, i) { matched[r.item.id] = true; rank[r.item.id] = i; });
      }
      var shown = 0;
      cards.forEach(function (c) {
        var id = c.getAttribute('data-id');
        var typeOk = activeType === 'all' || c.getAttribute('data-type') === activeType;
        var searchOk = !matched || matched[id];
        if (typeOk && searchOk) {
          c.style.display = '';
          c.style.order = (id in rank) ? rank[id] : 0;
          shown++;
        } else {
          c.style.display = 'none';
        }
      });
      // hide a section when it has no visible cards (or is filtered out by type)
      groups.forEach(function (g) {
        var vis = g.querySelectorAll('.card:not([style*="display: none"])').length;
        g.hidden = vis === 0;
        var cnt = g.querySelector('[data-count]');
        if (cnt) cnt.textContent = vis;
      });
      if (countEl) countEl.textContent = shown + (shown === 1 ? ' resource' : ' resources');
      if (emptyEl) emptyEl.hidden = shown !== 0;
    }

    if (searchEl) searchEl.addEventListener('input', apply);
    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        chips.forEach(function (x) { x.classList.remove('active'); });
        chip.classList.add('active');
        activeType = chip.getAttribute('data-type');
        apply();
      });
    });
    apply();

    // ---- active-section highlight in the nav ----
    var navLinks = Array.prototype.slice.call(document.querySelectorAll('.nav-links a[data-nav]'));
    if (navLinks.length && 'IntersectionObserver' in window) {
      var navMap = {};
      navLinks.forEach(function (a) { navMap[a.getAttribute('data-nav')] = a; });
      var obs = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting && navMap[en.target.id]) {
            navLinks.forEach(function (a) { a.classList.remove('active'); });
            navMap[en.target.id].classList.add('active');
          }
        });
      }, { rootMargin: '-45% 0px -50% 0px' });
      groups.forEach(function (g) { obs.observe(g); });
    }
  }

  // ---- keyboard: '/' focuses search, Esc clears + blurs ----
  document.addEventListener('keydown', function (e) {
    var s = document.getElementById('search');
    if (!s) return;
    var t = e.target || {};
    var typing = /^(input|textarea|select)$/i.test(t.tagName || '') || t.isContentEditable;
    if (e.key === '/' && !typing) {
      e.preventDefault();
      s.focus();
    } else if (e.key === 'Escape' && document.activeElement === s) {
      s.value = '';
      s.dispatchEvent(new Event('input'));
      s.blur();
    }
  });

  // ---- copy-to-clipboard (item page) ----
  document.querySelectorAll('.copy').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var el = document.getElementById(btn.getAttribute('data-target'));
      if (!el) return;
      navigator.clipboard.writeText(el.textContent).then(function () {
        var old = btn.textContent;
        btn.textContent = 'Copied ✓';
        btn.classList.add('done');
        setTimeout(function () { btn.textContent = old; btn.classList.remove('done'); }, 1600);
      });
    });
  });
})();
"""


if __name__ == "__main__":
    raise SystemExit(build(repo_root()))
