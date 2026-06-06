# OpenTikZ — Product Spec

## Positioning

A TikZ resource library for academic conceptual diagrams. Copyable icons,
editable architecture templates, and AI-consumable skills that let Claude Code
modify templates so researchers produce figures fast without writing TikZ from
scratch.

## Target user

Researchers who write papers in LaTeX, need conceptual diagrams (system block
diagrams, neural net architectures, pipelines, flowcharts), and don't want to
hand-write TikZ. The "middle layer" — comfortable with LaTeX, not with raw TikZ.

## Why TikZ for this (and not SVG/PNG)

Conceptual/overview diagrams are TikZ's irreplaceable strength:
- Fonts and math symbols match the paper body exactly (SVG/PNG can't)
- Vector, infinite scaling, print quality
- Text is searchable/accessible in the PDF
- Parametric, version-controllable, batch-recolorable

Data plots are deliberately out of scope — those go to pgfplots/matplotlib.

## Differentiation

Templates exist everywhere (scattered across StackExchange, personal repos).
The gap is "templates + an AI that can reliably edit them." The Skills layer
encodes how to safely modify each figure, turning TikZ's "hard to edit" pain
into an AI-assisted strength. That is the moat.

## Three-layer content model

- **Icons** — atomic elements, standalone-compilable, individually copyable.
- **Templates** — complete editable figures; the core value.
- **Skills** — structured edit instructions an AI agent consumes to modify
  templates accurately (add/remove nodes, recolor, change counts, adapt to
  conference column widths).

## Core UX principles

- Self-contained, standalone-compilable `.tex`
- One-click copy
- CI pre-rendered previews (not browser-side rendering)
- Light/dark palettes
- Clear license (code MIT, content CC0)

## Licensing decision

- Code: MIT (highest recognition, simplest)
- Graphic content: CC0 (zero-friction academic reuse; recognition comes from
  quality, not mandatory attribution)

## Non-goals

Data plots, pixel-perfect PNG→TikZ, brand logos, general illustration.

## Success definition

Become the default place to find TikZ conceptual figures: listed in
awesome-tikz, cited in papers (provide BibTeX), dozens of contributors. This is
a respected community public-good project, not a venture-scale business —
academic users rarely pay, so sustainability is via sponsors/donations. Healthy
mindset: high-quality portfolio + community contribution; growth is a bonus.
