---
name: using-opentikz
description: Use when a user wants a TikZ figure for a paper — an icon, an editable architecture/pipeline/flow template, or an example — and wants you to find, edit, and verify it. The single repo-wide skill for working with the OpenTikZ library.
---

# Using OpenTikZ

OpenTikZ is a library of copyable TikZ **icons**, editable **templates** (neural
nets, encoder-decoder, training pipelines, system block diagrams, flowcharts),
and full **examples**. This skill is how you go from a user's request to a
finished, compiling `.tex` figure — reliably, and without guessing.

There is **one** skill (this file). Per-template knowledge lives in each
template's `edit_contract` (inside its `meta.json`), which you read at edit time.
Do not look for per-template `skill.md` files; they no longer exist.

## 0. First: which mode are you in, and where is the library?

**Pick the mode:**
- **Mode A — produce a figure for the user's own project** (the default). The
  OpenTikZ library is read-only and lives elsewhere; the user is working in their
  own paper/LaTeX project. You will *copy* a figure out of the library and edit the
  copy in their project. Never modify the library.
- **Mode B — contribute back to the OpenTikZ repo itself.** The user is editing the
  library: their working directory *is* the repo. Edit in place and run the repo
  tooling (see §6).

**Locate the library root (`OTROOT`) for Mode A:**
1. If the environment variable `${CLAUDE_PLUGIN_ROOT}` is set, you were installed as
   a Claude Code plugin: `OTROOT = ${CLAUDE_PLUGIN_ROOT}`.
2. Otherwise (cloned repo / another agent), `OTROOT` is the OpenTikZ repo root — the
   directory two levels above this `SKILL.md` (`skills/using-opentikz/SKILL.md` →
   `../../`).
3. If you can only read the repo remotely (e.g. over GitHub, no local clone), treat
   the GitHub repo as `OTROOT` and fetch raw file contents on demand.

Confirm `OTROOT` once (e.g. list `OTROOT`/catalog.json) before relying on it. The
**output target is always the user's current working directory**, never `OTROOT`.

## 1. Communicate precisely (do this first, throughout)

Your job is to produce the figure the user actually wants, not a plausible guess.
Classify every ambiguity before acting:

**Material ambiguity → ask, or offer two concrete alternatives.**
Trigger when the answer changes the figure's *structure or identity*, is *hard to
reverse*, or you would otherwise be guessing between genuinely different intents.
Ask one crisp question with concrete options; never a vague "what do you want?".

- "draw a transformer" → encoder-only, decoder-only, or encoder-decoder? (ask)
- "add attention" → self-attention or cross-attention, and where? (ask)
- "highlight the new part" → which part is new? (ask)
- Use **offer-two-alternatives** when seeing beats describing — an aesthetic or
  layout fork (two color schemes, two layouts). Produce both and let the user
  pick. Don't use it for continuous quantities (widths, counts).

**Safe-default ambiguity → proceed, state the assumption in one line, keep it
cheap to reverse.** When there is a sensible default and changing it is a
one-line tweak, don't interrupt — just decide and tell the user what you assumed.

- palette: default light Okabe-Ito unless "dark" is mentioned.
- width: default standalone (no `\resizebox`) unless a venue/column width is named.
- spacing / size / an unspecified-but-conventional count: use the template default
  (e.g. a 4-layer net `4,6,6,2`).

**Anti-interrogation guardrail.** Ask at most ~2–3 questions up front, batched;
resolve everything else with assume-and-state. Every delivery ends with a
one-line summary: *"Assumptions: light palette, single-column width, 4 layers —
say the word to change any."*

## 2. Workflow

1. **Understand & classify.** Restate the goal in one sentence; classify
   ambiguity per §1; ask the (few) material questions, batched.
2. **Discover.** Read `catalog.json` at `${OTROOT}` (see §0). Match the request to
   icons / templates / examples by `name`, `tags`, `domain`. If several fit,
   present the candidates (with their `id`s) and let the user choose; if one
   clearly fits, name it and proceed.
3. **Select & confirm.** Confirm the chosen base plus the material parameters
   (e.g. layer counts, labels, which part is highlighted).
