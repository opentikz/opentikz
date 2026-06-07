# Skill: edit the encoder-decoder template

Companion skill for `templates/encoder-decoder/template.tex`. It tells an AI agent
(or human) how to modify this figure safely without breaking compilation. See
`../../skills/color-palettes/skill.md` for the palette and
`../../docs/DESIGN_GUIDE.md` for global conventions.

## Structure

A left-to-right "hourglass" laid out from computed x-edges (no manual
coordinates to chase). Parameters live in the `==== parameters ====` block:

- `\blockH` — height of the input/output blocks (cm). Also the height of each
  trapezoid's **wide (outer) edge**.
- `\latentH` — height of the bottleneck `z` (cm). Also each trapezoid's **narrow
  (inner) edge**, so the shapes meet `z` flush.
- `\trapW` — width of the encoder/decoder trapezoids.
- `\blockW`, `\latentW` — widths of the input/output blocks and `z`.
- `\gap` — horizontal gap between every part (also the arrow length).
- Label macros: `\inputlabel \encoderlabel \latentlabel \decoderlabel \outputlabel`
  (use math like `$z$`, `$\hat{x}$` freely).

The body computes running left/right edges (`\xiL,\xiR,\xeL,...`) and centres
(`\xiC,\xeC,...`), then draws, in order:

- **Encoder** trapezoid (wide left → narrow right), `fill=otblue!18`, named text
  node `(enc)` at its centre.
- **Decoder** trapezoid (narrow left → wide right), `fill=otteal!18`, text node `(dec)`.
- **input** / **output** rectangle nodes (`ioblock` style, neutral `otgray`).
- **z** bottleneck rectangle node (`latentblk` style, `otorange` highlight).
- Four **flow** arrows along the centre line connecting the parts.

Named nodes for targeting: `(input) (enc) (z) (dec) (output)`.

Styles: `ioblock`, `trap`, `latentblk`, `lbl`, `flow`.

## Common edit operations

**Rename a part** — edit the matching label macro, e.g.
`\def\encoderlabel{Encoder}` → `{CNN Encoder}`, or `\def\latentlabel{$z$}` →
`{$\mathbf{z}$}`. No layout changes needed.

> Caution: `\latentlabel` is drawn **inside** the small `z` block, which is only
> `\latentW` wide (≈0.9cm) — a short symbol like `$z$` fits, but a long label
> (e.g. "Latent code") will overflow the box and overlap the arrows. For a long
> latent label, move it **below** the block like the I/O labels: blank the inside
> label and add one underneath —
> `\node[lbl, below=3pt of z] {Latent code};` (the inside-`z` `\node ... {\latentlabel}`
> line becomes `{}`). The encoder/decoder labels live inside wide trapezoids and
> have no such limit.

**Recolor** — change the color *name* (never a hex/stock color):
- Encoder: in the encoder `\filldraw`, `fill=otblue!18, draw=otblue!75!black`.
- Decoder: in the decoder `\filldraw`, `fill=otteal!18, draw=otteal!70!black`.
- Bottleneck: the `latentblk` style (`otorange`).
- Whole figure to one hue: set encoder + decoder to the same name.

**Make the bottleneck tighter / wider** — change `\latentH` (and `\latentW`).
Because the trapezoids' inner edge equals `\latentH`, they stay flush with `z`
automatically. A very small `\latentH` exaggerates compression.

**Resize blocks / spacing** — `\blockH`/`\blockW` for the I/O blocks, `\trapW`
for trapezoid length, `\gap` for spacing (and arrow length).

**Add a stage** (e.g. a second latent or a "quantizer" between encoder and z) —
insert another running edge pair after the relevant part, e.g. between `\xeR` and
`\xzL` add `\xqL/\xqR`, push the later edges along by its width + `\gap`, draw the
new node, and add the extra `flow` arrow. Keep every part's vertical centre on
`y=0`.

**Add a cross-attention block** — to show the decoder attending to the encoder
(seq2seq / transformer style), add a block above the bottleneck that the encoder
feeds and that feeds the decoder. Place it with `positioning` relative to `(z)`
and connect with `flow` arrows; recolour by giving it a palette name:
```
\node[rounded corners=3pt, draw=otblue!80!black, fill=otblue!18,
      minimum width=2cm, minimum height=0.9cm, font=\sffamily\small,
      above=0.9cm of z] (xattn) {Cross-attn};
\draw[flow] (enc) to[out=70,in=180] (xattn);   % encoder features -> cross-attn
\draw[flow] (xattn) to[out=0,in=110] (dec);    % cross-attn -> decoder
```
"make it blue" = the `otblue` fill/draw above; use another palette name to recolour.
Keep the named nodes `(enc)`/`(z)`/`(dec)` intact — the new block hangs off them.

**Show input/output as data** (image/sequence) — replace the `ioblock` node's
body: give it `{\includegraphics...}` (needs `graphicx`) or stack small squares;
keep the node name `input`/`output` so arrows still attach.

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
(`\trapW`/`\blockH`/`\gap`) and resize the rest. To change the intrinsic
**aspect ratio** rather than just scale, adjust those same parameters.

## Constraints

- Must stay **standalone-compilable** (`\documentclass{standalone}`).
- Keep each trapezoid's inner-edge height equal to `\latentH` (it already reads
  `\lh = \latentH/2`) so encoder/decoder stay flush with `z`.
- Preserve the node names `(input) (enc) (z) (dec) (output)` — the contract this
  skill targets.
- Colors only via the five palette names (tints/shades like `otblue!18` are
  fine); never inline hex or stock xcolor names.
- After editing, re-render: `python3 tools/render_preview.py templates/encoder-decoder/template.tex -o templates/encoder-decoder/preview.svg` and validate with `python3 tools/validate.py --strict`.
