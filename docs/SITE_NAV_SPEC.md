# Spec — Site header nav + search elevation (and Phase 2 routes)

Status: **ready to implement**. Owner: SDE agent. All work is in
`tools/build_site.py` (stdlib only — **no new dependencies, no framework/bundler**).
Rebuild with `python3 tools/build_site.py`; `site/` stays gitignored.

## Why / positioning guardrails (read first — do not violate)

OpenTikZ is **not** Flaticon/Lucide/Phosphor (pure icon libraries). Our moat is the
three-layer model **icons → templates → skills** + AI-editability. The site's job is
to communicate that AND let people grab/edit — not to be "another icon grid."

Borrow from the references: **Lucide's restraint, Phosphor's search UX, copy-first
interactions, keyboard friendliness.** Keep our own visual identity (editorial
blueprint: Fraunces + IBM Plex, warm paper, TikZ coordinate-grid background, palette
accents). **Do NOT** (a) flatten the three sections back into one grid, (b) demote
templates/skills to "just another icon," (c) introduce accounts/pricing/marketplace
chrome, or (d) add a JS framework.

---

## Phase 1 — Sticky header + elevated search (do this first)

### 1. Sticky header nav bar
Replace/extend the current `masthead`. Applies to **both** the index and item pages.

- **Sticky** at top (`position:sticky; top:0; z-index` above content), full-width,
  slim. Background = paper with a subtle blur + bottom border (`var(--line)`); reuse
  existing tokens, no new gray theme.
- **Left:** `OpenTikZ` wordmark → links to home (`index.html` / `../index.html` on
  item pages). Keep the blue `TikZ` + animated orange caret identity.
- **Nav links** (right of wordmark): `Icons` · `Templates` · `Examples` · `Docs`
  · `GitHub ★`.
  - On the **index**, the three content links are in-page anchors:
    `#icons` / `#templates` / `#examples`.
  - On **item pages**, they point back to `index.html#icons` etc.
  - `Docs` → for now link to the repo README (`https://github.com/opentikz/opentikz#readme`);
    becomes `/docs` in Phase 2. (Acceptable placeholder; don't build a docs page now.)
  - `GitHub ★` → `https://github.com/opentikz/opentikz` (new tab,
    `rel="noopener"`). A star glyph is fine; live star count is **out of scope**.
- The current tagline moves out of the header into the hero so the bar stays slim.

### 2. Section anchors
Index content sections must carry `id="icons"`, `id="templates"`, `id="examples"`,
plus `scroll-margin-top` ≈ header height so anchored scrolls aren't hidden under the
sticky bar. Smooth scroll already enabled (`html{scroll-behavior:smooth}`).

### 3. Elevate search (Phosphor-style prominence)
- Search input becomes a clear focal element in the hero: larger, centered,
  `max-width ≈ 640px`. Placeholder: `Search icons, templates, tags…  ( / )`.
- **Keep all existing behavior**: Fuse.js fuzzy search, section-aware filtering,
  empty-section collapse, type chips, live counts. This is a visual/placement
  change, not a logic rewrite.
- Decision: **header is sticky; the search + chips live in the hero and scroll
  away** (matches Lucide — avoids fragile double-sticky stacking). Don't make both
  sticky.

### 4. Keyboard
- Pressing `/` when not already typing in an input/textarea focuses the search box
  and prevents the literal `/` being entered.
- `Esc` while focused in search clears it and blurs.

### 5. Active-section highlight (nice-to-have, not blocking)
Highlight the nav link for the section currently in view via `IntersectionObserver`.
If skipped, anchor links must still scroll to the correct section.

### 6. Mobile (< 720px)
- No horizontal overflow (hard requirement — current site passes at 390px; keep it).
- Nav links wrap to a second row (horizontally scrollable if needed); `GitHub ★`
  stays visible. A hamburger is acceptable but **not required** — prefer the simpler
  wrapped row given the minimal-JS ethos.

### Phase 1 acceptance criteria
- [x] Sticky header renders and stays pinned on scroll on index **and** item pages.
- [x] Nav anchors jump to the right section on index; from item pages they return to
      `index.html#<section>`.
- [x] `GitHub` → repo, `Docs` → README; both open correctly.
- [x] `/` focuses search (no stray `/` typed); `Esc` clears+blurs.
- [x] Search still filters section-aware; empty sections still collapse; counts live.
- [x] No horizontal overflow at 390px; nav usable on mobile.
- [x] `python3 tools/build_site.py` succeeds; output still 16 items / 17 pages.
- [x] No new dependencies; generator still stdlib-only; `site/` still gitignored.
- [x] Visual identity preserved (Fraunces/IBM Plex, grid-bg, palette accents).

---

## Phase 2 — Routes + Docs + quick-view (later: when icons scale / pre-launch)

Lower-detail forward plan; do **not** start without a go-ahead.

1. **Promote sections to real routes** for scale + SEO (Roadmap Step 4 wants
   indexable pages): generate `icons/index.html`, `templates/index.html`,
   `examples/index.html`, each a scoped grid + search. Header links become real
   navigation; add active-route state. Home becomes a curated landing (hero +
   three-layer explainer + featured items + CTA) rather than the full grid.
2. **`/docs` page** — render the skills story (the differentiator) + key
   `DESIGN_GUIDE` points; link each template's companion skill. This is where we
   tell the "why us" that Lucide/Phosphor structurally can't.
3. **Lucide-style side-panel quick-view** — clicking an icon card opens a slide-over
   with preview + one-click copy `.tex` **without full navigation**. This folds in
   the still-open backlog P1 (copy affordance on cards) — the highest-value
   conversion item.
4. **SEO** — per-page `<title>`/meta, `sitemap.xml`, OpenGraph image per item.

### Phase 2 non-goals
No framework/bundler, no accounts/marketplace/pricing, no flattening the three
layers, no live GitHub star-count service.

---

## Test bar (both phases)
- `python3 tools/build_site.py` clean build.
- Real-browser pass (Chrome via puppeteer-core, as done in prior reviews): header
  sticky, nav anchors, `/` focus, section-aware search, mobile no-overflow, copy
  buttons. Keep the existing 14/14 interactive checks green.
- `python3 tools/validate.py --strict` and `build_catalog.py --check` unaffected
  (site changes must not touch content validation).
