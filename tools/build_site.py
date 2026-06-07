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


def masthead(home_href: str, *, compact: bool = False) -> str:
    cls = "masthead compact" if compact else "masthead"
    return f"""<header class="{cls}">
  <a class="wordmark" href="{home_href}">Open<span class="tik">TikZ</span><span class="caret">┃</span></a>
  <p class="tagline">{html.escape(TAGLINE)}</p>
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


def item_page(item: dict, code: str, tex_name: str, css_href: str) -> str:
    name = html.escape(item["name"])
    desc = html.escape(item.get("description", ""))
    preview = f"../previews/{item['id']}.svg"
    is_template = item["type"] == "template"
    skill_note = ""
    if is_template:
        skill_note = (
            '<p class="skill-note">This template ships a companion '
            '<strong>skill</strong> (<code>skill.md</code>) so an AI agent can edit it '
            'reliably — add/remove parts, recolor, change counts, adapt to a column width.</p>'
        )
    return (
        head(f"{item['name']} — OpenTikZ", css_href, description=item.get("description", TAGLINE))
        + masthead("../index.html", compact=True)
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

    cards = "".join(
        card(it, f"previews/{it['id']}.svg", f"item/{it['id']}.html", i)
        for i, it in enumerate(items)
    )
    chips = ['<button class="chip active" data-type="all">all</button>']
    for t in ("icon", "template", "example"):
        if counts.get(t):
            chips.append(f'<button class="chip" data-type="{t}">{TYPE_LABEL[t]}s · {counts[t]}</button>')
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
        + masthead("index.html")
        + f"""<section class="hero">
  <p class="lede">{html.escape(LEDE)}</p>
  <p class="stats">
    <span><b>{counts.get('icon', 0)}</b> icons</span>
    <span><b>{counts.get('template', 0)}</b> templates</span>
    <span><b>{counts.get('example', 0)}</b> examples</span>
  </p>
</section>

<section class="controls">
  <div class="search-wrap">
    <input id="search" type="search" placeholder="Search icons, templates, tags…" autocomplete="off" aria-label="Search resources">
  </div>
  <div class="chips" id="chips">
      {chips_html}
  </div>
  <p class="result-count" id="count"></p>
</section>

<main id="gallery" class="grid">
{cards}</main>
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
        (site / "item" / f"{it['id']}.html").write_text(
            item_page(it, code, tex_name, "../assets/style.css"), encoding="utf-8"
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

/* ---------- masthead ---------- */
.masthead{max-width:1180px; margin:0 auto; padding:48px 28px 22px; border-bottom:1px solid var(--line)}
.masthead.compact{padding:26px 28px 18px}
.wordmark{
  display:inline-block; text-decoration:none; font-family:"Fraunces",serif;
  font-weight:900; font-size:clamp(34px,6vw,58px); letter-spacing:-.02em; line-height:1;
}
.masthead.compact .wordmark{font-size:30px}
.wordmark .tik{color:var(--otblue)}
.wordmark .caret{color:var(--otorange); animation:blink 1.2s steps(1) infinite; margin-left:.04em}
@keyframes blink{50%{opacity:0}}
.tagline{margin:.5em 0 0; color:var(--muted); font-size:1.02rem}
.masthead.compact .tagline{font-size:.9rem}

/* ---------- hero ---------- */
.hero{max-width:1180px; margin:0 auto; padding:30px 28px 8px}
.hero .lede{font-size:clamp(1.05rem,2.2vw,1.4rem); max-width:54ch; margin:.2em 0 .8em;
  font-family:"Fraunces",serif; font-weight:400; color:#34322b}
.stats{display:flex; gap:26px; color:var(--muted); font-size:.95rem; margin:0}
.stats b{font-variant-numeric:tabular-nums; color:var(--otblue); font-weight:600}

/* ---------- controls ---------- */
.controls{max-width:1180px; margin:0 auto; padding:18px 28px 6px;
  position:sticky; top:0; background:linear-gradient(var(--paper) 78%,transparent);
  z-index:5; backdrop-filter:blur(2px)}
.search-wrap{position:relative}
#search{
  width:100%; padding:14px 16px 14px 42px; font:inherit; color:var(--ink);
  background:#fff; border:1.5px solid var(--line-strong); border-radius:10px;
  transition:border-color .15s, box-shadow .15s;
}
#search::placeholder{color:#A6A294}
#search:focus{outline:none; border-color:var(--otblue);
  box-shadow:0 0 0 4px rgba(0,114,178,.12)}
.search-wrap::before{content:"\\2315"; position:absolute; left:15px; top:50%;
  transform:translateY(-50%) rotate(-12deg); color:#A6A294; font-size:1.1rem}
.chips{display:flex; flex-wrap:wrap; gap:8px; margin-top:12px}
.chip{
  font:500 .85rem/1 "IBM Plex Mono",monospace; padding:7px 13px; cursor:pointer;
  background:#fff; color:var(--muted); border:1.5px solid var(--line-strong);
  border-radius:999px; transition:.15s;
}
.chip:hover{border-color:var(--otblue); color:var(--ink)}
.chip.active{background:var(--ink); color:var(--paper); border-color:var(--ink)}
.result-count{color:var(--muted); font-size:.82rem; margin:12px 2px 0;
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

@media(max-width:720px){
  .item-top{grid-template-columns:1fr; gap:22px}
  .controls{position:static}
}
"""

APP_JS = r"""(function () {
  // ---- search + filter (index page) ----
  var catalogEl = document.getElementById('catalog');
  var gallery = document.getElementById('gallery');
  if (catalogEl && gallery) {
    var data = JSON.parse(catalogEl.textContent);
    var cards = Array.prototype.slice.call(gallery.querySelectorAll('.card'));
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
      var order = null;
      if (q && fuse) {
        order = fuse.search(q).map(function (r) { return r.item.id; });
      }
      var shown = 0;
      cards.forEach(function (c) { c.style.display = 'none'; });
      var list = order || data.map(function (d) { return d.id; });
      list.forEach(function (id, i) {
        var c = byId[id];
        if (!c) return;
        if (activeType !== 'all' && c.getAttribute('data-type') !== activeType) return;
        c.style.display = '';
        c.style.order = i;
        shown++;
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
  }

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
