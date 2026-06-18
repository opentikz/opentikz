# How-it-works + README Expressiveness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the site's "How it works" section and the README *show* OpenTikZ's prompt → editable-TikZ → figure workflow and its accuracy/time advantage over raw LLM TikZ, instead of asserting it.

**Architecture:** Rebuild the home page's `how` section in `tools/build_site.py` into a four-beat narrative — a *why-TikZ* band, a *magic-moment* centerpiece (prompt + editable code + rendered figure), a *why-OpenTikZ* verdict-card band, then the existing carousel reframed as proof. The magic moment is data-driven from a `featured` entry in `skills-demos/skills-demos.json` carrying a real TikZ excerpt. The README mirrors the key parts in condensed markdown.

**Tech Stack:** Python 3 stdlib only (no new deps), single-file static-site generator (`tools/build_site.py`), inline `STYLE_CSS`. No JS framework. No test runner in this repo — verification is "build the site, then grep the generated `site/index.html` / CSS for expected markers."

## Global Constraints

- **Stdlib only** — `tools/build_site.py` must not gain third-party imports.
- **Palette discipline** — content `.tex` colors come from the shared palette, never raw inline hex. (The new TikZ *excerpt* uses palette colors `otblue`/`otteal` etc.) The site stylesheet `STYLE_CSS` may use hex consistent with its existing style; prefer `var(--ot*)` where a palette color fits.
- **Everything shown is committed source** — no mockups in the final build; the magic-moment figure is the committed `skills-demos/encdec-xattn.svg`, and its code excerpt is faithful to `templates/encoder-decoder/template.tex` (real macros `\xdC`, `\bh`, `\trapW`, `flow` style, `otblue`).
- **Fair tone** — the "raw LLM TikZ" card lists real, common failure modes; not a strawman.
- **`catalog.json`, `validate.py`, `meta.schema.json` are untouched** — presentation only.
- **`site/` is gitignored** — commits contain source only; build locally to verify.
- **Build command:** `python3 tools/build_site.py` (needs `catalog.json`, already committed).
- **Preview command:** `python3 -m http.server -d site` → http://localhost:8000

---

## File Structure

- `skills-demos/skills-demos.json` — add `featured: true` + `tex_excerpt` to the encoder-decoder entry. *Responsibility: data for the magic-moment centerpiece.*
- `tools/build_site.py` — three new builder functions (`magic_moment`, `why_tikz_band`, `why_opentikz_band`), wired into `home_page()`; the static `how` section is removed; the carousel heading is reframed; new CSS appended to `STYLE_CSS`. *Responsibility: render the four-beat home page.*
- `README.md` — reordered Quick start (AI workflow leads), new "Why TikZ, and why OpenTikZ" section with comparison table + concrete edit, gallery moved below. *Responsibility: GitHub-facing positioning.*

---

## Task 1: Data — flag the featured demo and add its TikZ excerpt

**Files:**
- Modify: `skills-demos/skills-demos.json` (the `encoder-decoder` entry)

**Interfaces:**
- Produces: a demo object with `featured: true` and `tex_excerpt` (a string; lines beginning with `+` are AI-added lines). `magic_moment()` in Task 2 consumes both.

- [ ] **Step 1: Write the failing check**

Run (expects the field to be absent *before* the change):

```bash
python3 -c "import json; d=json.load(open('skills-demos/skills-demos.json')); print(sum(1 for x in d if x.get('featured')))"
```

Expected now: `0`

- [ ] **Step 2: Edit the encoder-decoder entry**

Replace the encoder-decoder object (currently the third entry) so it reads exactly:

```json
  {
    "dimension": "structural",
    "dimension_label": "Structural edit",
    "template_id": "encoder-decoder",
    "prompt": "add a cross-attention block and make it blue",
    "before_svg": "encdec-before.svg",
    "after_svg": "encdec-xattn.svg",
    "changed": "A blue cross-attention block added — the decoder now attends to the encoder (a documented skill op).",
    "featured": true,
    "tex_excerpt": "  % decoder → output (existing)\n  \\draw[flow] (\\xdR,0) -- (\\xoL,0);\n+ % cross-attention block (decoder attends to encoder)\n+ \\node[draw=otblue!80!black, fill=otblue!18, rounded corners=2pt,\n+   minimum width=\\trapW cm, minimum height=0.7cm]\n+   (xattn) at (\\xdC,\\bh+0.9) {\\sffamily\\small Cross-Attn};\n+ \\draw[flow, draw=otblue] (enc) to[bend left=20] (xattn);\n+ \\draw[flow, draw=otblue] (xattn) -- (dec);"
  }
```

