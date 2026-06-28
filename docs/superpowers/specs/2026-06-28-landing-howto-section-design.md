# Landing page: "How to use" scenario carousel — design

**Date:** 2026-06-28
**Status:** Approved (brainstorm), pending implementation plan
**Scope:** Landing page (`home_page()` in `tools/build_site.py`) ONLY this round. The
`/skills/` page and `CLAUDE.md` non-goals are deliberately out of scope (handled in
a later round).

## Problem

The home page has two weak spots: (1) two redundant lines clutter the hero/footer
(the `N icons · M templates · K examples · CC0` counts line, plus the
`Prefer no AI?…` line added earlier), and (2) the page never shows a visitor the
*distinct ways* to actually use OpenTikZ. We add a visual, tabbed "How to use"
section that walks through four concrete usage scenarios.

## Product decision recorded (relaxes two CLAUDE.md non-goals)

The owner has decided the current skill's **PNG→TikZ** behaviour is acceptable to
showcase, and that **text-description → figure** is a supported output. This
contradicts two non-goals currently written in `CLAUDE.md` ("Data plots out of
scope", "Pixel-perfect PNG→TikZ conversion"). Per the owner's scoping, this spec
touches only the landing page; **`CLAUDE.md` will be reconciled in the later
`/skills/` round.** Until then the repo's own docs intentionally lag the homepage.

## Goals

- Visitor immediately sees four ways to use OpenTikZ, each explained *visually*.
- The section reuses the existing carousel machinery (no new JS framework).
- Section is **data-driven** from a manifest, so swapping/adding a scenario's
  assets is a manifest edit, not an HTML rewrite.
- Ship with real assets for scenarios ①②④; scenario ③ ships as a clearly-labeled
  placeholder until the owner supplies a real PNG→TikZ asset.

## Non-goals (YAGNI)

- No changes to `/skills/`, `README.md`, or `CLAUDE.md` this round.
- No new carousel/JS library — reuse `.carousel` + `app.js` behaviour already used
  by the hero and demos carousels.
- The existing "See it on real templates" demos carousel **stays** (coexists).

## Design

### Part 1 — Deletions (in `home_page()`)

- Remove the hero `.cta-sub` counts line and the `.show-alt` (`Prefer no AI?…`)
  line from `<section class="showcase">`.
- Remove the `.cta-sub` counts line from the bottom `<section class="cta-band">`.
- Leave the `Get started` / `Browse the library` buttons intact.

### Part 2 — New "How to use" section

- **Placement:** between the hero `</section class="showcase">` and the
  `{demos_section}` interpolation (i.e. immediately before "See it on real
  templates"). The demos carousel is unchanged and remains after it.
- **Mechanism:** a tabbed, auto-rotating carousel that reuses the existing
  `.carousel` structure and `app.js` autoplay/prev-next/dot behaviour. The demos
  carousel already renders *labeled* dots (`<button class="demo-dot"><span>…</span></button>`);
  the new section uses the same pattern with the four scenario names as the
  horizontal tab labels. Autoplay interval 5000ms (`data-autoplay data-interval="5000"`),
  matching the other carousels.
- **Two slide layouts** (slides are heterogeneous — the renderer branches on a
  `layout` field):
  - `steps` (scenario ①): three mini-steps left→right, each a small visual +
    caption.
  - `inout` (scenarios ②③④): an `input → (prompt/skill) → output` triptych, the
    same three-cell shape the demos carousel uses (`before / prompt / after`).
- A placeholder slide (scenario ③ until its asset lands) renders the `inout` shell
  with a visible "preview — sample coming" label instead of a missing image.

### Part 3 — The four scenarios + asset sources

| # | Tab label | Layout | Visual | Asset source |
|---|---|---|---|---|
| ① | Use icons | `steps` | ① Browse to find an icon → ② Copy `.tex` (or download SVG/PNG) → ③ `\input` it into your figure | compose from existing icon SVGs under `icons/` — buildable now |
| ② | Edit a template | `inout` | before → prompt → after | reuse the existing featured `skills-demos` cross-attention pair (`encdec-before.svg` / `encdec-xattn.svg`) |
| ③ | PNG → TikZ | `inout` | input PNG → generated TikZ preview | **owner-provided** real input PNG + generated `.tex`/preview; placeholder until supplied |
| ④ | Describe → TikZ | `inout` | text prompt → generated figure preview | **generated now** by running the `using-opentikz` skill on a real description; commit the `.tex` + rendered preview |

### Part 4 — Data model

- Add a manifest `skills-demos/landing-howto.json` (sibling of the existing
  `skills-demos.json`), an array of scenario objects:
  ```json
  {
    "id": "use-icons",
    "tab_label": "Use icons",
    "layout": "steps",                // "steps" | "inout"
    "steps": [                         // present when layout == "steps"
      {"img": "...svg", "caption": "Browse to find an icon"},
      {"img": "...svg", "caption": "Copy the .tex (or download SVG/PNG)"},
      {"img": "...svg", "caption": "\\input it into your figure"}
    ],
    "input_img": "...", "prompt": "...", "output_img": "...",  // present when layout == "inout"
    "placeholder": false,              // true → render the "sample coming" shell
    "caption": "one-line explainer"
  }
  ```
- `build_site.py` gains a `howto_carousel(scenarios, ...)` renderer (mirrors
  `demos_carousel`) that branches on `layout`. `build()` loads
  `landing-howto.json` the same way it loads `skills-demos.json` and passes the
  list to `home_page()`.
- Scenario asset image files live under `skills-demos/` (or a new
  `landing-howto/` dir) and are committed alongside the manifest.

### Build / ship sequence

1. Deletions + new section shell + manifest with ①②④ real and ③ as placeholder.
2. Generate scenario ④'s figure by running the skill; commit its `.tex` + preview;
   wire into the manifest.
3. Scenario ③ stays a placeholder until the owner supplies the PNG→TikZ asset;
   landing it later is a one-line manifest edit (`placeholder: false` + asset paths).

## Risks / things to verify

- **Asset honesty:** the site advertises "no mockups — rendered from committed
  source." Scenario ④'s output must be a *real* skill-generated figure; scenario ③
  must stay an explicit placeholder (not a faked result) until a real asset exists.
- **Carousel reuse:** confirm `app.js` autoplay/dot logic is generic enough to drive
  a third carousel instance on the page (id-scoped), alongside hero + demos.
- **Heterogeneous slides:** the `steps` vs `inout` branch must not break the shared
  carousel sizing (the demos work fixed slide height to avoid section jump — keep
  that).
- **Scenario ① visuals:** the three step images should read clearly at small size;
  if raw icon SVGs are too sparse, a light composed panel per step may be needed.
