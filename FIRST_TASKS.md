# First tasks for Claude Code

Hand these to Claude Code in order. Read `CLAUDE.md` and everything in `docs/`
before starting.

## Task 1 — Scaffold the repo

Create the full directory structure from `CLAUDE.md`. Write:
- `meta.schema.json` (JSON Schema for the fields in DESIGN_GUIDE.md)
- `tools/validate.py` — checks each .meta.json against the schema AND that each
  .tex compiles standalone (latexmk).
- `tools/render_preview.py` — compiles a .tex and produces a trimmed .svg
  preview (latexmk + pdf2svg or dvisvgm).
- `tools/build_catalog.py` — walks icons/ templates/ examples/, reads each
  .meta.json, emits catalog.json.
- `LICENSE-CODE` (MIT), `LICENSE-CONTENT` (CC0), `.gitignore` for LaTeX aux.

## Task 2 — First icon end-to-end

Create one icon (`icons/systems/server/`) with `server.tex`, `server.meta.json`,
following DESIGN_GUIDE.md. Run validate + render_preview to prove the toolchain
works. This is the reference pattern for all later icons.

## Task 3 — Color palette skill

Create `skills/color-palettes/` with a color-blind-friendly default palette
defining named colors (otblue, otorange, otteal, otpurple, otgray) plus a
dark-friendly variant. All later content references these.

## Task 4 — First template + companion skill

Build `templates/neural-net/` — a parametric feed-forward neural network
(layer count and neurons-per-layer as top-of-file parameters). Write its
`skill.md` per DESIGN_GUIDE.md. Then TEST the skill: in a fresh prompt, ask
Claude Code to "add a layer" and "recolor to teal" using only the skill, and
verify it edits correctly.

## Task 5 — CI

GitHub Actions workflow: on PR, run validate.py, render previews for changed
items, regenerate catalog.json, and post the rendered previews as a PR comment.

## Then

Proceed through `docs/ROADMAP.md` Step 2 (scale to 30–50 icons, 5 templates,
2 examples). Remember Step 0 (demand validation) should ideally happen before
heavy content work.
