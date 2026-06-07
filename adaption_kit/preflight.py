"""preflight.py - lint a dataset before spending credits on a real run.

The headline check is anchor UNIQUENESS. Adaption always applies deduplication
keyed on the prompt, so templated prompts whose only variety lives in context
columns collapse to a handful of unique rows. This module detects that and warns
how many rows dedup will collapse, plus reports fill rates, empties, and encoding.

Pure standard library. Reads CSV and JSONL with utf-8-sig so a BOM does not
corrupt the first header or key.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Severity levels, ordered worst-last so we can take a max.
PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
_RANK = {PASS: 0, WARN: 1, FAIL: 2}

# Completions longer than this many characters are flagged. Most adaptation
# targets sit well under this; very long answers usually mean a whole document
# leaked into one cell and will dominate or get truncated downstream.
LONG_COMPLETION_CHARS = 8000

# Fraction of identical normalized anchors at or above which we treat the anchor
# as "almost entirely identical" and fail (it will fully collapse under dedup).
NEAR_CONSTANT_THRESHOLD = 0.98

# Characters that signal a decoding problem: the classic mojibake marker, the
# Unicode replacement char, and raw C0 control bytes other than tab/newline.
_REPLACEMENT_CHAR = "�"
_MOJIBAKE_MARKERS = ("Ã©", "Ã¨", "Â ", "â")


@dataclass
class FieldStat:
    """Per-column fill statistics."""

    name: str
    present: int  # rows where the column exists and is non-empty
    total: int

    @property
    def fill_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.present / self.total


@dataclass
class LintReport:
    """Result of :func:`lint_dataset`.

    ``status`` is the worst of all checks. ``checks`` is a list of
    ``(level, message)`` tuples in the order they were produced.
    """

    path: str
    status: str = PASS
    row_count: int = 0
    fmt: str = ""
    encoding: str = "utf-8"
    columns: List[str] = field(default_factory=list)
    anchor: str = ""  # "prompt" or "completion"
    anchor_column: str = ""
    unique_anchor_values: int = 0
    duplicate_rows: int = 0  # rows that dedup would collapse (row_count - unique)
    field_stats: List[FieldStat] = field(default_factory=list)
    empty_cells: int = 0
    # Extended diagnostics (additive; older callers can ignore these).
    near_duplicate_rows: int = 0  # extra collapse once case/whitespace normalized
    unique_anchor_values_normalized: int = 0
    empty_anchor_cells: int = 0  # anchor cells that are empty or whitespace only
    long_completion_rows: int = 0  # completions over the soft length ceiling
    max_completion_chars: int = 0
    suspicious_encoding_rows: int = 0  # rows showing mojibake or control bytes
    checks: List[Tuple[str, str]] = field(default_factory=list)

    # -- helpers ---------------------------------------------------------

    def add(self, level: str, message: str) -> None:
        self.checks.append((level, message))
        if _RANK[level] > _RANK[self.status]:
            self.status = level

    @property
    def unique_anchor_rate(self) -> float:
        if self.row_count == 0:
            return 0.0
        return self.unique_anchor_values / self.row_count

    def summary(self) -> str:
        """Human-readable, printable multi-line summary."""
        lines: List[str] = []
        lines.append("adaption-kit preflight report")
        lines.append("=" * 60)
        lines.append("file        : " + self.path)
        lines.append("format      : " + (self.fmt or "unknown"))
        lines.append("encoding    : " + self.encoding)
        lines.append("rows        : " + str(self.row_count))
        lines.append("columns     : " + (", ".join(self.columns) if self.columns else "(none)"))
        if self.anchor:
            lines.append(
                "anchor      : "
                + self.anchor
                + " -> column '"
                + self.anchor_column
                + "'"
            )
            lines.append(
                "unique anchor values: "
                + str(self.unique_anchor_values)
                + " / "
                + str(self.row_count)
                + " ("
                + _pct(self.unique_anchor_rate)
                + ")"
            )
            lines.append(
                "dedup would collapse: "
                + str(self.duplicate_rows)
                + " row(s)"
            )
            if self.near_duplicate_rows:
                lines.append(
                    "near duplicate anchors: "
                    + str(self.near_duplicate_rows)
                    + " more fold after normalizing case and whitespace"
                )
        if self.field_stats:
            lines.append("")
            lines.append("metadata fill rate:")
            for fs in self.field_stats:
                lines.append(
                    "  - "
                    + fs.name.ljust(24)
                    + str(fs.present).rjust(7)
                    + " / "
                    + str(fs.total)
                    + "  ("
                    + _pct(fs.fill_rate)
                    + ")"
                )
        lines.append("empty cells : " + str(self.empty_cells))
        if self.max_completion_chars:
            lines.append(
                "longest completion: "
                + str(self.max_completion_chars)
                + " char(s)"
                + (
                    " (" + str(self.long_completion_rows) + " over limit)"
                    if self.long_completion_rows
                    else ""
                )
            )
        if self.suspicious_encoding_rows:
            lines.append(
                "encoding flags: "
                + str(self.suspicious_encoding_rows)
                + " row(s) with mojibake/control bytes"
            )
        lines.append("")
        lines.append("checks:")
        for level, msg in self.checks:
            lines.append("  [" + level + "] " + msg)
        lines.append("")
        lines.append("RESULT: " + self.status)
        return "\n".join(lines)


def _pct(x: float) -> str:
    return str(round(x * 100, 1)) + "%"


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def _detect_encoding(path: Path) -> str:
    """Report whether the file carries a UTF-8 BOM. We always *read* with
    utf-8-sig regardless, so this is informational only."""
    raw = path.read_bytes()[:3]
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig (BOM)"
    return "utf-8"


def _load_rows(path: Path) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    """Return ``(format, rows, columns)``.

    Supports .csv, .jsonl/.ndjson, and .json (array of objects). Always opens
    with ``encoding="utf-8-sig"`` so a byte order mark is stripped safely.
    """
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _load_csv(path)
    if suffix in (".jsonl", ".ndjson"):
        return _load_jsonl(path)
    if suffix == ".json":
        return _load_json(path)
    raise ValueError(
        "unsupported file type '" + suffix + "'. Use .csv, .jsonl, or .json."
    )


def _load_csv(path: Path) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        columns = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    return "csv", rows, columns


def _load_jsonl(path: Path) -> Tuple[str, List[Dict[str, Any]], List[str]]:
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
            for k in obj:
                if k not in seen:
                    seen.add(k)
                    columns.append(k)
    return "jsonl", rows, columns


def _load_json(path: Path) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    with path.open("r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        # Allow a top-level wrapper like {"data": [...]} or {"rows": [...]}.
        for key in ("data", "rows", "records", "examples"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
        else:
            data = [data]
    if not isinstance(data, list):
        raise ValueError("JSON root must be a list of objects (or wrap one).")
    rows: List[Dict[str, Any]] = []
    columns: List[str] = []
    seen = set()
    for obj in data:
        if not isinstance(obj, dict):
            obj = {"value": obj}
        rows.append(obj)
        for k in obj:
            if k not in seen:
                seen.add(k)
                columns.append(k)
    return "json", rows, columns


def _cell_text(value: Any) -> str:
    """Normalize a cell to a string for emptiness/uniqueness checks."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, dict)):
        try:
            return json.dumps(value, sort_keys=True, ensure_ascii=False).strip()
        except (TypeError, ValueError):
            return str(value).strip()
    return str(value).strip()


