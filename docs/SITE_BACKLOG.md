# Website backlog (Step 4 → launch)

PM review notes for the static site (`tools/build_site.py`). Captured 2026-06-07
after a real-browser test pass (Chrome via puppeteer-core): 14/14 interactive
checks green (gallery, search, type filter, copy-to-clipboard, responsive). The
**layout is approved for MVP** — these are the prioritized improvements to make
before a public launch (Step 5). Check items off as they land.

Priority key: **P1** = do before public launch · **P2** = strongly wanted ·
**P3** = polish / nice-to-have.

## Information architecture

- [x] **P1 — Split the three content types into distinct tabs/sections, not one
      flat grid behind a tag filter.** _(done 244e207: three labelled sections —
      Icons / Templates / Examples — each with heading + count + grid; search and
      chips are section-aware.)_ Today all 16 items (9 icons · 5 templates ·
      2 examples) tile into a single area and are only separable via the filter
      chips. The three layers are conceptually different products (atomic icons vs.
      editable templates vs. paper-grade examples) and should read as three
      first-class destinations — e.g. top-level tabs (`Icons` / `Templates` /
      `Examples`), or three labelled sections on the landing page, each with its
      own heading and grid. The filter chips can stay as a secondary control, but
      the primary structure should make the three layers obvious at a glance.
      Keep search working across all tabs.

## Conversion (the core funnel: find → see → copy)

- [x] **P1 — Surface the companion skill (the differentiator).** Template item
      pages only *mention* `skill.md` in a callout; you can't read or download it.
      Skills are the stated "soul of the product" — render the skill markdown on
      the template page, or link/download it. (Also flagged in code review.)
      _(done 244e207: skill.md rendered on template pages via a built-in Markdown
      converter, in a collapsible block with a "Copy skill.md" button.)_
- [ ] **P1 — Shorten the path to "copy".** The core conversion (copy `.tex`) lives
      one click inside the item page. Add a copy affordance on the gallery card
      (e.g. on hover) so the highest-value action isn't gated behind navigation.
      Roadmap Step 0 explicitly tracks copy-button clicks > stars > pageviews.
- [ ] **P2 — First-visit clarity.** A cold visitor may not instantly grasp the
      items are paste-ready, standalone-compilable, and CC0. Add one line of
      "how to use" near the hero.

## Launch polish

- [ ] **P3 — Favicon + OpenGraph image** for social sharing (Reddit / TeX SE /
      Twitter in Step 5). No share preview today.
- [ ] **P3 — Deduplicate the counts.** `9 / 5 / 2` appear twice (hero stats and
      filter chips). Pick one home for them.
- [ ] **P3 — Result-count contrast** under the chips is a touch low; bump it.

## Not blocking (defer)

- [ ] Card domain labels (`ml`, `systems`) are very muted — consider raising
      contrast or promoting them.
- [ ] No on-site dark-mode toggle (mildly ironic given the figures support a dark
      palette). Nice future feature, not MVP.

## Verified working (no action needed — recorded for context)

- Fuzzy search (Fuse.js 7.0.0, SRI-pinned) returns correct top hits; type filters
  count 9 / 5 / 2 correctly; empty state works.
- Copy-to-clipboard writes the raw, un-escaped `.tex` and confirms ("Copied ✓").
- Per-item preview SVGs load; build-time cards are SEO-indexable.
- Responsive: no horizontal overflow at 390px.
- Generator is stdlib-only and auto-feeds from `catalog.json` (adding content
  needs zero site edits).
