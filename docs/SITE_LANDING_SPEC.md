# Spec — Two-surface site: marketing Home (`/`) + Browse tool (`/browse/`)

Status: **ready to implement** (has a content prerequisite, see §6). Owner: SDE agent.
All site work in `tools/build_site.py` (stdlib only — **no framework/bundler/deps**).
Builds with `python3 tools/build_site.py`; `site/` stays gitignored.

Decision (PM): the landing page splits into **two surfaces, each does one job**:
- **Home `/`** = pure *convince*. A fancy showcase of faithful conference-paper-figure
  reproductions (e.g. a LoRA-style diagram) + the "how it works" story + CTAs. **No
  content grid, no search box on Home.**
- **Browse `/browse/`** = pure *tool*. The current sectioned index (Icons / Templates /
  Examples) + Fuse search + chips. This is where people find & grab.

This supersedes the "Phase 2 routes" timing in `SITE_NAV_SPEC.md` (we pull routes
forward). The **sticky header** from `SITE_NAV_SPEC.md` is a shared prerequisite for
both surfaces — build it first or together.

## Positioning guardrails (unchanged — do not violate)
Not Flaticon/Lucide/Phosphor (pure icon grids). Our moat is **icons → templates →
skills + AI-editability**. Home exists because our value is invisible in a thumbnail
grid; it must *sell the outcome* (paper-grade figures) and *route into content* — not
be wallpaper. Keep the editorial-blueprint identity (Fraunces + IBM Plex, warm paper,
TikZ grid bg, palette accents). No accounts/pricing/marketplace chrome.

---

## 1. Routing / output structure
```
site/
  index.html              ← Home (marketing)
  browse/index.html       ← Browse (search + Icons/Templates/Examples sections)
  item/<id>.html          ← per-item pages (unchanged content; fix relative paths)
  previews/<id>.svg
  assets/{style.css,app.js}
  .nojekyll
```
- Mind **relative path depth**: Browse is one level deep (`/browse/`), so its asset
  refs are `../assets/...`, card links `../item/<id>.html`, preview `../previews/...`.
  Item pages already use `../`. Home is at root (`assets/...`). Get these right —
  broken links are the #1 risk of this refactor; verify all in the test pass.
- Item page "back" link → `../browse/` (was `../index.html`).

## 2. Shared sticky header (per `SITE_NAV_SPEC.md`)
- `OpenTikZ` wordmark → Home (`/`).
- Nav: `Browse` (→ `/browse/`), `Icons` `Templates` `Examples` (→ `/browse/#icons`
  etc.), `Docs` (→ repo README for now), `GitHub ★` (→ repo, new tab).
- **Active state**: highlight `Home` vs `Browse` by current surface.
- **Header search affordance**: a search icon (and `/` shortcut) that, when used from
  Home, navigates to `/browse/` and focuses the search box (e.g.
  `/browse/?q=` or focus-on-load). On Browse, `/` just focuses the existing input.