- [ ] **Step 3: Run the check to verify it passes**

```bash
python3 -c "import json; d=json.load(open('skills-demos/skills-demos.json')); f=[x for x in d if x.get('featured')]; print(len(f), 'featured;', 'tex_excerpt' in f[0])"
```

Expected: `1 featured; True`

- [ ] **Step 4: Confirm the site still builds with the new data**

```bash
python3 tools/build_site.py && echo OK
```

Expected: ends with the `built site/ …` line then `OK` (no traceback).

- [ ] **Step 5: Commit**

```bash
git add skills-demos/skills-demos.json
git commit -m "Site: flag encoder-decoder demo featured + add TikZ excerpt for magic moment"
```

---

## Task 2: Build the four-beat home page (builders + wiring)

**Files:**
- Modify: `tools/build_site.py` — add three functions near `demos_carousel` (after it, ~line 330); edit `home_page()` body; reframe the carousel heading inside `demos_carousel`.

**Interfaces:**
- Consumes: `skills-demos.json` `featured` demo + `tex_excerpt` (Task 1); module-level `html` (already imported); `by_id` and `demos` already available inside `home_page()`.
- Produces: `magic_moment(demos, by_id, prefix="") -> str`, `why_tikz_band() -> str`, `why_opentikz_band() -> str`. The home page emits sections in order: why-tikz → magic (`id="how"`) → why-opentikz → carousel.

- [ ] **Step 1: Write the failing check**

Using the site built at the end of Task 1, confirm the new markers are absent:

```bash
grep -c "magic-card\|why-tikz\|cmp-cards" site/index.html
```

Expected: `0`

- [ ] **Step 2: Add the three builder functions**

Insert immediately **after** the end of `demos_carousel` (just before `def home_page(`):

```python
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
```

- [ ] **Step 3: Wire the new sections into `home_page()` and remove the static `how` block**

In `home_page()`, find the line `    demos_section = demos_carousel(demos, by_id)` (near the top of the function) and add the three computed sections right after it:

```python
    demos_section = demos_carousel(demos, by_id)
    magic = magic_moment(demos, by_id)
    why_tikz = why_tikz_band()
    why_opentikz = why_opentikz_band()
```

Then in the returned f-string, replace this exact block:

```python
{lightbox}
  <section class="how" id="how">
    <h2>How it works</h2>
    <ol class="steps">
      <li><span class="step-n">1</span><h3>Clone the repo</h3>
        <p>Pull OpenTikZ into your project — the icons, templates, and the <strong>using-opentikz</strong> skill come with it.</p></li>
      <li><span class="step-n">2</span><h3>Describe the diagram</h3>
        <p>Tell your AI agent the figure you want — "a training pipeline with two GPUs feeding a transformer," in plain words.</p></li>
      <li><span class="step-n">3</span><h3>The agent assembles it</h3>
        <p>Guided by the skill, the agent reuses the existing icons, blocks, and templates to build editable TikZ — no hand-writing from scratch.</p></li>
    </ol>
  </section>
{demos_section}
```

with:

```python
{lightbox}
{why_tikz}
{magic}
{why_opentikz}
{demos_section}
```

(Order: hero → why-tikz → magic moment (`#how`) → why-opentikz → carousel. The hero "See how it's built" link targets `#how`, which now lands on the magic moment — preserved.)

- [ ] **Step 4: Reframe the carousel heading as proof**

Inside `demos_carousel()`'s returned f-string, change:

```python
    <h2>Skills in action</h2>
    <p class="skills-sub">One prompt, one precise edit — across different kinds of change.</p>
```

to:

```python
    <h2>See it on real templates</h2>
    <p class="skills-sub">Every before/after is rendered from committed source — the same kind of edit, across different templates.</p>
```

- [ ] **Step 5: Build and verify the markers now appear in order**

```bash
python3 tools/build_site.py && \
python3 - <<'PY'
h = open('site/index.html').read()
for m in ('why-tikz','magic-card','ml-add','cmp-cards','See it on real templates'):
    assert m in h, f"MISSING: {m}"
# order: why-tikz before magic before why-ot before carousel
order = [h.index('why-tikz'), h.index('magic-card'), h.index('cmp-cards'), h.index('skills-carousel')]
assert order == sorted(order), f"OUT OF ORDER: {order}"
# the real prompt text shows in the magic moment
assert 'add a cross-attention block and make it blue' in h
print("OK", order)
PY
```

