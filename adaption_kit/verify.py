"""verify.py - prove rows are CORRECT before you pay to adapt them.

For checkable domains, looking right is not good enough. This command keeps a row
only if it actually checks out, locally and for free, before any credits are spent:

  - math: the final answer the worked solution reaches must be equivalent to a gold
    answer (normalized string, then numeric, then symbolic via sympy if installed).
  - code: the solution must run and pass the unit tests shipped with it. Each
    candidate runs in a fresh, short-lived subprocess with a hard timeout, so a bad
    row can only ever crash its own child, never your machine or the build.

Adapting unverified rows is the most common way beginners burn credits on multiple
tries: you pay to polish data that was wrong to begin with. Filter first, then run.

The symbolic math tier needs sympy (``pip install adaption-devkit[verify]`` or
``pip install sympy``). Without it, math falls back to string + numeric checks and
the report says so. Code verification is pure standard library.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import textwrap
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FTimeout
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from .preflight import _cell_text, _load_rows

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
_RANK = {PASS: 0, WARN: 1, FAIL: 2}

# Run child python processes with no console window on Windows, so verifying a
# whole dataset does not flash a terminal window per row.
_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
_CODE_TIMEOUT = 8  # seconds per candidate

try:  # optional symbolic tier
    from sympy import simplify, sympify  # type: ignore
    _HAVE_SYMPY = True
except Exception:  # pragma: no cover - depends on environment
    _HAVE_SYMPY = False

_EXEC = ThreadPoolExecutor(max_workers=4)


# --------------------------------------------------------------------------- math
def extract_boxed(text: str) -> Optional[str]:
    """Content of the LAST \\boxed{...}, handling nested braces."""
    idx = text.rfind(r"\boxed")
    if idx == -1:
        return None
    i = text.find("{", idx)
    if i == -1:
        return None
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1 : j].strip()
    return None


def extract_final_answer(solution: str) -> Optional[str]:
    b = extract_boxed(solution)
    if b is not None:
        return b
    if "####" in solution:
        return solution.rsplit("####", 1)[1].strip()
    lines = [ln for ln in solution.strip().splitlines() if ln.strip()]
    if not lines:
        return None
    last = lines[-1]
    m = re.search(r"(?:answer is|equals|=)\s*\$?([^\$.]+?)\$?\s*\.?$", last, re.I)
    if m:
        return m.group(1).strip()
    nums = re.findall(r"-?\d[\d,]*\.?\d*", last)
    return nums[-1] if nums else None


_REPL = [
    (r"\left", ""), (r"\right", ""), (r"\,", ""), (r"\!", ""), (r"\;", ""),
    (r"\dfrac", r"\frac"), (r"\tfrac", r"\frac"), (r"\cdot", "*"), (r"\times", "*"),
    (r"^\circ", ""), (r"\%", ""), (r"\$", ""), ("$", ""),
]


def _normalize(s: str) -> str:
    if s is None:
        return ""
    s = s.strip()
    for a, b in _REPL:
        s = s.replace(a, b)
    s = s.strip().rstrip(".")
    s = re.sub(r"\s+", "", s)
    while len(s) >= 2 and s[0] in "({" and s[-1] in ")}":
        s = s[1:-1]
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)
    return s


def _to_sympy_str(s: str) -> str:
    s = s.replace(r"\frac", "frac").strip()
    for _ in range(6):
        new = re.sub(r"frac\{([^{}]*)\}\{([^{}]*)\}", r"((\1)/(\2))", s)
        if new == s:
            break
        s = new
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"sqrt(\1)", s)
    s = re.sub(r"\\sqrt", "sqrt", s)
    s = s.replace("{", "(").replace("}", ")")
    s = s.replace("^", "**").replace("\\pi", "pi").replace("\\", "")
    return s


def _try_float(s: str) -> Optional[float]:
    s = s.strip()
    try:
        return float(s)
    except Exception:
        pass
    m = re.fullmatch(r"\(?\s*(-?\d+\.?\d*)\s*/\s*(-?\d+\.?\d*)\s*\)?", s)
    if m:
        try:
            return float(m.group(1)) / float(m.group(2))
        except Exception:
            return None
    return None


def _sympy_equal(a: str, b: str) -> bool:
    ea, eb = sympify(_to_sympy_str(a)), sympify(_to_sympy_str(b))
    return ea == eb or simplify(ea - eb) == 0


def answers_equivalent(gold: Optional[str], pred: Optional[str], timeout: float = 3.0) -> bool:
    if gold is None or pred is None:
        return False
    ng, npd = _normalize(gold), _normalize(pred)
    if not ng or not npd:
        return False
    if ng == npd:
        return True
    fg, fp = _try_float(ng), _try_float(npd)
    if fg is not None and fp is not None:
        return abs(fg - fp) <= 1e-6 * max(1.0, abs(fg), abs(fp))
    if not _HAVE_SYMPY:
        return False
    try:
        return bool(_EXEC.submit(_sympy_equal, ng, npd).result(timeout=timeout))
    except (FTimeout, Exception):
        return False


# --------------------------------------------------------------------------- code
def extract_code(output: str) -> str:
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", output, re.S)
    return m.group(1).strip() if m else output.strip()


def _coerce_tests(tests: Any) -> List[str]:
    import json
    if isinstance(tests, list):
        return [str(t) for t in tests]
    if isinstance(tests, str):
        s = tests.strip()
        try:
            v = json.loads(s)
            if isinstance(v, list):
                return [str(t) for t in v]
        except Exception:
            pass
        return [s] if s else []
    return []


def code_passes(output: str, tests: Any, setup: str = "") -> bool:
    """True only if the solution runs and passes EVERY assert-style test."""
    code = extract_code(output)
    tests = _coerce_tests(tests)
    if len(code) < 5 or not tests:
        return False
    harness = setup + "\n" + code + "\n\n_p = 0\n"
    for t in tests:
        harness += (
            "try:\n" + textwrap.indent(t.strip() or "pass", "    ")
            + "\n    _p += 1\nexcept Exception:\n    pass\n"
        )
    harness += "print('PASSED', _p)\n"
    with tempfile.TemporaryDirectory() as d:
        fp = os.path.join(d, "cand.py")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(harness)
        try:
            r = subprocess.run(
                [sys.executable, fp], capture_output=True, text=True,
                timeout=_CODE_TIMEOUT, cwd=d, creationflags=_NO_WINDOW,
            )
        except Exception:
            return False
    m = re.search(r"PASSED (\d+)", r.stdout or "")
    return bool(m) and int(m.group(1)) == len(tests)


# --------------------------------------------------------------------------- report
@dataclass
class VerifyReport:
    path: str
    kind: str
    status: str = PASS
    row_count: int = 0
    verified: int = 0
    failed: int = 0
    unverifiable: int = 0  # missing gold/tests
    out_path: str = ""
    sympy_available: bool = _HAVE_SYMPY
    checks: List = field(default_factory=list)

    def add(self, level: str, message: str) -> None:
        self.checks.append((level, message))
        if _RANK[level] > _RANK[self.status]:
            self.status = level

    @property
    def verify_rate(self) -> float:
        base = self.verified + self.failed
        return self.verified / base if base else 0.0

    def summary(self) -> str:
        lines = [
            "adaption-kit verification report",
            "=" * 60,
            "file          : " + self.path,
            "domain        : " + self.kind,
            "rows          : " + str(self.row_count),
            "verified      : " + str(self.verified),
            "failed check  : " + str(self.failed),
            "unverifiable  : " + str(self.unverifiable) + " (no gold/tests to check)",
            "verify rate   : " + str(round(self.verify_rate * 100, 1)) + "%",
        ]
        if self.kind == "math" and not self.sympy_available:
            lines.append("note          : sympy not installed; symbolic check skipped "
                         "(pip install sympy). Some correct rows may read as failed.")
        if self.out_path:
            lines.append("verified file : " + self.out_path)
        lines.append("")
        lines.append("checks:")
        for level, msg in self.checks:
            lines.append("  [" + level + "] " + msg)
        lines.append("")
        lines.append("RESULT: " + self.status)
        return "\n".join(lines)


def _pick(columns, requested, fallbacks):
    if requested:
        return requested if requested in columns else None
    for f in fallbacks:
        if f in columns:
            return f
    return None


def verify_dataset(
    path: "str | Path",
    kind: str,
    completion: Optional[str] = None,
    gold: Optional[str] = None,
    tests: Optional[str] = None,
    out: Optional["str | Path"] = None,
) -> VerifyReport:
    """Verify each row and (optionally) write only the rows that pass.

    Args:
        path: dataset (.csv/.jsonl/.json).
        kind: "math" or "code".
        completion: the worked-solution / code column.
        gold: (math) the gold-answer column. If absent, the answer is extracted
            from the completion and only checked for parseability.
        tests: (code) the column holding the unit tests (list or JSON string).
        out: if given, write only verified rows here.
    """
    p = Path(path)
    report = VerifyReport(path=str(p), kind=kind)
    if not p.exists():
        report.add(FAIL, "file does not exist")
        return report
    if kind not in ("math", "code"):
        report.add(FAIL, "kind must be 'math' or 'code'")
        return report

    fmt, rows, columns = _load_rows(p)
    report.row_count = len(rows)

    comp = _pick(columns, completion, ("completion", "worked_solution", "solution", "output", "answer"))
    if not comp:
        report.add(FAIL, "could not resolve a completion column; pass --completion")
        return report

    kept: List[dict] = []
    if kind == "math":
        gcol = _pick(columns, gold, ("gold", "expected_answer", "answer", "final_answer"))
        for r in rows:
            sol = _cell_text(r.get(comp))
            gold_val = _cell_text(r.get(gcol)) if gcol else extract_final_answer(sol)
            pred = extract_final_answer(sol)
            if not gold_val:
                report.unverifiable += 1
                continue
            if answers_equivalent(gold_val, pred):
                report.verified += 1
                kept.append(r)
            else:
                report.failed += 1
    else:  # code
        tcol = _pick(columns, tests, ("tests", "unit_tests", "test_list", "test"))
        if not tcol:
            report.add(FAIL, "could not resolve a tests column; pass --tests")
            return report
        for r in rows:
            sol = _cell_text(r.get(comp))
            t = r.get(tcol)
            if not t:
                report.unverifiable += 1
                continue
            if code_passes(sol, t):
                report.verified += 1
                kept.append(r)
            else:
                report.failed += 1

    base = report.verified + report.failed
    if base == 0:
        report.add(FAIL, "no rows could be checked (no gold/tests found)")
    elif report.verify_rate >= 0.95:
        report.add(PASS, str(round(report.verify_rate * 100, 1)) + "% of checkable rows verified")
    else:
        report.add(
            WARN,
            str(report.failed) + " row(s) did NOT verify and should be dropped before "
            "you spend credits. Keep only the " + str(report.verified) + " that passed.",
        )
    if report.unverifiable:
        report.add(WARN, str(report.unverifiable) + " row(s) had no gold answer / tests "
                   "to check against; they were not counted as verified.")

    if out:
        import json
        import csv
        outp = Path(out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        if outp.suffix.lower() == ".csv":
            cols: List[str] = []
            for r in kept:
                for k in r:
                    if k not in cols:
                        cols.append(k)
            with outp.open("w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=cols)
                w.writeheader()
                w.writerows(kept)
        else:
            with outp.open("w", encoding="utf-8") as fh:
                for r in kept:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        report.out_path = str(outp)
        report.add(PASS, "wrote " + str(len(kept)) + " verified row(s) -> " + str(outp))

    return report