def _normalize_anchor(text: str) -> str:
    """Collapse case and internal whitespace so near duplicate anchors that
    differ only in casing or spacing fold together. Used to estimate the extra
    collapse beyond exact duplicates."""
    return " ".join(text.split()).casefold()


def _looks_mojibake(text: str) -> bool:
    """Heuristic for a string that was decoded with the wrong codec or carries
    stray control bytes. Conservative: only flags obvious markers."""
    if _REPLACEMENT_CHAR in text:
        return True
    for marker in _MOJIBAKE_MARKERS:
        if marker in text:
            return True
    for ch in text:
        # C0 control characters other than tab, newline, carriage return.
        if ord(ch) < 32 and ch not in "\t\n\r":
            return True
    return False


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------


def lint_dataset(
    path: "str | Path",
    prompt: Optional[str] = None,
    completion: Optional[str] = None,
    context: Optional[Sequence[str]] = None,
) -> LintReport:
    """Lint a dataset for an Adaption ``datasets.run``.

    Args:
        path: CSV, JSONL, or JSON file.
        prompt: name of the prompt/instruction column (anchor candidate).
        completion: name of the completion column (anchor candidate).
        context: context column name(s); metadata, never an anchor.

    At least one of ``prompt`` or ``completion`` must be supplied and must exist
    in the data, because a run needs an anchor. The anchor's uniqueness drives
    the headline dedup-collapse warning.
    """
    p = Path(path)
    report = LintReport(path=str(p))

    if not p.exists():
        report.add(FAIL, "file does not exist")
        return report

    report.encoding = _detect_encoding(p)

    try:
        fmt, rows, columns = _load_rows(p)
    except ValueError as exc:
        report.add(FAIL, str(exc))
        return report
    except (json.JSONDecodeError, csv.Error, UnicodeDecodeError) as exc:
        report.add(FAIL, "could not parse file: " + str(exc))
        return report

    report.fmt = fmt
    report.columns = columns
    report.row_count = len(rows)

    if report.row_count == 0:
        report.add(FAIL, "no rows found")
        return report
    report.add(PASS, "loaded " + str(report.row_count) + " row(s)")

    # --- anchor resolution --------------------------------------------------
    if not prompt and not completion:
        report.add(
            FAIL,
            "no anchor specified. A run needs at least a 'prompt' or a "
            "'completion' column. Pass prompt=... or completion=...",
        )
        return report

    anchor_kind = ""
    anchor_col = ""
    if prompt:
        if prompt in columns:
            anchor_kind, anchor_col = "prompt", prompt
        else:
            report.add(FAIL, "prompt column '" + prompt + "' not found in file")
    if not anchor_col and completion:
        if completion in columns:
            anchor_kind, anchor_col = "completion", completion
        else:
            report.add(
                FAIL, "completion column '" + completion + "' not found in file"
            )

    if not anchor_col:
        # Both requested anchors missing.
        if (prompt and prompt not in columns) or (
            completion and completion not in columns
        ):
            return report
        report.add(FAIL, "could not resolve an anchor column")
        return report

    report.anchor = anchor_kind
    report.anchor_column = anchor_col
    if anchor_kind == "completion":
        report.add(
            PASS,
            "completion only anchor: platform will synthesize prompts from "
            "these high quality answers",
        )

    # --- uniqueness on the anchor (headline check) -------------------------
    anchor_values = [_cell_text(r.get(anchor_col)) for r in rows]
    non_empty_anchor = [v for v in anchor_values if v]
    empty_anchor = report.row_count - len(non_empty_anchor)
    unique_vals = len(set(non_empty_anchor))
    report.unique_anchor_values = unique_vals
    report.empty_anchor_cells = empty_anchor
    # Rows dedup would remove: duplicates among non-empty plus empty anchors.
    report.duplicate_rows = report.row_count - unique_vals

    # Near duplicate estimate: how many more rows collapse once we normalize case
    # and whitespace, beyond the exact-duplicate count already reported above.
    normalized_anchor = [_normalize_anchor(v) for v in non_empty_anchor]
    unique_norm = len(set(normalized_anchor))
    report.unique_anchor_values_normalized = unique_norm
    report.near_duplicate_rows = max(0, unique_vals - unique_norm)

    if empty_anchor:
        report.add(
            FAIL,
            str(empty_anchor)
            + " row(s) have an empty or whitespace only "
            + anchor_kind
            + " anchor. These cannot be adapted. Fix: drop these rows or fill "
            "the "
            + anchor_kind
            + " column before the run.",
        )

    rate = report.unique_anchor_rate
    collapsed = report.duplicate_rows
    if unique_vals <= 1 and report.row_count > 1:
        report.add(
            FAIL,
            "anchor is constant across all rows. Deduplication (always applied, "
            "keyed on the prompt) will collapse this to a single row. If the real "
            "variety lives in context columns, this is the classic templated prompt "
            "trap - move variety into the prompt or use a completion anchor.",
        )
    elif unique_norm <= 1 and report.row_count > 1:
        # Distinct raw values but they fold to one after case/whitespace
        # normalization. Dedup keys on the raw prompt, but this is still a sign
        # the variety is cosmetic and the run will barely learn anything.
        report.add(
            FAIL,
            "anchor values differ only by case or whitespace; after normalizing "
            "they collapse to a single distinct "
            + anchor_kind
            + ". Fix: introduce real semantic variety, not just formatting.",
        )
    elif (
        report.row_count >= 10
        and (unique_norm / report.row_count) <= (1.0 - NEAR_CONSTANT_THRESHOLD)
    ):
        # Not literally constant, but almost: a handful of distinct anchors
        # repeated across the whole file. This collapses to those few rows under
        # dedup, so a full run buys almost nothing.
        report.add(
            FAIL,
            "anchor is almost entirely identical: only "
            + str(unique_norm)
            + " distinct value(s) (normalized) across "
            + str(report.row_count)
            + " rows. Dedup will collapse this to roughly "
            + str(unique_norm)
            + " row(s). Fix: add real variety to the "
            + anchor_kind
            + " column, or use a completion anchor if the answers differ.",
        )
    elif rate < 0.5:
        report.add(
            WARN,
            "only "
            + _pct(rate)
            + " of anchors are unique ("
            + str(unique_vals)
            + " unique / "
            + str(report.row_count)
            + "). Dedup (keyed on the prompt) will collapse about "
            + str(collapsed)
            + " row(s). Templated prompts whose variety is only in context "
            "columns collapse here - check before paying for a full run.",
        )
    elif rate < 0.95:
        report.add(
            WARN,
            _pct(rate)
            + " of anchors are unique; dedup will drop roughly "
            + str(collapsed)
            + " near duplicate row(s).",
        )
    else:
        report.add(
            PASS,
            _pct(rate) + " of anchors are unique; dedup impact is minimal",
        )

    # --- near duplicate anchors (case/whitespace) --------------------------
    # Beyond exact duplicates: anchors that are the same once you fold case and
    # collapse whitespace. Dedup keys on the raw prompt so these survive, but
    # they add little and often indicate sloppy templating.
    if report.near_duplicate_rows > 0 and unique_norm > 1:
        report.add(
            WARN,
            str(report.near_duplicate_rows)
            + " additional anchor(s) are near duplicates (identical after "
            "normalizing case and whitespace): "
            + str(unique_vals)
            + " exact unique fold to "
            + str(unique_norm)
            + " normalized unique. Fix: dedupe these yourself so the run learns "
            "from genuinely distinct examples.",
        )

    # --- fill rates + empties ----------------------------------------------
    tracked: List[str] = [anchor_col]
    if context:
        tracked.extend([c for c in context if c not in tracked])
    # Also surface any other columns at a glance.
    for c in columns:
        if c not in tracked:
            tracked.append(c)

    total_empty = 0
    for col in tracked:
        present = 0
        for r in rows:
            if _cell_text(r.get(col)):
                present += 1
        fs = FieldStat(name=col, present=present, total=report.row_count)
        report.field_stats.append(fs)
        total_empty += report.row_count - present
    report.empty_cells = total_empty

    # Validate context columns exist and warn on poor fill.
    if context:
        for c in context:
            if c not in columns:
                report.add(WARN, "context column '" + c + "' not found in file")
                continue
            fs = next((f for f in report.field_stats if f.name == c), None)
            if fs and fs.fill_rate < 0.5:
                report.add(
                    WARN,
                    "context column '"
                    + c
                    + "' is only "
                    + _pct(fs.fill_rate)
                    + " filled",
                )

    if completion and completion in columns and anchor_kind != "completion":
        fs = next((f for f in report.field_stats if f.name == completion), None)
        if fs and fs.fill_rate < 1.0:
            report.add(
                WARN,
                "completion column '"
                + completion
                + "' is "
                + _pct(fs.fill_rate)
                + " filled; empty completions will be generated by the platform",
            )

    # --- very long completions ---------------------------------------------
    # Resolve the column that holds the target text: an explicit completion
    # column, or the anchor itself when the anchor is a completion.
    completion_col = ""
    if completion and completion in columns:
        completion_col = completion
    elif anchor_kind == "completion":
        completion_col = anchor_col
    if completion_col:
        long_rows = 0
        longest = 0
        for r in rows:
            length = len(_cell_text(r.get(completion_col)))
            if length > longest:
                longest = length
            if length > LONG_COMPLETION_CHARS:
                long_rows += 1
        report.long_completion_rows = long_rows
        report.max_completion_chars = longest
        if long_rows:
            report.add(
                WARN,
                str(long_rows)
                + " completion(s) exceed "
                + str(LONG_COMPLETION_CHARS)
                + " characters (longest "
                + str(longest)
                + "). Very long answers can dominate training or be truncated. "
                "Fix: split or summarize them so each target is a focused answer.",
            )

    # --- mixed or suspicious encodings -------------------------------------
    # We read every file utf-8-sig, so a BOM is handled. This catches content
    # that was decoded with the wrong codec upstream (mojibake) or carries raw
    # control bytes - both survive a clean utf-8 read and poison the corpus.
    suspicious = 0
    for r in rows:
        flagged = False
        for value in r.values():
            text = _cell_text(value)
            if text and _looks_mojibake(text):
                flagged = True
                break
        if flagged:
            suspicious += 1
    report.suspicious_encoding_rows = suspicious
    if suspicious:
        report.add(
            WARN,
            str(suspicious)
            + " row(s) contain replacement chars, mojibake (e.g. 'Ã©' for 'e' "
            "with accent), or control bytes. This usually means the source was "
            "decoded with the wrong codec before it reached this file. Fix: "
            "export the source again as clean UTF-8 and lint it again.",
        )

    return report
