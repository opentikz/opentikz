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
LEDE = ("Copyable icons, editable architecture templates, and one AI-editable skill "
        "— so researchers produce paper figures fast without writing TikZ from scratch.")

TYPE_ORDER = {"icon": 0, "template": 1, "example": 2, "skill": 3}
TYPE_LABEL = {"icon": "icon", "template": "template", "example": "example", "skill": "skill"}


def find_tex(item_dir: Path) -> Path | None:
    texs = sorted(item_dir.glob("*.tex"))
    return texs[0] if texs else None


def json_for_script(obj) -> str:
    """Serialize JSON safe to embed inside an inline <script> element.

    Neutralizes ``<``, ``>``, ``&`` (so contributor-supplied name/description/tags
    containing ``</script>`` or ``<!--`` cannot break out of the element — a
    stored-XSS vector) and the U+2028/U+2029 line separators that are valid in
    JSON but not in JS string literals. The result is still valid JSON for
    ``JSON.parse``.
    """
    return (
        json.dumps(obj, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace(" ", "\\u2028")
        .replace(" ", "\\u2029")
    )


# --------------------------------------------------------------------------- #
#  HTML fragments
# --------------------------------------------------------------------------- #
REPO_URL = "https://github.com/opentikz/opentikz"

# Inline SVG glyphs for the download/copy button bar (currentColor → inherit button color).
DL_ICON = ('<svg class="dl-ic" width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">'
           '<path d="M8 1.5v8m0 0L4.8 6.3M8 9.5l3.2-3.2M2.5 13.5h11" fill="none" '
           'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
           'stroke-linejoin="round"/></svg>')
COPY_ICON = ('<svg class="dl-ic" width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">'
             '<rect x="5" y="5" width="9" height="9" rx="1.6" fill="none" stroke="currentColor" '
             'stroke-width="1.6"/><path d="M11 5V3.2A1.2 1.2 0 0 0 9.8 2H3.2A1.2 1.2 0 0 0 2 3.2'
             'v6.6A1.2 1.2 0 0 0 3.2 11H5" fill="none" stroke="currentColor" stroke-width="1.6" '
             'stroke-linecap="round" stroke-linejoin="round"/></svg>')


def head(title: str, css_href: str, *, description: str = TAGLINE, browse_href: str = "") -> str:
    """``browse_href`` lets the '/' shortcut jump to Browse from surfaces that
    have no search input (Home, item pages); empty on Browse (focuses inline)."""
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
<body data-browse="{browse_href}">
<div class="grid-bg" aria-hidden="true"></div>
"""


def navbar(surface: str) -> str:
    """Shared sticky header — identical on every surface except active state and
    relative hrefs. surface in {home, browse, item, skills}."""
    if surface == "home":
        home, browse, sec, skills = "index.html", "browse/", "browse/", "skills/"
    elif surface == "browse":
        home, browse, sec, skills = "../index.html", "index.html", "", "../skills/"
    elif surface == "skills":
        home, browse, sec, skills = "../index.html", "../browse/", "../browse/", "index.html"
    else:  # item
        home, browse, sec, skills = "../index.html", "../browse/", "../browse/", "../skills/"
    browse_active = " active" if surface in ("browse", "item") else ""
    skills_active = " active" if surface == "skills" else ""
    return f"""<header class="navbar">
  <div class="nav-inner">
    <a class="wordmark" href="{home}">Open<span class="tik">TikZ</span><span class="caret">┃</span></a>
    <input type="checkbox" id="nav-toggle" class="nav-toggle" hidden>
    <label class="nav-burger" for="nav-toggle" aria-label="Toggle navigation menu">
      <span></span><span></span><span></span>
    </label>
    <nav class="nav-links">
      <a class="nav-browse{browse_active}" href="{browse}" data-nav="browse">Browse</a>
      <a href="{sec}#icons" data-nav="icons">Icons</a>
      <a href="{sec}#templates" data-nav="templates">Templates</a>
      <a href="{sec}#examples" data-nav="examples">Examples</a>
      <a class="nav-skills{skills_active}" href="{skills}" data-nav="skills">Skills</a>
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


def edit_contract_html(contract: dict, skills_href: str) -> str:
    """Render a template's edit_contract as a compact, read-only 'how to edit'
    block (parameters + operations), with a pointer to the one repo-wide skill."""
    params = ""
    for p in contract.get("parameters", []):
        meaning = html.escape(p.get("meaning", ""))
        if p.get("default"):
            meaning += f' <span class="param-def">default <code>{html.escape(p["default"])}</code></span>'
        params += (
            f"<tr><td><code>{html.escape(p.get('name', ''))}</code></td>"
            f"<td>{meaning}</td></tr>"
        )
    ops = "".join(
        f"<li><code>{html.escape(o.get('id', ''))}</code> — {html.escape(o.get('summary', ''))}</li>"
        for o in contract.get("operations", [])
    )
    naming = html.escape(contract.get("node_naming", ""))
    return f"""
  <section class="skill">
    <div class="skill-head">
      <h2>Edit contract <span>— how the AI edits this template</span></h2>
      <a class="skill-link-inline" href="{skills_href}">using-opentikz skill →</a>
    </div>
    <details class="skill-body" open>
      <summary>Parameters &amp; safe edit operations</summary>
      <div class="md">
        <h3>Parameters</h3>
        <table class="contract-params">{params}</table>
        <h3>Node naming</h3>
        <p><code>{naming}</code></p>
        <h3>Operations</h3>
        <ul>{ops}</ul>
      </div>
    </details>
  </section>
"""


def item_page(item: dict, code: str, tex_name: str, css_href: str) -> str:
    name = html.escape(item["name"])
    desc = html.escape(item.get("description", ""))
    preview = f"../previews/{item['id']}.svg"
    is_template = item["type"] == "template"
    contract = item.get("edit_contract")
    skill_note = ""
    skill_section = ""
    if is_template and contract:
        skill_note = (
            '<p class="skill-note">This template ships an <strong>edit contract</strong> '
            '(in its <code>meta.json</code>) that the repo-wide '
            '<a href="../skills/">using-opentikz</a> skill reads to edit it reliably — '
            'the parameters and safe operations are listed below.</p>'
        )
        skill_section = edit_contract_html(contract, "../skills/")
    return (
        head(f"{item['name']} — OpenTikZ", css_href,
             description=item.get("description", TAGLINE), browse_href="../browse/")
        + navbar("item")
        + f"""<main class="item">
  <a class="back" href="../browse/">← browse the library</a>
  <div class="item-top">
    <div class="item-canvas"><img src="{preview}" alt="{name} preview"></div>
    <div class="item-head">
      {badge(item['type'])}
      <h1>{name}</h1>
      <p class="lede">{desc}</p>
      {skill_note}
      {metadata_table(item)}
      <p class="tags">{tag_list(item.get('tags', []))}</p>
      <div class="downloads">
        <button class="dl-btn dl-primary dl-copy" data-target="src">{COPY_ICON}Copy .tex</button>
        <button class="dl-btn" data-tex="src" data-name="{html.escape(tex_name)}">{DL_ICON}.tex</button>
        <a class="dl-btn" href="{preview}" download="{item['id']}.svg">{DL_ICON}SVG</a>
        <button class="dl-btn" data-png="{preview}" data-name="{item['id']}.png">{DL_ICON}PNG</button>
      </div>
    </div>
  </div>

  <details class="code-block">
    <summary class="code-head">
      <span class="filename">{html.escape(tex_name)}</span>
      <span class="code-toggle" aria-hidden="true"></span>
    </summary>
    <div class="code-body">
      <button class="copy code-copy" data-target="src">Copy .tex</button>
      <pre><code id="src">{html.escape(code)}</code></pre>
    </div>
  </details>
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


SECTION_TITLES = {"icon": "Icons", "template": "Templates", "example": "Examples"}


def demos_carousel(demos: list[dict], by_id: dict, prefix: str = "") -> str:
    """Skills-in-action carousel; one slide per capability dimension. Empty -> ''.
    ``prefix`` adjusts the demos/ path for the surface depth ('' Home, '../' skills)."""
    if not demos:
        return ""
    slides, dots = "", ""
    for i, g in enumerate(demos):
        tmpl = by_id.get(g.get("template_id"), {})
        tname = html.escape(tmpl.get("name", g.get("template_id", "")))
        dim = html.escape(g.get("dimension_label", g.get("dimension", "")))
        prompt = html.escape(g.get("prompt", ""))
        active = " active" if i == 0 else ""
        changed = (f'<p class="demo-changed">{html.escape(g["changed"])}</p>'
                   if g.get("changed") else "")
        slides += f"""      <div class="demo-slide{active}" data-slide="{i}">
        <div class="demo-head"><span class="demo-dim">{dim}</span><span class="demo-tmpl">on {tname}</span></div>
        <div class="demo-trip">
          <figure class="demo-fig"><img src="{prefix}demos/{html.escape(g['before_svg'])}" alt="before" loading="lazy"><figcaption>before</figcaption></figure>
          <div class="demo-prompt"><span class="demo-prompt-label">prompt</span><code>&ldquo;{prompt}&rdquo;</code></div>
          <figure class="demo-fig"><img src="{prefix}demos/{html.escape(g['after_svg'])}" alt="after" loading="lazy"><figcaption>after</figcaption></figure>
        </div>
        {changed}
      </div>
"""
        dots += f'<button class="demo-dot{active}" data-dot="{i}" aria-label="{dim}"><span>{dim}</span></button>'
    return f"""
  <section class="skills-demo">
    <h2>See it on real templates</h2>
    <p class="skills-sub">Every before/after is rendered from committed source — the same kind of edit, across different templates.</p>
    <div class="carousel skills-carousel" id="skills-carousel" tabindex="0" data-autoplay data-interval="5000" aria-roledescription="carousel" aria-label="Skills in action">
      <button class="car-nav car-prev" aria-label="Previous">←</button>
      <div class="car-track">
{slides}      </div>
      <button class="car-nav car-next" aria-label="Next">→</button>
    </div>
    <div class="car-dots">{dots}</div>
  </section>
"""


def before_after_slider(before_svg: str, after_svg: str, *,
                        before_label: str = "before", after_label: str = "after",
                        prefix: str = "") -> str:
    """Draggable before/after compare slider. ``before_svg``/``after_svg`` are
    filenames under demos/; ``prefix`` adjusts depth ('' on Home). Built on a
    native range input (keyboard + no-JS fallback at 50%); app.js adds pointer
    drag. The after image is revealed to the RIGHT of the bar."""
    b, a = html.escape(before_svg), html.escape(after_svg)
    bl, al = html.escape(before_label), html.escape(after_label)
    return f"""    <div class="ba" data-ba style="--pos:50%">
      <img class="ba-img ba-before-img" src="{prefix}demos/{b}" alt="{bl}" loading="lazy">
      <img class="ba-img ba-after-img" src="{prefix}demos/{a}" alt="{al}" loading="lazy">
      <span class="ba-tag ba-tag-l" aria-hidden="true">{bl}</span>
      <span class="ba-tag ba-tag-r" aria-hidden="true">{al}</span>
      <span class="ba-bar" aria-hidden="true"></span>
      <span class="ba-handle" aria-hidden="true">&#8646;</span>
      <input class="ba-range" type="range" min="0" max="100" value="50"
             aria-label="Compare {bl} and {al}">
    </div>
"""


def magic_moment(demos: list[dict], by_id: dict, prefix: str = "") -> str:
    """The 'how it works' centerpiece: prompt -> editable TikZ -> rendered figure.
    Uses the demo flagged ``featured`` (fallback: first demo). Empty -> ''.
    ``prefix`` adjusts the demos/ path for surface depth ('' Home)."""
    if not demos:
        return ""
    demo = next((d for d in demos if d.get("featured")), demos[0])
    tmpl = by_id.get(demo.get("template_id"), {})
    tname = html.escape(tmpl.get("name", demo.get("template_id", "")))
    prompt = html.escape(demo.get("prompt", ""))
    after = html.escape(demo.get("after_svg", ""))
    # Render the excerpt line-by-line; a leading '+' marks an AI-added line.
    code_lines = ""
    for raw in demo.get("tex_excerpt", "").split("\n"):
        added = raw.startswith("+")
        text = html.escape(raw[1:].rstrip() if added else raw.rstrip())
        cls = " ml-add" if added else ""
        code_lines += f'<span class="ml-line{cls}">{text or "&nbsp;"}</span>\n'
    return f"""
  <section class="how magic" id="how">
    <h2>How it works</h2>
    <p class="magic-sub">Tell your AI agent what you want. It edits a real template &mdash; and you get TikZ that compiles.</p>
    <div class="magic-card">
      <div class="magic-prompt"><span class="magic-label">you type</span><code>&ldquo;{prompt}&rdquo;</code></div>
      <div class="magic-body">
        <div class="magic-pane">
          <span class="magic-label">editable TikZ <em>on {tname}</em></span>
          <pre class="magic-code">{code_lines}</pre>
        </div>
        <div class="magic-pane">
          <span class="magic-label">renders to</span>
          <figure class="magic-fig"><img src="{prefix}demos/{after}" alt="rendered figure after the edit" loading="lazy"></figure>
        </div>
      </div>
    </div>
  </section>
"""


def why_tikz_band() -> str:
    """Beat 1: why a TikZ figure (source, not an image) beats a raster screenshot."""
    return r"""
  <section class="why-tikz">
    <h2>Why TikZ</h2>
    <div class="why-grid">
      <article class="why-card">
        <h3>Vector quality</h3>
        <p>Crisp at any zoom, sharp in print and on screen &mdash; no pixelated screenshots, no re-exporting at 300&nbsp;dpi.</p>
      </article>
      <article class="why-card">
        <h3>Native to your paper</h3>
        <p>Same fonts, math (<code>$\mathbf{W}x$</code>), and <code>\ref</code>/<code>\cite</code> as the document. The figure looks part of the paper, not pasted on top.</p>
      </article>
      <article class="why-card">
        <h3>Text, so it's diffable</h3>
        <p>It's source, not a binary. Version it in git, tweak one number, recompile &mdash; review the change in a pull request.</p>
      </article>
    </div>
  </section>
"""


def why_opentikz_band() -> str:
    """Beat 3: why an edit anchored to a real template beats raw LLM TikZ."""
    return """
  <section class="why-ot">
    <h2>Why not just ask ChatGPT for TikZ?</h2>
    <p class="why-ot-sub">You can &mdash; here's what changes when the edit is anchored to a real template.</p>
    <div class="cmp-cards">
      <article class="cmp-card cmp-bad">
        <h3>Raw LLM TikZ</h3>
        <ul>
          <li>Often won't compile on the first try</li>
          <li>Invents packages and macros that don't exist</li>
          <li>Picks random hex colors, inconsistent across figures</li>
          <li>No stable structure &mdash; re-editing means re-describing everything</li>
          <li>You burn time on compile-error round-trips</li>
        </ul>
      </article>
      <article class="cmp-card cmp-good">
        <h3>OpenTikZ + skill</h3>
        <ul>
          <li>Compiles standalone, first try</li>
          <li>Starts from a real, parametric template</li>
          <li>Shared palette &mdash; colors stay consistent</li>
          <li>Stable node names, so the next edit is precise</li>
          <li>An <code>edit_contract</code> tells the agent exactly how to change it</li>
        </ul>
      </article>
    </div>
  </section>
"""


def home_page(featured: list[dict], by_id: dict, counts: dict, demos: list[dict], css_href: str) -> str:
    """Marketing Home — no content grid, no search box (per spec)."""
    demos_section = demos_carousel(demos, by_id)
    magic = magic_moment(demos, by_id)
    why_tikz = why_tikz_band()
    why_opentikz = why_opentikz_band()

    # Hero carousel: one featured figure per slide (flagship first). Each slide is a
    # zoomable figure + caption (name deep-links to the item page). DISTINCT id and
    # slide/dot classes (#hero-carousel / .hero-slide / .hero-dot) so it never shares
    # state with the skills-in-action carousel (#skills-carousel / .demo-slide / .demo-dot).
    hero_slides, hero_dots = "", ""
    for i, it in enumerate(featured):
        name = html.escape(it["name"])
        active = " active" if i == 0 else ""
        hero_slides += f"""        <div class="hero-slide{active}" data-slide="{i}" data-id="{html.escape(it['id'])}" data-name="{name}">
          <figure class="hero-fig">
            <button class="hero-zoom" type="button" data-zoom="{i}" aria-label="Enlarge {name}">
              <img src="previews/{it['id']}.svg" alt="{name}" loading="lazy">
              <span class="zoom-hint" aria-hidden="true">&#128269; click to enlarge</span>
            </button>
            <figcaption class="hero-cap">{badge(it['type'])}<a href="item/{it['id']}.html">{name}</a></figcaption>
          </figure>
        </div>
"""
        hero_dots += f'<button class="hero-dot{active}" data-dot="{i}" aria-label="Show {name}"></button>'

    # Lightbox modal, emitted once. The figure is filled in by app.js from the
    # featured slides (same ordered list as the hero carousel).
    lightbox = """  <div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Figure viewer" aria-hidden="true" hidden>
    <div class="lb-backdrop" data-lb-close></div>
    <div class="lb-panel" role="document">
      <button class="lb-nav lb-prev" type="button" aria-label="Previous figure">&larr;</button>
      <figure class="lb-fig">
        <img id="lb-img" src="" alt="">
        <figcaption class="lb-cap"><span id="lb-badge"></span><a id="lb-link" href="#"></a></figcaption>
      </figure>
      <button class="lb-nav lb-next" type="button" aria-label="Next figure">&rarr;</button>
      <button class="lb-close" type="button" aria-label="Close" data-lb-close>&times;</button>
    </div>
  </div>
"""

    return (
        head("OpenTikZ — paper-ready TikZ figures from a copyable library", css_href,
             description=("Paper-ready conceptual TikZ figures — simple and fast: copyable icons, "
                          "editable templates, and one AI-editable skill."),
             browse_href="browse/")
        + navbar("home")
        + f"""<main class="home">
  <section class="showcase">
    <a class="hero-logo" href="index.html" aria-label="OpenTikZ home">Open<span class="tik">TikZ</span><span class="caret">┃</span></a>
    <h1>Paper-ready figures &mdash; simple and fast.</h1>
    <p class="show-lede">Copyable icons, editable templates, and one AI-editable <em>skill</em>.</p>
    <div class="carousel hero-carousel" id="hero-carousel" tabindex="0" data-autoplay data-interval="5000" aria-roledescription="carousel" aria-label="Featured figures">
      <button class="car-nav car-prev" type="button" aria-label="Previous figure">&larr;</button>
      <div class="car-track">
{hero_slides}      </div>
      <button class="car-nav car-next" type="button" aria-label="Next figure">&rarr;</button>
    </div>
    <div class="car-dots hero-dots">{hero_dots}</div>
    <div class="cta-row">
      <a class="btn btn-primary" href="browse/">Browse the library →</a>
      <a class="btn btn-ghost" href="#how">See how it's built</a>
    </div>
  </section>
{lightbox}
{why_tikz}
{magic}
{why_opentikz}
{demos_section}
  <section class="roadmap">
    <h2>On the roadmap</h2>
    <div class="roadmap-cards">
      <article class="rm-card">
        <span class="rm-tag">in development · next release</span>
        <h3>Prompt-to-diagram <span>natural language → TikZ</span></h3>
        <p>Describe the figure you want; get editable TikZ you can drop straight into
           the library — assembled from templates and skills.</p>
      </article>
      <article class="rm-card">
        <span class="rm-tag">in development · next release</span>
        <h3>Graph-to-diagram <span>graph / spec → TikZ</span></h3>
        <p>Give a node–edge spec (JSON · DOT · adjacency); get a laid-out, editable
           figure you can refine like any template.</p>
      </article>
    </div>
  </section>

  <section class="cta-band">
    <h2>Build your next figure faster.</h2>
    <a class="btn btn-primary" href="browse/">Browse the library →</a>
    <p class="cta-sub">{counts.get('icon', 0)} icons · {counts.get('template', 0)} templates · {counts.get('example', 0)} examples · content <code>CC0&nbsp;1.0</code></p>
  </section>
</main>
"""
        + footer()
        + f'<script src="{css_href.replace("style.css", "app.js")}"></script>\n'
        + "</body>\n</html>\n"
    )


def browse_page(items: list[dict], css_href: str) -> str:
    """Tool surface under /browse/ — sectioned grid + Fuse search."""
    counts = {"icon": 0, "template": 0, "example": 0}
    for it in items:
        counts[it["type"]] = counts.get(it["type"], 0) + 1

    groups_html = ""
    idx = 0
    for t in ("icon", "template", "example"):
        members = [it for it in items if it["type"] == t]
        if not members:
            continue
        cards = ""
        for it in members:
            cards += card(it, f"../previews/{it['id']}.svg", f"../item/{it['id']}.html", idx)
            idx += 1
        groups_html += f"""  <section class="group" id="{t}s" data-group="{t}">
    <div class="group-head">
      <h2>{SECTION_TITLES[t]}</h2>
      <span class="group-count" data-count>{len(members)}</span>
    </div>
    <div class="grid">
{cards}    </div>
  </section>
"""

    chips = ['<button class="chip active" data-type="all">all</button>']
    for t in ("icon", "template", "example"):
        if counts.get(t):
            chips.append(f'<button class="chip" data-type="{t}">{SECTION_TITLES[t].lower()} · {counts[t]}</button>')
    chips_html = "\n      ".join(chips)

    # Embedded in an inline <script> below — must be HTML-script-safe so a
    # contributor's name/description/tags can't break out of the element.
    search_index = json_for_script(
        [
            {"id": it["id"], "name": it["name"], "type": it["type"],
             "domain": it.get("domain", []), "tags": it.get("tags", []),
             "description": it.get("description", "")}
            for it in items
        ]
    )

    return (
        head("Browse — OpenTikZ", css_href, browse_href="")
        + navbar("browse")
        + f"""<section class="hero hero-browse">
  <h1 class="browse-title">Browse the library</h1>
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


def skills_page(demos: list[dict], by_id: dict, css_href: str) -> str:
    """The Skills surface — explains how to use the one repo-wide skill and why it
    edits each figure accurately (the edit_contract), with the shared demo
    carousel and the cross-cutting reference material. It does NOT enumerate the
    editable templates — those are discovered by the agent in the catalog."""
    carousel = demos_carousel(demos, by_id, prefix="../")
    return (
        head("Skills — OpenTikZ", css_href,
             description=("One repo-wide skill lets an AI edit OpenTikZ figures precisely — "
                          "ask in plain language, it edits via each template's edit_contract and verifies."),
             browse_href="")
        + navbar("skills")
        + f"""<main class="skills-page">
  <section class="skills-intro">
    <h1>Edit figures with AI</h1>
    <p class="lede">OpenTikZ ships <strong>one</strong> skill,
      <a href="{REPO_URL}/blob/main/skills/using-opentikz/SKILL.md" target="_blank" rel="noopener"><code>using-opentikz</code></a>:
      it takes an AI agent from a plain-language request to a finished, compiling figure —
      and confirms the ambiguous details with you instead of guessing.</p>
  </section>
{carousel}
  <section class="skills-how">
    <h2>How to use it</h2>
    <p class="skills-index-sub">Point any agent that can read this repo (Claude Code, or an assistant with the files) at the skill, then just describe the change you want.</p>
    <ol class="skills-steps">
      <li><strong>Ask in plain language.</strong> &ldquo;Add a cross-attention layer to the encoder-decoder and make it blue&rdquo;, &ldquo;recolor the database orange&rdquo;, &ldquo;give the net one more hidden layer&rdquo;. No TikZ required.</li>
      <li><strong>The agent finds the figure.</strong> It matches your request against <code>catalog.json</code> and confirms which icon, template, or example to start from.</li>
      <li><strong>It edits, then verifies.</strong> It applies the change, keeps the figure parametric and palette-correct, and compiles the standalone <code>.tex</code> before handing it back — never an uncompiled guess.</li>
      <li><strong>You stay in control.</strong> On anything material it asks first; on safe defaults (palette, width) it proceeds and tells you what it assumed in one line.</li>
    </ol>
  </section>

  <section class="skills-why">
    <h2>Why it edits each figure accurately</h2>
    <p class="skills-index-sub">The skill doesn&rsquo;t hand-parse TikZ and hope. Every template ships a structured <code>edit_contract</code> in its <code>meta.json</code> that tells the agent exactly how that figure is built — so edits land on the right parts.</p>
    <div class="skill-links">
      <div class="skill-link">
        <h3>Named parameters</h3>
        <p>Counts, sizes, spacing, and labels are driven by a <code>\\def</code> block the contract enumerates — so &ldquo;one more layer&rdquo; is a parameter change, not a redraw.</p>
      </div>
      <div class="skill-link">
        <h3>Stable node names</h3>
        <p>A documented naming scheme (e.g. <code>L2-3</code>, <code>(enc)</code>) lets the agent target a specific part and attach new arrows without breaking the layout.</p>
      </div>
      <div class="skill-link">
        <h3>Safe operations &amp; invariants</h3>
        <p>The contract lists the edits that are known-safe (recolor, add/remove a part, resize) and the rules an edit must never break — guardrails against plausible-but-wrong changes.</p>
      </div>
      <div class="skill-link">
        <h3>One shared palette</h3>
        <p>Colors are five named palette entries, never inline hex — so a recolor stays consistent and colour-blind-friendly across the whole figure.</p>
      </div>
    </div>
  </section>

  <section class="skills-libwide">
    <h2>The shared conventions it draws on</h2>
    <p class="skills-index-sub">Beyond each template&rsquo;s contract, the skill applies the library&rsquo;s common conventions — so colour, annotations, and layout stay consistent across every figure it touches, not just the one you asked about. These are the references it works from:</p>
    <div class="skill-links">
      <a class="skill-link" href="{REPO_URL}/blob/main/reference/color-palettes/color-palettes.md" target="_blank" rel="noopener">
        <h3>Color palettes <span>&#8599;</span></h3>
        <p>The shared, colour-blind-friendly palette it recolors from (light + dark variants) — so a tweak never introduces an off-palette hex.</p>
      </a>
      <a class="skill-link" href="{REPO_URL}/blob/main/reference/annotations/annotations.md" target="_blank" rel="noopener">
        <h3>Annotations <span>&#8599;</span></h3>
        <p>The patterns it follows when adding labels, callout leaders, grouping braces, highlight boxes, and step badges — drawn consistently from the palette.</p>
      </a>
      <a class="skill-link" href="{REPO_URL}/blob/main/reference/layout/layout.md" target="_blank" rel="noopener">
        <h3>Layout <span>&#8599;</span></h3>
        <p>The placement rules it keeps to — relative positioning, alignment, even distribution, and fitting a figure to a paper column width.</p>
      </a>
    </div>
  </section>
</main>
"""
        + footer()
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
    (site / "browse").mkdir(parents=True)
    (site / "skills").mkdir(parents=True)
    (site / "previews").mkdir(parents=True)
    (site / "assets").mkdir(parents=True)

    (site / "assets" / "style.css").write_text(STYLE_CSS, encoding="utf-8")
    (site / "assets" / "app.js").write_text(APP_JS, encoding="utf-8")
    (site / ".nojekyll").write_text("", encoding="utf-8")
    # Custom domain for GitHub Pages. site/ is rebuilt from scratch each run, so
    # the CNAME must be (re)written here rather than committed under site/.
    (site / "CNAME").write_text("opentikz.org\n", encoding="utf-8")

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

    # Browse surface (the tool) under /browse/.
    (site / "browse" / "index.html").write_text(
        browse_page(catalog, "../assets/style.css"), encoding="utf-8")

    # Skills-in-action demos (optional, content-driven). Copy the committed
    # before/after SVGs into site/demos/; the section auto-hides if none exist.
    demos: list[dict] = []
    demos_json = root / "skills-demos" / "skills-demos.json"
    if demos_json.exists():
        demos = json.loads(demos_json.read_text(encoding="utf-8"))
        (site / "demos").mkdir(exist_ok=True)
        for g in demos:
            for key in ("before_svg", "after_svg"):
                src = root / "skills-demos" / g[key]
                if src.exists():
                    shutil.copyfile(src, site / "demos" / g[key])

    # Home surface (marketing). The hero showcase is examples-only: a flagship
    # paper-grade figure, never a bare icon/template. Prefer the example items
    # flagged featured (flagship first); fall back to all examples so the page
    # still builds before any flagship is flagged.
    by_id = {it["id"]: it for it in catalog}
    counts = {"icon": 0, "template": 0, "example": 0}
    for it in catalog:
        counts[it["type"]] = counts.get(it["type"], 0) + 1
    featured = [it for it in catalog if it.get("featured") and it["type"] == "example"]
    featured.sort(key=lambda it: (0 if "lora" in it["id"] else 1, it["name"].lower()))
    if not featured:
        featured = [it for it in catalog if it["type"] == "example"]
    (site / "index.html").write_text(
        home_page(featured, by_id, counts, demos, "assets/style.css"), encoding="utf-8")

    # Skills surface.
    (site / "skills" / "index.html").write_text(
        skills_page(demos, by_id, "../assets/style.css"), encoding="utf-8")

    print(f"built site/ — {len(catalog)} items, {n_prev} previews, "
          f"{len(catalog)+3} pages (home + browse + skills + items); "
          f"featured={len(featured)}, demos={len(demos)}")
    return 0


# --------------------------------------------------------------------------- #
#  Assets (kept here so the script is the single source of truth)
# --------------------------------------------------------------------------- #
STYLE_CSS = r""":root{
  --paper:#FBFAF6; --ink:#1B1A16; --muted:#6F6C61; --line:#E6E3D8; --line-strong:#D6D2C4;
  --otblue:#0072B2; --otorange:#E69F00; --otteal:#009E73; --otpurple:#A85C86; --otgray:#5A5A5A;
  --grid:rgba(0,114,178,.05);
  --shadow:0 1px 0 var(--line-strong), 0 18px 40px -28px rgba(27,26,22,.45);
  --maxw:1180px; --gutter:28px;   /* single source of truth for the layout container */
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
.nav-inner{max-width:var(--maxw); margin:0 auto; padding:11px var(--gutter);
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
/* hamburger toggle — hidden on desktop, shown at the mobile breakpoint */
.nav-toggle{display:none}
.nav-burger{display:none; width:42px; height:38px; flex:none; cursor:pointer; padding:0;
  border:1px solid var(--line); border-radius:9px; background:transparent;
  align-items:center; justify-content:center; flex-direction:column; gap:4px}
.nav-burger span{display:block; width:18px; height:2px; border-radius:2px; background:var(--ink);
  transition:transform .2s ease, opacity .2s ease}

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
  max-width:var(--maxw); margin:6px auto 0; padding:14px var(--gutter) 60px;
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
.item{max-width:var(--maxw); margin:0 auto; padding:8px var(--gutter) 70px}
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

/* ---------- downloads (bold action bar) ---------- */
.downloads{display:flex; flex-wrap:wrap; align-items:center; gap:10px; margin:22px 0 0}
.dl-btn{display:inline-flex; align-items:center; gap:7px; cursor:pointer; text-decoration:none;
  font:600 .9rem "IBM Plex Sans",sans-serif; color:var(--ink); background:#fff;
  border:1.5px solid var(--line-strong); border-radius:10px; padding:10px 16px;
  transition:transform .15s, box-shadow .15s, border-color .15s, color .15s}
.dl-btn .dl-ic{flex:none}
.dl-btn:hover{border-color:var(--otblue); color:var(--otblue); transform:translateY(-1px);
  box-shadow:0 8px 18px -12px rgba(0,114,178,.6)}
.dl-primary{background:var(--otblue); color:#fff; border-color:var(--otblue);
  box-shadow:0 10px 24px -12px rgba(0,114,178,.7)}
.dl-primary:hover{background:var(--otblue); color:#fff; filter:brightness(1.07)}
.dl-primary.done{background:var(--otteal); border-color:var(--otteal); color:#fff; filter:none}

/* ---------- code block (collapsed by default) ---------- */
.code-block{margin:34px 0 0; border:1px solid var(--line-strong); border-radius:12px;
  overflow:hidden; box-shadow:var(--shadow); background:#1c1b1f}
.code-head{display:flex; align-items:center; justify-content:space-between; cursor:pointer;
  padding:12px 16px; background:#26242b; list-style:none; user-select:none}
.code-head::-webkit-details-marker{display:none}
.code-block[open] .code-head{border-bottom:1px solid #34313b}
.filename{font-family:"IBM Plex Mono",monospace; font-size:.82rem; color:#cfc9d6}
.code-toggle{display:inline-flex; align-items:center; font:500 .8rem "IBM Plex Mono",monospace;
  color:var(--otorange)}
.code-toggle::before{content:"\25B8"; margin-right:7px}
.code-toggle::after{content:"View source"}
.code-block[open] .code-toggle{color:#cfc9d6}
.code-block[open] .code-toggle::before{content:"\25BE"}
.code-block[open] .code-toggle::after{content:"Hide source"}
.code-body{position:relative}
.code-copy{position:absolute; top:12px; right:14px; z-index:2}
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
.group{max-width:var(--maxw); margin:10px auto 0; padding:0 var(--gutter); scroll-margin-top:74px}
.group[hidden]{display:none}
.group-head{display:flex; align-items:baseline; gap:12px; padding:20px 0 10px;
  border-bottom:1px solid var(--line-strong)}
.group-head h2{margin:0; font-family:"Fraunces",serif; font-weight:600;
  font-size:1.55rem; letter-spacing:-.01em}
.group-count{font-family:"IBM Plex Mono",monospace; font-size:.82rem; color:var(--muted);
  background:#F1EFE6; border:1px solid var(--line); border-radius:999px; padding:3px 9px}
.group .grid{max-width:none; margin:0; padding:18px 0 6px}

/* ---------- edit contract (template pages) ---------- */
.skill{margin:36px 0 0}
.skill-head{display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:12px}
.skill-head h2{margin:0; font-family:"Fraunces",serif; font-weight:600; font-size:1.4rem}
.skill-head h2 span{font-family:"IBM Plex Sans",sans-serif; font-weight:400;
  font-size:.82rem; color:var(--muted)}
.skill-link-inline{font:500 .82rem "IBM Plex Mono",monospace; color:var(--otblue);
  text-decoration:none; white-space:nowrap}
.skill-link-inline:hover{text-decoration:underline}
.contract-params{width:100%; border-collapse:collapse; margin:.4em 0 .2em; font-size:.9rem}
.contract-params td{padding:6px 10px 6px 0; border-bottom:1px solid var(--line); vertical-align:top}
.contract-params td:first-child{width:34%; white-space:nowrap}
.param-def{color:var(--muted); font-size:.86em}
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

/* ---------- Home / marketing surface ---------- */
.home{max-width:var(--maxw); margin:0 auto; padding:0 var(--gutter)}

/* figure-led, centred hero — the figure is the largest element */
.showcase{max-width:880px; margin:0 auto; padding:50px 0 42px; text-align:center}
/* large brand lockup, centred above the headline (mirrors the navbar wordmark) */
.hero-logo{display:inline-block; text-decoration:none; font-family:"Fraunces",serif;
  font-weight:900; letter-spacing:-.025em; line-height:1; margin:0 0 .5em;
  font-size:clamp(2.6rem,7vw,4.6rem)}
.hero-logo .tik{color:var(--otblue)}
.hero-logo .caret{color:var(--otorange); animation:blink 1.2s steps(1) infinite; margin-left:.03em}
.showcase h1{font-family:"Fraunces",serif; font-weight:900; letter-spacing:-.025em;
  font-size:clamp(1.55rem,3.6vw,2.3rem); line-height:1.08; margin:0 0 .25em; color:#34322b}
.show-lede{font-family:"Fraunces",serif; font-weight:400; color:#34322b;
  font-size:clamp(1.05rem,2vw,1.3rem); max-width:48ch; margin:0 auto 1.5em}
.show-lede em{font-style:italic; color:var(--otblue)}
.cta-row{display:flex; flex-wrap:wrap; gap:12px; justify-content:center; margin-top:1.4em}
.btn{display:inline-block; text-decoration:none; font-weight:600; font-size:.98rem;
  padding:12px 20px; border-radius:10px; transition:.15s; border:1.5px solid transparent}
.btn-primary{background:var(--otblue); color:#fff; box-shadow:0 10px 24px -12px rgba(0,114,178,.7)}
.btn-primary:hover{filter:brightness(1.06); transform:translateY(-1px)}
.btn-ghost{border-color:var(--line-strong); color:var(--ink)}
.btn-ghost:hover{border-color:var(--otblue); color:var(--otblue)}

.how,.cta-band{padding:42px 0; border-top:1px solid var(--line)}
.how h2{font-family:"Fraunces",serif; font-weight:600;
  font-size:1.7rem; margin:0 0 20px; letter-spacing:-.01em}

/* hero figure carousel (Home) — one featured figure per slide, click to zoom */
.hero-carousel{margin:0 auto 1.1em; width:min(100%,860px); outline:none}
.hero-carousel:focus-visible{box-shadow:0 0 0 3px rgba(0,114,178,.22); border-radius:16px}
.hero-slide{display:none}
.hero-slide.active{display:block; animation:fade .25s both}
.hero-fig{margin:0}
.hero-zoom{display:block; width:100%; cursor:zoom-in; position:relative; padding:30px 30px 24px;
  border:1px solid var(--line); border-radius:14px; background:
    linear-gradient(rgba(0,0,0,.03) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,0,0,.03) 1px,transparent 1px) #fff;
  background-size:24px 24px; transition:border-color .15s, box-shadow .15s}
.hero-zoom:hover{border-color:var(--line-strong); box-shadow:var(--shadow)}
.hero-zoom:focus-visible{outline:2px solid var(--otblue); outline-offset:2px}
.hero-zoom img{display:block; width:100%; height:360px; object-fit:contain; margin:0 auto}
.zoom-hint{position:absolute; top:12px; right:12px; font:500 .72rem "IBM Plex Mono",monospace;
  color:var(--ink); background:rgba(255,255,255,.92); border:1px solid var(--line-strong);
  border-radius:999px; padding:5px 11px; box-shadow:var(--shadow); transition:opacity .15s}
.hero-cap{display:flex; align-items:center; justify-content:center; gap:10px; margin-top:14px}
.hero-cap a{font-family:"Fraunces",serif; font-weight:600; font-size:1.12rem; letter-spacing:-.01em;
  color:var(--ink); text-decoration:none}
.hero-cap a:hover{color:var(--otblue); text-decoration:underline}
.hero-dots{margin-top:14px}
.hero-dot{width:10px; height:10px; padding:0; cursor:pointer; border-radius:50%;
  background:#fff; border:1.5px solid var(--line-strong); transition:.15s}
.hero-dot:hover{border-color:var(--otblue)}
.hero-dot.active{background:var(--ink); border-color:var(--ink)}

/* lightbox modal */
.lightbox{position:fixed; inset:0; z-index:100; display:grid; place-items:center; padding:4vh 4vw}
.lightbox[hidden]{display:none}
.lb-backdrop{position:absolute; inset:0; background:rgba(20,19,15,.72);
  backdrop-filter:blur(4px); animation:lbfade .2s both}
.lb-panel{position:relative; z-index:1; display:flex; align-items:center; gap:14px;
  width:min(96vw,1200px); max-height:92vh; animation:lbpop .22s cubic-bezier(.2,.7,.2,1) both}
.lb-fig{flex:1; min-width:0; margin:0; background:#fff; border-radius:16px;
  box-shadow:0 30px 80px -30px rgba(0,0,0,.8); padding:24px 24px 16px; display:flex;
  flex-direction:column; max-height:92vh}
.lb-fig img{display:block; width:100%; height:auto; max-height:78vh; object-fit:contain; margin:0 auto}
.lb-cap{display:flex; align-items:center; justify-content:center; gap:10px; margin-top:12px}
.lb-cap a{font-family:"Fraunces",serif; font-weight:600; font-size:1.1rem; color:var(--ink);
  text-decoration:none}
.lb-cap a:hover{color:var(--otblue); text-decoration:underline}
.lb-nav{flex:none; width:46px; height:46px; border-radius:50%; cursor:pointer; font-size:1.2rem;
  background:rgba(255,255,255,.94); border:1.5px solid var(--line-strong); color:var(--ink); transition:.15s}
.lb-nav:hover{border-color:var(--otblue); color:var(--otblue)}
.lb-close{position:absolute; top:-6px; right:-6px; width:40px; height:40px; border-radius:50%;
  cursor:pointer; font-size:1.4rem; line-height:1; background:#fff; border:1.5px solid var(--line-strong);
  color:var(--ink); box-shadow:var(--shadow); transition:.15s}
.lb-close:hover{border-color:var(--otorange); color:var(--otorange)}
@keyframes lbfade{from{opacity:0}to{opacity:1}}
@keyframes lbpop{from{opacity:0; transform:scale(.97)}to{opacity:1; transform:none}}
.lightbox.no-anim .lb-backdrop,.lightbox.no-anim .lb-panel{animation:none}
body.lb-open{overflow:hidden}
@media(prefers-reduced-motion: reduce){
  .lb-backdrop,.lb-panel,.hero-slide.active{animation:none}
}

/* why-tikz band */
.why-tikz{padding:42px 0; border-top:1px solid var(--line)}
.why-tikz h2{font-family:"Fraunces",serif; font-weight:600; font-size:1.7rem; margin:0 0 18px; letter-spacing:-.01em}
.why-grid{display:grid; grid-template-columns:repeat(3,1fr); gap:20px}
.why-card{background:#fff; border:1px solid var(--line); border-radius:14px; padding:20px 20px; box-shadow:var(--shadow)}
.why-card h3{font-family:"Fraunces",serif; font-weight:600; font-size:1.1rem; margin:0 0 .35em}
.why-card p{margin:0; color:#4a473f; font-size:.92rem}
.why-card code{font-size:.82em}

/* magic moment (prompt -> editable TikZ -> figure) */
.magic .magic-sub{color:var(--muted); margin:0 0 20px; font-size:.98rem}
.magic-card{background:#fff; border:1px solid var(--line); border-radius:16px; padding:20px; box-shadow:var(--shadow)}
.magic-label{display:block; font-family:"IBM Plex Mono",monospace; font-size:.68rem; color:var(--muted);
  text-transform:uppercase; letter-spacing:.06em; margin-bottom:7px}
.magic-label em{font-style:normal; color:var(--otblue)}
.magic-prompt{margin-bottom:18px}
.magic-prompt code{display:block; background:#FFF8EC; border:1px solid #F0DDB6; border-radius:10px;
  padding:12px 14px; color:#5b5341; font-size:.95rem; line-height:1.4}
.magic-body{display:grid; grid-template-columns:1.15fr 1fr; gap:18px; align-items:stretch}
.magic-pane{min-width:0}
.magic-code{margin:0; background:#0F1422; border-radius:10px; padding:14px 16px; overflow-x:auto;
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.8rem; line-height:1.6; color:#CBD5E1}
.magic-code .ml-line{display:block; white-space:pre}
.magic-code .ml-add{background:rgba(0,158,115,.14); color:#7EE0A8;
  box-shadow:inset 3px 0 0 var(--otteal); padding-left:7px; margin-left:-10px}
.magic-fig{margin:0; height:100%; border:1px solid var(--line); border-radius:10px; padding:18px; background:
    linear-gradient(rgba(0,0,0,.028) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,0,0,.028) 1px,transparent 1px) #fcfcfa; background-size:18px 18px;
  display:flex; align-items:center; justify-content:center}
.magic-fig img{display:block; width:100%; max-height:240px; object-fit:contain}

/* why-opentikz verdict cards */
.why-ot{padding:42px 0; border-top:1px solid var(--line)}
.why-ot h2{font-family:"Fraunces",serif; font-weight:600; font-size:1.7rem; margin:0 0 .25em; letter-spacing:-.01em}
.why-ot-sub{color:var(--muted); margin:0 0 20px; font-size:.98rem}
.cmp-cards{display:grid; grid-template-columns:1fr 1fr; gap:18px}
.cmp-card{background:#fff; border:1px solid var(--line); border-radius:14px; padding:20px 22px; box-shadow:var(--shadow)}
.cmp-card h3{font-family:"Fraunces",serif; font-weight:600; font-size:1.15rem; margin:0 0 .6em; display:flex; align-items:center; gap:.4em}
.cmp-card ul{margin:0; padding-left:1.1em}
.cmp-card li{margin:.4em 0; font-size:.92rem; color:#4a473f}
.cmp-card code{font-size:.82em}
.cmp-bad{border-top:3px solid #C2554D}
.cmp-bad h3::before{content:"\2717"; color:#C2554D}
.cmp-good{border-top:3px solid var(--otteal)}
.cmp-good h3::before{content:"\2713"; color:var(--otteal)}

/* stack the two-column sections on narrow screens */
@media (max-width:720px){
  .why-grid,.magic-body,.cmp-cards{grid-template-columns:1fr}
}
.cta-band{text-align:center; border-bottom:none}
.cta-band h2{font-family:"Fraunces",serif; font-weight:900; letter-spacing:-.02em;
  font-size:clamp(1.6rem,3.4vw,2.4rem); margin:0 0 .6em}
.cta-sub{color:var(--muted); font-size:.85rem; margin:1.1em 0 0; font-family:"IBM Plex Mono",monospace}

/* skills-in-action carousel */
.skills-demo{padding:42px 0; border-top:1px solid var(--line); text-align:center}
.skills-demo h2{font-family:"Fraunces",serif; font-weight:600; font-size:1.7rem; margin:0 0 .2em; letter-spacing:-.01em}
.skills-sub{color:var(--muted); margin:0 auto 22px; font-size:.95rem}
.carousel{display:flex; align-items:center; gap:10px}
.car-track{flex:1; min-width:0}
.demo-slide{display:none}
.demo-slide.active{display:block; animation:fade .25s both}
@keyframes fade{from{opacity:0}to{opacity:1}}
.demo-head{display:flex; align-items:baseline; justify-content:center; gap:10px; margin-bottom:14px}
.demo-dim{font-family:"IBM Plex Mono",monospace; font-weight:500; font-size:.8rem; color:#fff;
  background:var(--otblue); border-radius:999px; padding:4px 11px}
.demo-tmpl{font-family:"IBM Plex Mono",monospace; font-size:.8rem; color:var(--muted)}
.demo-trip{display:grid; grid-template-columns:1fr auto 1fr; gap:18px; align-items:center}
.demo-fig{margin:0; border:1px solid var(--line); border-radius:12px; padding:18px; background:
    linear-gradient(rgba(0,0,0,.028) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,0,0,.028) 1px,transparent 1px) #fcfcfa; background-size:18px 18px}
.demo-fig img{display:block; width:100%; max-height:220px; object-fit:contain; margin:0 auto}
.demo-fig figcaption{font-family:"IBM Plex Mono",monospace; font-size:.7rem; color:var(--muted);
  margin-top:8px; text-transform:uppercase; letter-spacing:.06em}
.demo-prompt{position:relative; max-width:200px; margin:0 auto}
.demo-prompt-label{display:block; font-family:"IBM Plex Mono",monospace; font-size:.68rem; color:var(--muted);
  text-transform:uppercase; letter-spacing:.06em; margin-bottom:6px}
.demo-prompt code{display:block; background:#FFF8EC; border:1px solid #F0DDB6; border-radius:8px;
  padding:10px 12px; color:#5b5341; font-size:.84rem; line-height:1.4}
.demo-prompt::before,.demo-prompt::after{content:"→"; position:absolute; top:50%;
  transform:translateY(-50%); color:var(--otorange); font-size:1.1rem}
.demo-prompt::before{left:-15px} .demo-prompt::after{right:-15px}
.demo-changed{color:var(--muted); font-size:.85rem; margin:16px auto 0; max-width:62ch}
.car-nav{flex:none; width:40px; height:40px; border-radius:50%; cursor:pointer; font-size:1.05rem;
  background:#fff; border:1.5px solid var(--line-strong); color:var(--ink); transition:.15s}
.car-nav:hover{border-color:var(--otblue); color:var(--otblue)}
.car-dots{display:flex; flex-wrap:wrap; justify-content:center; gap:8px; margin-top:20px}
.demo-dot{cursor:pointer; font:500 .76rem "IBM Plex Mono",monospace; color:var(--muted);
  background:#fff; border:1.5px solid var(--line-strong); border-radius:999px; padding:5px 11px; transition:.15s}
.demo-dot:hover{border-color:var(--otblue)}
.demo-dot.active{background:var(--ink); color:var(--paper); border-color:var(--ink)}

/* roadmap teaser */
.roadmap{padding:42px 0; border-top:1px solid var(--line)}
.roadmap h2{font-family:"Fraunces",serif; font-weight:600; font-size:1.4rem; margin:0 0 16px;
  letter-spacing:-.01em; color:var(--muted)}
.roadmap-cards{display:grid; grid-template-columns:repeat(auto-fit,minmax(290px,1fr)); gap:18px}
.rm-card{border:1.5px dashed var(--line-strong); border-radius:14px; padding:20px 22px; background:rgba(255,255,255,.5)}
.rm-tag{display:inline-block; font-family:"IBM Plex Mono",monospace; font-size:.68rem; text-transform:uppercase;
  letter-spacing:.06em; color:var(--otorange); background:#FFF8EC; border:1px solid #F0DDB6;
  border-radius:999px; padding:4px 10px; margin-bottom:10px}
.rm-card h3{font-family:"Fraunces",serif; font-weight:600; font-size:1.2rem; margin:0 0 .3em}
.rm-card h3 span{font-family:"IBM Plex Mono",monospace; font-weight:400; font-size:.8rem; color:var(--muted); margin-left:6px}
.rm-card p{margin:0; color:#4a473f; font-size:.93rem}

/* ---------- skills page ---------- */
.skills-page{max-width:var(--maxw); margin:0 auto; padding:0 var(--gutter)}
.skills-intro{max-width:680px; margin:0 auto; padding:46px 0 8px; text-align:center}
.skills-intro h1{font-family:"Fraunces",serif; font-weight:900; letter-spacing:-.02em;
  font-size:clamp(2rem,4.5vw,2.8rem); margin:0 0 .25em}
.skills-intro .lede{font-family:"Fraunces",serif; font-weight:400; color:#34322b;
  font-size:clamp(1.02rem,1.8vw,1.2rem); margin:0 auto}
.skills-intro .lede code{font-family:"IBM Plex Mono",monospace; font-size:.9em}
.skills-libwide,.skills-how,.skills-why{padding:36px 0; border-top:1px solid var(--line)}
.skills-libwide h2,.skills-how h2,.skills-why h2{font-family:"Fraunces",serif; font-weight:600;
  font-size:1.5rem; margin:0 0 6px; letter-spacing:-.01em}
.skills-index-sub{color:var(--muted); margin:0 0 20px; font-size:.92rem; max-width:620px}
.skills-steps{margin:0; padding:0; list-style:none; counter-reset:step;
  display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:16px}
.skills-steps li{counter-increment:step; position:relative; background:#fff;
  border:1px solid var(--line); border-radius:12px; padding:18px 20px 18px 54px;
  box-shadow:var(--shadow); color:#4a473f; font-size:.9rem; line-height:1.5}
.skills-steps li::before{content:counter(step); position:absolute; left:18px; top:16px;
  width:26px; height:26px; border-radius:50%; background:var(--otblue); color:#fff;
  font:600 .9rem "IBM Plex Sans",sans-serif; display:flex; align-items:center; justify-content:center}
.skills-steps strong{color:var(--ink)}
.skill-links{display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px}
.skill-link{display:block; text-decoration:none; background:#fff; border:1px solid var(--line);
  border-radius:12px; padding:18px 20px; box-shadow:var(--shadow);
  transition:transform .16s, border-color .16s, box-shadow .16s}
.skill-link:hover{transform:translateY(-3px); border-color:var(--line-strong)}
.skill-link h3{margin:0 0 .3em; font-family:"Fraunces",serif; font-weight:600; font-size:1.12rem;
  color:var(--ink); display:flex; justify-content:space-between; align-items:center; gap:8px}
.skill-link h3 span{color:var(--otblue); font-family:"IBM Plex Sans",sans-serif; font-weight:600}
.skill-link p{margin:0; color:#4a473f; font-size:.9rem}

/* Browse tool-surface header */
.hero-browse{padding-top:40px}
.browse-title{font-family:"Fraunces",serif; font-weight:900; letter-spacing:-.02em;
  font-size:clamp(1.7rem,4vw,2.4rem); margin:0 0 .5em}

@media(max-width:980px){
  .lb-panel{flex-wrap:wrap; justify-content:center}
  .lb-nav{order:2}
}
@media(max-width:720px){
  :root{--gutter:18px}            /* one place sets the mobile gutter for every container */
  .item-top{grid-template-columns:1fr; gap:22px}
  /* navbar collapses to a hamburger; links become an overlay dropdown */
  .nav-inner{padding:10px var(--gutter); gap:10px; flex-wrap:nowrap; position:relative}
  .nav-burger{display:flex; position:absolute; right:var(--gutter); top:50%;
    transform:translateY(-50%)}
  .nav-links{position:absolute; top:calc(100% + 1px); left:0; right:0; margin:0;
    flex-direction:column; flex-wrap:nowrap; align-items:stretch; gap:0;
    background:rgba(251,250,246,.98); backdrop-filter:blur(8px);
    border-bottom:1px solid var(--line); box-shadow:0 14px 30px rgba(27,26,22,.09);
    max-height:0; overflow-y:hidden; transition:max-height .26s ease; padding:0 var(--gutter)}
  .nav-toggle:checked ~ .nav-links{max-height:80vh; overflow-y:auto; padding:4px var(--gutter) 10px}
  .nav-links a{padding:13px 6px; font-size:1rem; border-radius:0;
    border-bottom:1px solid var(--line)}
  .nav-links a:last-child{border-bottom:0}
  /* burger → X when open */
  .nav-toggle:checked ~ .nav-burger span:nth-child(1){transform:translateY(6px) rotate(45deg)}
  .nav-toggle:checked ~ .nav-burger span:nth-child(2){opacity:0}
  .nav-toggle:checked ~ .nav-burger span:nth-child(3){transform:translateY(-6px) rotate(-45deg)}
  .hero{padding:34px 20px 8px}
  .showcase{padding:32px 0 26px}
  .steps{grid-template-columns:1fr}
  .hero-zoom{padding:18px}
  .hero-zoom img{height:240px}
  .zoom-hint{font-size:.66rem; padding:4px 8px}
  .lightbox{padding:2vh 3vw}
  .lb-fig{padding:14px}
  .lb-nav{width:40px; height:40px}
  .demo-trip{grid-template-columns:1fr; gap:12px}
  .demo-prompt{max-width:none}
  .demo-prompt::before,.demo-prompt::after{display:none}
  .carousel{gap:6px}
  .car-nav{width:34px; height:34px}
}

/* ---------- before/after compare slider ---------- */
.ba{--pos:50%; position:relative; width:100%; max-width:560px; aspect-ratio:16/7;
    margin:0 auto; border:1px solid var(--line-strong); border-radius:12px; overflow:hidden;
    background:var(--paper); touch-action:none; cursor:ew-resize}
.ba-img{position:absolute; inset:0; width:100%; height:100%; object-fit:contain; padding:10px}
.ba-after-img{clip-path:inset(0 0 0 var(--pos))}
.ba-before-img{clip-path:inset(0 calc(100% - var(--pos)) 0 0)}
.ba-tag{position:absolute; bottom:8px; font:600 .62rem/1 "IBM Plex Mono",monospace;
        letter-spacing:.08em; text-transform:uppercase; padding:3px 8px; border-radius:5px;
        background:rgba(0,0,0,.55); color:#fff}
.ba-tag-l{left:8px} .ba-tag-r{right:8px; color:var(--otblue)}
.ba-bar{position:absolute; top:0; bottom:0; left:var(--pos); width:2px;
        background:#fff; transform:translateX(-1px); pointer-events:none}
.ba-handle{position:absolute; top:50%; left:var(--pos); width:30px; height:30px;
           transform:translate(-50%,-50%); border-radius:50%; background:#fff; color:var(--ink);
           display:flex; align-items:center; justify-content:center; font:14px monospace;
           box-shadow:0 2px 8px rgba(0,0,0,.4); pointer-events:none}
.ba-range{position:absolute; inset:0; width:100%; height:100%; margin:0; opacity:0; cursor:ew-resize}
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

    // support ?q= (prefill+run) and ?focus= from the Home search hand-off
    var params = new URLSearchParams(location.search);
    var q0 = params.get('q');
    if (q0 && searchEl) searchEl.value = q0;

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
    if (searchEl && (q0 || params.get('focus'))) searchEl.focus();

    // ---- active-section highlight (only the section links; Browse stays active) ----
    var sectionLinks = {};
    ['icons', 'templates', 'examples'].forEach(function (k) {
      var a = document.querySelector('.nav-links a[data-nav="' + k + '"]');
      if (a) sectionLinks[k] = a;
    });
    if (Object.keys(sectionLinks).length && 'IntersectionObserver' in window) {
      var obs = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting && sectionLinks[en.target.id]) {
            Object.keys(sectionLinks).forEach(function (k) { sectionLinks[k].classList.remove('active'); });
            sectionLinks[en.target.id].classList.add('active');
          }
        });
      }, { rootMargin: '-45% 0px -50% 0px' });
      groups.forEach(function (g) { obs.observe(g); });
    }
  }

  // ---- keyboard: '/' focuses search (or jumps to Browse); Esc clears + blurs ----
  document.addEventListener('keydown', function (e) {
    var s = document.getElementById('search');
    var t = e.target || {};
    var typing = /^(input|textarea|select)$/i.test(t.tagName || '') || t.isContentEditable;
    if (e.key === '/' && !typing && s) {
      e.preventDefault();
      s.focus();
    } else if (e.key === 'Escape' && s && document.activeElement === s) {
      s.value = '';
      s.dispatchEvent(new Event('input'));
      s.blur();
    }
  });

  // ---- mobile nav: close the hamburger menu on link tap / Esc ----
  var navToggle = document.getElementById('nav-toggle');
  if (navToggle) {
    document.querySelectorAll('.nav-links a').forEach(function (a) {
      a.addEventListener('click', function () { navToggle.checked = false; });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && navToggle.checked) navToggle.checked = false;
    });
  }

  // ---- copy-to-clipboard (item page) ----
  document.querySelectorAll('.copy, .dl-copy').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();          // primary copy lives outside <summary>, but be safe
      var el = document.getElementById(btn.getAttribute('data-target'));
      if (!el) return;
      navigator.clipboard.writeText(el.textContent).then(function () {
        var old = btn.innerHTML;   // innerHTML preserves any inline icon on restore
        btn.innerHTML = 'Copied ✓';
        btn.classList.add('done');
        setTimeout(function () { btn.innerHTML = old; btn.classList.remove('done'); }, 1600);
      });
    });
  });

  // ---- downloads (item page): .tex from inlined source, PNG via canvas ----
  function triggerDownload(href, name) {
    var a = document.createElement('a');
    a.href = href; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
  }
  document.querySelectorAll('[data-tex]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var el = document.getElementById(btn.getAttribute('data-tex'));
      if (!el) return;
      var url = URL.createObjectURL(new Blob([el.textContent], { type: 'application/x-tex' }));
      triggerDownload(url, btn.getAttribute('data-name') || 'figure.tex');
      setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    });
  });
  document.querySelectorAll('[data-png]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var img = new Image();
      img.onload = function () {
        var scale = 3;
        var w = img.naturalWidth || 600, h = img.naturalHeight || 400;
        var c = document.createElement('canvas');
        c.width = w * scale; c.height = h * scale;
        var ctx = c.getContext('2d');
        ctx.fillStyle = '#ffffff';                 // figures assume a white background
        ctx.fillRect(0, 0, c.width, c.height);
        ctx.drawImage(img, 0, 0, c.width, c.height);
        c.toBlob(function (blob) {
          var url = URL.createObjectURL(blob);
          triggerDownload(url, btn.getAttribute('data-name') || 'figure.png');
          setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
        }, 'image/png');
      };
      img.src = btn.getAttribute('data-png');
    });
  });

  // ---- per-instance carousels (supports multiple on one page) ----
  // Each .carousel keeps its OWN active index; all inner queries are scoped to the
  // element so the hero (#hero-carousel/.hero-slide/.hero-dot) and the skills demo
  // (#skills-carousel/.demo-slide/.demo-dot) never share state.
  var carousels = Array.prototype.slice.call(document.querySelectorAll('.carousel'));
  carousels.forEach(function (car) {
    var slides = Array.prototype.slice.call(
      car.querySelectorAll('.hero-slide, .demo-slide'));
    if (!slides.length) return;
    // dots live in a sibling .car-dots (or any node with [data-dots-for=id])
    var dotWrap = car.parentNode
      ? car.parentNode.querySelector('.car-dots')
      : null;
    var dots = dotWrap
      ? Array.prototype.slice.call(dotWrap.querySelectorAll('.hero-dot, .demo-dot'))
      : [];
    var idx = 0;
    function show(n) {
      idx = (n + slides.length) % slides.length;
      slides.forEach(function (s, i) { s.classList.toggle('active', i === idx); });
      dots.forEach(function (d, i) { d.classList.toggle('active', i === idx); });
    }
    car._show = show;
    Object.defineProperty(car, '_index', { get: function () { return idx; } });
    var prev = car.querySelector('.car-prev'), next = car.querySelector('.car-next');
    if (prev) prev.addEventListener('click', function () { show(idx - 1); });
    if (next) next.addEventListener('click', function () { show(idx + 1); });
    dots.forEach(function (d, i) { d.addEventListener('click', function () { show(i); }); });
    // keyboard only when THIS carousel (or something inside it) has focus
    car.addEventListener('keydown', function (e) {
      var t = e.target || {};
      if (/^(input|textarea|select)$/i.test(t.tagName || '')) return;
      if (e.key === 'ArrowLeft') { e.preventDefault(); show(idx - 1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); show(idx + 1); }
    });
    show(0);

    // ---- autoplay (opt-in via data-autoplay; honors reduced motion) ----
    // Pauses on hover, keyboard focus, a hidden tab, or an external hold
    // (the lightbox). Manual navigation restarts the countdown so the slide
    // never advances the instant after you click.
    var prefersReduced = window.matchMedia
      && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (car.hasAttribute('data-autoplay') && slides.length > 1 && !prefersReduced) {
      var autoMs = parseInt(car.getAttribute('data-interval'), 10) || 5000;
      var hover = false, focused = false, external = false, timer = null;
      function autoActive() { return !(hover || focused || external || document.hidden); }
      function start() {
        if (timer) clearInterval(timer);
        timer = setInterval(function () { if (autoActive()) show(idx + 1); }, autoMs);
      }
      car._pauseAuto = function () { external = true; };
      car._resumeAuto = function () { external = false; };
      car.addEventListener('mouseenter', function () { hover = true; });
      car.addEventListener('mouseleave', function () { hover = false; });
      car.addEventListener('focusin', function () { focused = true; });
      car.addEventListener('focusout', function () { focused = false; });
      car.addEventListener('click', start);    // manual nav resets the cadence
      car.addEventListener('keydown', start);
      document.addEventListener('visibilitychange', function () {
        if (!document.hidden) start();         // realign cadence when the tab returns
      });
      start();
    }
  });

  // ---- click-to-zoom lightbox (Home hero) ----
  var lb = document.getElementById('lightbox');
  var hero = document.getElementById('hero-carousel');
  if (lb && hero) {
    var figs = Array.prototype.slice.call(hero.querySelectorAll('.hero-slide'));
    var lbImg = document.getElementById('lb-img');
    var lbLink = document.getElementById('lb-link');
    var lbBadge = document.getElementById('lb-badge');
    var lbPrev = lb.querySelector('.lb-prev');
    var lbNext = lb.querySelector('.lb-next');
    var lbIdx = 0;
    var lastFocus = null;
    var reduceMotion = window.matchMedia
      && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function focusable() {
      return Array.prototype.slice.call(lb.querySelectorAll(
        'button, [href], img[tabindex], [tabindex]:not([tabindex="-1"])'))
        .filter(function (el) { return el.offsetParent !== null || el === document.activeElement; });
    }

    function render(n) {
      lbIdx = (n + figs.length) % figs.length;
      var slide = figs[lbIdx];
      var img = slide.querySelector('img');
      lbImg.src = img.getAttribute('src');
      lbImg.alt = slide.getAttribute('data-name') || '';
      var link = slide.querySelector('.hero-cap a');
      var badgeEl = slide.querySelector('.hero-cap .badge');
      lbLink.textContent = slide.getAttribute('data-name') || '';
      lbLink.setAttribute('href', link ? link.getAttribute('href') : '#');
      lbBadge.innerHTML = badgeEl ? badgeEl.outerHTML : '';
    }

    function openLb(n, trigger) {
      lastFocus = trigger || document.activeElement;
      render(n);
      lb.hidden = false;
      lb.setAttribute('aria-hidden', 'false');
      if (reduceMotion) lb.classList.add('no-anim');
      if (hero._pauseAuto) hero._pauseAuto();   // hold autoplay while zoomed
      document.body.classList.add('lb-open');   // lock scroll
      var close = lb.querySelector('.lb-close');
      if (close) close.focus();
    }

    function closeLb() {
      lb.hidden = true;
      lb.setAttribute('aria-hidden', 'true');
      lb.classList.remove('no-anim');
      if (hero._resumeAuto) hero._resumeAuto();   // resume autoplay on close
      document.body.classList.remove('lb-open');
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    // open via the per-slide zoom button
    Array.prototype.slice.call(hero.querySelectorAll('.hero-zoom')).forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        openLb(parseInt(btn.getAttribute('data-zoom'), 10) || 0, btn);
      });
    });
    if (lbPrev) lbPrev.addEventListener('click', function () { render(lbIdx - 1); });
    if (lbNext) lbNext.addEventListener('click', function () { render(lbIdx + 1); });
    Array.prototype.slice.call(lb.querySelectorAll('[data-lb-close]')).forEach(function (el) {
      el.addEventListener('click', closeLb);
    });

    document.addEventListener('keydown', function (e) {
      if (lb.hidden) return;
      if (e.key === 'Escape') { e.preventDefault(); closeLb(); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); render(lbIdx - 1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); render(lbIdx + 1); }
      else if (e.key === 'Tab') {
        // focus trap
        var f = focusable();
        if (!f.length) return;
        var first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
  }

  // before/after compare sliders
  document.querySelectorAll('[data-ba]').forEach(function (ba) {
    var range = ba.querySelector('.ba-range');
    if (!range) return;
    function apply() { ba.style.setProperty('--pos', range.value + '%'); }
    range.addEventListener('input', apply);
    apply();
    var dragging = false;
    function setFromX(clientX) {
      var r = ba.getBoundingClientRect();
      var p = Math.max(0, Math.min(100, (clientX - r.left) / r.width * 100));
      range.value = p; apply();
    }
    ba.addEventListener('pointerdown', function (e) { dragging = true; setFromX(e.clientX); });
    window.addEventListener('pointermove', function (e) { if (dragging) setFromX(e.clientX); });
    window.addEventListener('pointerup', function () { dragging = false; });
  });
})();
"""


if __name__ == "__main__":
    raise SystemExit(build(repo_root()))
