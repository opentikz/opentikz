# Spec — Site tweaks: Home navbar · Roadmap cards · Skills page · demo set

Status: **ready to implement** (changes 3 + 4 have content prerequisites). Owner: SDE
agent. All site work in `tools/build_site.py` + its inlined `app.js`/`style.css`
(stdlib only — **no new deps, no framework, no TeX for the build**). Build:
`python3 tools/build_site.py`.

Guardrails unchanged: editorial-blueprint identity (Fraunces + IBM Plex, warm paper,
TikZ grid bg, palette accents); not Flaticon/Lucide/Phosphor; moat = icons → templates
→ **skills** + AI-editability; no accounts/pricing/marketplace; keep `validate.py
--strict` / `build_catalog.py --check` green; `site/` gitignored.

Four independent changes — ship in any order.

---

## Change 1 — Remove the search affordance from the Home navbar

The Home header currently shows a `Search` pill (`nav-search`) that routes to
`/browse/?focus=1`; no other surface (Browse, item) has it. The header should read the
**same on every surface**.

**Do this (`navbar()` ≈ build_site.py:144):**
- Delete the `search_affordance` block and the `{search_affordance}` slot — the Home
  navbar then matches Browse/item (wordmark · Browse · Icons · Templates · Examples ·
  Skills · Docs · GitHub).
- Remove the now-dead CSS: `.nav-search`, `.nav-search:hover`, `.nav-search .mag`
  (≈ build_site.py:792–795).
- **Keyboard `/`:** keep it working **only where a real search box exists** (Browse —
  it focuses `#search`). Remove the "no search box → jump to Browse `?focus=1`" fallback
  (the `else { … data-browse … }` branch ≈ app.js:1042–1045) so Home/item have no
  hidden search entry. Browse's `Esc`-to-clear and its `?q=`/`?focus=` prefill stay.
- `?focus=1` is now only ever produced by nothing on-site; leaving Browse's reader of it
  is harmless (deep links / manual URLs still work). Don't remove Browse's reader.

**Acceptance:** Home navbar markup === Browse/item navbar markup except active-state and
relative hrefs (and the new `Skills` link from Change 3); no `Search` pill anywhere;
pressing `/` on Home/item does nothing (no navigation), on Browse focuses search; no dead
`.nav-search` CSS; build green.

---

## Change 2 — Roadmap teaser: two cards (Prompt-to-diagram + Graph-to-diagram)

The roadmap band (`roadmap` section ≈ build_site.py:418) currently has one card. Make it
**two**, both clearly "in development," same restrained styling:

1. **Prompt-to-diagram** — `natural language → TikZ`. *"Describe the figure you want; get
   editable TikZ you can drop into the library."*
2. **Graph-to-diagram** — `graph / spec → TikZ`. *"Give a node–edge spec (JSON · DOT ·
   adjacency); get a laid-out, editable figure."*

- Both tagged **"in development — next release"** (the existing muted / dashed treatment).
- The band already uses an `auto-fit` grid (`.roadmap-cards`, minmax(290px,1fr)); two
  cards should sit side-by-side on desktop and stack on mobile with **no overflow at
  360px**. Verify the heading copy still reads well with two ("On the roadmap").
- **Still NO SVG→TikZ** (declared CLAUDE.md non-goal: pixel/vector raster→TikZ). Only
  these two cards.

**Truthfulness hook:** `docs/ROADMAP.md` currently lists only the prompt item under
"Future". **Add a second matching entry** for *Graph-to-diagram (graph/spec → TikZ)* so
both cards are backed by a real roadmap line, not vapor.

**Acceptance:** two in-development cards (Prompt-to-diagram, Graph-to-diagram), correct
copy + "in development" tag, side-by-side desktop / stacked mobile, no 360px overflow; no
SVG→TikZ; ROADMAP.md has both Future entries.

---

## Change 3 — `Skills` as its own navbar page (`/skills/`)

Skills are the stated **soul of the product** but have no home of their own — they're only
glimpsed inside template item pages. Add a dedicated **Skills** page and a nav link, the
"why us" surface Lucide/Phosphor structurally can't have. **Do not change** the existing
skill.md rendering on template item pages, or any Browse logic.

**Route / output:**
```
site/skills/index.html        ← new
```
- One level deep, like `/browse/` → asset refs `../assets/…`, links into items
  `../item/<id>.html`, demos `../demos/…`. Get path depth right (the #1 refactor risk).

**Navbar (`navbar()`):** add a `Skills` link (→ `skills/` from Home, `../skills/` from
item, `index.html`→`skills/` resolved per surface like the others). Place it after
`Examples`, before `Docs`. Add an **active state** for the Skills surface (mirror
`nav-browse.active`); pass a new `surface == "skills"` value when rendering this page.

**Page content (content-driven from what already exists — no new prose to invent):**
1. **Header / explainer** — short: *"Every template ships a companion `skill.md`: precise,
   structured instructions that let an AI edit the figure correctly — add/remove a part,
   recolor from the palette, change counts, restructure, adapt to a venue — without
   hand-writing TikZ."* Keep it to ~2–3 lines, editorial tone.
2. **Skills in action** — reuse the **same carousel component** built for Home
   (`demos_carousel`) so the demonstrations live here too. Factor the carousel so both Home
   and this page can render it from the same `skills-demos.json` (no duplicate markup/JS;
   one source of truth). On the Skills page it can be the centerpiece.
3. **Companion skills index** — list the **5 template skills** (read each
   `templates/<name>/skill.md`'s H1 / the template's name + summary), each deep-linking to
   that template's item page where the full skill renders (e.g. `→ encoder-decoder`,
   `→ neural-net`, …). Source these from the catalog (`type=="template"`, has skill.md),
   not a hard-coded list, so new templates appear automatically.
