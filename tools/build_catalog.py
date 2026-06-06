#!/usr/bin/env python3
"""Build catalog.json from every content item's metadata.

Walks icons/, templates/, examples/, reads each ``*.meta.json``, and writes a
stable, sorted ``catalog.json`` at the repo root. This file is AUTO-GENERATED —
never hand-edit it; re-run this script instead.

Each catalog entry is the item's metadata plus a ``path`` field giving the
item's directory relative to the repo root.

Use ``--check`` to verify catalog.json is up to date without writing (CI), which
exits non-zero if it would change.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _common import iter_meta_files, load_json, rel, repo_root

CATALOG_NAME = "catalog.json"


def build(root: Path) -> list[dict]:
    """Return the catalog as a sorted list of entries."""
    entries: list[dict] = []
    for meta_path in iter_meta_files(root):
        meta = load_json(meta_path)
        entry = dict(meta)
        entry["path"] = rel(meta_path.parent, root)
        entries.append(entry)
    entries.sort(key=lambda e: (e.get("type", ""), e.get("id", "")))
    return entries


def serialize(entries: list[dict]) -> str:
    """Deterministic JSON text (sorted keys, trailing newline)."""
    return json.dumps(entries, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify catalog.json is current without writing; exit 1 if stale.",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    entries = build(root)
    text = serialize(entries)
    catalog_path = root / CATALOG_NAME

    if args.check:
        current = catalog_path.read_text(encoding="utf-8") if catalog_path.exists() else ""
        if current != text:
            print(f"error: {CATALOG_NAME} is out of date; run tools/build_catalog.py")
            return 1
        print(f"{CATALOG_NAME} is up to date ({len(entries)} item(s))")
        return 0

    catalog_path.write_text(text, encoding="utf-8")
    print(f"wrote {rel(catalog_path, root)} ({len(entries)} item(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
