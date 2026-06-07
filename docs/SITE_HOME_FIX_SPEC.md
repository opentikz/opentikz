# Spec — Home fixes: container alignment + figure-led hero + gallery

Status: **ready to implement**. Owner: SDE agent. All in `tools/build_site.py`
(stdlib only — no new deps). Build: `python3 tools/build_site.py`. Two issues found
in PM review of `8c233ad`, both confirmed in-browser (Chrome via puppeteer-core).

Positioning guardrails unchanged (see `SITE_LANDING_SPEC.md` / `SITE_NAV_SPEC.md`):
editorial-blueprint identity, no framework, Home = pure marketing (no grid/search),
let the figure sell the outcome.

---

## Fix 1 — Unify the layout container (the real cause of "nav not aligned")

The header markup is already a shared `navbar()` component — **not** the problem. The
defect is that the **horizontal container (max-width + gutter) was copy-pasted with
divergent values**, so content left-edges drift from the wordmark:

| Container | current max-width | measured left @1280px | vs wordmark (78px) |
|---|---|---|---|
| `.nav-inner` (header) | 1180 | — | baseline |
| `.grid` (Browse) | 1180 | 78 | ✓ aligned |
| `.home` (Home) | **1120** | 108 | ✗ **+30px** |
| `.item` (item) | **1000** | 140 | ✗ **+62px** |

**Do this:**
- Add a single token: `:root{ --maxw:1180px; --gutter:28px; }`.
- Make `.nav-inner` **and every surface's main content container** use it:
  `max-width:var(--maxw); margin-inline:auto; padding-inline:var(--gutter);`
  → applies to `.nav-inner`, `.home` (and its child sections so they don't add their
  own offset), `.grid`, `.item`.
- Mobile override sets `--gutter` (e.g. 18px) in one place instead of per-selector.
- If a narrower reading measure is wanted on item pages, constrain **inner** elements
  (text/code), not the outer container — the container's left edge must align with the
  wordmark on all surfaces.

**Acceptance:** wordmark `.left` == main-content `.left` on Home, Browse, and item
(re-run the alignment probe; all three must read "✓ aligned"). The centered search
hero on Browse (`.hero`, intentionally narrow+centered) is exempt.

---

## Fix 2 — Hero: figure-led, centered (figure is the star)

Current hero is a 2-col "figure-left / big-headline-right" split — it inverts the
hierarchy (text shouts, the figure is a small left thumbnail in a SaaS-screenshot
card) and reads as the generic "left image / right text" trope. Replace with a
**single centered column** where the flagship figure is the largest element.

Replace the `.showcase` 2-col grid with a vertical, centered stack inside the unified
container:

1. **Headline** — one tight line, Fraunces (e.g. "Paper-grade figures from a
   library."). Drop the multi-line giant headline.
2. **Lede** — one short line under it (optional, ≤ ~14 words).
3. **Flagship figure — the centerpiece**: large and centered, ~70–85% of container
   width, `max-height` ≈ 440–480px (up from 340). Sits on the TikZ-grid canvas but
   with **light chrome** — subtle 1px border, **no heavy SaaS drop-shadow**. Keep the
   small "homage after Hu et al., 2021 (LoRA)" caption beneath the art.
4. **Decomposition caption** (the bridge): centered chip strip under the figure —
   `built from ▢ layer · ▢ encoder-decoder · ✎ skill.md →`, each deep-linking to its
   item page. Keep this prominent; it's our differentiator.
5. **CTAs** centered below: primary `Browse the library →` (`browse/`), secondary
   `See how it's built` (scrolls to How-it-works).

Notes: figure must be the visually dominant element. On mobile it already stacks;
ensure the figure stays full-width and legible (no overflow at 360px).

---

## Fix 3 — Gallery: larger equal-height tiles, grid (not carousel)

`Reproductions & examples` currently reuses the cramped Browse `.card` and the row is
uneven (3rd tile taller/offset). Replace with a dedicated gallery tile:

- **Bigger preview canvas** per tile (give the figures room — they're the product),
  **equal height** across the row (consistent canvas `aspect-ratio` + stretch).
- **3-up responsive grid** on desktop → 2-up → 1-up; **no carousel** (carousels hide
  content; with ≤3 items a grid is better). _Revisit a carousel only when
  reproductions exceed ~6 — log it, don't build it now._
- Each tile links to its item page; keep the type badge + title.
- Fix the uneven-height/offset bug (don't let one tile's taller canvas break the row).

---

## Acceptance criteria
- [x] One `--maxw`/`--gutter` token; `.nav-inner`, `.home`(+sections), `.grid`,
      `.item` all consume it. Alignment probe: wordmark left == content left on Home,
      Browse, item (all ✓).
- [x] Hero is a single centered column; the flagship figure is the largest element
      (≥ ~440px tall on desktop), light chrome, no heavy shadow.
- [x] Decomposition chips centered under the figure, deep-linking correctly.
- [x] CTAs centered below the figure; both work.
- [x] Gallery tiles are larger, equal-height, clean 3→2→1 responsive grid, no carousel.
- [x] No horizontal overflow at 360px on Home.
- [x] `build_site.py` builds; `validate.py --strict` + `build_catalog.py --check` pass
      (17 items); stdlib-only; `site/` gitignored; identity preserved.

## Test bar
Re-run the puppeteer alignment probe (must show ✓ on all three surfaces) + screenshot
Home hero and gallery for visual sign-off. Keep Browse's prior interactive checks
green (this change is Home-CSS + container-token; don't touch Browse logic).

## Non-goals
No carousel yet, no framework, no new content (uses the existing LoRA flagship +
2 examples), no change to Browse behavior.
