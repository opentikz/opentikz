# Contributing to OpenTikZ

Thanks for helping build the "Flaticon for academic TikZ". This guide covers how
to add content, the rules that keep it consistent and AI-editable, and the local
workflow to validate your work before opening a pull request.

If anything here is unclear, ask in [Discussions](https://github.com/opentikz/opentikz/discussions)
— improving this guide is a welcome contribution too. Use **Issues** for bugs and
concrete, closeable tasks; use **Discussions** for questions, ideas, and sharing
figures you built.

## Licensing — read this first

OpenTikZ is dual-licensed, and the split matters:

- **Graphic content** — every `.tex` figure, its `.meta.json`, and rendered
  `.svg` preview — is **CC0 1.0** (public domain dedication). By contributing
  content you agree to release it under CC0 so researchers can reuse it with zero
  friction. **Do not** submit figures you cannot dedicate to the public domain,
  and **do not** reproduce copyrighted/trademarked material (company logos,
  branded marks — a declared non-goal). The one maintainer-approved exception
  is the curated `icons/brands/` set, whose shape data comes from the CC0
  [simple-icons](https://simple-icons.org) project; the TikZ code is CC0, but
  the marks remain trademarks of their owners — see `icons/brands/README.md`.
- **Code** — build tooling under `tools/` and the site generator — is **MIT**.

Set `"license": "CC0-1.0"` in every content `.meta.json`.

## What to contribute

OpenTikZ has three content layers. Pick the one that fits:

| Layer | Lives in | What it is |
|-------|----------|-----------|
| **Icon** | `icons/<domain>/<name>/` | An atomic, single-concept element (server, GPU, neuron, database). |
| **Template** | `templates/<name>/` | A complete, **parametric** conceptual figure meant to be edited as a starting point — **carries a required `edit_contract` in its `meta.json`**. |
| **Example** | `examples/<name>/` | A fixed, paper-grade **showcase** composed of ≥2 library items (`composed_of`), shown as-is — **no `edit_contract`**. |

### Template vs. example: which layer?

The dividing line is **the `edit_contract`, and it is deliberate**:

- If the figure is worth editing parametrically — it has a clear parameter
  surface (spacing/count/label `\def`s) and a stable node-naming scheme an AI can
  target — it is a **template**, and it MUST ship an `edit_contract`.
- If the figure is a fixed reference composition — its value is "look, this is
  what the library assembles into," not "edit me" — it is an **example**, defined
  by `composed_of` (the ids it is built from) and carrying **no** `edit_contract`.

So the presence of an `edit_contract` *is* the definition of a template. Don't add
one to an example: examples are already editable directly (the skill edits any
`.tex`), they just don't promise the contract's safety rails. If you find yourself
wanting to parametrize and contract an example, that figure has become a template —
move it to `templates/`, rename `figure.*` → `template.*`, and add the contract.

**In scope:** system/architecture/pipeline/flow diagrams for papers.
**Out of scope** (see [`CLAUDE.md`](CLAUDE.md)): data plots (use pgfplots/matplotlib),
PNG→TikZ tracing, brand/company logos (except the curated `icons/brands/` set —
see its README), general illustration.

Good first contributions: a new **icon** in `systems/` or `ml/`, or an **example**
that reuses existing templates.

## Hard rules (all content)

These are enforced by `tools/validate.py` and by review — content that breaks
them won't merge:

1. **Standalone-compilable.** Every `.tex` uses `\documentclass{standalone}` and
   compiles on its own with `pdflatex`/`lualatex`/`xelatex`.
2. **Sibling `.meta.json`.** Every content item has one, validated against
   [`meta.schema.json`](meta.schema.json).
3. **Palette colors only.** Never hard-code hex inline. Use the named palette
   colors (`otblue`, `otorange`, `otteal`, `otpurple`, `otgray`, …) from
   [`reference/color-palettes/`](reference/color-palettes/). Tints/shades like
   `otblue!18` or `otteal!75!black` are fine. Default to the color-blind-friendly
   palette; provide a dark-friendly variant where feasible.
4. **Semantic node names.** Name nodes for what they are — `(enc)`, `(input)`,
   `(layer1)` — never `(a)`, `(b)`, or bare coordinates. Connect nodes by name,
   not absolute coordinates, so figures stay editable. See
   [`docs/DESIGN_GUIDE.md`](docs/DESIGN_GUIDE.md).
5. **Parametric.** Put counts, spacing, and sizes in `\def`s / pgfkeys at the top
   of the file so they're easy to change. Prefer the `positioning` library
   (`right=of`, `below=of`) over absolute coordinates.
6. **Never hand-edit `catalog.json`.** It is generated — run
   `tools/build_catalog.py`.
7. **2-space indentation**, one logical element per line where practical.

Full conventions live in [`docs/DESIGN_GUIDE.md`](docs/DESIGN_GUIDE.md). Read it
before your first contribution.

## Directory layout per item

```
icons/<domain>/<name>/
  <name>.tex            # the figure (standalone)
  <name>.meta.json      # metadata (schema-validated)
  <name>.svg            # generated preview — commit it

templates/<name>/
  template.tex
  template.meta.json    # REQUIRED edit_contract — how an AI edits this template
  preview.svg

examples/<name>/
  figure.tex
  figure.meta.json
  preview.svg
```

## Metadata (`.meta.json`)

Validated against [`meta.schema.json`](meta.schema.json). Required fields:

```json
{
  "id": "gpu",
  "name": "GPU",
  "type": "icon",
  "domain": ["systems"],
  "tags": ["gpu", "accelerator", "cuda", "compute", "hardware"],
  "author": "Your Name or handle",
  "license": "CC0-1.0",
  "requires": ["tikz"],
  "preview": "gpu.svg",
  "description": "One-line description of the item."
}
```

- `id` — globally unique, stable, kebab-case (`^[a-z0-9]+(?:-[a-z0-9]+)*$`).
- `type` — `icon` · `template` · `example`.
- `domain` — browse grouping (e.g. `systems`, `ml`, `pipeline`). At least one.
- `tags` — free-form search keywords.
- `requires` — LaTeX packages / TikZ libraries the `.tex` preamble needs.
- `preview` — relative path to the generated `.svg`.
- Optional: `venue` (column widths it's tuned for), `description`, `featured`,
  `composed_of` (ids of items an example is built from), and — templates only —
  `edit_contract` (below).

## `edit_contract` (templates only)

A template's `edit_contract` (a field in its `meta.json`) is the differentiator —
it is the structured knowledge the `skills/using-opentikz/` skill reads to edit
the figure correctly. It replaces the old per-template `skill.md`. Five parts
(see [`templates/neural-net/template.meta.json`](templates/neural-net/template.meta.json)
for a worked example):

1. **`parameters`** — the `\def` macros that drive the figure: `name` (with
   backslash), `type`, `meaning`, optional `default`/`invariant`.
2. **`node_naming`** — the scheme the skill targets (e.g. `L<layer>-<neuron>`).
3. **`styles`** — the tikz style names (each `<name>/.style=` in the `.tex`).
4. **`operations`** — real, safe edits (`id` + `summary`): add/remove a part,
   recolor, change counts, resize, etc.
5. **`invariants`** — rules an edit must never break.

`validate.py` checks that every `parameters[].name` and `styles[]` entry actually
exists in the `.tex`, so the contract can't drift. Only document operations the
template can actually back. Cross-cutting how-to (dark palette, venue widths) lives
once in the skill, not per template; see `reference/` for palette/annotations/layout.

## Local workflow

```bash
python3 -m pip install -r requirements.txt        # one-time: installs jsonschema

# 1. create your item's .tex + .meta.json (copy an existing item as a starting point)

# 2. render the preview SVG (needs LaTeX: latexmk + dvisvgm, or pdf2svg + pdfcrop)
python3 tools/render_preview.py icons/systems/gpu/gpu.tex \
        -o icons/systems/gpu/gpu.svg

# 3. validate metadata + standalone compile
python3 tools/validate.py --strict

# 4. regenerate the catalog (never edit catalog.json by hand)
python3 tools/build_catalog.py
```

**No LaTeX locally?** `tools/validate.py` (without `--strict`) still checks your
metadata and skips the compile step; CI compiles and renders on every PR. But
please commit a real `.svg` preview — generate it on a machine with LaTeX, or ask
a maintainer in the PR.

### Toolchain

CI uses a TeX distribution (`latexmk`) plus `dvisvgm`. Locally, TinyTeX +
`dvisvgm` works well. The renderer defaults to the **dvisvgm DVI route**
(`latexmk -dvi` → `dvisvgm`); pass `--backend pdf2svg` for the PDF route.

## Pull request checklist

Before opening a PR, confirm:

- [ ] `.tex` compiles standalone (`pdflatex`/`lualatex`/`xelatex`).
- [ ] Sibling `.meta.json` present and `tools/validate.py --strict` passes.
- [ ] Colors use **palette names**, no inline hex.
- [ ] Node names are semantic; connections reference names, not coordinates.
- [ ] Generated `.svg` preview committed.
- [ ] `catalog.json` regenerated via `tools/build_catalog.py` (not hand-edited);
      `tools/build_catalog.py --check` is clean.
- [ ] Templates: an `edit_contract` is included and documents real edit operations
      (and `validate.py` confirms its parameters/styles exist in the `.tex`).
- [ ] Content `.meta.json` has `"license": "CC0-1.0"`; you can release it as CC0.

CI runs `validate.py --strict` and `build_catalog.py --check` on every PR and
renders previews — keep both green.

## Code of conduct

Be respectful and constructive. Assume good faith. Harassment isn't tolerated.

Thanks for contributing — every clean, reusable figure saves a researcher an
afternoon of fighting TikZ.
