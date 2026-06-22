# Landing Page IA Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the OpenTikZ landing page into a focused AI-workflow funnel led by a figure-first hero with a draggable before/after compare slider.

**Architecture:** All changes live in `tools/build_site.py` — the static-site generator. The Home surface (`home_page()`) is re-ordered into 7 sections; a new `before_after_slider()` component and `library_gallery()` section are added; `magic_moment` is absorbed into the hero and removed; `why_tikz_band` is slimmed. Styling lives in the `STYLE_CSS` constant, behavior in the `APP_JS` constant, both emitted to `site/assets/`.

**Tech Stack:** Python 3 standard library only (no third-party build deps). Plain HTML/CSS/JS in generated output. Before/after slider built on a native `<input type="range">`; "view source" built on a native `<details>` element — both keyboard-accessible with no-JS fallback.

## Global Constraints

- `tools/build_site.py` must use the **Python standard library only** — no new dependencies.
- Colors in generated CSS use the existing palette tokens already in `STYLE_CSS` (e.g. `--otblue`, `--otorange`); never introduce new raw hex where a token exists.
- Build command (run from repo root): `python3 tools/build_site.py`. It must exit 0 and regenerate `site/`.
- No `.tex`, `.meta.json`, `catalog.json`, `meta.schema.json`, or other-surface (`item/`, `browse/`, `skills/`) changes. This plan touches the Home surface + shared `STYLE_CSS`/`APP_JS` only.
- There is no pytest harness. "Tests" are: `python3 -c` assertions for pure helpers, `grep` on generated `site/index.html`, a manual browser check, and `python3 tools/validate.py` as a guard.
- Featured before/after assets (already in `site/demos/` and `skills-demos/`): `encdec-before.svg` (before) and `encdec-xattn.svg` (after); featured prompt: "add a cross-attention block and make it blue". Source of truth: `skills-demos/skills-demos.json` (the entry with `"featured": true`).
- Hero copy and CTA wording in this plan are the agreed drafts; do not invent alternatives. Primary CTA "Get started" → `skills/`; secondary "Browse the library →" → `browse/`.
- Locate edit sites by **function name** (line numbers shift as you edit).

---

### Task 1: `before_after_slider()` component (helper + CSS + JS)

Self-contained draggable compare-slider component. Not yet wired into any page; verified standalone.

**Files:**
- Modify: `tools/build_site.py` — add `before_after_slider()` near the other section helpers (after `demos_carousel`, ~line 330); add CSS to the `STYLE_CSS` constant; add JS to the `APP_JS` constant.

**Interfaces:**
- Produces: `before_after_slider(before_svg: str, after_svg: str, *, before_label: str = "before", after_label: str = "after", prefix: str = "") -> str` — returns an HTML `<div class="ba" data-ba>` fragment. `before_svg`/`after_svg` are filenames resolved under `{prefix}demos/`.
- Produces (CSS): classes `.ba`, `.ba-img`, `.ba-before-img`, `.ba-after-img`, `.ba-tag`, `.ba-tag-l`, `.ba-tag-r`, `.ba-bar`, `.ba-range`, `.ba-handle`; CSS var `--pos`.
- Produces (JS): a `[data-ba]` initializer in `APP_JS` driving `--pos` from the range input + pointer drag.

- [ ] **Step 1: Write the helper function**

In `tools/build_site.py`, after the `demos_carousel` function, add:

```python
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
```

- [ ] **Step 2: Verify the helper output via a quick assertion**

Run:
```bash
python3 -c "import sys; sys.path.insert(0,'tools'); import build_site as b; s=b.before_after_slider('encdec-before.svg','encdec-xattn.svg'); assert 'data-ba' in s and 'demos/encdec-before.svg' in s and 'demos/encdec-xattn.svg' in s and 'type=\"range\"' in s and '--pos:50%' in s; print('OK')"
```
Expected: prints `OK`.

- [ ] **Step 3: Add slider CSS to `STYLE_CSS`**

