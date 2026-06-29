# Changelog

All notable changes to OpenTikZ are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