4. **Copy, then edit (Mode A) / edit in place (Mode B).**
   - **Mode A:** copy the chosen item's `.tex` from `OTROOT` into the user's project
     (a sensible path like `figures/<name>.tex`); tell the user where you put it.
     Edit *that copy*, never the file under `OTROOT`. If the figure is already in
     the user's project, edit it there. For a **template**, read its `edit_contract`
     from `OTROOT`'s `catalog.json` (or the item's `meta.json`) and: edit only the
     contract's `parameters`; follow its `operations` as the recipe; keep every
     `invariant`; preserve the `node_naming` scheme; colours via palette names only.
     For an **icon/example** (no contract), edit under the same hard rules.
   - **Mode B:** edit the item in place inside the repo, under the same rules.
5. **Verify by compiling — in the user's project (Mode A).** Run the user's LaTeX on
   the copied/edited file (`latexmk -pdf <file>.tex`, or `pdflatex`). Fix failures
   before returning — never hand back a figure you didn't compile. (Regenerating
   `.svg` previews and `catalog.json` is a *Mode B / contributor* task — skip it
   when producing a figure for a user.)
6. **Deliver.** Return the edited `.tex` and the one-line assumptions summary.

## 3. Hard rules (never violate)

- The `.tex` must stay **standalone-compilable** (`\documentclass{standalone}`).
- **Colors only via the five palette names** (`otblue otorange otteal otpurple
  otgray`); tints/shades like `otblue!15` are fine. Never inline a hex value or a
  stock xcolor name (`blue`, `red`). See `reference/color-palettes/`.
- **Preserve node names / the `node_naming` scheme** — they are the contract that
  lets edits target the right parts. Give any new node a clear semantic name.
- **Keep figures parametric** — drive counts/spacing/labels through the `\def`
  block at the top; don't hard-code what a parameter already controls.

## 4. Common cross-template operations

These work the same across templates; the per-template `edit_contract` lists the
specific parameter/style names to touch.

**Recolor.** Change the palette color *name* in the relevant style or node, never
a hex. "Make it teal" = `otblue` → `otteal` in that style's `fill`/`draw`.

**Switch to the dark palette.** Replace the light `\definecolor` block with the
dark block from `reference/color-palettes/color-palettes.md` — the names are
identical, so the body is unchanged. The dark palette is for **dark
backgrounds**: also set `\pagecolor{otpaper}`
(`\definecolor{otpaper}{HTML}{1E1E1E}`), or the tints render washed-out grey on a
white page.

**Adapt to a venue / column width.** Wrap the whole `tikzpicture` in `\resizebox`
(needs `\usepackage{graphicx}`):
```
\resizebox{\columnwidth}{!}{\begin{tikzpicture} ... \end{tikzpicture}}
```
In a paper use `\columnwidth` (single column) or `\textwidth` (full width); to
test a target in the standalone file give an explicit width
(`\resizebox{8.4cm}{!}{...}`). Common targets: CVPR/ICCV/ACL single column
≈ 8.4cm, full/double width ≈ 17.8cm; NeurIPS/ICML text ≈ 13.9cm. Caveat:
`\resizebox` scales text too — if the figure is far wider than the column, first
reduce content/spacing (the template's spacing parameters) and resize the rest.

## 5. Reference material

- `reference/color-palettes/` — the canonical five-color Okabe-Ito palette (light
  + dark blocks), the single source of truth for colors.
- `reference/annotations/` — how to add callouts, braces, and highlight labels.
- `reference/layout/` — positioning, alignment, and spacing patterns.
- `docs/DESIGN_GUIDE.md` — global conventions (line width, node naming, metadata).

## 6. Mode B procedure — contributing back (editing the repo itself)

If the user is adding/changing library content (not just producing a figure for
their paper), the repo tooling applies:

- regenerate the preview: `python3 tools/render_preview.py <file>.tex -o <dir>/preview.svg`
- regenerate the catalog: `python3 tools/build_catalog.py`
- validate: `python3 tools/validate.py --strict`
- a new/edited template needs an `edit_contract` in its `meta.json` (see §4 of
  `docs/DESIGN_GUIDE.md`); `validate.py` checks its parameters/styles exist in the
  `.tex`.
