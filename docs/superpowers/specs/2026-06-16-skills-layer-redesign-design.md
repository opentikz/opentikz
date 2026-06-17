# Design: OpenTikZ skills-layer redesign

Date: 2026-06-16
Status: ready for review

## Problem

The current skills layer has two structural defects:

1. **Per-template companion skills do not scale.** Each template ships a prose
   `skill.md`. In `templates/neural-net/skill.md`, only ~1/3 of the content is
   template-specific (the `\layersizes`/`\layerlabels` equal-length rule, the
   `L<layer>-<neuron>` node-naming contract, the `edges` layer constraint). The
   other ~2/3 is boilerplate copied into every template's skill: palette rules,
   dark-mode switching, the venue-width `\resizebox` recipe, render/validate
   commands, "never inline hex". N templates means N copies of that boilerplate,
   and the audit confirmed these prose files **drift** — a node/style name in a
   `skill.md` that no longer matches its `.tex` will silently break any AI that
   follows it.

2. **The "library-wide skills" split is the wrong abstraction.** `color-palettes`,
   `annotations`, and `layout` are *reference knowledge*, not editing procedures.
   Treating each as a separate "skill" fragments cross-cutting knowledge that
   should be stated once.

The right reframe is **not** "one skill vs N skills". It is:

- separate the **procedure** (how to go from a request to a finished figure) from
  the **per-template data** (each template's edit contract), and
- separate the **communication discipline** (how to resolve ambiguity with the
  user) from **domain knowledge** (how to edit TikZ safely).

## Audience (decided)

**Downstream researchers (end users).** A researcher vendors/clones OpenTikZ into
their own LaTeX paper repo and uses Claude Code there. Consequences that shape
this design:

- `catalog.json` and every `meta.json` are committed, so they ship with the repo
  — discovery-by-catalog and per-template contracts are available downstream.
- The skill must **not** assume the repo's Python tooling runs downstream
  (`validate.py`/`render_preview.py` need TeX + ghostscript + Python). The target
  user *does* have LaTeX, so the skill's verification step is "compile the
  standalone `.tex` with the user's own `latexmk`/`pdflatex`". SVG/preview
  regeneration stays a **contributor-side** step, out of the end-user skill.
- There is no plugin packaging, so auto-discovery via `.claude/skills/` does not
  apply downstream. The realistic entry point is a single well-known file the
  user points Claude at — which favours one consolidated skill over N scattered
  ones.

## Decisions (locked)

- **Architecture A**: one procedural skill + structured per-template contracts.
- **Contract location**: a new `edit_contract` object inside each
  `template.meta.json`.
- **`skills/` → `reference/` restructure**: accepted (not the minimal-churn
  option).
- **Machine-check scope**: `validate.py` checks only **existence** —
  `edit_contract.parameters[].name` and `edit_contract.styles[]` must appear in
  the sibling `.tex`. `operations`/`invariants` remain prose, not machine-checked.
- **Contracts are templates-only.** Icons and examples get no `edit_contract`.

## Design

### 1. The single skill: `skills/using-opentikz/SKILL.md`

One procedural skill that replaces all five per-template `skill.md` files. Its
sections:

**1a. Communication discipline (first section — the priority).**
An ambiguity classifier, *not* "always ask":

- **Material ambiguity → ask, or offer two concrete alternatives.** Trigger when
  the answer changes the figure's structure/identity, is hard to reverse, or you
  would otherwise be guessing between genuinely different intents.
  - "draw a transformer" → encoder-only / decoder-only / encoder-decoder? → ask
    (offer the 3 concrete options).
  - "add attention" → self- or cross-attention, and where? → ask.
  - "highlight the new part" → which part is new? → ask.
  - *Offer two alternatives* is reserved for aesthetic/layout forks where seeing
    beats describing (two colour schemes, two layouts) — not for continuous
    quantities.
- **Safe-default ambiguity → proceed, state the assumption in one line, keep it
  cheap to reverse.**
  - palette: default light Okabe-Ito unless "dark" is mentioned.
  - width: default standalone (no `\resizebox`) unless a venue/column width is named.
  - spacing/size, or an unspecified-but-conventional count: use template defaults
    (e.g. a 4-layer net `4,6,6,2`).
- **Anti-interrogation guardrail**: at most ~2–3 up-front questions, batched;
  everything else is assume-and-state. Delivery always ends with a one-line
  "assumptions: X, Y, Z — say the word to change any".

**1b. The workflow.**
1. Understand the request; classify ambiguity per 1a.
2. **Discover**: read `catalog.json`; match the request to icons/templates/
   examples; if several fit, present the candidates.
3. **Select & confirm**: confirm the chosen base plus the material parameters.
4. **Edit**: read the chosen item's `.tex` and (for templates) its
   `edit_contract`; apply only contract-sanctioned operations; honour the
   invariants; colours via palette names only.
5. **Verify**: compile the edited standalone `.tex` with the user's LaTeX
   (`latexmk -pdf` / `pdflatex`); fix failures before returning. No SVG/preview
   regeneration.
6. **Deliver**: the edited `.tex` plus the one-line assumptions summary.

**1c. Hard constraints** (carried from CLAUDE.md): standalone class, palette-only
colours, node-naming convention, keep figures parametric.

**1d. Reference pointers**: links to `reference/color-palettes/`,
`reference/annotations/`, `reference/layout/`, and `docs/DESIGN_GUIDE.md`.

### 2. `edit_contract` in `template.meta.json`

Structured form of each template's genuinely-unique knowledge. Example
(neural-net):

```json
"edit_contract": {
  "parameters": [
    {"name": "\\layersizes",  "type": "list<int>", "meaning": "neuron count per layer; length = number of layers", "default": "{4,6,6,2}"},
    {"name": "\\layerlabels", "type": "list<str>", "meaning": "one label per layer", "invariant": "same length as \\layersizes"},
    {"name": "\\layersep",    "type": "length-cm",  "meaning": "horizontal gap between layers"},
    {"name": "\\neuronsep",   "type": "length-cm",  "meaning": "vertical gap between neurons"},
    {"name": "\\neuronsize",  "type": "length-cm",  "meaning": "neuron diameter"}
  ],
  "node_naming": "L<layer>-<neuron>, 1-based, e.g. L2-3",
  "styles": ["neuron", "edge", "layerlabel"],
  "operations": [
    {"id": "add-layer",    "summary": "append a count to \\layersizes AND a label to \\layerlabels (keep equal length)"},
    {"id": "remove-layer", "summary": "delete one entry from each list at the same position"},
    {"id": "resize-layer", "summary": "edit one entry in \\layersizes only"},
    {"id": "recolor",      "summary": "change the palette name in the neuron/edge/layerlabel style; never a hex"}
  ],
  "invariants": [
    "\\layersizes and \\layerlabels stay equal length",
    "preserve the L<layer>-<neuron> node-naming scheme",
    "do not remove \\pgfdeclarelayer{edges} / \\pgfsetlayers"
  ]
}
```

- **Machine-checked (existence only)**: every `parameters[].name` must appear as a
  `\def<name>` in the sibling `.tex`; every `styles[]` entry must appear as
  `<style>/.style=` in the `.tex`. This is the anti-drift guard that kills the
  audit's "stale skill.md reference" class.
- **Prose (not machine-checked)**: `operations`, `invariants`, and the `meaning`/
  `type`/`default`/`invariant` strings on parameters. The skill obeys them; the
  validator does not parse them.

### 3. Restructure & deletions

- **Delete** the five `templates/*/skill.md`. Structured content moves into the
  template's `edit_contract`; shared prose (venue widths, dark mode, render
  command) is stated once in `skills/using-opentikz/SKILL.md`.
