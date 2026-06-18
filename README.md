# OpenTikZ

> A TikZ resource library for academic conceptual diagrams — copyable icons,
> editable architecture templates, and one AI-consumable skill that lets Claude
> Code modify those templates, so researchers produce paper figures fast without
> writing TikZ from scratch.

OpenTikZ is the "Flaticon for academic TikZ", focused on conceptual/overview
figures — system block diagrams, neural-network architectures, pipelines, and
flowcharts. **Data plots are out of scope** (use pgfplots/matplotlib).

## Quick start

The fastest path is to let an AI agent do the TikZ for you:

1. **Clone OpenTikZ into your project** — the icons, templates, and the
   `using-opentikz` skill come with it.
2. **Tell Claude Code the figure or edit you want** — *"draw an encoder–decoder
   with a cross-attention block,"* or, pointing at a template, *"add a hidden
   layer / recolor this blue / fit it to a CVPR column."* The skill plus each
   template's `edit_contract` guide the agent to edit real TikZ correctly.
3. **Get editable TikZ that compiles** — every file is
   `\documentclass{standalone}`, so it builds with `pdflatex`, `lualatex`, or
   `xelatex`, no extra setup.

Prefer to grab one by hand? **[Browse the gallery](#gallery)**, copy its `.tex`,
and you're done — no AI required.

## Why TikZ, and why OpenTikZ

**Why TikZ at all?** A TikZ figure is *source code*, not an image:

- **Vector quality** — crisp at any zoom, sharp in print; no pixelated screenshots.
- **Native to your paper** — same fonts, math (`$\mathbf{W}x$`), and
  `\ref`/`\cite` as the document, so the figure looks part of the paper.
- **Diffable** — version it in git, tweak one number, recompile.

**Why not just ask ChatGPT for TikZ directly?** You can — but raw LLM TikZ tends
to fight you. OpenTikZ anchors the edit to a real, parametric template:

| What you care about | Raw LLM TikZ | OpenTikZ + skill |
| --- | --- | --- |
| Compiles first try | Often not | Yes, standalone |
| Packages / macros | Sometimes invented | Real, declared in `requires` |
| Colors | Random hex | Shared palette |
| Re-editing later | Re-describe everything | Stable node names |
| AI guidance | None | Each template ships an `edit_contract` |

Because every template is parametric, palette-correct, and carries an
`edit_contract`, an agent edits it **accurately** and **fast** instead of
hand-writing TikZ that may not compile.

### A concrete edit

Starting from [`templates/encoder-decoder/`](templates/encoder-decoder/), tell
Claude Code:

> *"add a cross-attention block and make it blue"*

Guided by the template's `edit_contract` — using the shared palette and the
template's stable node names — it adds:

```tex
% cross-attention block (decoder attends to encoder)
\node[draw=otblue!80!black, fill=otblue!18, rounded corners=2pt,
  minimum width=\trapW cm, minimum height=0.7cm]
  (xattn) at (\xdC,\bh+0.9) {\sffamily\small Cross-Attn};
\draw[flow, draw=otblue] (enc) to[bend left=20] (xattn);
\draw[flow, draw=otblue] (xattn) -- (dec);
```

…and it compiles standalone, first try.

## Gallery

A taste of the library below — every preview is rendered from the committed `.tex`
source (no mockups). **The full, searchable catalog with copy-to-clipboard lives
on the [website](#website)**; or browse [`examples/`](examples/),
[`templates/`](templates/), and [`icons/`](icons/) directly.

### Examples — paper-grade figures combining icons + templates

<table>
<tr>
<td align="center" width="33%"><a href="examples/lora/"><img src="examples/lora/preview.svg" alt="LoRA (low-rank adaptation)" width="260"></a><br><sub><b>LoRA</b> · low-rank adaptation</sub></td>
<td align="center" width="33%"><a href="examples/flash-attention/"><img src="examples/flash-attention/preview.svg" alt="FlashAttention" width="260"></a><br><sub><b>FlashAttention</b> · tiled attention</sub></td>
<td align="center" width="33%"><a href="examples/gan/"><img src="examples/gan/preview.svg" alt="Generative adversarial network" width="260"></a><br><sub><b>GAN</b> · generator / discriminator</sub></td>
</tr>
</table>

### Templates — editable, AI-modifiable (each ships an `edit_contract`)

<table>
<tr>
<td align="center" width="33%"><a href="templates/neural-net/"><img src="templates/neural-net/preview.svg" alt="Feed-forward neural network" width="240"></a><br><sub><b>Feed-forward</b> neural network</sub></td>
<td align="center" width="33%"><a href="templates/encoder-decoder/"><img src="templates/encoder-decoder/preview.svg" alt="Encoder-decoder (bottleneck)" width="240"></a><br><sub><b>Encoder-decoder</b> · bottleneck</sub></td>
<td align="center" width="33%"><a href="templates/training-pipeline/"><img src="templates/training-pipeline/preview.svg" alt="Training pipeline" width="240"></a><br><sub><b>Training pipeline</b> · loss/optimizer loop</sub></td>
</tr>
</table>

<sub>…and more — system block diagrams, flowcharts, ResNet blocks, distributed
training, inference serving. See [`templates/`](templates/).</sub>

### Icons — atomic, single-concept, independently copyable

<table>
<tr>
<td align="center" width="20%"><a href="icons/systems/server/"><img src="icons/systems/server/server.svg" alt="Server" width="84"></a><br><sub>Server</sub></td>
<td align="center" width="20%"><a href="icons/systems/gpu/"><img src="icons/systems/gpu/gpu.svg" alt="GPU" width="84"></a><br><sub>GPU</sub></td>
<td align="center" width="20%"><a href="icons/systems/cloud/"><img src="icons/systems/cloud/cloud.svg" alt="Cloud" width="84"></a><br><sub>Cloud</sub></td>
<td align="center" width="20%"><a href="icons/ml/neuron/"><img src="icons/ml/neuron/neuron.svg" alt="Neuron" width="84"></a><br><sub>Neuron</sub></td>
<td align="center" width="20%"><a href="icons/ml/attention/"><img src="icons/ml/attention/attention.svg" alt="Attention block" width="84"></a><br><sub>Attention</sub></td>
</tr>
</table>

<sub>…and many more across <code>systems/</code> and <code>ml/</code>. See
[`icons/`](icons/) or search the [website](#website).</sub>

> Previews are transparent SVGs; labels read best on a light background. The live
> [website](#website) renders them on paper-white tiles.

## Three-layer content model

- **`icons/`** — atomic, single-concept TikZ elements, each compiles standalone
  and is independently copyable.
- **`templates/`** — complete, editable conceptual figures (the core value); each
  carries an `edit_contract` in its `meta.json` describing how to edit it safely.
- **`skills/using-opentikz/`** — the one repo-wide skill that lets an AI agent go
  from a request to a finished figure (discover, edit, verify), backed by the
  per-template `edit_contract`s and the `reference/` material below.

## Repository layout

```
icons/<domain>/<name>/      <name>.tex + <name>.meta.json + <name>.svg
templates/<name>/           template.tex + template.meta.json (+ edit_contract) + preview.svg
skills/using-opentikz/      the one repo-wide skill (SKILL.md)
reference/                  color-palettes/, annotations/, layout/
examples/<name>/            paper-grade figures combining icons + templates
skills-demos/               before/after SVGs for the website's "skills in action"
tools/                      build_catalog.py, render_preview.py, build_site.py, validate.py
meta.schema.json            JSON Schema for every .meta.json
catalog.json                AUTO-GENERATED — do not hand-edit
```

See [`CLAUDE.md`](CLAUDE.md) and [`docs/`](docs/) for the full product spec,
design guide, and roadmap. Want to add a figure? See [`CONTRIBUTING.md`](CONTRIBUTING.md).

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

## Website

A static gallery (search + per-item pages with copyable `.tex`) is generated from
`catalog.json` and the committed `.svg` previews — no LaTeX needed:

```bash
python3 tools/build_catalog.py     # ensure catalog.json is current
python3 tools/build_site.py        # generates site/ (gitignored)
python3 -m http.server -d site     # preview at http://localhost:8000
```

It is live at **[opentikz.org](https://opentikz.org)**, deployed to GitHub Pages
automatically via `.github/workflows/pages.yml` on push to `main`. Client-side
search uses Fuse.js (CDN, pinned + SRI).

## Citing OpenTikZ

Content is CC0, so a citation is never required — but if OpenTikZ saved you time,
it is appreciated. Use the **"Cite this repository"** button on GitHub (powered by
[`CITATION.cff`](CITATION.cff)), or the BibTeX below:

```bibtex
@misc{opentikz,
  title        = {{OpenTikZ}: a TikZ resource library for academic conceptual diagrams},
  author       = {{OpenTikZ contributors}},
  year         = {2026},
  howpublished = {\url{https://opentikz.org}},
  note         = {Content licensed CC0 1.0}
}
```

## Licensing

- **Code** (scripts, build tooling): MIT — see [`LICENSE-CODE`](LICENSE-CODE).
- **Graphic content** (`.tex` figures and previews): CC0 1.0 — see
  [`LICENSE-CONTENT`](LICENSE-CONTENT).

By contributing graphic content you agree to release it under CC0 1.0. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).
