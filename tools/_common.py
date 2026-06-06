"""Shared helpers for the OpenTikZ tooling scripts.

Kept dependency-free (stdlib only) so it can be imported by every tool.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

# Top-level directories that hold catalogable content items.
CONTENT_DIRS = ("icons", "templates", "examples")


def repo_root() -> Path:
    """Return the repository root, resolved relative to this file.

    tools/_common.py -> repo root is the parent of tools/.
    """
    return Path(__file__).resolve().parent.parent


def iter_meta_files(root: Path | None = None) -> Iterator[Path]:
    """Yield every ``*.meta.json`` under the content directories, sorted."""
    base = root or repo_root()
    for content_dir in CONTENT_DIRS:
        d = base / content_dir
        if not d.is_dir():
            continue
        yield from sorted(d.rglob("*.meta.json"))


def load_json(path: Path) -> dict:
    """Load a JSON file, raising a clear error on malformed content."""
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:  # pragma: no cover - message clarity
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc


def tex_sibling(meta_path: Path) -> Path:
    """Return the .tex expected alongside a .meta.json.

    ``foo/bar.meta.json`` -> ``foo/bar.tex``.
    """
    return meta_path.with_name(meta_path.name[: -len(".meta.json")] + ".tex")


def rel(path: Path, root: Path | None = None) -> str:
    """Return ``path`` relative to the repo root as a POSIX string."""
    base = root or repo_root()
    return path.resolve().relative_to(base).as_posix()
