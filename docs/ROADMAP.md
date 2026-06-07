# OpenTikZ — Roadmap (MVP)

## Step 0 — Demand validation (do FIRST, ~1 weekend, zero code)

Build a landing page: 3–4 high-quality architecture-diagram screenshots, a
one-line positioning, and a Star/email-signup CTA. Post to r/LaTeX and TeX
StackExchange. Watch 48-hour response. This falsifies "is this a real need?"
before writing real code. Proceed only if response is positive.

Track real signals, not vanity: copy-button clicks > stars > pageviews.

## Step 1 — Repo skeleton + automation (~1 week)

- Create GitHub org `opentikz`
- Set licenses (MIT code / CC0 content)
- Directory structure (icons/ templates/ skills/, each item = .tex + .meta.json)
- Write `meta.schema.json` validation
- CI: on PR, compile .tex + render SVG preview + post preview back as comment
- `tools/build_catalog.py`, `tools/render_preview.py`, `tools/validate.py`

## Step 2 — Cold-start content (~2–3 weeks)

- 30–50 icons (ML/systems-focused, broadest audience)
- 5 templates (neural net, encoder-decoder, training pipeline, system block
  diagram, flowchart)
- 2 examples (icons+templates combined into paper-grade figures showing real use)

Quality decides everything; an empty repo attracts no one.

## Step 3 — Skills layer (~1–2 weeks, parallel with templates)

Write a companion skill for each of the 5 templates. Test in Claude Code:
issue "add a layer / recolor / change node count / adapt to CVPR" commands and
verify the AI edits correctly. This is the soul of the product — polish until
smooth.

## Step 4 — Website (~1–2 weeks)

GitHub Pages (`opentikz.github.io`, CNAME to a real domain early). Static site +
client-side search (Fuse.js reading catalog.json) + per-item copyable code +
per-item indexable pages (SEO). Show CI-rendered previews.

## Step 5 — Launch + community (ongoing)

Strong README (big gallery + 3-line quick start) and CONTRIBUTING.md. Register
in awesome-tikz. Post to Reddit/TeX SE/Twitter. Provide BibTeX citation. Then
watch real metrics.

## Timeline

Validate 1 wknd → skeleton 1 wk → content 2–3 wk → skills 1–2 wk (parallel) →
website 1–2 wk → launch. ~6–8 weeks to first public release, IF Step 0 passes.

## Open decisions still to confirm

1. Self-hosted domain from day one? (recommended: yes, CNAME early)
2. Exact CC0 vs CC-BY for content (leaning CC0)
3. Browser live-preview (TikZJax) as a later enhancement? (not MVP)

## Future (post-launch exploration)

- **Prompt-to-diagram (natural language → TikZ)** — describe the figure you want
  and get editable TikZ that drops into the library (uses templates + skills under
  the hood). In development for a near-term release.
- **Graph-to-diagram (graph/spec → TikZ)** — give a node–edge specification
  (JSON / DOT / adjacency) and get a laid-out, editable figure. In development.

  NOTE: both are spec/text → TikZ generation, **not** image/SVG → TikZ tracing
  (a declared non-goal).
