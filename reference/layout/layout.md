# Skill: OpenTikZ layout

How to **position and arrange** nodes in an OpenTikZ figure — place blocks
relative to each other, align rows and columns, distribute evenly, and fit a
figure to a paper column. This is the skill to follow when a user says *"space
these evenly"*, *"align these blocks"*, *"stack it vertically"*, *"make it two
rows"*, or *"fit it to a CVPR column"*.

The goal is **relative, parametric** placement: a figure whose spacing is driven
by a few named distances, so it can be re-flowed or rescaled without rewriting
every coordinate. Avoid scattering absolute `(x,y)` coordinates — they make a
figure impossible for a human or an AI to edit safely.

## Required libraries

```latex
\usetikzlibrary{positioning}   % right=of / below=of, node distance
\usetikzlibrary{fit}           % size a container to a set of nodes (optional)
\usetikzlibrary{chains}        % auto-chain a sequence (optional, pipelines)
```

## Relative placement with `positioning`

Place each node relative to the previous one, not at an absolute coordinate. Set
a single `node distance` and reuse it so the whole figure breathes together.

```latex
\begin{tikzpicture}[node distance=8mm and 12mm]   % vertical and horizontal gap
  \node[block] (input)  {input};
  \node[block, right=of input]  (encoder) {encoder};
  \node[block, right=of encoder] (decoder) {decoder};
  \node[block, below=of encoder] (loss)    {loss};
\end{tikzpicture}
```

`right=of`/`below=of` keep nodes aligned on a shared axis automatically. Change
the one `node distance` to loosen or tighten the entire layout.

## Alignment

- **Same row / column:** chaining with `right=of`/`below=of` keeps nodes on a
  shared centre line for free.
- **Align to a different node's edge:** anchor explicitly, e.g.
  `below=of encoder.south west, anchor=north west` to left-align a stack.
- **A grid of blocks:** drive both indices from a `\foreach`, spacing by a named
  step so rows and columns stay regular:

```latex
\def\dx{1.6} \def\dy{1.2}
\foreach \r in {0,1,2}
  \foreach \c in {0,1,2,3}
    \node[block] at (\c*\dx, -\r*\dy) {};
```

## Even distribution

For N items spread across a fixed span, compute positions from the index rather
than hand-placing each — so adding/removing one re-spaces automatically:

```latex
\def\N{5} \def\span{8}            % 5 nodes across 8 cm
\foreach \i in {1,...,\N}
  \node[block] at ({(\i-1)/(\N-1)*\span}, 0) {\i};
```

Changing `\N` re-distributes everything; this is how skills "add a layer" or
"use 6 neurons instead of 4" without disturbing alignment.

## Fitting a figure to a paper column

Conceptual figures usually need to land at a fixed text width. Three levers, in
order of preference:

1. **Reduce `node distance`** and node sizes first — the figure stays crisp
   because nothing is scaled.
2. **Scale the picture** uniformly when the structure is fixed:
   `\begin{tikzpicture}[scale=0.85, transform shape]` (`transform shape` scales
   node text too, so labels shrink with the drawing).
3. **Wrap in `\resizebox`** as a last resort to hit an exact width:
   `\resizebox{\columnwidth}{!}{ ... tikzpicture ... }`.

Common targets (single text column):

| Venue style              | Single column | Full text width |
|--------------------------|---------------|-----------------|
| IEEE / CVPR two-column   | ~3.25 in      | ~7.0 in         |
| ACL / NeurIPS            | ~3.2 in       | ~5.5 in (1-col) |
| Beamer slide (4:3)       | —             | ~4.5 in usable  |

Keep `\documentclass[border=...]{standalone}` while authoring; the consumer wraps
the figure in `figure`/`\includegraphics` or pastes the `tikzpicture` directly.

## How to apply

- **"Space evenly"** → index-driven `\foreach` distribution; never nudge nodes
  one at a time.
- **"Align these"** → put them in a `right=of`/`below=of` chain, or anchor to a
  shared edge.
- **"Stack vertically / make it a row"** → swap `right=of` ↔ `below=of`; the rest
  of the relative graph follows.
- **"Make it N wide / tall"** → change the count `\N` (and/or `node distance`),
  not the coordinates.
- **"Fit a CVPR/NeurIPS column"** → tighten `node distance` first; if still wide,
  add `scale=…, transform shape`; only then `\resizebox{\columnwidth}{!}{…}`.

## Constraints

- Prefer **relative** placement (`positioning`) and **named distances** over
  absolute coordinates, so the figure stays re-flowable and AI-editable.
- Keep node **names semantic** (see `[[docs/DESIGN_GUIDE.md]]`) — layout edits
  target nodes by name; a renamed node breaks the template's edit contract.
- When scaling to fit, use `transform shape` so text scales with the drawing;
  a scaled picture with unscaled labels reads as broken.
- One `node distance` (or a small set of named steps) per figure — don't mix ad
  hoc gaps that can't be adjusted together.
- Colors still come from the palette (`[[reference/color-palettes]]`); layout never
  introduces a new color.

See `cheatsheet.tex` / `cheatsheet.svg` for a rendered reference of relative
placement, grid distribution, and column-fit scaling.
