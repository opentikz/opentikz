# Landing page IA redesign — design spec

Date: 2026-06-18
Status: approved direction, pending spec review
Scope: the Home surface (`home_page()` in `tools/build_site.py`) and its supporting
section helpers + the embedded `STYLE_CSS` / `APP_JS`. No `.tex`, `.meta.json`,
catalog, or other-surface changes.

## Problem

The current landing page reads as "muddled" — confirmed by inspection:

- **Three persuasion bands stacked** (Why TikZ → How it works → Why not ChatGPT)
  before any single value statement lands. The argument is split across three places.
- **Redundancy:** "How it works" (`magic_moment`) and "See it on real templates"
  (`demos_carousel`) demonstrate the *same* prompt→figure mechanic. Two sections,
  one idea.
- **The hero doesn't state the value proposition.** It shows a carousel of pretty
  example figures; the actual differentiator (AI edits real templates) is buried
  three sections down.
- **No narrative spine** — sections don't build on each other in an obvious order.

## Decisions (locked during brainstorming)

1. **Scope:** redesign the *whole* landing-page information architecture, not just
   the top block.
2. **Lead:** the page leads with the **AI workflow** (matches the recent README
   change). "Browse the library" is the secondary path.
3. **Structure:** Approach A — a linear funnel: *show the magic → prove it
   generalizes → answer the obvious objection → reveal the library → convert.*
4. **Hero style:** **figure-first**, with the rendered output as the hero and a
   **before/after compare slider** as its centerpiece. The TikZ **code is
   de-emphasized** (our users do not write TikZ; the AI does) — present only as an
   optional "view TikZ source" toggle, as quiet proof the output is real, editable
   source rather than a black-box image.
5. **Slider default:** the wipe bar sits **centered** (50%).
6. **Use real rendered figures** in the slider, not placeholders.

## New page IA (top → bottom)

| # | Section | Source | Job |
|---|---------|--------|-----|
| 1 | **Hero** — figure-first + before/after slider | rewrite of `showcase`; absorbs `magic_moment` | State the value prop; show one deep, real prompt→figure result you can wipe between |
| 2 | **See it on real templates** — before/after carousel | reuse `demos_carousel` | Prove it generalizes — not one cherry-picked demo |
| 3 | **Why not just ask ChatGPT?** — comparison cards | reuse `why_opentikz_band` | Answer the sharpest objection to an AI-TikZ pitch |
| 4 | **The library you're drawing from** — figure gallery + counts + Browse CTA | new `library_gallery()`, fed by today's `featured` examples | Reveal the library; route to Browse |
| 5 | **Why TikZ** — slim 3-point strip | restyle `why_tikz_band` | Foundational reassurance (vector / native / diffable), at proper weight |
| 6 | **On the roadmap** | reuse roadmap block | Forward-looking credibility |
| 7 | **Final CTA band** | reuse `cta-band` | Convert |

### What changes vs. today

- **`magic_moment` section is removed from the Home page.** Its job (one deep
  prompt→figure example) moves into the hero. Its code-excerpt rendering logic is
  reused for the hero's "view TikZ source" toggle. The function may be deleted or
  kept only if reused elsewhere (it is not used on other surfaces today — verify
  and delete if dead).
- **Today's hero carousel of example figures** is demoted to section 4
  ("The library you're drawing from") as a compact thumbnail gallery.
- **`why_tikz_band` is restyled** from three full cards to a slim inline 3-point
  strip. Copy unchanged; visual weight reduced.
- **Section order** changes to the table above.

## Hero block — detailed design

Centered, figure-first. Top to bottom:

1. Animated `OpenTikZ┃` wordmark (keep existing `.hero-logo`).
2. **Headline** (draft): "Describe your figure. Get it, paper-ready."
3. **Lede** (draft): "Your AI agent edits a real TikZ template — you never write
   TikZ yourself."
4. **Prompt caption** — the featured demo's prompt, styled as a rounded "you said"
   chip: *"add a cross-attention block and make it blue"*.
5. **Before/after compare slider** (the centerpiece) — see component spec below.
   Uses the featured demo's real SVGs: `encdec-before.svg` (left/before) and
   `encdec-xattn.svg` (right/after).
6. **"▸ view TikZ source"** toggle — collapsed by default; expands to the featured
   demo's `tex_excerpt` (added lines highlighted), reusing `magic_moment`'s
   line renderer. De-emphasized styling.