Expected: `OK [ ... ascending four numbers ... ]`

- [ ] **Step 6: Commit**

```bash
git add tools/build_site.py
git commit -m "Site: rebuild How-it-works into why-TikZ + magic-moment + why-OpenTikZ"
```

---

## Task 3: Style the new sections

**Files:**
- Modify: `tools/build_site.py` — append CSS to `STYLE_CSS` after the `.steps p{…}` rule (line ~1002, before `.cta-band{…}`).

**Interfaces:**
- Consumes: markup classes produced in Task 2 (`magic*`, `ml-line`, `ml-add`, `why-tikz`, `why-grid`, `why-card`, `why-ot`, `why-ot-sub`, `cmp-cards`, `cmp-card`, `cmp-bad`, `cmp-good`) and existing CSS vars (`--otblue`, `--otteal`, `--line`, `--ink`, `--paper`, `--muted`, `--shadow`).

- [ ] **Step 1: Write the failing check**

```bash
grep -c "\.magic-card{\|\.why-grid{\|\.cmp-cards{" tools/build_site.py
```

Expected: `0`

- [ ] **Step 2: Insert the CSS**

Find this exact line in `STYLE_CSS`:

```css
.steps p{margin:0; color:#4a473f; font-size:.95rem}
```

Insert immediately **after** it:

```css

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
```

- [ ] **Step 3: Build and verify the CSS is present and the page references it**

```bash
python3 tools/build_site.py && \
grep -q "\.magic-card{" site/assets/style.css && \
grep -q "\.cmp-good h3::before" site/assets/style.css && \
echo "CSS OK"
```

Expected: `CSS OK`

- [ ] **Step 4: Eyeball the result in a browser**

```bash
python3 -m http.server -d site 8000
```

Open http://localhost:8000 — confirm, top to bottom: hero → **Why TikZ** (3 cards) → **How it works** magic moment (prompt, dark code panel with green-highlighted added lines on the left, rendered encoder-decoder figure on the right) → **Why not just ask ChatGPT** (two verdict cards, ✗ red / ✓ teal) → **See it on real templates** carousel. Resize narrow to confirm columns stack. Ctrl-C to stop.

- [ ] **Step 5: Commit**

```bash
git add tools/build_site.py
git commit -m "Site: style why-TikZ band, magic-moment centerpiece, verdict cards"
```

---

## Task 4: Rewrite the README lead and add the why-section

**Files:**
- Modify: `README.md` — Quick start (ll. ~12–19) and insert a new section before `## Gallery` (l. ~21).

**Interfaces:**
- Consumes: nothing from earlier tasks (independent prose). The TikZ snippet matches Task 1's `tex_excerpt` for consistency.

- [ ] **Step 1: Replace the Quick start block**

Replace this exact block:

```markdown
## Quick start

1. Browse the **[gallery](#gallery)** below and pick an icon, template, or example.
2. Copy its `.tex` into your project — every file compiles standalone with
   `pdflatex`, `lualatex`, or `xelatex`, no extra setup.
3. Want changes? Tell Claude Code *"add a hidden layer / recolor this blue / fit
   it to a CVPR column"* — the `using-opentikz` skill plus each template's
   `edit_contract` guide the AI to edit it correctly.
```

with:

```markdown
## Quick start

The fastest path is to let an AI agent do the TikZ for you:

1. **Clone OpenTikZ into your project** — the icons, templates, and the
   `using-opentikz` skill come with it.
2. **Tell Claude Code the figure or edit you want** — *"draw an encoder–decoder
   with a cross-attention block,"* or, pointing at a template, *"add a hidden
   layer / recolor this blue / fit it to a CVPR column."* The skill plus each
   template's `edit_contract` guide the agent to edit real TikZ correctly.
3. **Get editable TikZ that compiles** — every file is
   `\documentclass{standalone}`, so it builds with `pdflatex`, `lualatex`, or
   `xelatex`, no extra setup.

Prefer to grab one by hand? **[Browse the gallery](#gallery)**, copy its `.tex`,
and you're done — no AI required.
```

- [ ] **Step 2: Insert the why-section before `## Gallery`**

Immediately before the line `## Gallery`, insert:

