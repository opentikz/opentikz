# Usage paths + plugin packaging — design

**Date:** 2026-06-28
**Status:** Approved (brainstorm), pending implementation plan

## Problem

The website never answers the one question a visitor actually has: *"how do I
start using this?"* Today the home page funnels everyone through a single
**Get started → /skills/** button into a conceptual page about the AI skill, and
the concrete mechanics of getting OpenTikZ into an agent's hands are missing.
Two genuinely different audiences are conflated, and the AI path's setup step is
undefined:

- **Manual users** ("just give me a `server` icon / a neural-net figure to paste")
  are served only inside `/browse/`; the home page never acknowledges this path.
- **AI-assisted users** ("let my agent find a template, edit it, verify it
  compiles") have **no documented install step** — the README says "Clone
  OpenTikZ into your project," which is vague and does not match how a Claude Code
  skill is actually distributed.

We will fix this by (a) packaging OpenTikZ as a real Claude Code plugin so the
install commands actually run, (b) rewriting `SKILL.md` to work when installed
(library lives elsewhere, output lands in the user's project), and (c)
restructuring the website so the three usage scenarios and three install entries
are explained plainly.

## Goals

- A visitor can read the site and **know exactly how to start**, for their case.
- `/plugin marketplace add <https-url>` then `/plugin install opentikz@opentikz`
  **actually works** and exposes `/opentikz:using-opentikz`.
- The skill **functions when installed** — it finds the read-only library and
  writes the edited `.tex` into the user's own paper project.
- The manual copy-paste path is a **first-class** option on the site, not hidden.

## Non-goals (YAGNI)

- A curated "minimal example" subset of the library — we bundle **all** figures.
- Sharding/lazy-loading `catalog.json` — note it as a future lever only.
- Excluding `.svg` previews from the plugin — defer until weight actually matters.
- Implementing prompt-to-diagram / graph-to-diagram (scenario C) — stays roadmap.

## Key decision: bundle the full library, the growth lever is previews

Measured weights (2026-06-28):

| Agent-facing (functional) | Size |
| --- | --- |
| `catalog.json` | 48 KB |
| 31 figures' `.tex` | 79 KB |
| `.meta.json` (incl. `edit_contract`) | 36 KB |
| `reference/` | 14 KB |
| **Total** | **≈ 177 KB** |

| Website-only (agent never reads) | Size |
| --- | --- |
| `.svg` previews × 40 | **623 KB** |
| `site/` build output | 1.0 MB |

The agent discovers via `catalog.json` (text: names, tags, `edit_contract`) and
edits `.tex`; it never needs the SVGs. Functional content grows at ~5–6 KB per
figure, so even 500 figures is ~3 MB of text — trivial for a one-time install.
Therefore: **bundle every figure; never curate a subset.** If the install ever
gets heavy, the lever is "stop shipping `.svg` previews to the agent" (previews
are a website concern), and eventually shard `catalog.json` — both deferred.

## Scenario model (drives the SKILL.md rewrite)

Three variables determine the skill's behaviour: **where the library lives**,
**where output goes**, and **what the user wants done** (T1 fetch as-is, T2 edit
existing, T3 compose/new-from-description, T4 contribute back).

Concrete scenarios:

1. **Claude Code + plugin, in my own paper project** — main case. Library
   read-only at plugin root; output into the paper project.
2. **Claude Code + plugin, fetch a figure as-is** (T1) — copy in, no edit,
   compile to confirm.
3. **Other agent (Codex/Gemini/Cursor) pointed at the GitHub repo, in my paper
   project** — same as 1, library located differently. Sub-cases: **3a** a local
   clone exists (copy the file); **3b** only remote GitHub access (fetch raw
   content → write into the project).
4. **Manual skill install at `~/.claude/skills/opentikz`, in my paper project** —
   like 1; library at that directory.
5. **Contributor working inside the OpenTikZ repo** (T4) — edit in place + run
   tooling. The existing `SKILL.md` §6 path.
6. **(Non-skill) pure website copy-paste** — no agent involved; **out of scope**
   for `SKILL.md`, exists only as website scenario A.

These collapse into **two operating modes**:

- **Mode A — produce a figure into the user's own project** (covers 1/2/3/4).
  Library is read-only and elsewhere; **output goes to the CWD**; default is
  **copy-then-edit** (never mutate the read-only library; leave a git-trackable
  `.tex` in the user's project). Tasks T1/T2/T3 all live here, including "edit a
  figure already copied into my project" and 3b "fetch raw content then write."
- **Mode B — contribute back to the library** (scenario 5). Library == CWD;
  **edit in place** + regenerate preview/catalog + validate.

## Design

### ① Plugin packaging skeleton

- Add `.claude-plugin/marketplace.json` — marketplace name `opentikz`, listing one
  plugin whose source is the repo root.
- Add `.claude-plugin/plugin.json` — plugin name `opentikz`, with `version` and
  `description`.
- The existing `skills/using-opentikz/` becomes the plugin's skill, namespaced as
  `/opentikz:using-opentikz`.
- The plugin source is the **whole repo root** (bundling option a) — the full
  functional library ships with the skill. Previews/`site/` come along for now;
  that's acceptable at current weight.
- **Acceptance:** on a clean machine,
  `/plugin marketplace add https://github.com/<owner>/opentikz` then
  `/plugin install opentikz@opentikz` installs, and `/opentikz:using-opentikz`
  triggers the skill.

### ② Rewrite `SKILL.md` around the two modes

- Add an opening **"first decide: Mode A or Mode B"** classifier.
- **Mode A (default):**
  - **Step 0 — locate the read-only library and set the output target.** Library
    is the OpenTikZ install: the plugin root when plugin-installed,
    `~/.claude/skills/opentikz` when manually installed, or the repo the agent was
    pointed at (3a local / 3b remote). Output target is the user's current project
    (CWD).
  - Discover via `catalog.json` in the library → **copy the chosen `.tex` into the
    user's project** → edit the copy (read `edit_contract` from the library; keep
    every invariant; preserve `node_naming`; colours via palette names only) →
    **compile in the user's project**.
  - Handle "edit a figure already in my project" (the copy is already local; still
    read `edit_contract` from the library) and 3b (fetch raw `.tex` content from
    GitHub, write it into the project, then edit).
- **Mode B (contribute back):** library == CWD; edit in place; run
  `render_preview.py` / `build_catalog.py` / `validate.py`. This is the current §6
  content, relabelled as a mode.
- ⚙️ **Open implementation detail (pin down in the plan):** the exact mechanism by
  which the skill resolves the plugin root when plugin-installed (e.g.
  `${CLAUDE_PLUGIN_ROOT}` vs. paths relative to `SKILL.md`). Verify against a real
  install before finalising the wording.

### ③ Website: repurpose `/skills/` into a "How to use" tutorial

- **Install (three entries, mirroring the frontend-slides layout):**
  1. **Claude Code marketplace source** — `/plugin marketplace add <https-url>`
     then `/plugin install opentikz@opentikz`; use the HTTPS URL; the two commands
     are separate messages.
  2. **Manual install** — copy/clone into `~/.claude/skills/opentikz`; then
     `/using-opentikz` (standalone skills are not namespaced).
  3. **Other agents** (Codex/Gemini/Cursor/…) — point the agent at the GitHub repo
     or `SKILL.md`; it starts from `SKILL.md` and loads only the support files it
     needs.
- **Three scenarios:**
  - **A — manual copy** (no AI): browse → **Copy `.tex`** → paste. Given a
    first-class place.
  - **B — AI editing** (primary): install → `/opentikz:using-opentikz` → describe
    the change in plain language (with one real prompt example).
  - **C — generate from scratch** (roadmap): pointer to prompt/graph-to-diagram.
- Keep the lower half: **why it edits accurately** (`edit_contract`), the
  cross-cutting `reference/` material, and the demos carousel.
- Rename the nav item `Skills` → **`How to use`**.
- **Home page:** add a concise "three steps to start / or just copy" entry below
  the hero; point the `Get started` CTA at this page.

### ④ Sync README + docs

- Replace the README **Quick start** with the marketplace install + the three
  scenarios, matching the site (today's "Clone … into your project" is wrong/stale).
- Add `.claude-plugin/` to the repo-structure listing in `CLAUDE.md`.

## Build order (rough)

1. Plugin skeleton (`.claude-plugin/*`) + verify a real install/trigger.
2. Rewrite `SKILL.md` for the two modes; resolve the plugin-root mechanism against
   the real install.
3. Repurpose `/skills/` in `tools/build_site.py` (install entries + 3 scenarios +
   nav rename) and add the home-page entry; rebuild the site.
4. Sync README + `CLAUDE.md`.

## Risks / things to verify

- **Plugin-root resolution** for an installed skill must be confirmed empirically;
  the SKILL.md wording depends on it.
- **Manual-install command surface** (`/using-opentikz` vs `/opentikz:using-opentikz`)
  differs between plugin and standalone installs — the docs must state both
  correctly, exactly as the frontend-slides reference does.
- **Repo owner/URL** in the marketplace command must be the real public repo URL
  (HTTPS form) before the site copy is finalised.
