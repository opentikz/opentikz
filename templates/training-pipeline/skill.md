# Skill: edit the training-pipeline template

Companion skill for `templates/training-pipeline/template.tex`. It tells an AI
agent (or human) how to modify this figure safely without breaking compilation.
See `../../skills/color-palettes/skill.md` for the palette and
`../../docs/DESIGN_GUIDE.md` for global conventions.

## Structure

A supervised **training loop**, placed with the `positioning` library (no manual
coordinates). Parameters live in the `==== parameters ====` block:

- `\nodesep` — horizontal gap between forward stages (the tikz `node distance`).
- `\loopdrop` — how far below the model the optimizer sits.
- `\boxminw`, `\boxminh` — minimum stage box size.
- Label macros: `\datalabel \modellabel \losslabel \optlabel \labelslabel`
  `\predlabel \gradlabel \updatelabel` (math like `$\hat{y}$`, `$\nabla\mathcal{L}$` is fine).

Layout:

- **Forward path** (top, left→right): `(data)` → `(model)` → `(loss)`. The
  `(model)`→`(loss)` arrow carries the prediction label `\predlabel`.
- `(labels)` sits **above** `(loss)` and feeds into it.
- **Backward path** (the training loop, in purple): `(loss)` → `(opt)` →
  `(model)`. `(opt)` sits `\loopdrop` below the model. The two `back` arrows carry
  `\gradlabel` (gradients) and `\updatelabel` (weight update).

Named nodes for targeting: `(data) (model) (loss) (labels) (opt)`.

Styles: `stage` (base box), `io` (neutral grey boxes), `fwd` (forward arrows),
`back` (purple loop arrows), `elabel` / `blabel` (edge labels).

Role colors: model `otblue`, loss `otorange`, optimizer `otteal`, neutral I/O
`otgray`, the backward loop `otpurple`.

## Common edit operations

**Rename a stage / edit a label** — change the matching macro, e.g.
`\def\modellabel{Model}` → `{Transformer}`, `\def\optlabel{Optimizer}` →
`{Adam}`, `\def\gradlabel{gradients $\nabla\mathcal{L}$}` → `{$\partial\mathcal{L}/\partial\theta$}`.
For a **two-line** label use `\\` (boxes are `align=center`), e.g.
`\def\datalabel{Dataset\\(ImageNet)}`.

**Insert a forward stage** (e.g. an "Augment" step between data and model) — add
a node positioned `right=of` the previous stage and re-point the arrows. Give the
node a **semantic name matching its role** (here `(augment)`, not a generic name):
```
\node[io, right=of data] (augment) {Augment};
\node[stage, fill=otblue!18, right=of augment] (model) {\modellabel};  % was right=of data
...
\draw[fwd] (data) -- (augment);
\draw[fwd] (augment) -- (model);   % replaces (data)--(model)
```
Keep each new node on the same baseline (use `right=of`). A new processing stage
can use the neutral `io` style or a palette-tinted `stage` (e.g. `fill=otteal!18`).

**Recolor** — change the color *name* on the relevant node's `fill=` (and the
matching `draw` if set), never a hex/stock color. The backward loop color is the
`back` and `blabel` styles (`otpurple!85!black`).

**Tighten / loosen layout** — `\nodesep` for horizontal spacing, `\loopdrop` for
how deep the optimizer sits (raise it if the loop labels feel cramped), `\boxminw`/
`\boxminh` for box size.

**Drop the optimizer box** (show just "backprop" returning to the model) — delete
the `(opt)` node and its two `back` arrows, and replace them with a single curved
return arrow:
`\draw[back] (loss.south) to[out=-90,in=-90] node[below,blabel]{backprop} (model.south);`

**Add a validation branch / second loss** — add another node below or above and
connect with a `fwd` arrow; keep the main loop intact.

**Switch to the dark palette** — replace the light `\definecolor` block with the
dark block from `skills/color-palettes/skill.md` (same names, no body edits).
The dark palette is for **dark backgrounds**: also set `\pagecolor{otpaper}`
(`\definecolor{otpaper}{HTML}{1E1E1E}`, see the palette skill), otherwise the
tints render washed-out grey on a white page.

**Adapt to a venue / column width** — to match a *specific* width, wrap the whole
`tikzpicture` in `\resizebox` (needs `\usepackage{graphicx}`):
```
\resizebox{\columnwidth}{!}{\begin{tikzpicture} ... \end{tikzpicture}}
```
In a paper use `\columnwidth` (one column) or `\textwidth` (full width); to test a
target in this standalone file give an explicit width, e.g. `\resizebox{8.4cm}{!}{...}`.
This scales the figure proportionally and reliably hits the width (verified: an
8.4cm request renders 8.4cm wide). Common targets: CVPR/ICCV/ACL single column
≈ 8.4cm (3.3in), full/double width ≈ 17.8cm (7in); NeurIPS/ICML text ≈ 13.9cm
(5.5in). Caveat: `\resizebox` scales text too — if the figure is far wider than the
column the labels shrink below body size, so first reduce content/spacing
(`\nodesep`/`\boxminw`) and resize the rest. To change the intrinsic
**aspect ratio** rather than just scale, adjust those same parameters.

## Constraints

- Must stay **standalone-compilable** (`\documentclass{standalone}`).
- Preserve the node names `(data) (model) (loss) (labels) (opt)` — the contract
  this skill targets. If you add stages, give them clear semantic names too.
- Keep the forward arrows `fwd` and the loop arrows `back` visually distinct
  (the loop is purple) so the training cycle stays readable.
- Colors only via the five palette names (tints/shades like `otblue!18` are
  fine); never inline hex or stock xcolor names.
- After editing, re-render: `python3 tools/render_preview.py templates/training-pipeline/template.tex -o templates/training-pipeline/preview.svg` and validate with `python3 tools/validate.py --strict`.