4. **Cross-cutting skills** (optional, nice) — the repo also has `skills/color-palettes`,
   `skills/annotations`, `skills/layout`. If low-cost, list them as a second group
   ("Library-wide skills") linking to the repo paths; if it complicates the build, defer
   and log it — don't block this change on it.

**Build wiring:** generate `skills/index.html` in `build()` alongside Home/Browse; count it
in the page total/print line; ensure the carousel JS in `app.js` initializes on this page
too (the `#carousel` hook already gates on element presence, so it should "just work" once
the markup is emitted — verify).

**Acceptance:** `/skills/` builds and is linked from every navbar with correct active
state; explainer + carousel + template-skills index render; every template-skill link
resolves to the right item page (no broken links at this path depth); template list is
catalog-driven; **template item pages' existing skill.md rendering and Browse behavior are
unchanged**; mobile no overflow at 360px; build/validate/catalog green.

---

## Change 4 — Reset the "Skills in action" demo set (diversify across templates)

Today all three demos are on the **same feed-forward neural network**, and the
light→dark one is weak. Replace the set so it spans **different items and dimensions** —
that breadth is the whole point of the carousel. New order (carousel + dots follow array
order in `skills-demos/skills-demos.json`):

| # | Dimension | Template / item | Prompt |
|---|---|---|---|
| 1 | **Recolor (palette-correct)** | an **icon** — suggest `gpu` | "recolor the GPU icon orange" |
| 2 | **Add a part** | `neural-net` (FFNN) | "add a hidden layer" |
| 3 | **Structural edit** | `encoder-decoder` | "add a cross-attention block and make it blue" |

- **Remove** the light→dark slide and the current recolor/add slides that all target the
  FFNN; rebuild the JSON to the three rows above.
- Keep the existing data shape: `{ dimension, dimension_label, template_id, prompt,
  before_svg, after_svg, changed? }`. `template_id` now varies (`gpu`, `neural-net`,
  `encoder-decoder`) — the carousel's "on <template name>" sub-label already resolves via
  `by_id`, so an **icon** id like `gpu` must resolve too (it's in the catalog → fine).
- The carousel + section-auto-hide + per-dimension dots are unchanged; only the data and
  the committed SVGs change.

### ⚠️ Content prerequisite (separate task; needs TeX at content-time only)
Each slide needs **real before/after renders**, like any preview — not mockups:
1. **Recolor icon** — render `icons/.../gpu` as-is (before) and with its palette colour
   swapped to `otorange` (after). (Pick a different icon/colour if `gpu` doesn't read well
   recolored — keep it a clean, obvious recolor.)
2. **Add a layer** — reuse the existing `nn-light.svg` (before) + `nn-add.svg` (after);
   these already exist, no re-render needed.
3. **Cross-attention** — render `encoder-decoder` before, then apply the edit and render
   after. **Truthfulness gate:** this must be an edit the **encoder-decoder `skill.md`
   actually documents.** If the skill doesn't yet cover "add a cross-attention block,"
   either (a) add that operation to `templates/encoder-decoder/skill.md` first (preferred —
   it's a real, useful skill op; the `attention` icon can be the block), or (b) swap demo 3
   for a structural edit the skill *does* document. Don't ship a demo the skill can't back.

Commit the new demo SVGs under `skills-demos/`; delete the now-unused `nn-dark.svg` /
`nn-teal.svg` if nothing else references them. Until the two new renders land, the
carousel can run on whatever slides exist (it just shows fewer) — never ship an empty or
mocked slide.

**Acceptance:** carousel shows **three slides across three different items** (icon recolor
· FFNN add-layer · encoder-decoder structural), each a **real** before/after render, each
labeled by dimension + template; no light→dark slide; prev/next/dots/keys still work;
mobile stacks; demo `template_id`s all resolve to real catalog items; section still
auto-hides with no data.

---

## Test bar
Real-browser pass (Chrome via puppeteer-core, as in prior reviews):
- Home/item navbar has no search pill; `/` does nothing off-Browse, focuses search on
  Browse; Browse `Esc`/`?q=` intact.
- Roadmap shows exactly two in-development cards (Prompt-to-diagram + Graph-to-diagram),
  no SVG→TikZ, no 360px overflow.
- `/skills/` loads, linked + active in navbar, carousel + template-skill links all
  resolve; item-page skill.md rendering unchanged.
- Carousel: three slides on three different items, real renders, prev/next/dots/keys,
  mobile stacks, auto-hide with no data.
- 0 broken links across all surfaces at every path depth; `validate.py --strict` +
  `build_catalog.py --check` pass; stdlib-only; `site/` gitignored; identity preserved.

## Non-goals
No SVG→TikZ (any framing); no framework/bundler; no new runtime deps; no server-side PNG;
no flattening the three layers; don't touch Browse search/filter/collapse logic or the
existing per-template skill.md rendering.
