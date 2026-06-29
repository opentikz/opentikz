# Homepage restyle (round 2) — design

**Date:** 2026-06-28
**Status:** Approved (brainstorm), pending implementation plan
**Scope:** Landing page only — `home_page()` and `STYLE_CSS` in
`tools/build_site.py`, plus one cross-reference fix on the How-to-use
(`skills_page()`) link. No content/catalog/template changes.

## Problem

The home page has accumulated rough edges: the "Why TikZ" reasons strip looks
unstyled (system-ui fonts, bland), the hero carousel's circular side arrows are
visually heavy, the "Get started" hero button leads away from the page (and reads
as broken), the two "Why" sections are out of order, the "Why not ChatGPT" title
is left-aligned with a redundant subtitle, the "On the roadmap" teaser no longer
earns its space, and section boundaries are inconsistent. There is also no
on-page install path — a visitor must navigate to the How-to-use page to see how
to add the skill.

## Goals

- A clean, consistent section rhythm with one horizontal rule per boundary.
- An on-page **Get started** install section so a visitor can copy the install
  commands without leaving home.
- Cohesive card styling for the "Why TikZ" reasons, matching the page's other
  cards.
- A lighter hero carousel (flat chevrons, not circular buttons).

## Non-goals (YAGNI)

- No changes to `/browse/`, `/skills/` content (only the one `#roadmap` link is
  repointed), `README.md`, or `CLAUDE.md`.
- No new JS carousel behaviour — chevron change is CSS/markup only.
- No new install copy invented — reuse the exact commands already shipped on the
  How-to-use page.

## Design

### New section order (top → bottom)

```
hero
─ Get started            (NEW)
─ 4 ways to use OpenTikZ  (unchanged)
─ Why TikZ                (moved up; restyled)
─ Why not just ask ChatGPT? (title centered, subtitle removed)
─ cta-band
```

Each `─` is exactly one `border-top:1px solid var(--line)` on the lower section.
"On the roadmap" is deleted entirely.

### Changes, item by item

1. **Hero CTA.** Delete the `Get started` button from the hero `.cta-row`. The
   remaining `Browse the library →` button becomes the single primary CTA
   (`btn btn-primary`). No anchor/link to a get-started target is added to the
   hero — the new section sits immediately below it.

2. **Hero carousel chevrons.** Replace the circular `.car-nav` arrow buttons
   (used by `hero_carousel()`) with **flat, borderless chevrons** overlaid at the
   left/right figure edges: no background circle, no border; a muted glyph that
   takes the accent color on hover. The dot row is unchanged. This is a CSS change
   to `.car-nav` (or a hero-scoped override) plus, if needed, the glyph markup;
   `app.js` behaviour is untouched. The demos/howto carousels already render
   without side arrows, so scope the restyle so it does not regress them.

3. **Get started section (new).** Inserted between the hero `</section>` and the
   `{howto_section}` interpolation. Structure:
   - `<section class="getstarted" id="get-started">` with a `border-top` rule.
   - h2 in the shared Fraunces 1.7rem section-title treatment (same as
     `.why-ot h2` / `.howto h2`).
   - One energetic one-line lede.
   - The two **real** install commands, copied verbatim from the How-to-use
     page's recommended card:
     ```
     /plugin marketplace add https://github.com/opentikz/opentikz
     /plugin install opentikz@opentikz
     ```
     rendered as two `<pre><code>` blocks (two separate Claude Code messages), with
     a one-line note that it's then used via `/opentikz:using-opentikz`.
   - A "more ways to install →" link to the repo README
     (`{REPO_URL}` / `{REPO_URL}#readme`), for the clone / GitHub-agent paths.

4. **Why TikZ — restyle + move.** Move `why_tikz_band()` above
   `why_opentikz_band()` in `home_page()`. Restyle:
   - h2 promoted to the shared Fraunces 1.7rem section-title treatment.
   - The three `.wts-item`s become **bordered cards** matching the visual language
     of `.cmp-card` / `.install-card` (border, radius, padding), using the site
     font stack (IBM Plex Sans / Fraunces) instead of `system-ui`, each with a
     **leading numeral** (1 · 2 · 3 or `01`/`02`/`03`).
   - Keep the three existing reasons and their copy verbatim.

5. **Why not just ask ChatGPT — title + subtitle.** Center the `.why-ot` heading
   (and its block) and delete the `.why-ot-sub` paragraph
   (`You can — here's what changes…`). The comparison cards are unchanged.

6. **Delete roadmap.** Remove the entire `<section class="roadmap">…</section>`
   from `home_page()`. Its CSS may remain unused or be removed. **Cross-reference
   fix:** `skills_page()` links scenario 3 to `../index.html#roadmap` (the deleted
   anchor) — repoint it to the roadmap content that still lives on the How-to-use
   page (an on-page `#…` anchor there) or drop the link, so no dead `#roadmap`
   target remains.

7. **Horizontal rules.** Standardize every home section boundary to exactly one
   `border-top:1px solid var(--line)` on the lower section, including
   hero→get-started. Remove any double rules introduced by the reordering.

### Decisions recorded (from brainstorm)

- Hero "Get started" button: **deleted** (not repointed).
- Carousel arrows: **flat chevrons** (not removed, not relocated).
- Why TikZ reasons: **bordered cards** with leading numeral.
- New section anchor id: `#get-started`.
- "more ways to install" target: repo **README**.

## Risks / things to verify

- **Chevron scoping:** `.car-nav` is shared markup; confirm the hero is the only
  carousel that renders `.car-nav` buttons (demos/howto don't), or scope the new
  style under `.hero-carousel` so other carousels can't regress.
- **No dead anchors:** after deleting roadmap, grep the built site for
  `#roadmap` — the only reference is the skills-page scenario-3 link; it must be
  repointed.
- **Install copy parity:** the new section's commands must match the How-to-use
  page's recommended card exactly (no drift between the two install snippets).
- **Section rhythm:** verify no section ends up with two top borders or none after
  the reorder + roadmap deletion.
- **Build + freshness:** `tools/build_site.py` rebuilds cleanly; no preview/catalog
  regeneration needed (no content changed).