Find the `STYLE_CSS` constant (the hero block starts with the comment `/* ---------- hero` / `/* figure-led, centred hero`). Append these rules at the end of `STYLE_CSS` (just before the closing `"""`):

```css
/* ---------- before/after compare slider ---------- */
.ba{--pos:50%; position:relative; width:100%; max-width:560px; aspect-ratio:16/7;
    margin:0 auto; border:1px solid var(--border); border-radius:12px; overflow:hidden;
    background:var(--surface,#0d0f15); touch-action:none; cursor:ew-resize}
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
           transform:translate(-50%,-50%); border-radius:50%; background:#fff; color:#11131a;
           display:flex; align-items:center; justify-content:center; font:14px monospace;
           box-shadow:0 2px 8px rgba(0,0,0,.4); pointer-events:none}
.ba-range{position:absolute; inset:0; width:100%; height:100%; margin:0; opacity:0; cursor:ew-resize}
```

- [ ] **Step 4: Add slider JS to `APP_JS`**

Find the `APP_JS` constant. Append this initializer at the end of the script body (before the closing `"""`); if `APP_JS` wraps everything in a `DOMContentLoaded` handler, add it inside that handler instead:

```javascript
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
```

- [ ] **Step 5: Build and confirm no regression**

Run:
```bash
python3 tools/build_site.py && grep -c "before/after compare slider" site/assets/style.css && grep -c "data-ba" site/assets/app.js
```
Expected: build exits 0; each `grep -c` prints `1`. (No page uses the slider yet — that's Task 2.)

- [ ] **Step 6: Commit**

```bash
git add tools/build_site.py site/assets/style.css site/assets/app.js
git commit -m "Add before/after compare slider component (helper + CSS + JS)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Figure-first hero (absorbs magic_moment)

Rewrite the hero (`<section class="showcase">`) inside `home_page()` to: wordmark, headline, lede, "you said" prompt chip, the before/after slider (featured demo SVGs), a de-emphasized `<details>` "view TikZ source", and the two CTAs. Remove the old example carousel and the `magic_moment` section call from `home_page`.

**Files:**
- Modify: `tools/build_site.py` — `home_page()` (~427-526); add a small `render_tex_excerpt()` helper.

**Interfaces:**
- Consumes: `before_after_slider(...)` from Task 1; the `demos` list passed into `home_page`; `skills-demos.json` field `tex_excerpt` on the featured demo.
- Produces: `render_tex_excerpt(tex: str) -> str` — renders excerpt lines as `<span class="ml-line">` / `<span class="ml-line ml-add">` (reuses existing `.magic-code`/`.ml-line`/`.ml-add` CSS).

- [ ] **Step 1: Add the `render_tex_excerpt` helper**

In `tools/build_site.py`, just above `magic_moment`, add:

```python
def render_tex_excerpt(tex: str) -> str:
    """Render a demo tex_excerpt: a leading '+' marks an AI-added line."""
    out = ""
    for raw in tex.split("\n"):
        added = raw.startswith("+")
        text = html.escape(raw[1:].rstrip() if added else raw.rstrip())
        cls = " ml-add" if added else ""
        out += f'<span class="ml-line{cls}">{text or "&nbsp;"}</span>\n'
    return out
```

- [ ] **Step 2: Replace the hero markup in `home_page`**

In `home_page()`, the returned f-string opens with `<main class="home">` then `<section class="showcase">...</section>` followed by `{lightbox}`. Replace the entire `<section class="showcase"> ... </section>` block (the wordmark through the `cta-row` closing `</section>`) AND the following `{lightbox}` line with:

```python
    # Featured demo drives the hero slider + view-source. Guard against no demos.
    demo = next((d for d in demos if d.get("featured")), (demos[0] if demos else None))
    if demo:
        slider = before_after_slider(demo["before_svg"], demo["after_svg"],
                                     before_label="before", after_label="after")
        hero_prompt = html.escape(demo.get("prompt", ""))
        hero_src = render_tex_excerpt(demo.get("tex_excerpt", ""))
    else:
        slider, hero_prompt, hero_src = "", "", ""
```

Then in the f-string body, replace the old `showcase` section + `{lightbox}` with:

```html
  <section class="showcase">
    <a class="hero-logo" href="index.html" aria-label="OpenTikZ home">Open<span class="tik">TikZ</span><span class="caret">&#9475;</span></a>
    <h1>Describe your figure. Get it, paper-ready.</h1>
    <p class="show-lede">Your AI agent edits a real TikZ template &mdash; you never write TikZ yourself.</p>
    <p class="hero-prompt"><span class="hero-prompt-label">you said</span><code>&ldquo;{hero_prompt}&rdquo;</code></p>
{slider}
    <details class="hero-src"><summary>view TikZ source</summary><pre class="magic-code">{hero_src}</pre></details>
    <div class="cta-row">
      <a class="btn btn-primary" href="skills/">Get started</a>
      <a class="btn btn-ghost" href="browse/">Browse the library &rarr;</a>
    </div>
  </section>
```

- [ ] **Step 3: Remove the now-dead hero-carousel and lightbox setup in `home_page`**

Delete the `hero_slides, hero_dots = "", ""` loop block and the `lightbox = """..."""` assignment near the top of `home_page` (they fed the old carousel/lightbox, now removed). Also delete the `magic = magic_moment(demos, by_id)` line and the `{magic}` reference in the f-string body. Leave `demos_section`, `why_tikz`, `why_opentikz` assignments for now.

- [ ] **Step 4: Add hero CSS to `STYLE_CSS`**

Append to `STYLE_CSS`:

```css
/* ---------- figure-first hero additions ---------- */
.hero-prompt{display:inline-flex; align-items:center; gap:8px; margin:0 auto .9em;
  background:rgba(255,255,255,.05); border:1px solid color-mix(in srgb,var(--otorange) 45%,transparent);
  border-radius:30px; padding:9px 16px; font:.92rem "IBM Plex Mono",monospace; max-width:92%}
.hero-prompt-label{font:600 .58rem "IBM Plex Mono",monospace; letter-spacing:.08em;
  text-transform:uppercase; color:var(--otorange)}
.hero-prompt code{background:none; padding:0}
.hero-src{margin:.9em auto 0; max-width:560px; text-align:left}
.hero-src summary{font:.78rem "IBM Plex Mono",monospace; opacity:.6; cursor:pointer; list-style:none}
.hero-src summary::before{content:"\25B8 "; }
.hero-src[open] summary::before{content:"\25BE "; }
.hero-src .magic-code{margin-top:.5em}
```

- [ ] **Step 5: Build and verify the hero renders**

Run:
```bash
python3 tools/build_site.py && grep -q "Describe your figure" site/index.html && grep -q 'class="ba"' site/index.html && grep -q "view TikZ source" site/index.html && grep -q "encdec-before.svg" site/index.html && echo "HERO OK"
```
Expected: prints `HERO OK`.

- [ ] **Step 6: Manual browser check**

Open `site/index.html` in a browser. Confirm: headline + prompt chip show; the slider shows the encoder-decoder figure with a centered bar; **dragging the handle wipes between before and after and the shared elements line up across the wipe**; "view TikZ source" expands to show the excerpt with the added lines highlighted; both CTAs are present.

> If the two SVGs do NOT align across the wipe (different canvas/scale), STOP and report it — fall back per spec (constrain both to a common box, or use a crossfade). Do not silently ship a broken wipe.

- [ ] **Step 7: Commit**

```bash
git add tools/build_site.py site/
git commit -m "Hero: figure-first with before/after slider; absorb magic moment

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Library gallery section

Add a `library_gallery()` section (figure thumbnails → item pages, counts line, Browse CTA) built from the `featured` examples list.

**Files:**
- Modify: `tools/build_site.py` — add `library_gallery()` near the other section helpers; call it from `home_page`; add CSS to `STYLE_CSS`.

**Interfaces:**
- Consumes: `featured` (list of example items) and `counts` (dict) already passed into `home_page`.
- Produces: `library_gallery(featured: list[dict], counts: dict) -> str`.

- [ ] **Step 1: Add the `library_gallery` function**

```python
def library_gallery(featured: list[dict], counts: dict) -> str:
    """Compact thumbnail grid of featured figures + counts + Browse CTA."""
    thumbs = ""
    for it in featured:
        name = html.escape(it["name"])
        thumbs += f"""      <a class="lib-thumb" href="item/{html.escape(it['id'])}.html">
        <img src="previews/{html.escape(it['id'])}.svg" alt="{name}" loading="lazy">
        <span>{name}</span>
      </a>
"""
    return f"""
  <section class="library">
    <h2>The library you&rsquo;re drawing from</h2>
    <p class="library-sub">Editable templates and copyable icons &mdash; the figures your agent starts from.</p>
    <div class="lib-grid">
{thumbs}    </div>
    <div class="cta-row"><a class="btn btn-primary" href="browse/">Browse the library &rarr;</a></div>
    <p class="cta-sub">{counts.get('icon', 0)} icons &middot; {counts.get('template', 0)} templates &middot; {counts.get('example', 0)} examples &middot; content <code>CC0&nbsp;1.0</code></p>
  </section>
"""
```

- [ ] **Step 2: Call it from `home_page`**

Near the top of `home_page`, add: `library = library_gallery(featured, counts)`. (Final placement in the section order happens in Task 5; for now append `{library}` to the f-string body just before the `roadmap` section so it renders.)

- [ ] **Step 3: Add library CSS to `STYLE_CSS`**

```css
/* ---------- library gallery ---------- */
.library{max-width:1000px; margin:0 auto; padding:46px 28px 8px; text-align:center}
.lib-grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:14px; margin:22px 0}
.lib-thumb{display:flex; flex-direction:column; gap:6px; text-decoration:none; color:inherit;
  border:1px solid var(--border); border-radius:10px; padding:12px; background:rgba(255,255,255,.02);
  transition:border-color .15s, transform .15s}
.lib-thumb:hover{border-color:var(--otblue); transform:translateY(-2px)}
.lib-thumb img{width:100%; height:90px; object-fit:contain}
.lib-thumb span{font:.78rem system-ui; opacity:.8}
```

- [ ] **Step 4: Build and verify**

Run:
```bash
python3 tools/build_site.py && grep -q 'class="library"' site/index.html && grep -q 'class="lib-thumb"' site/index.html && echo "LIBRARY OK"
```
Expected: prints `LIBRARY OK`. Open `site/index.html` and confirm the thumbnail grid renders and each thumb links to an item page.

- [ ] **Step 5: Commit**

```bash
git add tools/build_site.py site/
git commit -m "Add 'library you're drawing from' gallery section

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Slim the "Why TikZ" band

Restyle `why_tikz_band()` from three full cards into a slim inline 3-point strip. Copy is unchanged; only structure/markup + CSS change.

**Files:**
- Modify: `tools/build_site.py` — `why_tikz_band()` (~372-392); add CSS to `STYLE_CSS`.

- [ ] **Step 1: Replace the band markup**

Replace the body of `why_tikz_band()` with a slim strip (keep the three points' text verbatim):

```python
def why_tikz_band() -> str:
    """Foundational reassurance, slimmed to a 3-point inline strip."""
    return r"""
  <section class="why-tikz-slim">
    <h2>Why TikZ</h2>
    <div class="wts-strip">
      <div class="wts-item"><b>Vector quality</b><span>Crisp at any zoom, sharp in print &mdash; no pixelated screenshots.</span></div>
      <div class="wts-item"><b>Native to your paper</b><span>Same fonts, math, and <code>\ref</code>/<code>\cite</code> as the document.</span></div>
      <div class="wts-item"><b>Text, so it&rsquo;s diffable</b><span>It&rsquo;s source &mdash; version it in git, tweak one number, recompile.</span></div>
    </div>
  </section>
"""
```

- [ ] **Step 2: Add slim-strip CSS to `STYLE_CSS`**

```css
/* ---------- why-tikz (slim) ---------- */
.why-tikz-slim{max-width:980px; margin:0 auto; padding:40px 28px; text-align:center}
.wts-strip{display:grid; grid-template-columns:repeat(3,1fr); gap:26px; margin-top:18px; text-align:left}
.wts-item{display:flex; flex-direction:column; gap:4px}
.wts-item b{font:600 .95rem system-ui; color:var(--otblue)}
.wts-item span{font:.85rem/1.45 system-ui; opacity:.72}
@media(max-width:680px){.wts-strip{grid-template-columns:1fr}}
```

- [ ] **Step 3: Remove the now-dead old `.why-tikz`/`.why-grid`/`.why-card` CSS**

In `STYLE_CSS`, find and delete the old `.why-tikz`, `.why-grid`, `.why-card` rules (the old three-card layout). Verify they are not referenced elsewhere first:
```bash
grep -n "why-card\|why-grid" tools/build_site.py
```
Expected after edit: only matches (if any) are inside CSS you're deleting — no remaining HTML uses them. Remove the rules.

- [ ] **Step 4: Build and verify**

Run:
```bash
python3 tools/build_site.py && grep -q 'why-tikz-slim' site/index.html && ! grep -q 'class="why-card"' site/index.html && echo "WHYTIKZ OK"
```
Expected: prints `WHYTIKZ OK`.

- [ ] **Step 5: Commit**

```bash
git add tools/build_site.py site/
git commit -m "Slim 'Why TikZ' band to a 3-point strip

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Finalize section order + remove dead code + full verification

Put `home_page` sections in the spec order, delete the now-unused `magic_moment` function and its dead CSS/JS (old hero carousel, lightbox, old `.magic-*` card rules — but KEEP `.magic-code`/`.ml-line`/`.ml-add`, reused by the hero), and run full verification.

**Files:**
- Modify: `tools/build_site.py` — `home_page()` body order; delete `magic_moment()`; prune `STYLE_CSS` and `APP_JS` dead rules.

- [ ] **Step 1: Set the final section order in `home_page`**

Ensure the `<main class="home">` f-string body renders sections in exactly this order:

```
1. {hero showcase}     (literal markup from Task 2)
2. {demos_section}      (See it on real templates)
3. {why_opentikz}       (Why not just ask ChatGPT?)
4. {library}            (The library you're drawing from)
5. {why_tikz}           (Why TikZ — slim)
6. <section class="roadmap"> ... </section>
7. <section class="cta-band"> ... </section>
```

Move the `{library}` placeholder from its Task-3 temporary spot to position 4, and `{why_tikz}` to position 5.

- [ ] **Step 2: Delete the unused `magic_moment` function**

Confirm no remaining caller, then delete the whole `def magic_moment(...)` function:
```bash
grep -n "magic_moment" tools/build_site.py
```
Expected: after deletion, **zero** matches.

- [ ] **Step 3: Prune dead CSS in `STYLE_CSS`**

Delete CSS rules no longer referenced by any generated HTML: old hero-carousel rules (`.hero-slide`, `.hero-fig`, `.hero-zoom`, `.hero-cap`, `.hero-dot`, `.zoom-hint`), lightbox rules (`.lightbox`, `.lb-*`), and old magic-card rules (`.magic-card`, `.magic-prompt`, `.magic-body`, `.magic-pane`, `.magic-fig`, `.magic-sub`, `.magic-label`, `.how`, `.magic`). **Keep** `.magic-code`, `.ml-line`, `.ml-add` (used by the hero's view-source). Before deleting each, confirm it's unused:
```bash
for c in hero-slide hero-zoom lightbox lb-panel magic-card magic-prompt magic-pane magic-fig magic-sub; do echo "$c:"; grep -c "class=\"$c\|class=\".*$c" site/*.html site/**/*.html 2>/dev/null | grep -v ':0' || echo "  unused"; done
```
Expected: each listed class is `unused` in generated HTML before you remove its rule.

- [ ] **Step 4: Prune dead JS in `APP_JS`**

Remove the old hero-carousel initializer and the lightbox initializer from `APP_JS`. **Keep** the skills/demos carousel initializer (section 2 still uses `#skills-carousel`) and the Task-1 slider initializer. Verify the demos carousel selector is retained:
```bash
grep -q "skills-carousel" tools/build_site.py && grep -q "data-ba" tools/build_site.py && echo "JS KEPT OK"
```
Expected: prints `JS KEPT OK`.

- [ ] **Step 5: Full build + section-order verification**

Run:
```bash
python3 tools/build_site.py
python3 -c "
s=open('site/index.html').read()
order=['class=\"showcase\"','class=\"skills-demo\"','class=\"why-ot\"','class=\"library\"','why-tikz-slim','class=\"roadmap\"','class=\"cta-band\"']
pos=[s.find(x) for x in order]
assert all(p>0 for p in pos), list(zip(order,pos))
assert pos==sorted(pos), 'sections out of order: '+str(list(zip(order,pos)))
print('ORDER OK')
"
```
Expected: build exits 0; prints `ORDER OK`.

- [ ] **Step 6: Guard checks — validate + no dead refs**

Run:
```bash
python3 tools/validate.py && echo "VALIDATE OK"
grep -c "magic_moment\|hero-slide\|class=\"lightbox\"" site/index.html | grep -qx 0 && echo "NO DEAD REFS"
```
Expected: `VALIDATE OK` then `NO DEAD REFS`.

- [ ] **Step 7: Manual full-page browser check**

Open `site/index.html`. Walk top→bottom: hero slider drags and aligns; "See it on real templates" carousel still works (arrows/dots); "Why not ChatGPT" comparison renders; library grid links work; slim Why-TikZ strip; roadmap; final CTA. Resize to mobile width (~375px): no horizontal overflow, hero copy wraps, slider scales and stays usable, library grid and why-tikz strip collapse to one column.

- [ ] **Step 8: Commit**

```bash
git add tools/build_site.py site/
git commit -m "Finalize landing-page section order; remove dead carousel/lightbox/magic code

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review (completed by plan author)

**Spec coverage:**
- 7-section funnel → Tasks 2–5 (order locked in Task 5). ✓
- Figure-first hero + slider (centered, real SVGs) → Tasks 1–2. ✓
- Code de-emphasized via `<details>` view-source → Task 2. ✓
- Proof carousel reused → unchanged, ordered in Task 5 (section 2). ✓
- Why-not-ChatGPT reused → unchanged, ordered in Task 5 (section 3). ✓
- Library gallery (demoted examples + counts + Browse) → Task 3. ✓
- Slim Why-TikZ → Task 4. ✓
- magic_moment absorbed + removed → Tasks 2 & 5. ✓
- Lightbox open question → resolved to "drop" (Task 5 prunes it; gallery thumbs link to item pages). ✓
- CTA → skills/ (primary), browse/ (secondary) → Task 2. ✓
- stdlib only, no .tex/catalog changes → Global Constraints. ✓
- Asset-alignment risk → Task 2 Step 6 stop-and-report gate. ✓

**Placeholder scan:** No TBD/TODO; all code blocks are complete; copy is the agreed draft, stated verbatim. ✓

**Type consistency:** `before_after_slider` signature identical in Task 1 (definition) and Task 2 (call); `render_tex_excerpt` and `library_gallery` signatures consistent between definition and call sites; CSS class names (`.ba*`, `.lib-*`, `.wts-*`, `.hero-prompt`, `.hero-src`) consistent between markup and CSS tasks. ✓