7. **CTAs** — primary "Get started" → `skills/` (how to use it with your agent);
   secondary "Browse the library →" → `browse/`. *(CTA targets/labels are draft.)*

Copy in items 2–4 and 7 is **draft, to be refined after layout is built** — the
brainstorm focused on structure, not wording.

## Component: before/after compare slider

A reusable helper `before_after_slider(before_svg, after_svg, *, before_label,
after_label, prefix="")` emitting the markup; styling in `STYLE_CSS`; behavior in
`APP_JS`.

**Markup & behavior**
- A `position:relative` container with two absolutely-positioned, identically-sized
  layers: the *before* image (full) and the *after* image clipped via
  `clip-path: inset(0 0 0 var(--pos))` so the after is revealed to the right of the
  bar; the before clipped complementarily. A vertical bar + circular handle sit at
  `left: var(--pos)`.
- `--pos` defaults to `50%`.
- **The control is a native `<input type="range">`** (visually hidden / styled),
  driving `--pos`. This gives keyboard operability and a no-JS fallback for free.
  `APP_JS` adds pointer-drag affordance that updates the same range value, plus
  ARIA labelling.
- Corner tags "before" / "after"; a "← drag to compare →" hint.

**Accessibility / fallback**
- Range input → arrow-key operable; `aria-label="Compare before and after"`.
- With JS disabled, the slider renders statically at 50% (both halves visible) —
  still informative.

**Asset alignment (verify)**
- For a clean wipe, `encdec-before.svg` and `encdec-xattn.svg` must share the same
  canvas size / scale so shared elements line up across the bar. If they differ,
  fix by constraining both to a common max-width and centering; if structural
  divergence makes wiping look broken, fall back to a crossfade or side-by-side for
  this pair. **This is a verification step during implementation, not an assumption.**

**Reuse note:** the same component could later replace the triptych in
`demos_carousel` for consistency. Out of scope for this change to bound risk; noted
as a follow-up.

## Section: library gallery (new)

`library_gallery(featured, counts)` — a compact, static thumbnail grid of the
`featured` example figures (the list that feeds today's hero carousel), each linking
to its item page, followed by the counts line ("N icons · N templates · N examples ·
content CC0 1.0") and a primary "Browse the library →" CTA. Static grid (no
carousel) for clarity. The existing lightbox may be wired to these thumbnails for
click-to-enlarge; otherwise the lightbox is removed from Home.

## Implementation notes

- **All changes in `tools/build_site.py`** — stdlib only (per CLAUDE.md). No new
  build dependencies.
- Functions touched:
  - `home_page()` — new section order; drop `magic_moment` and the example carousel;
    add hero slider + `library_gallery`.
  - new `before_after_slider()`, new `library_gallery()`.
  - `why_tikz_band()` — restyle to slim strip.
  - `magic_moment()` — delete if unused after the hero absorbs it (verify no other
    caller).
- `STYLE_CSS` — add slider, slim Why-TikZ strip, library-gallery, and hero
  adjustments; remove now-dead rules (old `.magic*`, old hero-carousel rules if
  unused elsewhere).
- `APP_JS` — add the slider pointer-drag handler + "view TikZ source" toggle;
  remove hero-carousel JS if that carousel is gone (keep the skills/demos carousel
  JS, which section 2 still uses).
- Regenerate the site with `python tools/build_site.py`.

## Verification

- `python tools/build_site.py` runs clean; `site/index.html` regenerated.
- Open `site/index.html`: slider drags smoothly, defaults centered, before/after
  SVGs **align** across the wipe; "view source" toggle works; all 7 sections render
  in order; CTAs link correctly.
- Responsive check at mobile width: hero copy wraps, slider stays usable (scales to
  width, keeps aspect), no horizontal overflow.
- Keyboard: slider operable via the range input's arrow keys.
- `python tools/validate.py` passes (no content changed, but run as a guard).
- No `.tex` changed → no preview regeneration needed.

## Non-goals / deferred

- No `.tex`, content, catalog, or schema changes.
- Not converting `demos_carousel` slides to sliders (follow-up).
- Final hero copy / CTA wording — refined after the layout is built.
- No new analytics, search, or interactive features beyond the slider + toggle.

## Open questions

1. ~~Primary CTA destination~~ — **Decided:** primary "Get started" → `skills/`.
2. Keep the lightbox (wired to the library gallery) or drop it entirely? Default:
   wire it to the gallery if cheap; otherwise drop.
