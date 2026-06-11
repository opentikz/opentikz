# Spec — Hero: figure carousel + click-to-zoom lightbox (replaces the gallery)

Status: **ready to implement**. Owner: SDE agent. Build: `python3 tools/build_site.py`
(stdlib only — **no new deps, no framework, no lightbox library, no TeX for the build**).
Keep `validate.py --strict` / `build_catalog.py --check` green; `site/` gitignored;
preserve the editorial-blueprint identity (Fraunces + IBM Plex, warm paper, TikZ grid,
palette accents).

## PM decision (settled)
The Home hero becomes a **manual carousel** over the featured flagship figures, each
figure **click-to-zoom** into a full-screen lightbox. The now-redundant
**"Reproductions & examples" gallery is removed** — the hero carousel absorbs that role.
**No autoplay.**

### Why
- **P1-3:** the single static LoRA hero reads small on desktop; the wide figure's
  labels/equations are hard to read. Click-to-zoom fixes readability without giving the
  hero more permanent vertical space.
- **No duplication:** the same 3 featured items appear in the hero area AND the gallery
  today. A hero carousel + the existing gallery would show the same figures twice, plus
  stack two figure strips above the fold. So the gallery goes; the hero carousel is the
  single place featured figures live above the fold.
- **Manual, not auto:** the hero is the comprehension-critical zone. Auto-advance hurts
  reading and is an a11y smell. Manual prev/next + dots only.

Three independent changes.

---

## Change 1 — Hero figure → manual carousel

In `home_page()` (build_site.py:350), replace the single
`<figure class="show-fig">` (build_site.py:375) with a carousel over **all** `featured`
items (flagship first; order already set at build_site.py:611–613).

- **Reuse the carousel mechanics** from `demos_carousel` (build_site.py:310) + its
  prev/next/dots/keyboard JS — but this is a **single-figure** carousel (one preview SVG
  per slide), **not** the before/after triptych. Prefer **one shared JS init** keyed off a
  container, not a forked copy of the dot/keyboard logic.
- **Each slide:** the item's `previews/<id>.svg`, a small caption (item **name** + type
  `badge()`), and a visible **"click to enlarge"** affordance (🔍 corner button +
  `cursor: zoom-in` on the figure). The caption's name links to `item/<id>.html` (keep the
  deep link the gallery provided); clicking the **figure/zoom button** opens the lightbox
  (Change 2), not the item page.
- **Controls:** prev/next arrows + one dot per featured item; keyboard ←/→ when the
  carousel has focus. **No autoplay.**

### ⚠️ Two carousels on one page — the #1 risk
Home will now have **two** carousels (hero + skills-in-action). The current JS gates on a
single `document.getElementById('carousel')` (build_site.py:1195) and queries
`document.querySelectorAll('.demo-dot')` **globally** (build_site.py:1198).

- Give the hero carousel a **distinct id** (e.g. `#hero-carousel`) and **distinct slide/dot
  classes** (e.g. `.hero-slide` / `.hero-dot`) so it never collides with `.demo-slide` /
  `.demo-dot`.
- **Refactor the init to be per-instance:** `querySelectorAll('.carousel')`, and scope all
  inner queries (`.car-track`, dots, slides) to **each carousel element**, with independent
  active-index state. Verify the skills carousel still advances correctly and the two never
  share index state.

---

## Change 2 — Click-to-zoom lightbox

Clicking the hero figure (or its 🔍 button) opens a **full-screen modal** showing that
figure at readable size (SVG scales crisply — let it use most of the viewport).

- **Backdrop:** dimmed / blurred. **Close** via ✕ button, `Esc`, and click-on-backdrop.
- **Navigate inside the lightbox:** ←/→ moves between the featured figures (reuse the same
  ordered list as the hero carousel; opening from slide *n* starts at *n*).
- **A11y (required):** move focus into the modal on open, **trap** focus while open, return
  focus to the trigger on close; `role="dialog"` + `aria-modal="true"` + a label; **lock
  body scroll** while open; honor `prefers-reduced-motion` (no transition).
- **Stdlib/inline only:** modal markup emitted once in `home_page()`, behavior in the
  inlined `app.js`, styles in the inlined CSS. No lightbox library.

---

## Change 3 — Remove the redundant gallery

- Delete the `showcase-gallery` section (build_site.py:382–386) and the `tiles` builder
  (build_site.py:356–363) from the Home output (the "Reproductions & examples" heading goes
  with it).
- Remove the now-dead Home-only CSS once nothing references it: `.showcase-gallery`,
  `.gallery`, `.tile`, `.tile:hover`, `.tile-canvas`, `.tile-meta*` and their responsive
  rules (build_site.py:878–896, 990, 1015). **Verify** Browse uses `.card` (it does), not
  `.tile`, before deleting.
- Featured items stay reachable via the hero carousel slides (each links to
  `item/<id>.html`) and via Browse — no item becomes orphaned.

---

## Guardrails / non-goals
- **Manual only — NO autoplay.** A future autoplay (if ever) must pause on hover/focus and
  honor reduced-motion; out of scope now.
- Don't change the skills-in-action carousel's **data or markup** beyond the shared-JS
  refactor needed to support two instances.
- No new runtime deps, no framework, no lightbox library — hand-rolled. `site/` stays
  gitignored. Keep the editorial identity.

## Acceptance
- Home hero shows **one featured figure at a time** with prev/next + dots; ←/→ works on
  focus; **no autoplay**; each slide captioned (name + badge) and the name deep-links to the
  item page.
- Clicking the figure / 🔍 opens a **full-screen lightbox** that renders the figure large &
  **readable** (LoRA equations/labels legible); `Esc` / ✕ / backdrop close; ←/→ navigates
  within it; focus **trapped + restored**; reduced-motion respected; body scroll locked.
- **"Reproductions & examples" gallery removed**; no duplicate figure strip; no dead
  `.tile`/`.gallery` CSS.
- **Two carousels coexist** (hero + skills) with **independent** state; skills carousel
  behavior unchanged.
- Mobile **360px**: hero carousel + lightbox usable, **no overflow**; desktop **1280**:
  figure reads large on zoom.
- `validate.py --strict` + `build_catalog.py --check` green; stdlib only; `site/`
  gitignored; the build print line / page count still accurate.

## Test bar (real-browser, Chrome via puppeteer, as in prior reviews)
hero prev/next/dots/keys · click→lightbox readable · `Esc`/backdrop/✕ close · lightbox
←/→ · focus trap + restore · reduced-motion honored · two carousels independent · gallery
gone · 360px no overflow · 0 broken links across surfaces.
