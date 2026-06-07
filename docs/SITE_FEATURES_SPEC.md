# Spec — Item downloads · Skills demo · Roadmap teaser

Status: **ready to implement** (B has a content prerequisite). Owner: SDE agent.
Site work in `tools/build_site.py` + its inlined `app.js` (stdlib only — **no new
deps, no TeX needed for the build**). Build: `python3 tools/build_site.py`.

Guardrails unchanged: editorial-blueprint identity, no framework, Home = marketing,
keep `validate.py --strict` / `build_catalog.py --check` green, `site/` gitignored.

---

## Feature A — Download SVG / PNG / .tex on item pages

Add a small **Download** control to every item page (icons, templates, examples),
near the preview or the code block. All client-side — **does not** add build deps or
require TeX/rsvg.

- **SVG** — direct link to the committed preview: `<a href="../previews/<id>.svg"
  download="<id>.svg">`. Zero-cost (the figure SVG already ships).
- **.tex** — a button that builds a `Blob` from the already-inlined source
  (`#src` textContent) and downloads it as the original filename (e.g.
  `template.tex` / `<id>.tex`). Reuses what's on the page; no extra file copy.
- **PNG** — client-side rasterization (keeps the generator stdlib-only):
  1. Load the preview SVG into an `Image` (same-origin → no canvas taint).
  2. Draw to a `<canvas>` sized `naturalW*scale × naturalH*scale` with `scale≈3`
     for crisp output; fill a **white background** first (our figures assume white),
     then `drawImage`.
  3. `canvas.toBlob(... 'image/png')` → trigger download `<id>.png`.
  - The dvisvgm SVGs carry intrinsic width/height + viewBox, so the `Image` loads
    with real dimensions. If `naturalWidth` is 0 (edge), fall back to the viewBox.

**Acceptance:** SVG, PNG, `.tex` each download with the correct filename; PNG is
crisp (scaled) on a white background; works from `/item/<id>.html` at its path depth;
no new dependencies.

---

## Feature B — "Skills in action" demo (multi-dimension before → prompt → after carousel)

A new Home section (place after **How it works**) that finally *demonstrates* the
differentiator: skills letting an AI edit a figure precisely. Format chosen:
**before → prompt → after triptychs in a lightweight carousel.**

### Structure (important): one triptych = one capability dimension
Each carousel slide is **one self-contained triptych group**, and **each group shows a
different dimension of what skills can do.** The carousel is a tour across those
dimensions — together they prove skills aren't a one-trick edit but a precise,
multi-axis editing capability. Every slide is labeled with the dimension it
demonstrates.

Target dimensions (each = one group; pick a representative template + the literal
prompt for each):
1. **Add / remove a part** — e.g. neural-net *"add a hidden layer"*; encoder-decoder
   *"add a quantizer stage before the bottleneck."*
2. **Recolor (palette-correct)** — e.g. *"recolor the network teal."*
3. **Change counts** — e.g. *"make the third layer have 8 neurons."*
4. **Structural edit** — e.g. *"add a cross-attention block and make it blue."*
5. **Venue / column-width adaptation** — e.g. *"fit this to a CVPR single column."*
6. **Light → dark palette** — e.g. *"switch to the dark palette for slides."*

Start with **3–4 distinct dimensions**, grow over time. The point is *breadth of
capability*, so prioritize covering different dimensions over multiple examples of the
same one.

### Layout
- One slide (group) = a triptych: **[before figure] → [prompt chip] → [after figure]**,
  with a **dimension label** (e.g. "Recolor", "Add a layer", "Adapt to CVPR") plus a
  small sub-label naming the template. The prompt is the literal instruction a user
  would give. Optional one-line "what changed".
- **Carousel**: horizontal slides + prev/next buttons + dot indicators (one dot per
  dimension). Minimal vanilla JS in `app.js` (no library). Keyboard ←/→ optional;
  swipe optional. Consider showing the dimension name on/under each dot so the tour
  reads as "these are the different things skills can do."
- **Mobile**: the triptych stacks vertically (before → prompt → after); no overflow
  at 360px.
- Reuse the grid-canvas figure styling; keep it vector/lightweight.

### Data source (content-driven, pragmatic)
- A curated list the builder reads — e.g. `skills-demos.json` at repo root (or a
  `skills-demos/` dir), an **ordered array of groups**, each entry:
  `{ dimension, template_id, prompt, before_svg, after_svg, changed?: string }`
  where `dimension` is the capability label (e.g. "recolor", "add-layer", "cvpr-width").
- Builder renders one carousel slide per group, in array order. **If none exist → hide
  the section (or show one tasteful placeholder); never ship an empty carousel.**

### ⚠️ Content prerequisite (separate task, can run in parallel)
Each group's before/after figures must be **real renders**: take the template, apply
the skill's documented edit for that dimension, render *both* states to SVG, and
capture the exact prompt. Start with **3–4 groups spanning different dimensions**
(e.g. add-layer · recolor · structural/cross-attention · CVPR-width). Rendering needs
TeX (content-time only — the site build stays stdlib-only and just consumes the
committed SVGs). Each demo SVG is committed like any preview. Until ≥1 group lands, the
section uses the placeholder/hidden fallback.

**Acceptance:** carousel renders **multiple groups, each a distinct capability
dimension** (≥3 at launch), each labeled by its dimension; prev/next + per-dimension
dots work; prompt + labels shown; mobile stacks; no overflow; section auto-hides if no
demo data.

---

## Feature C — "On the roadmap" teaser (workflow→TikZ only)

A **restrained** band low on Home (below the gallery, above the footer) — **not** on
the hero. Teases one in-development feature, clearly labeled, no fake screenshots.

- **One card:** *Prompt-to-diagram (workflow → TikZ)* — "Describe the figure you want;
  get editable TikZ you can drop into the library. **In development — next release.**"
- Clear "in development / coming next" styling (muted, dashed border or a "soon" tag).
- **Do NOT include SVG→TikZ** — it brushes a declared CLAUDE.md non-goal
  (pixel/vector raster→TikZ); excluded by product decision.
- Structure the band so more roadmap cards can be added later.

### Truthfulness hook
Add a matching line to `docs/ROADMAP.md` (e.g. a "Prompt-to-diagram (workflow→TikZ)"
future item) so the teaser is backed by an actual roadmap entry, not vapor.

**Acceptance:** band renders with one clearly-labeled in-development card; only the
workflow-gen item (no SVG→TikZ); ROADMAP.md updated; doesn't overshadow shipped
content (placement below gallery).

---

## Sequencing
1. **Feature A** (downloads) — self-contained, no content dep; ship first.
2. **Feature C** (roadmap teaser) — small, no content dep.
3. **Feature B** (skills demo) — build the carousel + data wiring with the
   placeholder fallback; land the 2–3 real before/after renders as a parallel content
   task, then the section goes live.

## Test bar
Real-browser pass (Chrome via puppeteer-core): downloads produce SVG/PNG/.tex with
correct names (PNG non-empty, white bg); skills carousel advances + dots work + mobile
stacks + auto-hides with no data; roadmap band shows only the workflow card. Keep all
prior interactive checks (header, search, copy, alignment) green. `validate.py
--strict` + `build_catalog.py --check` pass; stdlib-only; `site/` gitignored.

## Non-goals
No SVG→TikZ teaser/placeholder; no video/GIF (static triptychs only for now); no
framework; no server-side PNG (client-side canvas only); no new runtime deps.
