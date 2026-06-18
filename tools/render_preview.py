#!/usr/bin/env python3
"""Render a trimmed .svg preview from a standalone .tex.

Pipeline (depends on backend):
  dvisvgm:  latexmk -dvi -> dvisvgm <dvi>     (-> <name>.svg beside the .tex)
  pdf2svg:  latexmk -pdf -> pdf2svg <pdf>

Backends (``--backend``, default ``dvisvgm``):
  dvisvgm   Compile to DVI, then dvisvgm reads the DVI and converts to SVG,
            cropping to the drawing's bbox (--bbox=min). The DVI route is used
            (not PDF input) because dvisvgm >=3 cannot drive Ghostscript >=10.01
            for PDF input; the DVI/PostScript-specials path works with current
            Ghostscript. Produces clean, self-contained SVG.
  pdf2svg   Compile to PDF, then pdf2svg (poppler-based, Ghostscript-free). The
            standalone class already crops to content, so no pdfcrop step.

The final backend choice for the project is intentionally deferred; both are
supported so previews can be compared on real content before committing to one.

Accepts a path to a single ``.tex`` file or to an item directory containing
exactly one ``.tex``.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BACKENDS = ("dvisvgm", "pdf2svg")


def _require(*tools: str) -> None:
    missing = [t for t in tools if shutil.which(t) is None]
    if missing:
        sys.exit(
            "error: required tool(s) not found on PATH: "
            + ", ".join(missing)
            + "\n       install a LaTeX distribution (latexmk) and the SVG backend."
        )


def resolve_tex(target: Path) -> Path:
    """Resolve a .tex from a file path or an item directory."""
    if target.is_file() and target.suffix == ".tex":
        return target
    if target.is_dir():
        candidates = sorted(target.glob("*.tex"))
        if len(candidates) == 1:
            return candidates[0]
        if not candidates:
            sys.exit(f"error: no .tex found in {target}")
        sys.exit(
            f"error: multiple .tex files in {target}; pass one explicitly: "
            + ", ".join(c.name for c in candidates)
        )
    sys.exit(f"error: not a .tex file or directory: {target}")


def _latexmk(tex: Path, out_dir: Path, fmt: str) -> Path:
    """Compile ``tex`` to ``fmt`` ("pdf" or "dvi") in ``out_dir``; return the file."""
    proc = subprocess.run(
        [
            "latexmk",
            f"-{fmt}",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={out_dir}",
            tex.name,
        ],
        cwd=tex.parent,
        capture_output=True,
        text=True,
    )
    out = out_dir / (tex.stem + "." + fmt)
    if proc.returncode != 0 or not out.exists():
        tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-20:])
        sys.exit(f"error: latexmk failed for {tex.name}\n{tail}")
    return out


def _render_dvisvgm(dvi: Path, svg: Path) -> None:
    # DVI input (not --pdf): dvisvgm >=3 cannot drive Ghostscript >=10.01 for PDF
    # input, but the DVI/PostScript-specials path works with current Ghostscript.
    #
    # --no-fonts: trace every glyph as a vector <path> instead of emitting SVG 1.1
    # <font>/<glyph> elements. Browsers dropped SVG-font support years ago, so the
    # font route silently falls back to a system font whose metrics don't match the
    # dvisvgm-computed <tspan> x-offsets — which splits multi-word labels apart
    # ("data-pa rallel", "IO -aware"). Outlined paths render identically everywhere.
    subprocess.run(
        ["dvisvgm", "--no-fonts", "--bbox=min", "--optimize",
         "--output=" + str(svg), str(dvi)],
        check=True,
        capture_output=True,
        text=True,
    )


def _render_pdf2svg(pdf: Path, svg: Path) -> None:
    # standalone already crops to content, so no pdfcrop step is needed.
    subprocess.run(["pdf2svg", str(pdf), str(svg)], check=True, capture_output=True, text=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="path to a .tex file or an item directory")
    parser.add_argument(
        "--backend",
        choices=BACKENDS,
        default="dvisvgm",
        help="SVG conversion backend (default: dvisvgm)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output .svg path (default: <name>.svg beside the .tex)",
    )
    args = parser.parse_args(argv)

    tex = resolve_tex(args.target)
    svg = args.output or tex.with_suffix(".svg")

    if args.backend == "dvisvgm":
        _require("latexmk", "dvisvgm")
    else:
        _require("latexmk", "pdf2svg")

    with tempfile.TemporaryDirectory(prefix="opentikz-render-") as tmp:
        work = Path(tmp)
        try:
            if args.backend == "dvisvgm":
                _render_dvisvgm(_latexmk(tex, work, "dvi"), svg)
            else:
                _render_pdf2svg(_latexmk(tex, work, "pdf"), svg)
        except subprocess.CalledProcessError as exc:
            out = (exc.stdout or "") + (exc.stderr or "")
            sys.exit(f"error: {args.backend} failed\n{out.strip()}")

    print(f"wrote {svg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
