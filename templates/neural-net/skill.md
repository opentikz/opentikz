# Skill: edit the feed-forward neural-network template

Companion skill for `templates/neural-net/template.tex`. It tells an AI agent (or
a human) how to modify this figure safely without breaking compilation. See
`../../skills/color-palettes/skill.md` for the palette and
`../../docs/DESIGN_GUIDE.md` for global conventions.

## Structure

The whole figure is driven by parameters in the `==== parameters ====` block at
the top of `\begin{document}`:

- `\layersizes` — a comma list of neuron counts, e.g. `{4,6,6,2}`. **Its length
  is the number of layers.** Layer 1 is the leftmost.
- `\layerlabels` — one label per layer; **must stay the same length as
  `\layersizes`** (e.g. `{Input,Hidden,Hidden,Output}`).
- `\layersep` — horizontal gap between layers (cm).
- `\neuronsep` — vertical gap between neurons in a layer (cm).
- `\neuronsize` — neuron diameter (cm).

How it draws (you rarely edit this part):

- Neurons are placed by two nested `\foreach` loops and named **`L<layer>-<neuron>`**
  (layer and neuron both 1-based), e.g. `(L1-1)`, `(L2-3)`. Each layer is
  vertically centred on `y=0`.
- Adjacent layers are **fully connected**; edges are drawn on a background
  `edges` layer so they sit behind the neurons.
- `\maxsize` / `\labely` are computed automatically so the label row sits just
  below the tallest layer — no manual tuning needed.

Styles: `neuron` (fill + draw), `edge` (connections), `layerlabel` (text). The
five palette colors (`otblue otorange otteal otpurple otgray`) are `\definecolor`'d
in the preamble.

## Common edit operations

**Add a layer** — append a count to `\layersizes` AND a label to `\layerlabels`
(keep the two lists equal length). To insert in the middle, add in the
corresponding position of both lists.
```
\def\layersizes{4,6,6,2}            ->  \def\layersizes{4,6,6,4,2}
\def\layerlabels{Input,Hidden,Hidden,Output}
                                    ->  \def\layerlabels{Input,Hidden,Hidden,Hidden,Output}
```
Everything else (positions, full connectivity, label row) updates automatically.

**Remove a layer** — delete one entry from each list (same position).

**Change neuron count in a layer** — edit that entry in `\layersizes` only
(e.g. third layer 6→8: `{4,6,8,2}`). The label list is unchanged.

**Recolor the network** — change the color *name* used by the `neuron` style;
do not touch the `\definecolor` block and never write a hex or a stock color.
```
neuron/.style={..., draw=otblue!75!black, fill=otblue!15, ...}
   -> teal:  draw=otteal!75!black, fill=otteal!15
```
To tint edges/labels too, change `otgray` references in the `edge` / `layerlabel`
styles. To color one layer differently, give those nodes an override, e.g. add
`\node[neuron, fill=otorange!20, draw=otorange!80!black] (L1-\n) ...` — but the
clean approach is one palette name per role.

**Resize / spacing** — `\neuronsize` for node size; `\neuronsep` (vertical) and
`\layersep` (horizontal) for spacing. Increase `\layersep` if edges look too
steep; increase `\neuronsep` if neurons crowd.

**Switch to the dark palette** — replace the light `\definecolor` block with the
dark block from `skills/color-palettes/skill.md` (same names, so no body edits).

**Adapt to a venue / column width** — the figure scales by setting the overall
size on the environment instead of editing every dimension. For a single ACL/CVPR
column (~3.3in ≈ 8.4cm wide) use:
```
\begin{tikzpicture}[scale=..., transform shape, ...]   % or
\resizebox{\columnwidth}{!}{ ... the tikzpicture ... }  % needs \usepackage{graphicx} in a paper
```
Inside the standalone preview, simplest is to reduce `\layersep`/`\neuronsep`
(e.g. 2.4→1.6, 1.1→0.8) and/or fewer neurons so the aspect ratio fits a narrow
column. For double-column/full-width, increase them.

## Constraints

- Must stay **standalone-compilable** (`\documentclass{standalone}`); don't
  remove the `\pgfdeclarelayer{edges}`/`\pgfsetlayers` lines or edges will draw
  over the neurons.
- Keep `\layersizes` and `\layerlabels` the **same length**.
- Preserve the **`L<layer>-<neuron>`** node-naming scheme — it is the contract
  this skill relies on for targeting nodes.
- Colors only via the five palette names (tints/shades like `otblue!15` are
  fine); never inline hex or stock xcolor names.
- After editing, re-render: `python3 tools/render_preview.py templates/neural-net/template.tex -o templates/neural-net/preview.svg` and validate with `python3 tools/validate.py --strict`.
