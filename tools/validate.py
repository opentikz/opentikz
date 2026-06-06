#!/usr/bin/env python3
"""Validate OpenTikZ content items.

For every ``*.meta.json`` under icons/, templates/, examples/:
  1. validate it against meta.schema.json (using the ``jsonschema`` library), and
  2. confirm a sibling ``.tex`` exists and compiles standalone via ``latexmk``.

The compile step is SKIPped (non-fatal) when no LaTeX engine is installed, so the
script still runs locally without a TeX distribution. Use ``--strict`` in CI,
where the compile is required and a SKIP becomes a failure.

Exit code is non-zero if any item FAILs.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _common import iter_meta_files, load_json, rel, repo_root, tex_sibling

SCHEMA_NAME = "meta.schema.json"


def _load_validator(root: Path):
    """Return a jsonschema validator for meta.schema.json, or exit on error."""
    try:
        import jsonschema  # noqa: WPS433 (local import: optional-at-import-time dep)
    except ModuleNotFoundError:
        sys.exit(
            "error: the 'jsonschema' package is required.\n"
            "       install it with:  python3 -m pip install -r requirements.txt"
        )
    schema = load_json(root / SCHEMA_NAME)
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def _latex_available() -> bool:
    return shutil.which("latexmk") is not None


def _compile_tex(tex: Path) -> tuple[bool, str]:
    """Compile a standalone .tex with latexmk in a temp dir. Returns (ok, log)."""
    with tempfile.TemporaryDirectory(prefix="opentikz-build-") as tmp:
        proc = subprocess.run(
            [
                "latexmk",
                "-pdf",
                "-interaction=nonstopmode",
                "-halt-on-error",
                f"-output-directory={tmp}",
                tex.name,
            ],
            cwd=tex.parent,
            capture_output=True,
            text=True,
        )
        ok = proc.returncode == 0 and (Path(tmp) / (tex.stem + ".pdf")).exists()
        return ok, (proc.stdout + proc.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="require LaTeX: turn compile SKIPs into FAILs (use in CI).",
    )
    parser.add_argument(
        "--no-compile",
        action="store_true",
        help="only validate metadata; never attempt to compile .tex.",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    validator = _load_validator(root)

    have_latex = _latex_available()
    do_compile = not args.no_compile
    if do_compile and not have_latex and not args.strict:
        print("note: latexmk not found; .tex compilation will be SKIPPED")

    n_pass = n_fail = n_skip = 0
    failures: list[str] = []

    for meta_path in iter_meta_files(root):
        item = rel(meta_path, root)
        # --- metadata ---
        try:
            meta = load_json(meta_path)
        except ValueError as exc:
            print(f"FAIL  {item}: {exc}")
            n_fail += 1
            failures.append(item)
            continue
        errors = sorted(validator.iter_errors(meta), key=lambda e: e.path)
        if errors:
            print(f"FAIL  {item}: schema validation")
            for err in errors:
                loc = "/".join(str(p) for p in err.path) or "(root)"
                print(f"        - {loc}: {err.message}")
            n_fail += 1
            failures.append(item)
            continue

        # --- .tex sibling ---
        tex = tex_sibling(meta_path)
        if not tex.exists():
            print(f"FAIL  {item}: missing sibling .tex ({rel(tex, root)})")
            n_fail += 1
            failures.append(item)
            continue

        # --- compile ---
        if not do_compile:
            print(f"PASS  {item} (compile disabled)")
            n_pass += 1
            continue
        if not have_latex:
            if args.strict:
                print(f"FAIL  {item}: latexmk not found (--strict)")
                n_fail += 1
                failures.append(item)
            else:
                print(f"SKIP  {item}: latexmk not found")
                n_skip += 1
            continue
        ok, log = _compile_tex(tex)
        if ok:
            print(f"PASS  {item}")
            n_pass += 1
        else:
            print(f"FAIL  {item}: standalone compile failed")
            tail = "\n".join(log.strip().splitlines()[-15:])
            print("        --- latexmk output (tail) ---")
            for line in tail.splitlines():
                print(f"        {line}")
            n_fail += 1
            failures.append(item)

    total = n_pass + n_fail + n_skip
    print(
        f"\n{total} item(s): {n_pass} passed, {n_fail} failed, {n_skip} skipped"
    )
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