```markdown
## Why TikZ, and why OpenTikZ

**Why TikZ at all?** A TikZ figure is *source code*, not an image:

- **Vector quality** — crisp at any zoom, sharp in print; no pixelated screenshots.
- **Native to your paper** — same fonts, math (`$\mathbf{W}x$`), and
  `\ref`/`\cite` as the document, so the figure looks part of the paper.
- **Diffable** — version it in git, tweak one number, recompile.

**Why not just ask ChatGPT for TikZ directly?** You can — but raw LLM TikZ tends
to fight you. OpenTikZ anchors the edit to a real, parametric template:

| What you care about | Raw LLM TikZ | OpenTikZ + skill |
| --- | --- | --- |
| Compiles first try | Often not | Yes, standalone |
| Packages / macros | Sometimes invented | Real, declared in `requires` |
| Colors | Random hex | Shared palette |
| Re-editing later | Re-describe everything | Stable node names |
| AI guidance | None | Each template ships an `edit_contract` |

Because every template is parametric, palette-correct, and carries an
`edit_contract`, an agent edits it **accurately** and **fast** instead of
hand-writing TikZ that may not compile.

### A concrete edit

Starting from [`templates/encoder-decoder/`](templates/encoder-decoder/), tell
Claude Code:

> *"add a cross-attention block and make it blue"*

Guided by the template's `edit_contract` — using the shared palette and the
template's stable node names — it adds:

```tex
% cross-attention block (decoder attends to encoder)
\node[draw=otblue!80!black, fill=otblue!18, rounded corners=2pt,
  minimum width=\trapW cm, minimum height=0.7cm]
  (xattn) at (\xdC,\bh+0.9) {\sffamily\small Cross-Attn};
\draw[flow, draw=otblue] (enc) to[bend left=20] (xattn);
\draw[flow, draw=otblue] (xattn) -- (dec);
```

…and it compiles standalone, first try.

```

- [ ] **Step 3: Verify the README structure**

```bash
python3 - <<'PY'
r = open('README.md').read()
for m in ('## Why TikZ, and why OpenTikZ', '| Compiles first try |', 'add a cross-attention block and make it blue', 'no AI required'):
    assert m in r, f"MISSING: {m}"
# why-section sits above the gallery
assert r.index('## Why TikZ, and why OpenTikZ') < r.index('## Gallery'), "why-section not above gallery"
# quick start leads with the AI path, not "Browse the gallery below and pick"
assert 'let an AI agent do the TikZ for you' in r
print("README OK")
PY
```

Expected: `README OK`

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "README: lead with AI workflow; add Why-TikZ / Why-OpenTikZ section"
```

---

## Task 5: Full-site integration check

**Files:** none modified — verification + final confirmation.

- [ ] **Step 1: Clean build**

```bash
rm -rf site && python3 tools/build_catalog.py && python3 tools/build_site.py && echo BUILT
```

Expected: `…built site/…` then `BUILT`, no traceback.

- [ ] **Step 2: Confirm `catalog.json` did not change** (we only touched presentation)

```bash
git status --porcelain catalog.json
```

Expected: empty output (no diff).

- [ ] **Step 3: Final visual pass**

```bash
python3 -m http.server -d site 8000
```

Open http://localhost:8000 and the skills page http://localhost:8000/skills/ — confirm the home page reads as the four-beat story and nothing regressed (hero carousel, lightbox, footer). Ctrl-C to stop.

- [ ] **Step 4: Confirm the working tree is clean**

```bash
git status --short
```

Expected: empty (all changes committed across Tasks 1–4; `site/` is gitignored).

---

## Self-Review (completed during planning)

- **Spec coverage:** why-TikZ band → Task 2/3; magic moment (layout B) → Tasks 1–3; why-OpenTikZ verdict cards (layout A) → Task 2/3; carousel reframe → Task 2; data-model `featured`+`tex_excerpt` → Task 1; README reorder + table + walkthrough + gallery-below → Task 4; honesty constraints → Global Constraints + Task 1. All spec sections map to a task.
- **Placeholder scan:** no TBD/TODO; every code/CSS/markdown block is complete and literal.
- **Type/name consistency:** `magic_moment(demos, by_id, prefix="")`, `why_tikz_band()`, `why_opentikz_band()` are defined in Task 2 and called with those exact names/signatures in `home_page()`; CSS classes in Task 3 match the markup emitted in Task 2 (`magic-card`, `ml-add`, `why-grid`, `cmp-cards`, `cmp-bad`, `cmp-good`); the README TikZ snippet matches Task 1's `tex_excerpt` (minus the diff `+` markers and context line).
- **Note on hex:** the no-raw-hex rule governs content `.tex`, not the site stylesheet; the new CSS uses hex consistent with the existing `STYLE_CSS` and palette vars where a palette color applies — this corrects the spec's over-broad verification line.
