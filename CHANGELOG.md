# Changelog

All notable changes to OpenTikZ are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **2 brand-logo templates** with full `edit_contract`s: `llm-serving-stack`
  (users → vLLM engine on a GPU cluster serving swappable model cards) and
  `agent-mcp-stack` (user → LLM core → MCP servers fanning out to tool cards).
  Both compose the new brand icons as inlined TikZ pics.

- **41 brand icons** under `icons/brands/` (new `brands` domain), for figures
  that reference real tools and platforms: developer tooling (Docker, Git,
  GitHub, Kubernetes, Linux, Python, Reddit), the ML stack (PyTorch,
  TensorFlow, Hugging Face, Keras, scikit-learn, NumPy, pandas, Jupyter,
  Google Colab, Kaggle, Weights & Biases), companies and platforms common in
  papers (Anthropic, Meta, NVIDIA, Google, Google Cloud), academic publishing
  (arXiv, Google Scholar, IEEE, ORCID, Overleaf, LaTeX, Semantic Scholar),
  and AI/LLM brands (Claude, DeepSeek, Google Gemini, Mistral AI, Perplexity,
  Qwen, Ollama, GitHub Copilot, LangChain, vLLM, Model Context Protocol). Shape data derives from the CC0
  [simple-icons](https://simple-icons.org) project; each mark ships in its
  official brand color and remains a trademark of its owner (see
  `icons/brands/README.md`). A maintainer-approved exception to the "no brand
  logos" non-goal, now documented in `CONTRIBUTING.md` / `CLAUDE.md`.

### Removed

- The `training-pipeline` template (superseded on the site gallery by the new
  brand-logo templates).

## [0.1.0] — 2026-06-29

First public release.

### Added

- **31 catalog items**: 20 copyable icons, 8 parametric templates, and 3
  paper-grade examples — covering system block diagrams, neural network
  architectures, training/inference pipelines, and flowcharts.
- **`using-opentikz` skill** — one repo-wide Claude Code skill that discovers
  content via `catalog.json`, edits the chosen item, and verifies it compiles.
  Per-template editing knowledge ships as a structured `edit_contract` inside
  each template's `meta.json`.
- **Reference knowledge** under `reference/` — color palettes, annotations, and
  layout guidance the skill reads at edit time.
- **Tooling** (`tools/`) — `build_catalog.py`, `render_preview.py`,
  `build_site.py`, and `validate.py` (schema + structural rules + standalone
  compile).
- **CI/CD** — PR validation + standalone-compile + preview-freshness checks;
  static site built and deployed to GitHub Pages on push to `main`.
- **Claude Code plugin** packaging via `.claude-plugin/`.

### Licensing

- Code (scripts, build tooling): MIT (`LICENSE-CODE`).
- Graphic content (`.tex` figures): CC0 (`LICENSE-CONTENT`).

[0.1.0]: https://github.com/opentikz/opentikz/releases/tag/v0.1.0
