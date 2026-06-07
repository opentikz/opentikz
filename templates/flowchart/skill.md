# Skill: edit the flowchart template

Companion skill for `templates/flowchart/template.tex`. It tells an AI agent (or
human) how to modify this figure safely without breaking compilation. See
`../../skills/color-palettes/skill.md` for the palette and
`../../docs/DESIGN_GUIDE.md` for global conventions.

## Structure

A top-to-bottom flowchart placed with the `positioning` library. Parameters live
in the `==== parameters ====` block:

- `\rowsep` — vertical gap between steps (the tikz `node distance`).
- `\boxminw`, `\boxminh` — minimum box size.
- Label macros: `\startlabel \readlabel \checklabel \proclabel \endlabel`
  `\errorlabel \yeslabel \nolabel \looplabel` (use `\\` for two-line labels).

Flowchart **shape vocabulary** (each is a style — pick by role):

- `terminal` — stadium / pill, for Start & End (`(start) (end)`), teal.
- `process` — rounded rectangle, for actions (`(read) (proc) (error)`), blue.
- `decision` — diamond, for a branch point (`(check)`), orange.
- `flow` — normal arrow; `loop` — purple arrow for a feedback/retry edge.

Layout: vertical spine `(start)`→`(read)`→`(check)`→`(proc)`→`(end)`; the
decision's **Yes** path continues down to `(proc)`, its **No** path goes right to
`(error)`, and a `loop` edge takes `(error)` back up to `(read)`.

Named nodes for targeting: `(start) (read) (check) (proc) (end) (error)`.

## Common edit operations

**Rename a step / branch label** — edit the matching macro, e.g.
`\def\checklabel{Valid?}` → `{Converged?}`, `\def\yeslabel{Yes}` → `{true}`.

**Add a process step** — insert a `process` node positioned `below=of` the
previous one and re-point the arrows (same pattern as the spine):
```
\node[process, below=of read] (clean) {Clean data};
\node[decision, below=of clean] (check) {\checklabel};  % was below=of read
...
\draw[flow] (read) -- (clean);
\draw[flow] (clean) -- (check);   % replaces (read)--(check)
```

**Add a second decision / branch** — add a `decision` node and route its two
outgoing `flow` arrows, labelling each with a `node[...]{Yes/No}` on the path
(see the existing `(check)` edges). Send one branch onward and the other to a
side node or back via a `loop` edge.

**Change a step's shape** — swap its style: a process becomes a decision with
`process` → `decision` (give it a `?` label), or a terminal with `process` →
`terminal`.

**Add an input/output step** (parallelogram convention) — TikZ has no built-in
parallelogram; use a `trapezium` (slanted box) for an I/O step:
`\node[base, shape=trapezium, trapezium left angle=70, trapezium right angle=110,
draw=otblue!70!black, fill=otblue!16, below=of start] (in) {Read file};`
(needs `shapes.geometric`, already loaded).

**Recolor** — change the color *name* in the relevant style (e.g. decision to
`fill=otpurple!18, draw=otpurple!80!black`); never a hex/stock color.

**Reroute / add a loop** — use the `loop` style for feedback edges. Orthogonal
routing helps: `(error.north) |- (read.east)` (up then left) or
`(a.south) |- (b.west)`. Put the edge label with `node[pos=..,above]{...}`.

**Switch to the dark palette** — replace the light `\definecolor` block with the
dark block from `skills/color-palettes/skill.md` (same names, no body edits).

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
(`\boxminw`/`\rowsep`) and resize the rest. To change the intrinsic
**aspect ratio** rather than just scale, adjust those same parameters.

## Constraints

- Must stay **standalone-compilable** (`\documentclass{standalone}`); keep the
  `shapes.geometric` (diamond) and `shapes.misc` (rounded rectangle / pill)
  libraries.
- Preserve the node names `(start) (read) (check) (proc) (end) (error)` and the
  per-role styles (`terminal`/`process`/`decision`) — the contract this skill
  targets. Give new nodes clear semantic names.
- Every decision's outgoing edges should be labelled (Yes/No or equivalent) so
  the control flow is unambiguous.
- Colors only via the five palette names (tints/shades allowed); never inline hex
  or stock xcolor names.
- After editing, re-render: `python3 tools/render_preview.py templates/flowchart/template.tex -o templates/flowchart/preview.svg` and validate with `python3 tools/validate.py --strict`.
