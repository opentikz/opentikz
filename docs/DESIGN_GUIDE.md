# OpenTikZ — Design Guide

Conventions that keep content consistent and make templates safely
AI-editable. Both human contributors and Claude Code must follow these.

The single skill that edits this content is `skills/using-opentikz/`; it reads
each template's `edit_contract` (below) and the `reference/` material.

## File format

- Every `.tex` uses `\documentclass{standalone}` and must compile on its own.
- Required preamble packages declared explicitly; list them in `.meta.json`
  under `requires`.
- 2-space indentation. One logical element per line where practical.

## Node naming convention

Nodes must have stable, descriptive names so the skill can target them:
- Use semantic names: `(enc)`, `(dec)`, `(attn1)`, `(input)`, not `(a)`, `(b)`.
- For repeated/indexed elements use a clear stem + index: `(layer1)`,
  `(layer2)`, `(node-1)`.
- Connections reference named nodes, never absolute coordinates, so the figure
  stays editable when nodes move.

## Color

- Never hard-code hex inline. Define palettes in `reference/color-palettes/` and
  reference named colors (e.g. `otblue`, `otorange`).
- Provide a light and a dark-friendly variant where feasible.
- Default palette should be color-blind friendly.

## Layout

- Prefer `positioning` library (`right=of`, `below=of`) over absolute coords.
- Keep figures parametric: counts, spacing, and sizes as `\def` or pgfkeys at
  the top of the file so they're easy to change.

## Sizing for venues

Templates should be adaptable to common column widths. The `using-opentikz` skill
documents the `\resizebox` recipe for switching between single-column and
double-column (e.g. CVPR/NeurIPS/ACL) widths once, for all templates.

## Metadata (.meta.json) required fields

`id`, `name`, `type` (icon|template|example), `domain` (array), `tags` (array),
`venue` (array, optional), `author`, `license`, `requires` (array), `preview`.
Optional: `description`, `featured`, `composed_of`, and — templates only —
`edit_contract` (below). Validated against `meta.schema.json`. Use `tags` for
search, `domain` for browse grouping.

## Edit contract (templates only)

Each template's `meta.json` carries an `edit_contract` — the structured,
machine-readable knowledge the `using-opentikz` skill consumes (it replaces the
old per-template `skill.md`). It has five parts:

1. `parameters` — the `\def` macros that drive the figure: each `name` (with
   backslash), an informal `type`, a `meaning`, and optional `default`/`invariant`.
2. `node_naming` — the scheme skills target, e.g. `L<layer>-<neuron>, 1-based`.
3. `styles` — the tikz style names (each appears as `<name>/.style=` in the `.tex`).
4. `operations` — safe, contract-sanctioned edits (`id` + `summary`); prose.
5. `invariants` — rules an edit must never break; prose.

`validate.py` cross-checks **existence**: every `parameters[].name` must appear as
a `\def` and every `styles[]` entry as a `/.style` in the sibling `.tex`, so the
contract can never drift from the source. `operations`/`invariants` are prose and
not machine-checked. See `templates/neural-net/template.meta.json` for a worked
example.
