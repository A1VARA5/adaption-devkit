"""convert.py - convert a dataset between the formats Adaption ingests.

One public function, :func:`convert_file`, infers the source and destination
format from the file extensions and rewrites the rows. Supported extensions:

    .csv     comma-separated values (header row)
    .jsonl   one JSON object per line (also accepts .ndjson)
    .parquet columnar (optional; needs pyarrow, imported lazily)

Files are always read with ``utf-8-sig`` so a byte order mark never corrupts the
first header or key, and always written as plain ``utf-8``. The function returns
the number of data rows written, so callers can sanity-check the round trip.

Why this exists: the platform ingests CSV and JSONL cleanly, but real corpora
arrive in whichever format the upstream tool emitted. Converting locally, BOM
safe, beats hand-rolling a one-off script every time and keeps the column set
intact so a downstream ``lint`` and ``run`` see exactly the same fields.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Extensions we recognize, grouped by handler.
_CSV_EXT = {".csv"}
_JSONL_EXT = {".jsonl", ".ndjson"}
_PARQUET_EXT = {".parquet"}
_SUPPORTED = _CSV_EXT | _JSONL_EXT | _PARQUET_EXT


class UnsupportedFormat(ValueError):
    """Raised when a file extension is not one we can read or write."""


class OptionalDependencyMissing(RuntimeError):
    """Raised when a format needs a package that is not installed (pyarrow)."""


def convert_file(src: str, dst: str) -> int:
    """Convert ``src`` to ``dst``, inferring both formats from the extensions.

    Args:
        src: input file (.csv, .jsonl/.ndjson, or .parquet).
        dst: output file (.csv, .jsonl/.ndjson, or .parquet).

    Returns:
        The number of data rows written.

    Raises:
        FileNotFoundError: if ``src`` does not exist.
        UnsupportedFormat: if either extension is not supported.
        OptionalDependencyMissing: if a .parquet side is used without pyarrow.
    """
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        raise FileNotFoundError("input file does not exist: " + str(src_path))

    src_ext = src_path.suffix.lower()
    dst_ext = dst_path.suffix.lower()
    if src_ext not in _SUPPORTED:
        raise UnsupportedFormat(
            "unsupported input extension '"
            + src_ext
            + "'. Use .csv, .jsonl, or .parquet."
        )
    if dst_ext not in _SUPPORTED:
        raise UnsupportedFormat(
            "unsupported output extension '"
            + dst_ext
            + "'. Use .csv, .jsonl, or .parquet."
        )

    rows, columns = _read(src_path, src_ext)

    if dst_path.parent and not dst_path.parent.exists():
        dst_path.parent.mkdir(parents=True, exist_ok=True)

    return _write(dst_path, dst_ext, rows, columns)


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


def _read(path: Path, ext: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    if ext in _CSV_EXT:
        return _read_csv(path)
    if ext in _JSONL_EXT:
        return _read_jsonl(path)
    if ext in _PARQUET_EXT:
        return _read_parquet(path)
    raise UnsupportedFormat("unsupported input extension '" + ext + "'")


def _read_csv(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        columns = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    return rows, columns


def _read_jsonl(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    rows: List[Dict[str, Any]] = []
    columns: List[str] = []
    seen = set()
    with path.open("r", encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                obj = {"value": obj}
            rows.append(obj)
            for key in obj:
                if key not in seen:
                    seen.add(key)
                    columns.append(key)
    return rows, columns


def _read_parquet(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    pq = _import_parquet()
    table = pq.read_table(str(path))
    columns = list(table.column_names)
    # to_pylist yields one dict per row with native Python scalars.
    rows = table.to_pylist()
    return rows, columns


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def _write(
    path: Path, ext: str, rows: List[Dict[str, Any]], columns: List[str]
) -> int:
    if ext in _CSV_EXT:
        return _write_csv(path, rows, columns)
    if ext in _JSONL_EXT:
        return _write_jsonl(path, rows)
    if ext in _PARQUET_EXT:
        return _write_parquet(path, rows, columns)
    raise UnsupportedFormat("unsupported output extension '" + ext + "'")


def _csv_cell(value: Any) -> str:
    """Render a cell for CSV. Nested JSON values are serialized compactly so a
    round trip keeps the data rather than writing Python repr."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _write_csv(path: Path, rows: List[Dict[str, Any]], columns: List[str]) -> int:
    # Preserve discovered column order, then append any straggler keys that only
    # appear in later rows so no data is silently dropped.
    fieldnames = list(columns)
    seen = set(fieldnames)
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    # newline="" per the csv module; utf-8 (no BOM) on the way out.
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _csv_cell(row.get(k)) for k in fieldnames})
    return len(rows)


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> int:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=False))
            fh.write("\n")
    return len(rows)


def _write_parquet(
    path: Path, rows: List[Dict[str, Any]], columns: List[str]
) -> int:
    pa, pq = _import_parquet_full()
    fieldnames = list(columns)
    seen = set(fieldnames)
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    table = pa.Table.from_pylist(
        [{k: row.get(k) for k in fieldnames} for row in rows]
    )
    pq.write_table(table, str(path))
    return len(rows)


# ---------------------------------------------------------------------------
# Lazy optional import (pyarrow)
# ---------------------------------------------------------------------------


def _import_parquet() -> Any:
    """Import ``pyarrow.parquet`` lazily with a friendly error if missing."""
    try:
        import pyarrow.parquet as pq  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on env
        raise OptionalDependencyMissing(
            "Parquet support needs pyarrow, which is not installed. Install it "
            "with 'pip install adaption-kit[parquet]' (or 'pip install pyarrow')."
        ) from exc
    return pq


def _import_parquet_full() -> Tuple[Any, Any]:
    """Import both ``pyarrow`` and ``pyarrow.parquet`` for writing."""
    try:
        import pyarrow as pa  # type: ignore
        import pyarrow.parquet as pq  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on env
        raise OptionalDependencyMissing(
            "Parquet support needs pyarrow, which is not installed. Install it "
            "with 'pip install adaption-kit[parquet]' (or 'pip install pyarrow')."
        ) from exc
    return pa, pq
