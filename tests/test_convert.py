"""Tests for adaption_kit.convert.convert_file.

The contract under test:
    convert_file(src, dst) -> int
The format is inferred from each path's extension, source files are read BOM
safe with utf-8-sig, and the return value is the number of rows converted.

convert.py is an optional part of the toolkit. If it is not present these
tests skip cleanly so the rest of the suite still runs; when convert lands they
activate automatically and verify the row count, the JSONL line count, and a
CSV round trip.
"""

from __future__ import annotations

import pytest

from conftest import read_lines, write_csv

convert = pytest.importorskip(
    "adaption_kit.convert",
    reason="adaption_kit.convert is not present yet",
)


def _sample_rows():
    return [
        {"prompt": "Describe the serum.", "completion": "Hydrates in seconds."},
        {"prompt": "Describe the mascara.", "completion": "Smudge proof all day."},
        {"prompt": "Describe the toner.", "completion": "Balances every zone."},
    ]


def test_csv_to_jsonl_returns_row_count_and_line_count(tmp_path):
    """convert_file(src.csv, dst.jsonl) returns the row count.

    The produced JSONL must have exactly that many non empty lines.
    """
    rows = _sample_rows()
    src = write_csv(tmp_path / "src.csv", ["prompt", "completion"], rows)
    dst = tmp_path / "out.jsonl"

    count = convert.convert_file(src, dst)

    assert count == len(rows)
    assert dst.exists()
    assert len(read_lines(dst)) == len(rows)


def test_csv_to_jsonl_to_csv_round_trips(tmp_path):
    """CSV -> JSONL -> CSV preserves the row count and the cell values."""
    rows = _sample_rows()
    src = write_csv(tmp_path / "src.csv", ["prompt", "completion"], rows)
    jsonl = tmp_path / "mid.jsonl"
    back = tmp_path / "back.csv"

    n1 = convert.convert_file(src, jsonl)
    n2 = convert.convert_file(jsonl, back)

    assert n1 == n2 == len(rows)
    assert back.exists()

    # The round tripped CSV reloads to the same rows.
    import csv

    with back.open("r", encoding="utf-8-sig", newline="") as fh:
        reloaded = list(csv.DictReader(fh))
    assert len(reloaded) == len(rows)
    assert reloaded[0]["prompt"] == rows[0]["prompt"]
    assert reloaded[0]["completion"] == rows[0]["completion"]


def test_convert_reads_bom_source(tmp_path):
    """A BOM (utf-8-sig) source still converts; headers are not corrupted."""
    rows = _sample_rows()
    src = write_csv(
        tmp_path / "bom.csv", ["prompt", "completion"], rows, bom=True
    )
    dst = tmp_path / "out.jsonl"

    count = convert.convert_file(src, dst)

    assert count == len(rows)
    import json

    first = json.loads(read_lines(dst)[0])
    # The BOM did not leak into the first key name.
    assert "prompt" in first
