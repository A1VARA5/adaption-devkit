"""Shared pytest fixtures and tiny dataset writers.

These helpers build small files under pytest's ``tmp_path`` so every test is
self contained and never reads cookbook or sample_data. All writers use the
same on disk conventions the package reads (utf-8 for plain files, utf-8-sig
when a BOM is requested).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Sequence


def write_csv(
    path: Path,
    fieldnames: Sequence[str],
    rows: Sequence[Dict[str, object]],
    bom: bool = False,
) -> Path:
    """Write a small CSV. When ``bom`` is True, write a UTF-8 BOM up front.

    A BOM written with ``encoding="utf-8-sig"`` is the exact byte sequence the
    package strips with its utf-8-sig reads, so this lets us prove BOM safety.
    """
    encoding = "utf-8-sig" if bom else "utf-8"
    with path.open("w", encoding=encoding, newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def write_jsonl(path: Path, rows: Sequence[Dict[str, object]]) -> Path:
    """Write a small JSONL file (one JSON object per line)."""
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def read_lines(path: Path) -> List[str]:
    """Return the non empty lines of a text file, read BOM safe."""
    with path.open("r", encoding="utf-8-sig") as fh:
        return [line for line in (raw.strip() for raw in fh) if line]
