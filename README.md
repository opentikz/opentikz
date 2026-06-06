# OpenTikZ

> A TikZ resource library for academic conceptual diagrams — copyable icons,
> editable architecture templates, and AI-consumable skills that let Claude Code
> modify those templates, so researchers produce paper figures fast without
> writing TikZ from scratch.

OpenTikZ is the "Flaticon for academic TikZ", focused on conceptual/overview
figures — system block diagrams, neural-network architectures, pipelines, and
flowcharts. **Data plots are out of scope** (use pgfplots/matplotlib).

## Three-layer content model

- **`icons/`** — atomic, single-concept TikZ elements, each compiles standalone
  and is independently copyable.
- **`templates/`** — complete, editable conceptual figures (the core value).
- **`skills/`** — structured instructions that let an AI agent reliably modify a
  template (add/remove a node, recolor, change counts, adapt to a column width).

## Repository layout

```
icons/<domain>/<name>/      <name>.tex + <name>.meta.json + <name>.svg
templates/<name>/           template.tex + template.meta.json + skill.md + preview.svg
skills/                     color-palettes/, annotations/, layout/
examples/<name>/            paper-grade figures combining icons + templates
tools/                      build_catalog.py, render_preview.py, validate.py
meta.schema.json            JSON Schema for every .meta.json
catalog.json                AUTO-GENERATED — do not hand-edit
```

See [`CLAUDE.md`](CLAUDE.md) and [`docs/`](docs/) for the full product spec,
design guide, and roadmap.

## Tooling

```bash
python3 -m pip install -r requirements.txt   # installs jsonschema
python3 tools/validate.py                     # validate metadata + compile .tex
python3 tools/build_catalog.py                # regenerate catalog.json
python3 tools/render_preview.py <item>        # render a trimmed .svg preview
```

`validate.py` and `render_preview.py` need a LaTeX toolchain (`latexmk`) plus an
SVG backend (`dvisvgm`, or `pdf2svg` + `pdfcrop`). Without LaTeX installed,
`validate.py` still checks metadata and skips the compile step.

## Licensing

- **Code** (scripts, build tooling): MIT — see [`LICENSE-CODE`](LICENSE-CODE).
- **Graphic content** (`.tex` figures and previews): CC0 1.0 — see
  [`LICENSE-CONTENT`](LICENSE-CONTENT).
