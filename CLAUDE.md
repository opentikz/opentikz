# OpenTikZ — Project Context for Claude Code

> This file is read automatically by Claude Code. It gives you (the AI agent)
> everything needed to work on this project. Read it fully before acting.

## What this project is

OpenTikZ is a community library of **TikZ resources for academic conceptual
diagrams** — system block diagrams, neural network architectures, pipelines,
and flowcharts. It is the "Flaticon for academic TikZ", focused specifically on
conceptual/overview figures (NOT data plots).

**One-line positioning:** A TikZ resource library for paper diagrams — copyable
icons, editable architecture templates, and skills that let Claude Code modify
those templates so researchers can produce figures fast without writing TikZ
from scratch.

## Target user

Researchers who already write papers in LaTeX, need to draw system/architecture/
pipeline/flow diagrams, but don't want to hand-write TikZ. We call them the
"middle layer": comfortable with LaTeX, not comfortable building TikZ from zero.

## Explicit non-goals (do NOT build these)

- Data plots (line/bar/scatter/heatmap) — those belong to pgfplots/matplotlib
- Pixel-perfect PNG→TikZ conversion (technically an under-determined problem)
- Brand/company logos (trademark risk)
- General-purpose illustration

## The three-layer content model

1. **Icons** (`icons/`) — atomic, single-concept TikZ elements (server, GPU,
   cloud, database, neuron, attention block, user, arrow/pipe). Each compiles
   standalone and is independently copyable.

2. **Templates** (`templates/`) — complete, editable conceptual figures (neural
   net, encoder-decoder, training pipeline, federated learning, system block
   diagram, flowchart). This is the core value.

3. **Skills** (`skills/`) — THE KEY DIFFERENTIATOR. Structured instructions that
   let an AI agent (you) reliably modify a template: how to add/remove a node,
   recolor, change node count, adapt to a conference column width. Each template
   ships with a companion skill so a user can say "add a cross-attention layer
   to this transformer template and make it blue" and you can do it correctly
   without guessing.

## Hard rules for all content

- Every `.tex` file MUST compile standalone (`\documentclass{standalone}`).
- Every content item has a sibling `.meta.json` validated against
  `meta.schema.json`.
- Colors come from a shared palette (see `skills/color-palettes/`), never
  hard-coded hex inline.
- Node names follow the convention in `docs/DESIGN_GUIDE.md` so skills can
  target parts reliably.
- Provide light + dark friendly palettes where feasible.

## Licensing

- Code (scripts, build tooling): MIT
- Graphic content (.tex figures): CC0 (maximize academic reuse, zero friction)
- State this clearly; never mix them up.

## Repo structure (target)

```
opentikz/
├── CLAUDE.md                 # this file
├── README.md                 # public-facing, gallery + quick start
├── CONTRIBUTING.md           # how to submit, format rules
├── LICENSE-CODE              # MIT
├── LICENSE-CONTENT           # CC0
├── meta.schema.json          # JSON Schema for all .meta.json
├── catalog.json              # AUTO-GENERATED, do not hand-edit
├── docs/
│   ├── DESIGN_GUIDE.md       # line width, colors, node naming
│   ├── PRODUCT_SPEC.md       # full product spec
│   └── ROADMAP.md            # MVP steps
├── icons/<domain>/<name>/
│   ├── <name>.tex
│   ├── <name>.meta.json
│   └── <name>.svg            # AUTO-GENERATED preview
├── templates/<name>/
│   ├── template.tex
│   ├── template.meta.json
│   ├── skill.md              # companion skill for AI editing
│   └── preview.svg           # AUTO-GENERATED
├── skills/
│   ├── color-palettes/
│   ├── annotations/
│   └── layout/
├── examples/<name>/          # full paper-grade figures combining the above
└── tools/
    ├── build_catalog.py      # scans tree -> catalog.json
    ├── render_preview.py     # latexmk + pdf2svg -> .svg
    └── validate.py           # schema + standalone-compile checks
```

## How you (Claude Code) should work on this

- When adding an icon/template: create the `.tex`, write the `.meta.json`,
  then run `tools/validate.py` and `tools/render_preview.py` on it.
- Never hand-edit `catalog.json`; regenerate it via `tools/build_catalog.py`.
- When writing a template, also write its `skill.md` describing structure,
  common edit operations, and constraints.
- Keep `.tex` parametric and clearly named — both humans and AI must be able to
  edit it safely.
- Prefer many small, well-named files over large monolithic ones.

## Current status

Bootstrapping. See `docs/ROADMAP.md` for the MVP step we're on.
