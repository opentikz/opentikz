# OpenTikZ — Design Guide

Conventions that keep content consistent and make templates safely
AI-editable. Both human contributors and Claude Code must follow these.

## File format

- Every `.tex` uses `\documentclass{standalone}` and must compile on its own.
- Required preamble packages declared explicitly; list them in `.meta.json`
  under `requires`.
- 2-space indentation. One logical element per line where practical.

## Node naming convention

Nodes must have stable, descriptive names so skills can target them:
- Use semantic names: `(enc)`, `(dec)`, `(attn1)`, `(input)`, not `(a)`, `(b)`.
- For repeated/indexed elements use a clear stem + index: `(layer1)`,
  `(layer2)`, `(node-1)`.
- Connections reference named nodes, never absolute coordinates, so the figure
  stays editable when nodes move.

## Color

- Never hard-code hex inline. Define palettes in `skills/color-palettes/` and
  reference named colors (e.g. `otblue`, `otorange`).
- Provide a light and a dark-friendly variant where feasible.
- Default palette should be color-blind friendly.

## Layout

- Prefer `positioning` library (`right=of`, `below=of`) over absolute coords.
- Keep figures parametric: counts, spacing, and sizes as `\def` or pgfkeys at
  the top of the file so they're easy to change.

## Sizing for venues

Templates should be adaptable to common column widths. Document in each
template's `skill.md` how to switch between single-column and double-column
(e.g. CVPR/NeurIPS/ACL) widths.

## Metadata (.meta.json) required fields

`id`, `name`, `type` (icon|template|skill), `domain` (array), `tags` (array),
`venue` (array, optional), `author`, `license`, `requires` (array), `preview`.
Validated against `meta.schema.json`. Use `tags` for search, `domain` for
browse grouping.

## Companion skill (templates only)

Each template ships `skill.md` documenting three things:
1. Structure — what named parts exist and how they relate.
2. Common edit operations — add/remove node, recolor, change count, resize,
   adapt to a venue width — each with the exact approach.
3. Constraints — must stay standalone-compilable, palette variables to use,
   naming conventions to preserve.
