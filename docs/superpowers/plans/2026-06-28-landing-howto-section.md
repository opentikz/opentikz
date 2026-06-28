# Landing "How to use" Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tabbed, auto-rotating "How to use" scenario carousel to the landing page (four usage scenarios), and delete two redundant hero/footer lines.

**Architecture:** Data-driven from a new `skills-demos/landing-howto.json` manifest. A new `howto_carousel()` renderer in `tools/build_site.py` (mirrors the existing `demos_carousel()`) emits a `.carousel` that **reuses the existing `.demo-slide`/`.demo-dot` classes**, so `site/assets/app.js`'s per-instance carousel logic drives it with **zero JS changes**. Two slide layouts: `steps` (a 1-2-3 workflow) and `inout` (input→output). Ships with real assets for scenarios ①②④; scenario ③ is a labeled placeholder until the owner supplies a real PNG→TikZ asset.

**Tech Stack:** Python 3 stdlib static-site generator (`tools/build_site.py`), JSON manifest, `tools/render_preview.py` (LaTeX→SVG), existing `app.js` carousel.

## Global Constraints

- Scope is the **landing page only**. Do NOT touch `/skills/` (`skills_page`), `README.md`, or `CLAUDE.md` this round.
- `tools/build_site.py` stays **stdlib-only** and builds HTML via f-strings (literal braces doubled `{{ }}`).
- **No new JS / carousel library** — reuse `.carousel` + `app.js` by emitting `.demo-slide` slides and `.demo-dot` dots inside a sibling `.car-dots`, exactly as `demos_carousel()` does. Autoplay via `data-autoplay data-interval="5000"`.
- **No mockups:** scenario ④'s output must be a real skill-produced figure rendered from committed source; scenario ③ must render an explicit "sample coming" placeholder, never a faked result.
- The existing "See it on real templates" demos carousel **stays** and is unchanged.
- `site/` is gitignored — never commit it. `catalog.json` is auto-generated — don't hand-edit.
- Four scenarios, in order: ① Use icons (`steps`); ② Edit a template (`inout`); ③ PNG → TikZ (`inout`, placeholder); ④ Describe → TikZ (`inout`).
- Scenario ④ prompt (chosen default, distinct from ②'s encoder-decoder): **"draw a training pipeline: dataset → model → loss → optimizer"** → produces the `training-pipeline` template figure.

---

### Task 1: Delete redundant hero + footer lines

**Files:**
- Modify: `tools/build_site.py` — `home_page()`

**Interfaces:**
- Produces: a home page whose hero `<section class="showcase">` ends at the `.cta-row` buttons, and whose bottom `.cta-band` has no counts line.

- [ ] **Step 1: Remove the two hero lines**

In `home_page()`, delete these two consecutive lines inside `<section class="showcase">`:

```python
    <p class="cta-sub">{counts.get('icon',0)} icons &middot; {counts.get('template',0)} templates &middot; {counts.get('example',0)} examples &middot; content <code>CC0&nbsp;1.0</code></p>
    <p class="show-alt">Prefer no AI? <a href="browse/">Browse the library</a> and copy any figure&rsquo;s <code>.tex</code> by hand.</p>
```

The `</section>` that followed them stays; the `.cta-row` buttons above them stay.

- [ ] **Step 2: Remove the bottom CTA-band counts line**

In `home_page()`, inside `<section class="cta-band">`, delete:

```python
    <p class="cta-sub">{counts.get('icon', 0)} icons · {counts.get('template', 0)} templates · {counts.get('example', 0)} examples · content <code>CC0&nbsp;1.0</code></p>
```

(The `<h2>` and the `Browse the library →` button in that band stay.)

- [ ] **Step 3: Remove the now-dead `.show-alt` CSS rule**

Delete the rule added previously (search the CSS block for it):

```python
.show-alt{color:var(--muted); font-size:.82rem; margin:.8em 0 0}
```

(Leave `.cta-sub` — it is general and may be reused elsewhere; only the markup lines are removed.)

- [ ] **Step 4: Rebuild and assert the lines are gone**

Run: `python3 tools/build_site.py`
Expected: completes without error.

Run: `grep -c "Prefer no AI" site/index.html`
Expected: `0`

Run: `grep -c "icons &middot;\|icons ·" site/index.html`
Expected: `0`

- [ ] **Step 5: Commit**

```bash
git add tools/build_site.py
git commit -m "Home: drop the counts line and the Prefer-no-AI line"
```

---

### Task 2: Generate scenario ④'s real "describe → TikZ" asset

**Files:**
- Create: `skills-demos/howto-describe.tex` (copied from the matched template)
- Create: `skills-demos/howto-describe.svg` (rendered preview)

**Interfaces:**
- Produces: `skills-demos/howto-describe.svg`, the real figure the skill yields for the scenario-④ prompt; Task 3's manifest references it as scenario ④'s `output_img`.

This task performs the scenario-④ flow for real (skill Mode A: a description matches a library template, which is produced and rendered). The prompt "draw a training pipeline…" matches `templates/training-pipeline/`.

- [ ] **Step 1: Copy the matched template's source as the produced figure**

Run:
```bash
cp templates/training-pipeline/template.tex skills-demos/howto-describe.tex
```

- [ ] **Step 2: Render it to SVG with the project tool**

Run: `python3 tools/render_preview.py skills-demos/howto-describe.tex -o skills-demos/howto-describe.svg`
Expected: exits 0 and writes `skills-demos/howto-describe.svg`. (Needs the LaTeX toolchain; this repo compiles previews already.)

- [ ] **Step 3: Verify the asset exists and is non-empty SVG**

Run: `test -s skills-demos/howto-describe.svg && head -c 60 skills-demos/howto-describe.svg`
Expected: prints the start of an `<?xml`/`<svg` document (non-empty).

- [ ] **Step 4: Commit**

```bash
git add skills-demos/howto-describe.tex skills-demos/howto-describe.svg
git commit -m "Assets: scenario 4 describe->TikZ figure (training pipeline), rendered from source"
```

---

### Task 3: Manifest + assets + renderer + build wiring + home insertion

**Files:**
- Create: `skills-demos/landing-howto.json`
- Create: `skills-demos/howto-icon.svg` (copied from a committed icon)
- Modify: `tools/build_site.py` — add `howto_carousel()`, extend `home_page()` signature + insert the section, wire `build()` to load the manifest + copy assets

**Interfaces:**
- Consumes: `skills-demos/howto-describe.svg` (Task 2); existing `skills-demos/encdec-before.svg`, `skills-demos/encdec-xattn.svg`.
- Produces: `howto_carousel(scenarios: list[dict], prefix: str = "") -> str`; `home_page(featured, by_id, counts, demos, howto, css_href)` (new `howto` param before `css_href`).

- [ ] **Step 1: Add the scenario-① icon asset**

Run:
```bash
cp icons/systems/server/server.svg skills-demos/howto-icon.svg
```

- [ ] **Step 2: Write the manifest**

Create `skills-demos/landing-howto.json`:

```json
[
  {
    "id": "use-icons",
    "tab_label": "Use icons",
    "layout": "steps",
    "steps": [
      {"img": "howto-icon.svg", "text": "Browse to find an icon"},
      {"code": ".tex · SVG · PNG", "text": "Copy the .tex (or download SVG/PNG)"},
      {"img": "howto-icon.svg", "text": "\\input it into your figure"}
    ],
    "caption": "Grab a single icon — no AI needed."
  },
  {
    "id": "edit-template",
    "tab_label": "Edit a template",
    "layout": "inout",
    "input_img": "encdec-before.svg",
    "prompt": "add a cross-attention block and make it blue",
    "output_img": "encdec-xattn.svg",
    "caption": "Tell the agent the change; it edits the template and verifies it compiles."
  },
  {
    "id": "png-to-tikz",
    "tab_label": "PNG → TikZ",
    "layout": "inout",
    "placeholder": true,
    "prompt": "turn this figure into editable TikZ",
    "caption": "Hand the agent a figure image; get editable TikZ back. (sample coming)"
  },
  {
    "id": "describe-to-tikz",
    "tab_label": "Describe → TikZ",
    "layout": "inout",
    "input_text": "draw a training pipeline: dataset → model → loss → optimizer",
    "output_img": "howto-describe.svg",
    "caption": "Describe a figure in words; the agent drafts it from the library."
  }
]
```

- [ ] **Step 3: Add the `howto_carousel()` renderer**

In `tools/build_site.py`, immediately after `demos_carousel()` (ends near line 330), add:

```python
def howto_carousel(scenarios: list[dict], prefix: str = "") -> str:
    """Landing 'How to use' carousel; one slide per usage scenario. Empty -> ''.
    Reuses the .demo-slide/.demo-dot classes so app.js drives it unchanged.
    Two layouts: 'steps' (a 1-2-3 workflow) and 'inout' (input -> output).
    ``prefix`` adjusts the howto/ asset path for surface depth ('' on Home)."""
    if not scenarios:
        return ""
    slides, dots = "", ""
    for i, s in enumerate(scenarios):
        label = html.escape(s.get("tab_label", ""))
        active = " active" if i == 0 else ""
        caption = (f'<p class="howto-cap">{html.escape(s["caption"])}</p>'
                   if s.get("caption") else "")
        if s.get("layout") == "steps":
            cells = ""
            for n, st in enumerate(s.get("steps", []), start=1):
                if st.get("img"):
                    vis = (f'<img src="{prefix}howto/{html.escape(st["img"])}" '
                           f'alt="" loading="lazy">')
                else:
                    vis = f'<code>{html.escape(st.get("code", ""))}</code>'
                cells += (f'<div class="howto-step"><span class="howto-step-n">{n}</span>'
                          f'<div class="howto-step-vis">{vis}</div>'
                          f'<p class="howto-step-cap">{html.escape(st.get("text", ""))}</p></div>')
            body = f'<div class="howto-steps">{cells}</div>'
        else:  # inout
            if s.get("placeholder"):
                in_cell = '<div class="howto-cell howto-ph">sample coming</div>'
                out_cell = '<div class="howto-cell howto-ph">preview coming</div>'
            elif s.get("input_img"):
                in_cell = (f'<figure class="howto-cell"><img src="{prefix}howto/'
                           f'{html.escape(s["input_img"])}" alt="input" loading="lazy">'
                           f'<figcaption>input</figcaption></figure>')
                out_cell = (f'<figure class="howto-cell"><img src="{prefix}howto/'
                            f'{html.escape(s["output_img"])}" alt="output" loading="lazy">'
                            f'<figcaption>editable TikZ</figcaption></figure>')
            else:
                in_cell = (f'<div class="howto-cell howto-intext">'
                           f'<code>&ldquo;{html.escape(s.get("input_text", ""))}&rdquo;</code>'
                           f'<figcaption>describe</figcaption></div>')
                out_cell = (f'<figure class="howto-cell"><img src="{prefix}howto/'
                            f'{html.escape(s["output_img"])}" alt="output" loading="lazy">'
                            f'<figcaption>editable TikZ</figcaption></figure>')
            prompt_lbl = (f'<span class="howto-prompt">&ldquo;{html.escape(s["prompt"])}&rdquo;</span>'
                          if s.get("prompt") else "")
            body = (f'<div class="howto-flow">{in_cell}'
                    f'<div class="howto-arrow">{prompt_lbl}<span>&rarr;</span></div>'
                    f'{out_cell}</div>')
        slides += f"""      <div class="demo-slide{active}" data-slide="{i}">
        <div class="howto-head"><span class="howto-label">{label}</span></div>
        {body}
        {caption}
      </div>
"""
        dots += (f'<button class="demo-dot{active}" data-dot="{i}" aria-label="{label}">'
                 f'<span>{label}</span></button>')
    return f"""
  <section class="howto">
    <h2>How to use it</h2>
    <p class="skills-sub">Four ways in &mdash; from copying one icon to describing a whole figure.</p>
    <div class="carousel howto-carousel" id="howto-carousel" tabindex="0" data-autoplay data-interval="5000" aria-roledescription="carousel" aria-label="How to use OpenTikZ">
      <button class="car-nav car-prev" aria-label="Previous">&larr;</button>
      <div class="car-track">
{slides}      </div>
      <button class="car-nav car-next" aria-label="Next">&rarr;</button>
    </div>
    <div class="car-dots">{dots}</div>
  </section>
"""
```

- [ ] **Step 4: Thread `howto` through `home_page()`**

Change the signature (line ~407):

```python
def home_page(featured: list[dict], by_id: dict, counts: dict, demos: list[dict], howto: list[dict], css_href: str) -> str:
```

Just below `demos_section = demos_carousel(demos, by_id)` add:

```python
    howto_section = howto_carousel(howto)
```

Insert the section between the hero showcase and the demos carousel — change:

```python
  </section>
{demos_section}
```

to:

```python
  </section>
{howto_section}
{demos_section}
```

- [ ] **Step 5: Wire `build()` to load the manifest and copy assets**

In `build()`, immediately after the existing demos-loading block (the one that ends copying into `site / "demos"`), add:

```python
    # Landing 'How to use' scenarios (content-driven). Copy referenced assets
    # into site/howto/; the section auto-hides if the manifest is absent/empty.
    howto: list[dict] = []
    howto_json = root / "skills-demos" / "landing-howto.json"
    if howto_json.exists():
        howto = json.loads(howto_json.read_text(encoding="utf-8"))
        (site / "howto").mkdir(exist_ok=True)
        for s in howto:
            names = [st.get("img") for st in s.get("steps", [])]
            names += [s.get("input_img"), s.get("output_img")]
            for name in filter(None, names):
                src = root / "skills-demos" / name
                if src.exists():
                    shutil.copyfile(src, site / "howto" / name)
```

Update the `home_page(...)` call (line ~746) to pass `howto`:

```python
        home_page(featured, by_id, counts, demos, howto, "assets/style.css"), encoding="utf-8")
```

- [ ] **Step 6: Rebuild and assert the section + assets**

Run: `python3 tools/build_catalog.py && python3 tools/build_site.py`
Expected: completes without error.

Run: `grep -c 'id="howto-carousel"' site/index.html`
Expected: `1`

Run: `grep -c "Describe &rarr; TikZ\|Describe → TikZ" site/index.html`
Expected: `1`

Run: `grep -c "sample coming" site/index.html`
Expected: `1`

Run: `ls site/howto/`
Expected: lists `howto-icon.svg`, `encdec-before.svg`, `encdec-xattn.svg`, `howto-describe.svg`.

- [ ] **Step 7: Commit**

```bash
git add skills-demos/landing-howto.json skills-demos/howto-icon.svg tools/build_site.py
git commit -m "Home: data-driven How-to-use carousel (4 scenarios), reuses app.js carousel"
```

---

### Task 4: Style the "How to use" section

**Files:**
- Modify: `tools/build_site.py` — the embedded `STYLE_CSS` block

**Interfaces:**
- Consumes: the class names emitted by `howto_carousel()` (`.howto`, `.howto-carousel`, `.howto-head`, `.howto-label`, `.howto-steps`, `.howto-step`, `.howto-step-n`, `.howto-step-vis`, `.howto-step-cap`, `.howto-flow`, `.howto-cell`, `.howto-intext`, `.howto-arrow`, `.howto-prompt`, `.howto-ph`, `.howto-cap`).

- [ ] **Step 1: Add the section CSS**

In `STYLE_CSS` (after the `.skills-demo` / demo carousel rules), add. Use existing palette vars only — no raw hex:

```python
.howto{margin:30px 0 0; text-align:center}
.howto h2{font-family:"Fraunces",serif; font-weight:600; font-size:1.5rem; margin:0 0 .2em}
.howto-carousel .demo-slide{min-height:300px}            /* fixed height: no section jump */
.howto-head{margin:0 0 12px}
.howto-label{font:500 .82rem/1 "IBM Plex Mono",monospace; color:var(--otblue);
  border:1px solid var(--line-strong); border-radius:999px; padding:5px 12px}
/* steps layout */
.howto-steps{display:grid; grid-template-columns:repeat(3,1fr); gap:16px; align-items:start}
.howto-step{border:1px solid var(--line); border-radius:8px; padding:14px}
.howto-step-n{display:inline-grid; place-items:center; width:24px; height:24px; border-radius:999px;
  background:var(--otblue); color:#fff; font:600 .8rem/1 "IBM Plex Mono",monospace}
.howto-step-vis{min-height:64px; display:grid; place-items:center; margin:10px 0}
.howto-step-vis img{max-height:64px; width:auto}
.howto-step-cap{margin:0; color:var(--muted); font-size:.85rem}
/* inout layout */
.howto-flow{display:grid; grid-template-columns:1fr auto 1fr; gap:14px; align-items:center}
.howto-cell{margin:0; border:1px solid var(--line); border-radius:8px; padding:12px;
  display:grid; place-items:center; min-height:150px}
.howto-cell img{max-height:130px; width:auto}
.howto-cell figcaption{font-family:"IBM Plex Mono",monospace; font-size:.7rem; color:var(--muted); margin-top:6px}
.howto-intext code{font-size:.85rem; color:var(--ink)}
.howto-ph{color:var(--muted); font-family:"IBM Plex Mono",monospace; font-size:.8rem;
  border-style:dashed}
.howto-arrow{display:grid; gap:6px; justify-items:center; color:var(--muted)}
.howto-prompt{font-family:"IBM Plex Mono",monospace; font-size:.72rem; color:var(--otblue); max-width:18ch}
.howto-cap{margin:14px auto 0; max-width:60ch; color:var(--muted); font-size:.9rem}
```

- [ ] **Step 2: Add the mobile stacking rule**

In the existing mobile `@media` block (the one near the bottom that already restacks `.demo-trip` to one column), add:

```python
  .howto-steps,.howto-flow{grid-template-columns:1fr}
  .howto-arrow span{transform:rotate(90deg); display:inline-block}
```

- [ ] **Step 3: Rebuild and assert CSS landed**

Run: `python3 tools/build_site.py`
Expected: completes without error.

Run: `grep -c "\.howto-flow{" site/assets/style.css`
Expected: `1`

Run: `grep -c "accent\|#[0-9a-fA-F]\{6\}" tools/build_site.py | xargs -I{} echo "raw-hex check ran"`
Then manually confirm no NEW raw hex was introduced in the howto rules (the `#fff` in `.howto-step-n` is the one allowed exception for badge contrast; if the file forbids even that, swap to an existing light var).
Expected: only `#fff` appears in the new rules.

- [ ] **Step 4: Visual smoke check (local server)**

Run: `python3 -m http.server 8000 -d site` (background) then
`curl -s http://localhost:8000/ | grep -c "howto-carousel"`
Expected: `1`. Then stop the server.

- [ ] **Step 5: Commit**

```bash
git add tools/build_site.py
git commit -m "Home: style the How-to-use carousel (steps + inout layouts, tabs)"
```

---

## Self-Review

**Spec coverage:**
- Part 1 deletions (hero counts, show-alt, cta-band counts) → Task 1. ✓
- Part 2 new section between hero and demos, reusing carousel, two layouts, autoplay → Tasks 3 (render/insert) + 4 (CSS). ✓
- Part 3 assets: ① icon step-strip → Task 3 (howto-icon.svg + steps); ② reuse demo pair → Task 3 manifest; ③ placeholder → Task 3 manifest + Task 4 `.howto-ph`; ④ real skill figure → Task 2. ✓
- Part 4 data model (`landing-howto.json` + renderer + build wiring) → Task 3. ✓
- Demos carousel stays / coexists → no task removes it; section inserted before it. ✓
- Non-goals (no `/skills/`, `README`, `CLAUDE.md`; no new JS) → respected; Task 3 reuses `.demo-slide`/`.demo-dot`, no `app.js` edit. ✓

**Placeholder scan:** No "TBD"/"appropriate"/"handle edge cases". Scenario ③'s "placeholder" is intentional rendered behavior, not a plan gap. Task 4 Step 3's raw-hex check is a concrete instruction with an explicit allowed exception (`#fff`), not a vague directive.

**Type/string consistency:** `howto` (param/var), `howto_carousel` (fn), `landing-howto.json`, `howto-describe.svg`, `howto-icon.svg`, `#howto-carousel`, class names — all used identically across Tasks 2–4. `home_page(..., howto, css_href)` signature and its call site both updated in Task 3 (Steps 4 + 5). Manifest field names (`tab_label`, `layout`, `steps`, `input_img`, `input_text`, `output_img`, `prompt`, `placeholder`, `caption`) match the renderer's `.get(...)` keys exactly.

**Known follow-ups (not blockers):** scenario ③ stays a placeholder until the owner supplies a real PNG→TikZ asset (then: add `input_img`/`output_img`, set `placeholder:false`, drop the asset into `skills-demos/`, rebuild). Scenario ④'s prompt is a chosen default ("training pipeline"), swappable in the manifest.
