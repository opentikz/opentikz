# Usage Paths + Plugin Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make OpenTikZ installable as a real Claude Code plugin and make the website explain plainly how to use it, for all three user scenarios.

**Architecture:** Add a `.claude-plugin/` marketplace+plugin skeleton so the whole repo installs as one plugin (the skill finds the bundled library via `${CLAUDE_PLUGIN_ROOT}`). Rewrite `SKILL.md` around two operating modes — Mode A (produce a figure into the user's own project, copy-then-edit) and Mode B (contribute back to the repo). Repurpose the site's `/skills/` page into a "How to use" tutorial (3 install entries × 3 scenarios), add a home-page entry, and sync the README + `CLAUDE.md`.

**Tech Stack:** Claude Code plugin manifests (JSON), Markdown (SKILL.md, docs), Python 3 stdlib static-site generator (`tools/build_site.py`), `tools/validate.py` / `tools/build_catalog.py` for content validation.

## Global Constraints

- Repo / marketplace identity: GitHub repo is `https://github.com/opentikz/opentikz`; marketplace name `opentikz`; plugin name `opentikz`; skill name stays `using-opentikz` → command `/opentikz:using-opentikz`. Copy these exact strings verbatim.
- Bundling: the plugin ships the **full** library; never curate a subset. Previews/`site/` may ride along.
- Plugin file resolution: installed plugins are copied to cache and **cannot read files outside the plugin dir**; the skill must reference bundled files via `${CLAUDE_PLUGIN_ROOT}` (plugin install) or relative to `SKILL.md` (non-plugin).
- No new runtime deps; `tools/*.py` stay stdlib-only. `catalog.json` is auto-generated — never hand-edit.
- Colors only via the five palette names; `.tex` stays `\documentclass{standalone}` (unchanged content, but don't break these).
- This project has **no pytest harness**; "tests" are: `tools/validate.py` passes, `tools/build_site.py` runs clean, `grep` assertions on generated HTML, and one real local plugin install.

---

### Task 1: Plugin packaging skeleton (`.claude-plugin/`)

**Files:**
- Create: `.claude-plugin/marketplace.json`
- Create: `.claude-plugin/plugin.json`

**Interfaces:**
- Produces: an installable plugin named `opentikz` from marketplace `opentikz`, exposing skill `using-opentikz` as `/opentikz:using-opentikz`. The plugin root contains `catalog.json`, `templates/`, `icons/`, `examples/`, `reference/`, `skills/using-opentikz/SKILL.md`.

- [ ] **Step 1: Write the marketplace manifest**

Create `.claude-plugin/marketplace.json`:

```json
{
  "name": "opentikz",
  "owner": { "name": "OpenTikZ contributors" },
  "description": "TikZ resources for academic conceptual diagrams.",
  "plugins": [
    {
      "name": "opentikz",
      "source": "./",
      "description": "Find, edit, and verify academic TikZ figures (icons, templates, examples) with the using-opentikz skill."
    }
  ]
}
```

- [ ] **Step 2: Write the plugin manifest**

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "opentikz",
  "version": "0.1.0",
  "description": "Find, edit, and verify academic TikZ figures (icons, templates, examples) with the using-opentikz skill.",
  "author": { "name": "OpenTikZ contributors" },
  "homepage": "https://opentikz.org",
  "repository": "https://github.com/opentikz/opentikz",
  "license": "MIT"
}
```

- [ ] **Step 3: Verify content tooling ignores the new dir**

Run: `python3 tools/validate.py`
Expected: PASS (the schema walk only touches `*.meta.json`; `.claude-plugin/*.json` are ignored). If it errors on `.claude-plugin/`, add that dir to the validator's ignore list and re-run.

Run: `python3 tools/build_catalog.py && git diff --stat catalog.json`
Expected: no change to `catalog.json` (the new dir contributes no catalog items).

- [ ] **Step 4: Verify a real local install end to end**

Run (separate Claude Code messages, or the CLI shown):
```bash
claude plugin marketplace add ./
claude plugin install opentikz@opentikz
```
Expected: marketplace `opentikz` added; plugin `opentikz` installs without error; `/opentikz:using-opentikz` appears as an available command. If the CLI is unavailable in this environment, record this step as "verify manually" and confirm the JSON validates with: `python3 -c "import json,sys; [json.load(open(p)) for p in ('.claude-plugin/marketplace.json','.claude-plugin/plugin.json')]; print('json ok')"`
Expected: `json ok`

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/marketplace.json .claude-plugin/plugin.json
git commit -m "Plugin: add marketplace + plugin manifest (opentikz@opentikz)"
```

---

### Task 2: Rewrite `SKILL.md` around Mode A / Mode B

**Files:**
- Modify: `skills/using-opentikz/SKILL.md`

**Interfaces:**
- Consumes: `${CLAUDE_PLUGIN_ROOT}` (set on plugin install) or the repo root two levels above `SKILL.md` (non-plugin).
- Produces: a skill whose Mode A copies a chosen `.tex` from the library into the user's CWD and edits the copy there; Mode B edits the repo in place + runs tooling.

- [ ] **Step 1: Add the mode classifier + library-resolution block after the intro**

Insert a new section immediately before the current `## 1. Communicate precisely` heading:

```markdown
## 0. First: which mode are you in, and where is the library?

**Pick the mode:**
- **Mode A — produce a figure for the user's own project** (the default). The
  OpenTikZ library is read-only and lives elsewhere; the user is working in their
  own paper/LaTeX project. You will *copy* a figure out of the library and edit the
  copy in their project. Never modify the library.
- **Mode B — contribute back to the OpenTikZ repo itself.** The user is editing the
  library: their working directory *is* the repo. Edit in place and run the repo
  tooling (see §6).

**Locate the library root (`OTROOT`) for Mode A:**
1. If the environment variable `${CLAUDE_PLUGIN_ROOT}` is set, you were installed as
   a Claude Code plugin: `OTROOT = ${CLAUDE_PLUGIN_ROOT}`.
2. Otherwise (cloned repo / another agent), `OTROOT` is the OpenTikZ repo root — the
   directory two levels above this `SKILL.md` (`skills/using-opentikz/SKILL.md` →
   `../../`).
3. If you can only read the repo remotely (e.g. over GitHub, no local clone), treat
   the GitHub repo as `OTROOT` and fetch raw file contents on demand.

Confirm `OTROOT` once (e.g. list `OTROOT`/catalog.json) before relying on it. The
**output target is always the user's current working directory**, never `OTROOT`.
```

- [ ] **Step 2: Rewrite Workflow steps 4–5 (copy-then-edit, compile in CWD)**

In `## 2. Workflow`, replace the current step **4. Edit** and step **5. Verify** with:

```markdown
4. **Copy, then edit (Mode A) / edit in place (Mode B).**
   - **Mode A:** copy the chosen item's `.tex` from `OTROOT` into the user's project
     (a sensible path like `figures/<name>.tex`); tell the user where you put it.
     Edit *that copy*, never the file under `OTROOT`. If the figure is already in
     the user's project, edit it there. For a **template**, read its `edit_contract`
     from `OTROOT`'s `catalog.json` (or the item's `meta.json`) and: edit only the
     contract's `parameters`; follow its `operations` as the recipe; keep every
     `invariant`; preserve the `node_naming` scheme; colours via palette names only.
     For an **icon/example** (no contract), edit under the same hard rules.
   - **Mode B:** edit the item in place inside the repo, under the same rules.
5. **Verify by compiling — in the user's project (Mode A).** Run the user's LaTeX on
   the copied/edited file (`latexmk -pdf <file>.tex`, or `pdflatex`). Fix failures
   before returning — never hand back a figure you didn't compile. (Regenerating
   `.svg` previews and `catalog.json` is a *Mode B / contributor* task — skip it
   when producing a figure for a user.)
```

- [ ] **Step 3: Relabel §6 as the Mode B procedure**

Change the `## 6. Contributing back (only when the user is editing the repo itself)`
heading to:

```markdown
## 6. Mode B procedure — contributing back (editing the repo itself)
```

Leave its body (the `render_preview.py` / `build_catalog.py` / `validate.py` steps)
unchanged.

- [ ] **Step 4: Verify the skill still validates and reads coherently**

Run: `python3 tools/validate.py`
Expected: PASS (validate.py does not parse SKILL.md prose, but confirm no incidental breakage).

Run: `grep -n "CLAUDE_PLUGIN_ROOT\|OTROOT\|Mode A\|Mode B" skills/using-opentikz/SKILL.md`
Expected: matches present in §0, §2, §6 — confirming the three edits landed.

- [ ] **Step 5: Commit**

```bash
git add skills/using-opentikz/SKILL.md
git commit -m "Skill: two modes (A produce-into-project / B contribute) + OTROOT resolution"
```

---

### Task 3: Repurpose `/skills/` into a "How to use" tutorial

**Files:**
- Modify: `tools/build_site.py` — `navbar()` (rename label), `skills_page()` (install + scenarios sections)

**Interfaces:**
- Consumes: `REPO_URL` (`https://github.com/opentikz/opentikz`), the existing `demos_carousel()` output, the existing `head()`/`navbar()`/`footer()` helpers.
- Produces: a `/skills/` page that leads with install entries + three scenarios, then keeps the existing "why accurate" / reference / demos content. Nav label reads "How to use".

- [ ] **Step 1: Rename the nav label "Skills" → "How to use"**

In `navbar()`, change the skills link text (keep the class and `data-nav` so CSS/JS are untouched):

```python
      <a class="nav-skills{skills_active}" href="{skills}" data-nav="skills">How to use</a>
```

- [ ] **Step 2: Add the install + scenarios sections at the top of `skills_page()`**

In `skills_page()`, immediately after the existing `<section class="skills-intro">…</section>` block and before `{carousel}`, insert:

```python
  <section class="skills-install">
    <h2>Install</h2>
    <div class="install-cards">
      <article class="install-card install-rec">
        <span class="install-tag">recommended · Claude Code</span>
        <h3>Claude Code plugin</h3>
        <p>Run these as <strong>two separate</strong> Claude Code messages:</p>
        <pre><code>/plugin marketplace add https://github.com/opentikz/opentikz</code></pre>
        <pre><code>/plugin install opentikz@opentikz</code></pre>
        <p>Then use it by typing <code>/opentikz:using-opentikz</code>. The plugin
           bundles the whole library, so the skill can find every icon and template.</p>
      </article>
      <article class="install-card">
        <span class="install-tag">any agent</span>
        <h3>Clone &amp; point your agent at it</h3>
        <pre><code>git clone https://github.com/opentikz/opentikz</code></pre>
        <p>Then tell your agent (Claude Code, Codex, Cursor, Gemini CLI…) to use
           <code>skills/using-opentikz/SKILL.md</code> from the clone. The library is
           the cloned repo, right beside the skill.</p>
      </article>
      <article class="install-card">
        <span class="install-tag">other agents · no clone</span>
        <h3>Point a GitHub-reading agent at the repo</h3>
        <p>Send the agent this repo and ask it to use the OpenTikZ skill:</p>
        <pre><code>https://github.com/opentikz/opentikz</code></pre>
        <p>It starts from <code>SKILL.md</code> and fetches only the files it needs.</p>
      </article>
    </div>
  </section>

  <section class="skills-scenarios">
    <h2>Three ways to use it</h2>
    <div class="scenario-cards">
      <article class="scenario-card">
        <h3>1 · Copy a figure by hand <span>no AI</span></h3>
        <p><a href="../browse/">Browse the library</a>, open any item, hit
           <strong>Copy .tex</strong>, and paste it into your paper. Every file is
           <code>\\documentclass{{standalone}}</code> and compiles as-is.</p>
      </article>
      <article class="scenario-card">
        <h3>2 · Edit with your AI agent <span>the main flow</span></h3>
        <p>After installing, just describe the change:</p>
        <pre><code>/opentikz:using-opentikz
&ldquo;add a cross-attention block to the encoder-decoder and make it blue&rdquo;</code></pre>
        <p>The agent finds the figure, copies it into <em>your</em> project, edits it
           via the template&rsquo;s <code>edit_contract</code>, and compiles it before
           handing it back.</p>
      </article>
      <article class="scenario-card">
        <h3>3 · Generate from scratch <span>roadmap</span></h3>
        <p>Describe a figure with no starting template, or hand over a node–edge spec.
           Prompt-to-diagram and graph-to-diagram are
           <a href="../index.html#roadmap">on the roadmap</a>.</p>
      </article>
    </div>
  </section>
```

- [ ] **Step 3: Add minimal CSS for the new cards**

In the page's stylesheet block in `build_site.py` (search for `.usage{` / the embedded CSS region used by these surfaces), add rules consistent with existing card styling:

```python
.skills-install{margin:34px 0 0; max-width:78ch}
.install-cards,.scenario-cards{display:grid; gap:16px; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); margin-top:1em}
.install-card,.scenario-card{border:1px solid var(--line); border-radius:8px; padding:16px}
.install-rec{border-color:var(--accent,#3b6ea5)}
.install-tag{font-family:"IBM Plex Mono",monospace; font-size:.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:.04em}
.install-card h3,.scenario-card h3{font-family:"Fraunces",serif; font-size:1.05rem; margin:.4em 0}
.scenario-card h3 span{font-family:"IBM Plex Mono",monospace; font-size:.65rem; color:var(--muted); margin-left:.4em}
.install-card pre,.scenario-card pre{overflow-x:auto}
```

(If `--accent` / font vars differ in this file, match the names already used nearby; do not introduce new hex outside this rule block.)

- [ ] **Step 4: Rebuild the site and assert the new content rendered**

Run: `python3 tools/build_catalog.py && python3 tools/build_site.py`
Expected: completes without error; prints/creates `site/`.

Run: `grep -c "plugin install opentikz@opentikz" site/skills/index.html`
Expected: `1` (≥1).

Run: `grep -o "How to use" site/index.html | head -1`
Expected: `How to use` (nav label present on home too).

Run: `grep -c "Three ways to use it" site/skills/index.html`
Expected: `1`.

- [ ] **Step 5: Commit**

```bash
git add tools/build_site.py
git commit -m "Site: repurpose /skills/ into How-to-use (install x 3 + scenarios x 3)"
```

---

### Task 4: Home-page "how to start" entry

**Files:**
- Modify: `tools/build_site.py` — `home_page()` (hero sub-copy + a compact start strip)

**Interfaces:**
- Consumes: the existing `home_page()` f-string and `.cta-row` markup.
- Produces: a home page that acknowledges both the AI path and the manual copy path, with `Get started` pointing at `/skills/` (the now-tutorial page).

- [ ] **Step 1: Add a compact start strip below the hero CTA row**

In `home_page()`, immediately after the `<p class="cta-sub">…</p>` line inside `<section class="showcase">`, insert:

```python
    <p class="show-alt">Prefer no AI? <a href="browse/">Browse the library</a> and copy any figure&rsquo;s <code>.tex</code> by hand.</p>
```

(The `Get started` button already targets `skills/`; leave it. This line surfaces the manual path as first-class.)

- [ ] **Step 2: Add the supporting CSS**

In the home page CSS block (search `.cta-sub`), add:

```python
.show-alt{color:var(--muted); font-size:.82rem; margin:.8em 0 0}
```

- [ ] **Step 3: Rebuild and assert**

Run: `python3 tools/build_site.py`
Expected: completes without error.

Run: `grep -c "Prefer no AI" site/index.html`
Expected: `1`.

Run: `grep -c 'href="skills/"' site/index.html`
Expected: `≥1` (the Get started CTA still points to the tutorial).

- [ ] **Step 4: Commit**

```bash
git add tools/build_site.py
git commit -m "Site: home surfaces the manual-copy path; Get started -> how-to-use"
```

---

### Task 5: Sync README + CLAUDE.md

**Files:**
- Modify: `README.md` — the `## Quick start` section
- Modify: `CLAUDE.md` — the repo-structure listing

**Interfaces:**
- Consumes: the exact install/scenario copy from Tasks 1 & 3 (keep identical strings).
- Produces: README + CLAUDE.md consistent with the shipped plugin and site.

- [ ] **Step 1: Replace the README Quick start**

In `README.md`, replace the current `## Quick start` block (the "Clone OpenTikZ into your project" numbered list and the "Prefer to grab one by hand?" line) with:

```markdown
## Quick start

**Use it with your AI agent (recommended).** Install the Claude Code plugin —
run these as two separate Claude Code messages:

```text
/plugin marketplace add https://github.com/opentikz/opentikz
/plugin install opentikz@opentikz
```

Then describe the figure or edit you want — *"draw an encoder–decoder with a
cross-attention block,"* or, pointing at a template, *"add a hidden layer / recolor
this blue / fit it to a CVPR column."* The skill finds the figure, copies it into
your project, edits it via each template's `edit_contract`, and compiles it before
handing it back. Invoke it as `/opentikz:using-opentikz`.

**Other agents (Codex, Cursor, Gemini CLI…).** `git clone` this repo and tell the
agent to use `skills/using-opentikz/SKILL.md`, or just point a GitHub-reading agent
at the repo URL.

**Prefer no AI?** [Browse the gallery](#gallery), copy a figure's `.tex`, and paste
it in — every file is `\documentclass{standalone}` and compiles as-is.
```

- [ ] **Step 2: Add `.claude-plugin/` to the CLAUDE.md repo structure**

In `CLAUDE.md`, in the `## Repo structure` tree, add a line under the top-level
entries (near `catalog.json`):

```text
├── .claude-plugin/           # marketplace.json + plugin.json (Claude Code plugin)
```

- [ ] **Step 3: Assert consistency**

Run: `grep -c "plugin install opentikz@opentikz" README.md`
Expected: `1`.

Run: `grep -c ".claude-plugin/" CLAUDE.md`
Expected: `≥1`.

- [ ] **Step 4: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "Docs: README quick start + CLAUDE.md structure match the plugin install"
```

---

## Self-Review

**Spec coverage:**
- Spec ① Plugin skeleton → Task 1. ✓
- Spec ② SKILL.md two modes + OTROOT resolution → Task 2. ✓
- Spec ③ `/skills/` tutorial (3 install entries + 3 scenarios + nav rename) → Task 3. ✓ Home entry → Task 4. ✓
- Spec ④ README + CLAUDE.md sync → Task 5. ✓
- "Keep why-accurate / reference / demos" → preserved (Task 3 inserts before `{carousel}` and leaves the lower sections intact). ✓
- Non-goals (no curated subset, no catalog sharding, no SVG exclusion, C stays roadmap) → respected; no task touches them. ✓

**Placeholder scan:** No "TBD"/"appropriate"/"etc." action steps; every code/content step shows the literal content. The only conditional is the CSS var-name match (Step 3.3 / 4.2), which gives an explicit fallback instruction, not a placeholder.

**Type/string consistency:** `opentikz` (marketplace), `opentikz` (plugin), `using-opentikz` (skill), `/opentikz:using-opentikz` (command), `https://github.com/opentikz/opentikz` (URL), `OTROOT` (skill variable) — used identically across Tasks 1–5. ✓

**Known follow-ups (not blockers):** Task 1 Step 4 may only be verifiable manually if the `claude` CLI isn't present in the execution environment — record the result honestly rather than asserting success.