- **Move** `skills/color-palettes/`, `skills/annotations/`, `skills/layout/` to
  `reference/<name>/`, renaming each `skill.md` to a non-"skill" name
  (`color-palettes.md`, `annotations.md`, `layout.md`). Their `.tex`/`.svg`
  cheatsheets and swatches stay as visual references.
- **New** `skills/using-opentikz/SKILL.md` is the only thing under `skills/`.
- The "three-layer content model" in CLAUDE.md is redefined: layer 3 changes from
  "per-template companion skills + cross-cutting skills" to "one repo-wide skill
  (`using-opentikz`) + reference material under `reference/`".

### 4. Tooling & schema updates

- **`meta.schema.json`**: add the `edit_contract` object (optional; templates
  only). Define sub-schemas for `parameters[]` (`name` required; `type`/`meaning`/
  `default`/`invariant` optional strings), `node_naming` (string), `styles[]`
  (string array), `operations[]` (`id`+`summary`), `invariants[]` (string array).
- **`validate.py`**: for any item with `edit_contract`, assert it is a template,
  and cross-check parameter/style **existence** against the sibling `.tex`
  (regex: `\def\<name>` and `<style>/.style`). Fail on missing entries.
- **No change** to `build_catalog.py`: it does `entry = dict(meta)`, copying every
  meta field verbatim, so `edit_contract` flows into `catalog.json` automatically
  and the site/skill can read it from the catalog.

