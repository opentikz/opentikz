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
  - **Step 0 — locate the read-only library and set the output target.** Resolve
    the library root (`OTROOT`) by this rule:
    1. If `${CLAUDE_PLUGIN_ROOT}` is set (plugin install) → `OTROOT = ${CLAUDE_PLUGIN_ROOT}`.
    2. Otherwise (clone / other agent) → `OTROOT` = the OpenTikZ repo root, i.e.
       the directory two levels above this `SKILL.md` (`skills/using-opentikz/SKILL.md`
       → `../../`).

    Output target is always the user's current project (CWD), never `OTROOT`.
  - Discover via `${OTROOT}/catalog.json` → **copy the chosen `.tex` from
    `${OTROOT}/...` into the user's project** → edit the copy (read `edit_contract`
    from the library; keep every invariant; preserve `node_naming`; colours via
    palette names only) → **compile in the user's project**.
  - Handle "edit a figure already in my project" (the copy is already local; still
    read `edit_contract` from `${OTROOT}`) and 3b (no local `OTROOT`: fetch raw
    `.tex`/`catalog.json` from the GitHub repo, write the `.tex` into the project,
    then edit).
- **Mode B (contribute back):** library == CWD; edit in place; run
  `render_preview.py` / `build_catalog.py` / `validate.py`. This is the current §6
  content, relabelled as a mode.
- **Resolved (was open):** `${CLAUDE_PLUGIN_ROOT}` is available inside SKILL.md
  content and points to the install cache (`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`).
  Installed plugins are **copied** to cache and **cannot reference files outside
  the plugin dir** (so `../catalog.json` fails) — which is exactly why the full
  library must be bundled at the plugin root. The fallback (rule 2 above) covers
  every non-plugin agent. Confirm `${CLAUDE_PLUGIN_ROOT}` resolves against a real
  install during the packaging task.

### ③ Website: repurpose `/skills/` into a "How to use" tutorial

- **Install (three entries — adapted to a library-backed skill).** Note: the
  frontend-slides "copy the skill into `~/.claude/skills/`" path does **not** work
  for OpenTikZ — our skill needs the whole library beside it, and a plugin in cache
  cannot read files outside its dir. So the entries are:
  1. **Claude Code plugin (recommended)** — `/plugin marketplace add <https-url>`
     then `/plugin install opentikz@opentikz`; use the HTTPS URL; the two commands
     are separate messages. Invoked as `/opentikz:using-opentikz`. The plugin
     bundles the full library and resolves it via `${CLAUDE_PLUGIN_ROOT}`.
  2. **Clone & point your agent at it** (Claude Code or any agent) — `git clone`
     the repo, then tell the agent to use `skills/using-opentikz/SKILL.md`. The
     library is the repo root, resolved relative to `SKILL.md` (covers scenarios
     3a/4).
  3. **Remote, no clone** (agents that can read GitHub) — point the agent at the
     repo URL; it starts from `SKILL.md` and fetches only the files it needs
     (scenario 3b).
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

- **Repo owner/URL** in the marketplace command must be the real public repo URL
  (HTTPS form) before the site copy is finalised. *(Still open — needs the owner.)*
- **`${CLAUDE_PLUGIN_ROOT}` resolution** — mechanism is confirmed by the docs
  (below); still verify it resolves correctly against one real install during the
  packaging task.
- **Non-plugin library resolution** relies on the agent locating the repo root two
  levels above `SKILL.md`; verify the clone-and-point path works end to end with at
  least one agent.

## Reference (Claude Code plugin format, verified 2026-06-28)

- Marketplace schema: https://code.claude.com/docs/en/plugin-marketplaces.md#marketplace-schema
  — `.claude-plugin/marketplace.json` with `name`, `owner{name,email?}`, `plugins[]`;
  a plugin entry may use `source: "./"` to point at the repo root.
- Plugin manifest: https://code.claude.com/docs/en/plugins-reference.md#plugin-manifest-schema
  — `.claude-plugin/plugin.json`, `name` required (kebab-case), `version`/`description`/`author` optional.
- Skills in plugins: https://code.claude.com/docs/en/plugins-reference.md#skills
  — `skills/<name>/SKILL.md`; invoked `/<plugin>:<skill>`.
- Env vars / file resolution: https://code.claude.com/docs/en/plugins-reference.md#environment-variables
  — `${CLAUDE_PLUGIN_ROOT}` usable in SKILL.md content; plugins are copied to cache
  and cannot reference files outside the plugin dir.