## 3. Home (`/`) — marketing surface
Top-to-bottom; this surface gets **bespoke layout/CSS** (more design-heavy than the
rest — that's expected). Sections:

1. **Hero showcase** — the centerpiece. A large, faithful reproduction of a real
   conference-paper figure (flagship: a LoRA-style low-rank-adaptation diagram),
   rendered from our committed `.svg`. One-line headline conveying "paper-grade
   figures, built from copyable/editable library pieces." Primary CTA
   **`Browse the library →`** (`/browse/`), secondary **`See how it's built`**
   (scrolls to the decomposition / how-it-works).
2. **Decomposable showcase (the bridge to content)** — the flagship figure lists the
   library pieces it's composed of as chips that deep-link into Browse/item pages:
   `built from ▢dataset · ▢gpu · ▢encoder-decoder template · ✎ edited via skill.md →`.
   This is the thing Lucide/Phosphor structurally cannot do; make it prominent.
3. **Showcase gallery** — 1–3 (grow later) reproductions in a row/carousel
   (flagship + our existing `examples/`), each linking to its item page.
4. **How it works** — the three-layer story in 3 steps: *grab icons → start from an
   editable template → tell your AI to edit it via the companion skill*. This is where
   we tell "why us." Keep it short, visual, skimmable.
5. **CTA band + footer** — `Browse the library →`, GitHub, license note (CC0 content /
   MIT code).

## 4. Browse (`/browse/`) — tool surface
- = the **current sectioned index**, relocated under `/browse/`, with the sticky
  header. Preserve ALL existing behavior verbatim: three sections (Icons 9 /
  Templates 5 / Examples 2), Fuse fuzzy search, section-aware filtering,
  empty-section collapse, type chips, live counts, copy buttons, skill rendering on
  item pages.
- Optional: read `?q=` on load to prefill+run search (supports the header search
  affordance from Home).

## 5. Showcase data source (how the builder knows what's featured + its pieces)
Make it **content-driven**, not hard-coded:
- Add two **optional** fields to example (and allow on any item) metadata:
  - `featured` (boolean) — include on the Home showcase.
  - `composed_of` (array of item `id`s) — the library pieces to list/deep-link.
- **Schema:** `meta.schema.json` has `additionalProperties:false`, so these MUST be
  added to the schema (optional, not required) or `validate.py` will fail. Add them.
- Builder: Home showcase = items with `featured:true`, ordered (flagship first). If
  none exist yet, Home falls back to a tasteful placeholder + the existing 2 examples
  so the page still builds and looks intentional.

## 6. ⚠️ Content prerequisite (blocking for a *good* Home — separate task)
Home is only as compelling as the reproductions behind it. Needs **≥1 flagship
paper-figure reproduction** built as a real `examples/<name>/` item (its own `.tex`
+ `.meta.json` + preview), e.g. a LoRA-style diagram, with `featured:true` and
`composed_of` set. Rules:
- Faithful **homage re-draw** in our palette/TikZ; caption "after Fig. N in 〈paper〉".
- Keep **CC0**; **no logos/trademarks** (already a CLAUDE.md non-goal).
- Must pass `validate.py --strict` like any item.
This can proceed **in parallel** with the site build (site uses the `featured`
fallback until the asset lands), but the Home isn't "done" until at least the flagship
exists.

## 7. Acceptance criteria
- [ ] `python3 tools/build_site.py` builds Home, `/browse/`, all item pages; no broken
      asset/preview/card/back links at any path depth (verify each surface).
- [ ] Home has **no** content grid and **no** search input; Browse has both.
- [ ] Header is shared, sticky, with correct active state (Home vs Browse) and working
      `Browse / Icons / Templates / Examples / Docs / GitHub` links.
- [ ] Header search affordance + `/` from Home lands on `/browse/` with search focused;
      `/` on Browse focuses the input.
- [ ] Decomposable showcase chips deep-link to the right item pages.
- [ ] Browse preserves section-aware search, empty-section collapse, chips, counts,
      copy `.tex` + copy `skill.md`, skill rendering — all still green.
- [ ] `featured`/`composed_of` added to `meta.schema.json` (optional); `validate.py
      --strict` and `build_catalog.py --check` pass.
- [ ] Mobile (390px): no horizontal overflow on either surface.
- [ ] No new dependencies; stdlib-only; identity preserved; `site/` gitignored.

## 8. Test bar
Real-browser pass (Chrome via puppeteer-core, as in prior reviews): both surfaces
load, header nav + active state, Home→Browse search hand-off, showcase deep-links,
Browse search/filter/collapse/copy, mobile no-overflow. Keep the prior 14/14
interactive checks green on Browse. Content validation untouched.

## 9. Suggested sequencing
1. **Shared header** (`SITE_NAV_SPEC.md` Phase 1) — prerequisite.
2. **Split routes**: relocate current index → `/browse/`, fix all relative paths,
   add header active state. (Browse fully working before Home is styled.)
3. **Marketing Home** `/` — hero showcase, decomposition, how-it-works, CTAs;
   `featured`/`composed_of` wiring + schema; placeholder fallback.
4. **Flagship reproduction** content task (§6) — can run in parallel; flips Home from
   placeholder to real.

## Non-goals
No framework/bundler, no accounts/pricing/marketplace, no live GitHub star service,
no flattening the three layers, no search box on Home.
