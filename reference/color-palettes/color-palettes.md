# Skill: OpenTikZ color palette

The single source of truth for colors in OpenTikZ. **All icons, templates, and
examples reference these named colors — never hard-code a hex value inline.**

Because every `.tex` must compile **standalone**, colors cannot be `\input` from
a shared file at build time. Instead, each content file **mirrors the palette
block below into its own preamble**. This file is the canonical definition those
copies must match.

## Named colors

The default palette is the color-blind-friendly **Okabe-Ito** set, chosen so
figures remain distinguishable under the common forms of color vision deficiency
and in grayscale print.

| Name       | Light (default) | Dark-tuned | Typical role                         |
|------------|-----------------|------------|--------------------------------------|
| `otblue`   | `#0072B2`       | `#56B4E9`  | primary blocks, main flow            |
| `otorange` | `#E69F00`       | `#E69F00`  | highlight / accent, "the new thing"  |
| `otteal`   | `#009E73`       | `#2EBE9B`  | success / data / secondary blocks    |
| `otpurple` | `#CC79A7`       | `#E08FBE`  | tertiary blocks, auxiliary paths     |
| `otgray`   | `#5A5A5A`       | `#B3B3B3`  | structure: outlines, text, arrows    |

Convention: use **fill tints** for surfaces (`fill=otblue!12`) and the **full
color** (often darkened: `draw=otblue!75!black`) for strokes, so adjacent blocks
read clearly. `otgray` is the neutral for outlines/arrows/labels.

## Light palette block (default — paste into preamble)

```latex
% --- OpenTikZ palette (light / default, color-blind-friendly Okabe-Ito) ---
\definecolor{otblue}{HTML}{0072B2}
\definecolor{otorange}{HTML}{E69F00}
\definecolor{otteal}{HTML}{009E73}
\definecolor{otpurple}{HTML}{CC79A7}
\definecolor{otgray}{HTML}{5A5A5A}
```

## Dark palette block (for dark backgrounds — same names, swap the block)

A figure switches to dark mode by replacing the light block with this one: the
**names are identical**, so no body edits are needed. You **must** also set a dark
page background — `\definecolor{otpaper}{HTML}{1E1E1E}` then `\pagecolor{otpaper}`.
The dark colors are tuned for a dark canvas; rendered on a white page the tints
look washed-out grey, which is the usual "the dark palette looks broken" mistake.

```latex
% --- OpenTikZ palette (dark-tuned, same names) ---
\definecolor{otpaper}{HTML}{1E1E1E}   % dark page background; \pagecolor{otpaper}
\definecolor{otblue}{HTML}{56B4E9}
\definecolor{otorange}{HTML}{E69F00}
\definecolor{otteal}{HTML}{2EBE9B}
\definecolor{otpurple}{HTML}{E08FBE}
\definecolor{otgray}{HTML}{B3B3B3}
```

> Open item (future, non-MVP): tint syntax like `otblue!15` mixes toward **white**,
> so on `otpaper` the tints lift toward white rather than blending into the dark
> background. A future enhancement could define dark-aware tints (e.g. mix toward
> `otpaper`). For MVP, the full colors + `\pagecolor{otpaper}` read fine.

## How to apply

- **New content**: paste the light block into the preamble; reference colors by
  name only (`fill=otteal!15`, `draw=otblue!75!black`, `text=otgray`).
- **Recolor a figure** (e.g. "make it teal"): change color *names* in the body
  (`otblue` → `otteal`); do not touch the `\definecolor` block and never
  introduce a raw hex or a built-in name like `blue`/`red`.
- **Re-theme to a different hue family**: keep using the five names; only their
  *roles* change. If a figure needs a sixth distinct color, prefer a tint/shade
  of an existing name (`otblue!60`) before adding a new one.
- **Dark variant**: swap the light block for the dark block; the body is
  unchanged because the names match.

## Constraints

- Never write a hex literal or a stock xcolor name (`blue`, `red`, `green!50`)
  in content. Always go through the five palette names (tints/shades allowed).
- Keep the `\definecolor` values byte-for-byte identical to the tables above so
  every figure shares one palette. `swatches.svg` is the visual reference.
- These five names are the contract skills target when recoloring — don't rename
  them.

See `swatches.tex` / `swatches.svg` for a rendered reference of both variants.
