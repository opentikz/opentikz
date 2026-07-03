# Brand icons

Logos of developer tools and platforms commonly cited in paper diagrams
(pipelines that shell out to Git, systems built on Kubernetes, models pulled
from Hugging Face, …). This directory is a **maintainer-approved exception** to
the "no brand logos" non-goal in `CLAUDE.md` / `CONTRIBUTING.md`.

## Provenance and licensing

- Shape data is derived from the [simple-icons](https://simple-icons.org)
  project (CC0 1.0), flattened to absolute `M/L/C/Z` path commands so TikZ's
  `svg.path` library parses it on any pgf version.
- The TikZ **code** in this directory is CC0 1.0 like all OpenTikZ content.
- CC0 covers copyright only: each logo remains a **trademark of its owner**,
  included here solely for identification. Using a mark in a figure does not
  imply endorsement by the trademark holder; make sure your use complies with
  the owner's brand guidelines.

## Conventions (differ from other icons)

- Each icon fills with its **official brand color**, defined once in the
  preamble as `\definecolor{brand<name>}{HTML}{...}` — brand marks keep their
  official color instead of the shared OpenTikZ palette. To render a mark
  monochrome, change that one `\definecolor` value.
- Coordinates are pre-scaled (1 SVG unit = 3pt, ~2.5cm per icon) and
  y-flipped at generation time, because `svg.path` ignores TikZ coordinate
  transforms. Edit the size by scaling the whole `tikzpicture`
  (e.g. `\resizebox` or `[scale=...]` — plain `scale` works since it is
  applied when the path is *used*, not parsed).
