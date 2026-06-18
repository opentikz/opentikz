# Design: Make "How it works" + README express OpenTikZ's real workflow and advantage

**Date:** 2026-06-17
**Status:** Approved (brainstorming) — ready for implementation plan
**Surfaces:** `tools/build_site.py` (home page), `skills-demos/skills-demos.json`, `README.md`

## Problem

The site's "How it works" section and the README describe OpenTikZ's value but
don't make a visitor *get* it. Specifically:

1. **The workflow is abstract.** "How it works" is three text steps (clone →
   describe → agent assembles) with no artifact. The "wow" — *type English, get
   editable TikZ that compiles* — is asserted, never shown.
2. **The advantage is invisible.** Nothing explains why this beats asking
   ChatGPT for TikZ directly (accuracy, time saved), nor why TikZ at all
   (LaTeX-native, vector quality).
3. **Positioning buries the lede.** Both surfaces lead with "browse & copy
   clipart," framing OpenTikZ as Flaticon when the differentiator is the
   AI-editable templates + skill.

The strongest existing asset — the skills-in-action before/after carousel — sits
below the fold and shows only rendered results, not the prompt→code linkage.

## Goal

Restructure the home page and README so a first-time visitor, in one scroll,
understands (a) **why TikZ**, (b) **the concrete prompt → editable TikZ →
figure workflow**, and (c) **why OpenTikZ is more accurate and faster than raw
LLM TikZ** — backed by real, committed-source proof.

## Approach (chosen: "Layered story", Approach C)

A four-beat narrative on the home page, each beat answering one gap, closing
with the existing carousel as proof. Two new bands frame the rebuilt workflow
centerpiece. The README mirrors the key parts in condensed form.

Rejected alternatives:
- **A (magic-moment-first):** compresses the "why" arguments — which the user
  said are the heart — into asides.
- **B (comparison-first):** reads as defensive before the visitor knows what the
  product is; weak for the positioning gap.

## Home-page structure (top to bottom)

1. **Hero** — existing; sharpen the subtitle to lead with the AI-edit workflow
   rather than "browse & copy."
2. **Why TikZ band** *(new)* — three columns:
   - **Vector quality** — crisp at any zoom, sharp in print/PDF; no pixelated
     screenshots or re-exports.
   - **Native to your paper** — same fonts, math (`$\mathbf{W}x$`), and
     `\ref`/`\cite` as the document; the figure looks part of the paper.
   - **Text, so it's diffable** — version it in git, tweak one number,
     recompile; no binary-asset round-trips.
3. **How it works → the magic moment** *(rebuilt, layout B "playground/IDE")* —
   replaces the three abstract text steps. Prompt on top; below it, editable
   TikZ (AI-added lines highlighted) and the rendered figure side-by-side.
   Uses the real encoder-decoder cross-attention edit.
4. **Why OpenTikZ, not raw ChatGPT band** *(new, layout A "verdict cards")* —
   two side-by-side cards, fair tone:
   - **Raw LLM TikZ** — often won't compile, invented packages/macros, random
     hex colors, no stable names to re-edit → many slow retries.
   - **OpenTikZ + skill** — compiles standalone first try, shared palette,
     stable node names, `edit_contract` guides the AI → accurate and fast.
5. **Skills-in-action carousel** *(existing)* — reframed heading positioning it
   as proof ("…and here it is editing real templates"). Carousel logic
   unchanged.
6. **Roadmap + CTA band** — unchanged.

### Visual decisions (locked via visual companion)

- **Centerpiece layout:** B — prompt on top, code + rendered preview
  side-by-side (an IDE/playground feel; sells "the code is the source of truth").
- **Comparison layout:** A — two verdict cards (red/green semantics tuned to the
  paper theme), honest failure modes, not a strawman.

## Implementation

### `tools/build_site.py`
- Rebuild the `<section class="how">` block (currently ll. ~397–407) into the
  layout-B magic-moment component inside `home_page()`.
- Add two new sibling sections in `home_page()`: a `why-tikz` band before the
  workflow and a `why-opentikz` band after it.
- Reframe the carousel section heading only; leave its rendering/JS unchanged.
- Optionally tighten the hero subtitle string.
- **CSS:** append new classes to `STYLE_CSS` (e.g. `.why-tikz`, `.magic`,
  `.magic-prompt`, `.magic-code`, `.magic-fig`, `.cmp-cards`, `.cmp-card`).
  Colors MUST use existing palette vars (`--otblue`, `--otorange`, `--otteal`,
  etc.) — never raw hex inline, per the project's hard rules. Added/removed code
  lines use a restrained green/red that fits the `--paper` theme.

### `skills-demos/skills-demos.json` (data model)
The magic moment needs real code, not just SVGs. Extend the featured
encoder-decoder entry with:
- `featured: true` — marks the single demo promoted into the magic-moment
  centerpiece (the others continue to feed the carousel).
- `prompt` — already present; reused verbatim as the "you type" line.
- `tex_excerpt` — the relevant TikZ lines pulled **verbatim** from
  `templates/encoder-decoder/template.tex`, with the AI-added lines marked
  (e.g. a leading `+ `) so the builder can highlight them.
- reuse the existing `after_svg` as the rendered figure.

`build_site.py`'s demo handling (ll. ~636–645) gains: pick the `featured` demo
for the magic moment. The carousel continues to show **all** demos (the featured
one may appear in both — it is the canonical example and reinforces the claim).
If no demo is flagged `featured`, fall back to the first demo so the page still
builds (mirrors the existing `featured` examples fallback pattern).

### `README.md`
- **Reorder the lead** so positioning leads with the AI workflow. Quick-start
  step 1 becomes the magic moment ("tell Claude Code the figure or edit you
  want"); "browse & copy" becomes a secondary path.
- **New compact "Why TikZ, and why OpenTikZ" section:** the three why-TikZ
  bullets + a small markdown comparison table (raw-LLM vs OpenTikZ) + one
  concrete prompt→edit walkthrough using the real cross-attention example with a
  short TikZ snippet.
- Gallery stays but moves below the why/workflow so the value prop reads first.

## Honesty / trust constraints

- Every figure shown is rendered from committed `.tex` source; no mockups in the
  final build (the visual-companion mockups were for layout selection only).
- The `tex_excerpt` is copied verbatim from the template, not hand-written for
  the marketing page.
- The "raw LLM" card describes real, common failure modes — kept fair, not a
  strawman.

## Out of scope (YAGNI)

- No real in-browser TikZ compiler / live editor — the playground is a static,
  pre-rendered depiction.
- No new JS framework or client dependency.
- No changes to `catalog.json`, `validate.py`, or the metadata schema.
- No new icons/templates/examples; this is presentation only.

## Affected files

- `tools/build_site.py` — new sections + CSS in `home_page()` / `STYLE_CSS`.
- `skills-demos/skills-demos.json` — `featured` flag + `tex_excerpt` on the
  encoder-decoder demo.
- `README.md` — reordered lead, new why-section, walkthrough.
- (No regeneration of `catalog.json` or previews required.)

## Verification

- `python3 tools/build_site.py` builds without error; `site/index.html` shows
  the four beats in order with the magic-moment code + figure and both bands.
- Local preview (`python3 -m http.server -d site`) visually confirms layout B
  centerpiece and layout A cards render on the paper theme.
- No raw hex colors introduced (grep the new CSS/markup against palette vars).
- README renders correctly on GitHub (table + snippet).