### 5. Website (`build_site.py`) updates

The site is coupled to the old model and must follow:

- **Item page** (`item_page`): remove the "Companion skill (skill.md)" section and
  its copy button. For templates, optionally render the `edit_contract` (parameters
  + operations) as a compact, read-only "how to edit" block, and link to the one
  `using-opentikz` skill on GitHub.
- **Skills page** (`skills_page`): rewrite from "one companion skill per template +
  library-wide skills" to "one repo-wide `using-opentikz` skill" plus a
  "Reference" section pointing at `reference/` (palette/annotations/layout). Update
  the GitHub blob URLs from `skills/...` to `reference/...`.
- **Marketing copy**: replace every "every template ships a companion `skill.md`"
  / "companion skills" / "library-wide skills" string (home lede, how-it-works
  steps, skills-page intro) with the new one-skill framing.
- Remove the now-dead `skill_md` file-loading per template in `build()`; drop the
  `template_skills` index or repurpose it for the `edit_contract` display.

### 6. Documentation updates

- **CLAUDE.md**: rewrite the three-layer model and the "How you should work"
  instruction "when writing a template, also write its `skill.md`" → "add an
  `edit_contract` to its `meta.json`". Update the repo-structure tree
  (`skills/` → `reference/` + `skills/using-opentikz/`). Update any `skills/`
  palette path.
- **CONTRIBUTING.md**: new template workflow (write `edit_contract`, not
  `skill.md`); updated `reference/` paths.
- **DESIGN_GUIDE.md**: document the `edit_contract` convention; add the `example`
  type and the missing optional meta fields the audit flagged; update palette path
  to `reference/color-palettes/`.
- **Cross-reference sweep**: update the `skills/color-palettes/skill.md` path
  referenced by all icon/template/example `.tex` header comments and by
  skills-demos to the new `reference/...` path. (Comments only — no compile
  impact, but they should not point at moved files.)

## Out of scope

- Adding `edit_contract` to icons or examples.
- Machine-checking `operations`/`invariants` semantics.
- The separate audit findings (CI preview-drift, the `build_site.py` `<script>`
  XSS, broader `validate.py` hard-rule enforcement). Tracked separately; this spec
  touches `validate.py`/`build_site.py` only for the contract/skill changes.
- A `clarifying-intent` skill split (Approach B). Start with the communication
  discipline as a section inside `using-opentikz`; split out later only if it
  needs reuse or the skill grows unfocused (YAGNI).

## Affected files (checklist)

New:
- `skills/using-opentikz/SKILL.md`

Moved (`skills/` → `reference/`, `skill.md` renamed):
- `color-palettes/`, `annotations/`, `layout/` (`.md` + `.tex` + `.svg` each)

Deleted:
- `templates/{encoder-decoder,flowchart,neural-net,system-block-diagram,training-pipeline}/skill.md`

Edited:
- `templates/*/template.meta.json` (add `edit_contract`)
- `meta.schema.json`, `tools/validate.py`, `tools/build_site.py`
- `CLAUDE.md`, `CONTRIBUTING.md`, `docs/DESIGN_GUIDE.md`
- `.tex` header comments in `icons/**`, `templates/**`, `examples/**`,
  `skills-demos/` (palette path → `reference/`)
- regenerate `catalog.json` via `build_catalog.py`

## Verification

- `python3 tools/build_catalog.py --check` clean after regeneration.
- `python3 tools/validate.py --strict` passes 28/28, and the new
  `edit_contract` existence check passes for all five templates (and would fail if
  a parameter/style is renamed in a `.tex` without updating the contract — add a
  deliberate-mismatch test).
- `python3 tools/build_site.py` builds with no references to deleted `skill.md`
  files and no remaining "companion skill" copy.
- Spot-check: follow `using-opentikz/SKILL.md` end-to-end on one real request
  (e.g. "add a hidden layer to the neural net and make it teal") and confirm the
  edited `.tex` compiles.
