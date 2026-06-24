"""decontaminate.py - drop training rows that overlap a benchmark test set.

If a row in your training data also appears (verbatim or near verbatim) in the
held-out test set the platform scores you against, your reported
``improvement_percent`` is inflated and will not survive a second look. This
module flags and removes any training row whose anchor text shares an n-gram with
any benchmark prompt, the standard 8-to-13-gram overlap check used by the data
quality literature.

You supply the benchmark file(s) yourself (e.g. a public GSM8K / MBPP / HumanEval
split, or your own held-out slice). Pure standard library; reads .csv, .jsonl, and
.json with utf-8-sig like the rest of the kit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .preflight import _cell_text, _load_rows  # reuse the shared loader

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
_RANK = {PASS: 0, WARN: 1, FAIL: 2}

DEFAULT_N = 13

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^a-z0-9 ]+")


def _normalize(text: str) -> str:
    text = (text or "").lower()
    text = _PUNCT.sub(" ", text)
    return _WS.sub(" ", text).strip()


def ngrams(text: str, n: int = DEFAULT_N) -> set:
    toks = _normalize(text).split()
    if len(toks) < n:
        # short texts: use the whole thing as a single shingle so exact short
        # duplicates are still caught.
        return {" ".join(toks)} if toks else set()
    return {" ".join(toks[i : i + n]) for i in range(0, len(toks) - n + 1)}


class Decontaminator:
    """Holds the benchmark n-gram set; flags any text that shares one."""

    def __init__(self, n: int = DEFAULT_N) -> None:
        self.n = n
        self.bench: set = set()

    def add_text(self, text: str) -> None:
        self.bench |= ngrams(text, self.n)

    def is_contaminated(self, text: str) -> bool:
        g = ngrams(text, self.n)
        if not g:
            return False
        return not g.isdisjoint(self.bench)


@dataclass
class DecontamReport:
    path: str
    status: str = PASS
    row_count: int = 0
    benchmark_rows: int = 0
    column: str = ""
    n: int = DEFAULT_N
    contaminated: int = 0
    kept: int = 0
    out_path: str = ""
    checks: List = field(default_factory=list)

    def add(self, level: str, message: str) -> None:
        self.checks.append((level, message))
        if _RANK[level] > _RANK[self.status]:
            self.status = level

    def summary(self) -> str:
        lines = [
            "adaption-kit decontamination report",
            "=" * 60,
            "file            : " + self.path,
            "anchor column   : " + (self.column or "(unresolved)"),
            "n-gram size     : " + str(self.n),
            "training rows   : " + str(self.row_count),
            "benchmark rows  : " + str(self.benchmark_rows),
            "contaminated    : " + str(self.contaminated),
            "kept            : " + str(self.kept),
        ]
        if self.out_path:
            lines.append("cleaned file    : " + self.out_path)
        lines.append("")
        lines.append("checks:")
        for level, msg in self.checks:
            lines.append("  [" + level + "] " + msg)
        lines.append("")
        lines.append("RESULT: " + self.status)
        return "\n".join(lines)


def _resolve_column(columns: Sequence[str], requested: Optional[str],
                    fallbacks: Sequence[str]) -> Optional[str]:
    if requested:
        return requested if requested in columns else None
    for f in fallbacks:
        if f in columns:
            return f
    return None


def _write_rows(path: Path, rows: List[Dict[str, Any]], fmt: str) -> None:
    import csv
    import json
    if fmt == "csv":
        cols: List[str] = []
        for r in rows:
            for k in r:
                if k not in cols:
                    cols.append(k)
        with path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    else:  # jsonl
        with path.open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def decontaminate(
    path: "str | Path",
    benchmarks: Sequence["str | Path"],
    column: Optional[str] = None,
    benchmark_column: Optional[str] = None,
    n: int = DEFAULT_N,
    out: Optional["str | Path"] = None,
) -> DecontamReport:
    """Remove training rows overlapping any benchmark prompt.

    Args:
        path: the training dataset (.csv/.jsonl/.json).
        benchmarks: one or more benchmark files to decontaminate against.
        column: anchor column in the training data (default: first of
            prompt/problem/question/instruction/text/input present).
        benchmark_column: anchor column in the benchmark files (same default).
        n: n-gram size (default 13).
        out: if given, write the kept rows here (.csv or .jsonl).
    """
    p = Path(path)
    report = DecontamReport(path=str(p), n=n)
    if not p.exists():
        report.add(FAIL, "file does not exist")
        return report

    fmt, rows, columns = _load_rows(p)
    report.row_count = len(rows)
    anchor_candidates = ("prompt", "problem", "question", "instruction", "text", "input")
    col = _resolve_column(columns, column, anchor_candidates)
    if not col:
        report.add(FAIL, "could not resolve an anchor column; pass --column")
        return report
    report.column = col

    decon = Decontaminator(n=n)
    bench_rows = 0
    for b in benchmarks:
        bp = Path(b)
        if not bp.exists():
            report.add(WARN, "benchmark file not found, skipped: " + str(bp))
            continue
        _, brows, bcols = _load_rows(bp)
        bcol = _resolve_column(bcols, benchmark_column, anchor_candidates)
        if not bcol:
            report.add(WARN, "no anchor column in benchmark " + str(bp) + ", skipped")
            continue
        for r in brows:
            decon.add_text(_cell_text(r.get(bcol)))
        bench_rows += len(brows)
    report.benchmark_rows = bench_rows

    if not decon.bench:
        report.add(FAIL, "no benchmark text loaded; nothing to decontaminate against")
        return report

    kept_rows: List[Dict[str, Any]] = []
    contaminated = 0
    for r in rows:
        if decon.is_contaminated(_cell_text(r.get(col))):
            contaminated += 1
        else:
            kept_rows.append(r)
    report.contaminated = contaminated
    report.kept = len(kept_rows)

    if contaminated == 0:
        report.add(PASS, "no overlap found; dataset is clean against these benchmarks")
    else:
        report.add(
            WARN,
            str(contaminated) + " row(s) overlap the benchmark by a "
            + str(n) + "-gram and were removed. Training on these inflates "
            "improvement_percent. Re-run after removing them.",
        )

    if out:
        outp = Path(out)
        out_fmt = "csv" if outp.suffix.lower() == ".csv" else "jsonl"
        outp.parent.mkdir(parents=True, exist_ok=True)
        _write_rows(outp, kept_rows, out_fmt)
        report.out_path = str(outp)
        report.add(PASS, "wrote " + str(len(kept_rows)) + " clean row(s) -> " + str(outp))

    return report
