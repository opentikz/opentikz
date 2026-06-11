# Contributing to OpenTikZ

Thanks for helping build the "Flaticon for academic TikZ". This guide covers how
to add content, the rules that keep it consistent and AI-editable, and the local
workflow to validate your work before opening a pull request.

If anything here is unclear, open an issue — improving this guide is a welcome
contribution too.

## Licensing — read this first

OpenTikZ is dual-licensed, and the split matters:

- **Graphic content** — every `.tex` figure, its `.meta.json`, and rendered
  `.svg` preview — is **CC0 1.0** (public domain dedication). By contributing
  content you agree to release it under CC0 so researchers can reuse it with zero
  friction. **Do not** submit figures you cannot dedicate to the public domain,
  and **do not** reproduce copyrighted/trademarked material (company logos,
  branded marks — a declared non-goal).
- **Code** — build tooling under `tools/` and the site generator — is **MIT**.

Set `"license": "CC0-1.0"` in every content `.meta.json`.

## What to contribute

OpenTikZ has three content layers. Pick the one that fits:

| Layer | Lives in | What it is |
|-------|----------|-----------|
| **Icon** | `icons/<domain>/<name>/` | An atomic, single-concept element (server, GPU, neuron, database). |
| **Template** | `templates/<name>/` | A complete, editable conceptual figure **+ a companion `skill.md`**. |
| **Example** | `examples/<name>/` | A paper-grade figure combining icons + templates to show real use. |

**In scope:** system/architecture/pipeline/flow diagrams for papers.
**Out of scope** (see [`CLAUDE.md`](CLAUDE.md)): data plots (use pgfplots/matplotlib),
PNG→TikZ tracing, brand/company logos, general illustration.

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
   [`skills/color-palettes/`](skills/color-palettes/). Tints/shades like
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
  template.meta.json
  skill.md              # REQUIRED — how an AI edits this template
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
- `type` — `icon` · `template` · `example` · `skill`.
- `domain` — browse grouping (e.g. `systems`, `ml`, `pipeline`). At least one.
- `tags` — free-form search keywords.
- `requires` — LaTeX packages / TikZ libraries the `.tex` preamble needs.
- `preview` — relative path to the generated `.svg`.
- Optional: `venue` (column widths it's tuned for), `description`, `featured`,
  `composed_of` (ids of items an example is built from).

## Companion `skill.md` (templates only)

A template's `skill.md` is the differentiator — it lets an AI agent edit the
figure correctly. Document three things (see existing templates for the shape,
e.g. [`templates/encoder-decoder/skill.md`](templates/encoder-decoder/skill.md)):

1. **Structure** — the named parts, the parameters (`\def`s), and how they relate.
2. **Common edit operations** — add/remove a part, recolor (by palette name),
   change counts, resize, adapt to a venue/column width — each with the **exact**
   approach (which line/macro to touch).
3. **Constraints** — must stay standalone-compilable, which node names to
   preserve, palette-only colors.

Only document operations the template can actually back. Don't ship a skill that
promises an edit the figure can't do.

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
- [ ] Templates: a `skill.md` is included and documents real edit operations.
- [ ] Content `.meta.json` has `"license": "CC0-1.0"`; you can release it as CC0.

CI runs `validate.py --strict` and `build_catalog.py --check` on every PR and
renders previews — keep both green.

## Code of conduct

Be respectful and constructive. Assume good faith. Harassment isn't tolerated.

Thanks for contributing — every clean, reusable figure saves a researcher an
afternoon of fighting TikZ.
