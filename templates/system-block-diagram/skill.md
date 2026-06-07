# Skill: edit the system-block-diagram template

Companion skill for `templates/system-block-diagram/template.tex`. It tells an AI
agent (or human) how to modify this figure safely without breaking compilation.
See `../../skills/color-palettes/skill.md` for the palette and
`../../docs/DESIGN_GUIDE.md` for global conventions.

## Structure

A 2D system architecture placed with the `positioning` library; a dashed
subsystem boundary is drawn with `fit` on a background layer. Parameters live in
the `==== parameters ====` block:

- `\rowsep`, `\colsep` — vertical / horizontal `node distance` between components.
- `\boxminw`, `\boxminh` — minimum size of process/external boxes.
- Label macros: `\clientlabel \gatewaylabel \svconelabel \svctwolabel \dblabel`
  `\cachelabel \grouplabel` (use `\\` for two-line labels — boxes are `align=center`).

Component **types** (each is a style — pick by role):

- `external` — dashed grey box, for things outside the system (the `(client)`).
- `process` — blue box, for services / compute (`(gateway) (svc1) (svc2)`).
- `store` — teal **cylinder**, for a datastore (`(db)`).
- `cachestore` — orange cylinder variant (`(cache)`).
- `group` — dashed container drawn around a set of nodes via `fit`.

Layout: `(client)` → `(gateway)`, which branches to `(svc1)` (above-right) and
`(svc2)` (below-right); `(db)` is right of `svc1`, `(cache)` right of `svc2`.
Arrows use the `link` style. The `(backend)` group `fit`s `svc1/svc2/db/cache`.

Named nodes for targeting: `(client) (gateway) (svc1) (svc2) (db) (cache) (backend)`.

## Common edit operations

**Rename a component** — edit its label macro, e.g.
`\def\gatewaylabel{API\\Gateway}` → `{Load\\Balancer}`.

**Add a component** — declare a node with the style for its role, positioned
relative to an existing node, then connect it. Example: a message queue between
the gateway and the services:
```
\node[cachestore, below=of cache] (queue) {Queue};   % orange store style
\draw[link] (gateway) |- (queue);
\draw[link] (queue) -- (svc2);
```
If the new node belongs to the subsystem, add it to the `fit` list:
`\node[group, fit=(svc1)(svc2)(db)(cache)(queue)] (backend) {};`

**Change a component's type** — swap its style: e.g. make a service a datastore
with `process` → `store`, or mark a box external with `process` → `external`.

**Add / change connections** — add `\draw[link] (a) -- (b);` lines. For a
two-way dependency use `<->` (`\draw[link, <->] ...`). To route around boxes use
`-|` / `|-` (orthogonal) or `to[bend left=20]`. Keep arrows reading left→right /
top→bottom where possible.

**Recolor** — change the color *name* in the relevant style (`process` →
`fill=otteal!16, draw=otteal!70!black`, etc.); never a hex/stock color. Keep
distinct roles in distinct palette colors so the diagram stays legible.

**Resize the subsystem box** — adjust `group`'s `inner sep` (padding), or change
which nodes are in its `fit=(...)` list. The label is a separate node anchored to
`backend.north west`; move it by editing its `xshift`/`yshift`.

**Switch to the dark palette** — replace the light `\definecolor` block with the
dark block from `skills/color-palettes/skill.md` (same names, no body edits).
The dark palette is for **dark backgrounds**: also set `\pagecolor{otpaper}`
(`\definecolor{otpaper}{HTML}{1E1E1E}`, see the palette skill), otherwise the
tints render washed-out grey on a white page. On dark, also lighten the `group`
`fill` (e.g. `fill=otgray!18`).

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
(`\colsep`/`\boxminw`) and resize the rest. To change the intrinsic
**aspect ratio** rather than just scale, adjust those same parameters.

## Constraints

- Must stay **standalone-compilable** (`\documentclass{standalone}`); keep the
  `shapes.geometric`, `fit`, and `backgrounds` libraries (cylinders + group box
  need them).
- The `group` node must come **after** the nodes it `fit`s, and stay inside
  `\begin{scope}[on background layer] ... \end{scope}` so it sits behind them.
- Preserve semantic node names; give any new components clear role-based names.
- Colors only via the five palette names (tints/shades allowed); never inline hex
  or stock xcolor names.
- After editing, re-render: `python3 tools/render_preview.py templates/system-block-diagram/template.tex -o templates/system-block-diagram/preview.svg` and validate with `python3 tools/validate.py --strict`.
