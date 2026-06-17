# Skill: OpenTikZ annotations

How to **annotate** an OpenTikZ figure — add labels, callouts, leader lines,
grouping braces, and highlight boxes onto an existing diagram — consistently and
with the shared palette. This is the skill to follow when a user says *"label the
bottleneck"*, *"add a brace grouping these layers"*, *"highlight the new block"*,
or *"point an arrow at the output"*.

Annotations sit **on top of** existing content. They never change the figure's
structure or node names — they reference them. Keep the diagram readable: a few
deliberate annotations beat many competing ones.

## Required libraries

Add only what each annotation uses to the figure's preamble (and mirror them in
the item's `requires`):

```latex
\usetikzlibrary{arrows.meta}              % Stealth/Latex arrow tips for callouts
\usetikzlibrary{decorations.pathreplacing}  % curly braces
\usetikzlibrary{positioning}              % place labels relative to nodes
\usetikzlibrary{fit, backgrounds}         % highlight box around a group
```

## Palette roles for annotations

Annotations use the shared palette (see `[[reference/color-palettes]]`), never raw
hex. Two roles cover almost everything:

- **`otgray`** — neutral annotation: labels, leader lines, braces, dimension
  marks. The default; it stays out of the figure's way.
- **`otorange`** — emphasis: highlight the *one* thing the annotation is drawing
  attention to ("the new layer", "where it fails"). Use sparingly — if
  everything is orange, nothing is.

Text is `otgray` at `\footnotesize` or `\small` so labels never out-shout node
content.

## The five annotation primitives

### 1. Text label on a node

Anchor a label to an existing named node with `positioning`; don't hard-code
coordinates.

```latex
\node[above=2pt of encoder, text=otgray, font=\footnotesize] {bottleneck};
```

### 2. Leader / callout line

A thin line from a label to its target, with a small arrow tip. Keep it short
and off the main flow.

```latex
\draw[otgray, line width=0.7pt, -{Stealth[length=4pt]}]
  (label.south) -- (target.north east);
```

### 3. Grouping brace

A curly brace that spans several nodes to name a group (e.g. "encoder stack").
`raise` lifts it clear of the content; the midpoint node carries the label.

```latex
\draw[otgray, line width=0.8pt, decorate,
      decoration={brace, amplitude=5pt, raise=4pt}]
  (top.north west) -- (bottom.south west)
  node[midway, left=8pt, text=otgray, font=\footnotesize, align=center] {encoder\\stack};
```

(`brace` needs only `decorations.pathreplacing` — core and always available. For
a hand-drawn look, load the `calligraphy` library and swap in `calligraphic
brace`, but plain `brace` is the portable default.)

### 4. Highlight box around a region

Draw attention to a sub-area with a tinted rounded rectangle on the `background`
layer so it sits *behind* the nodes. `fit` sizes it to the named nodes.

```latex
\begin{scope}[on background layer]
  \node[draw=otorange!80!black, fill=otorange!12, rounded corners=3pt,
        inner sep=6pt, fit=(attn)(ffn)] {};
\end{scope}
```

### 5. Step / order badge

A small numbered disc to show sequence (1 → 2 → 3) over a pipeline.

```latex
\node[circle, draw=otorange!80!black, fill=otorange!18, text=otgray,
      font=\footnotesize\bfseries, inner sep=1.5pt] at (block.north west) {1};
```

## How to apply

- **"Label X"** → primitive 1; place the label with `positioning` relative to
  `X`'s node name, `text=otgray`, `\footnotesize`.
- **"Point at / call out X"** → primitive 1 + 2: a label plus a thin
  `-{Stealth}` leader to the node's anchor.
- **"Group / bracket these"** → primitive 3 spanning the group's outermost nodes,
  with the group name at `midway`.
- **"Highlight / box this"** → primitive 4 on the background layer, `otorange`
  tint for emphasis or `otgray` for a neutral region.
- **"Number the steps"** → primitive 5, one badge per stage at a consistent
  anchor (e.g. `north west`).

## Constraints

- Annotations **reference** existing node names; they never rename or move
  structural nodes. If a target has no name, name it first (see
  `[[docs/DESIGN_GUIDE.md]]`), don't annotate by absolute coordinate.
- Palette names only (`otgray`, `otorange`, tints/shades). Never a raw hex or a
  stock color like `red`/`black!50`.
- Highlight boxes go on the **background layer** so they never occlude content.
- Keep it sparse: at most one emphasis (`otorange`) focus per figure; everything
  else neutral `otgray`.
- Label text small (`\footnotesize`/`\small`) so annotations read as a layer
  *about* the figure, not part of it.

See `cheatsheet.tex` / `cheatsheet.svg` for a rendered reference of all five
primitives.
