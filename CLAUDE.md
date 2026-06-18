# OpenTikZ — Project Context for Claude Code

> This file is read automatically by Claude Code. It gives you (the AI agent)
> everything needed to work on this project. Read it fully before acting.

## What this project is

OpenTikZ is a community library of **TikZ resources for academic conceptual
diagrams** — system block diagrams, neural network architectures, pipelines,
and flowcharts. It is the "Flaticon for academic TikZ", focused specifically on
conceptual/overview figures (NOT data plots).

**One-line positioning:** A TikZ resource library for paper diagrams — copyable
icons, editable architecture templates, and one repo-wide skill that lets Claude
Code modify those templates so researchers can produce figures fast without
writing TikZ from scratch.

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

2. **Templates** (`templates/`) — complete, **parametric** conceptual figures
   (neural net, encoder-decoder, training pipeline, system block diagram,
   flowchart, distributed training, inference serving). This is the core value.
   Every template carries an `edit_contract` — that contract IS what makes a
   figure a template (see the boundary rule below).

   **Template vs. example (the boundary):** a figure that is worth editing
   parametrically (clear parameter surface + stable node names an AI can target)
   is a **template** and MUST ship an `edit_contract`; a fixed reference figure
   whose value is "look what the library assembles into" is an **example**
   (defined by `composed_of`, no `edit_contract`). The presence of an
   `edit_contract` is the definition of a template — never add one to an example;
   if you want to, that figure has become a template, so move it to `templates/`.
   The full rule lives in `CONTRIBUTING.md`.

3. **Skill** (`skills/using-opentikz/`) — THE KEY DIFFERENTIATOR. One repo-wide
   skill that takes an AI agent (you) from a request to a finished figure:
   discover content via `catalog.json`, edit the chosen item, verify it compiles —
   while communicating precisely (ask on material ambiguity, assume-and-state on
   safe defaults). Per-template knowledge lives in each template's `edit_contract`
   (inside its `meta.json`), which the skill reads at edit time; cross-cutting
   reference knowledge (palette, annotations, layout) lives under `reference/`.
   So a user can say "add a cross-attention layer to this template and make it
   blue" and you do it correctly without guessing. There is no per-template
   `skill.md` — that knowledge is now the structured `edit_contract`.

## Hard rules for all content

- Every `.tex` file MUST compile standalone (`\documentclass{standalone}`).
- Every content item has a sibling `.meta.json` validated against
  `meta.schema.json`.
- Colors come from a shared palette (see `reference/color-palettes/`), never
  hard-coded hex inline.
- Node names follow the convention in `docs/DESIGN_GUIDE.md` so the skill can
  target parts reliably.
- Every template carries an `edit_contract` in its `meta.json` (parameters,
  node-naming, styles, operations, invariants); `validate.py` checks its
  parameters/styles exist in the `.tex`.
- Provide light + dark friendly palettes where feasible.

## Licensing

- Code (scripts, build tooling): MIT
- Graphic content (.tex figures): CC0 (maximize academic reuse, zero friction)
- State this clearly; never mix them up.

## Repo structure

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
│   └── ROADMAP.md            # MVP steps (with progress markers)
├── icons/<domain>/<name>/
│   ├── <name>.tex
│   ├── <name>.meta.json
│   └── <name>.svg            # AUTO-GENERATED preview
├── templates/<name>/
│   ├── template.tex
│   ├── template.meta.json    # includes the edit_contract for AI editing
│   └── preview.svg           # AUTO-GENERATED
├── skills/
│   └── using-opentikz/       # THE one repo-wide skill (SKILL.md)
├── reference/                # cross-cutting reference knowledge (NOT in catalog.json)
│   ├── color-palettes/
│   ├── annotations/
│   └── layout/
├── examples/<name>/          # full paper-grade figures combining the above
├── skills-demos/             # before/after SVGs for the "skills in action" site section
├── .github/workflows/
│   ├── ci.yml                # PR: validate + standalone-compile + preview freshness
│   └── pages.yml             # push to main: build_site.py -> GitHub Pages
└── tools/
    ├── _common.py            # shared stdlib helpers (repo_root, meta walking)
    ├── build_catalog.py      # scans tree -> catalog.json
    ├── render_preview.py     # compile + dvisvgm (DVI route) -> .svg
    ├── build_site.py         # catalog.json + previews -> static site/ (stdlib only)
    └── validate.py           # schema + structural rules + standalone compile
```

## How you (Claude Code) should work on this

- When adding an icon/template: create the `.tex`, write the `.meta.json`,
  then run `tools/validate.py` and `tools/render_preview.py` on it.
- Never hand-edit `catalog.json`; regenerate it via `tools/build_catalog.py`.
- When writing a template, add an `edit_contract` to its `meta.json` (parameters,
  node_naming, styles, operations, invariants) instead of a `skill.md`. The one
  skill in `skills/using-opentikz/` reads it; `validate.py` checks its
  parameters/styles exist in the `.tex`.
- Keep `.tex` parametric and clearly named — both humans and AI must be able to
  edit it safely.
- Mirror every `\usepackage{tikz}` / `\usetikzlibrary{...}` the `.tex` uses into
  the item's `requires` — `validate.py` now fails the build if they drift.
- After editing a `.tex`, regenerate its `.svg` preview (`render_preview.py`);
  CI rejects a PR whose source changed without a regenerated preview.
- Prefer many small, well-named files over large monolithic ones.

## Current status

Live. MVP Roadmap Steps 1–4 are complete: repo skeleton + CI, the cold-start
content (31 catalog items — 20 icons, 8 templates, 3 examples), the skills layer (one
repo-wide `using-opentikz` skill + per-template `edit_contract`s + `reference/`
material), and the static website (built by `tools/build_site.py`, deployed to
GitHub Pages). See `docs/ROADMAP.md` for per-step status and what remains
(Step 5: launch + community).
