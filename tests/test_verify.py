"""Tests for adaption_kit.verify.verify_dataset and its helpers.

These build tiny .jsonl / .csv files under tmp_path and assert the real status
and counts. The math tests are deliberately restricted to answer pairs that are
decidable by the string and numeric tiers so they pass whether or not sympy is
installed (CI core has no sympy). One symbolic case is guarded on
``verify._HAVE_SYMPY``.

Code verification runs real, short-lived subprocesses, so the candidate
functions are kept tiny.
"""

from __future__ import annotations

import json

from conftest import write_csv, write_jsonl

from adaption_kit import verify
from adaption_kit.verify import (
    VerifyReport,
    answers_equivalent,
    code_passes,
    extract_boxed,
    extract_final_answer,
    verify_dataset,
)


# --------------------------------------------------------------------- helpers
def test_extract_boxed_returns_last_and_handles_nested_braces():
    assert extract_boxed(r"the answer is \boxed{42}.") == "42"
    # Last boxed wins.
    assert extract_boxed(r"\boxed{1} then \boxed{2}") == "2"
    # Nested braces are balanced, not truncated at the first close.
    assert extract_boxed(r"\boxed{\frac{1}{2}}") == r"\frac{1}{2}"
    assert extract_boxed("no box here") is None


def test_extract_final_answer_prefers_boxed_then_hash():
    assert extract_final_answer(r"work \boxed{7}") == "7"
    assert extract_final_answer("a\nb\n#### 13") == "13"


def test_answers_equivalent_numeric_and_string_tiers():
    # Exact string match.
    assert answers_equivalent("42", "42")
    # Numeric / fraction equality via the numeric tier (no sympy needed).
    assert answers_equivalent("0.5", "1/2")
    # Clear mismatch.
    assert not answers_equivalent("42", "43")
    # Missing values never equate.
    assert not answers_equivalent(None, "1")
    assert not answers_equivalent("1", None)


# ------------------------------------------------------------------------ math
def test_math_happy_path_counts_verified_and_failed(tmp_path):
    """Boxed answers that match gold verify; one that disagrees fails."""
    src = write_jsonl(
        tmp_path / "math.jsonl",
        [
            # boxed 42 == gold 42 -> verified
            {"worked_solution": r"so the total is \boxed{42}.", "gold": "42"},
            # boxed 1/2 == gold 0.5 via numeric tier -> verified
            {"worked_solution": r"therefore \boxed{1/2}.", "gold": "0.5"},
            # boxed 43 != gold 42 -> failed
            {"worked_solution": r"hence \boxed{43}.", "gold": "42"},
        ],
    )

    report = verify_dataset(src, kind="math", completion="worked_solution", gold="gold")

    assert isinstance(report, VerifyReport)
    assert report.row_count == 3
    assert report.verified == 2
    assert report.failed == 1
    assert report.unverifiable == 0
    assert report.verify_rate == 2 / 3


def test_math_symbolic_case_only_when_sympy_available(tmp_path):
    """A symbolic-only pair (sqrt forms) verifies only when sympy is present."""
    src = write_jsonl(
        tmp_path / "sym.jsonl",
        [
            {"worked_solution": r"\boxed{\sqrt{4}}", "gold": "2"},
        ],
    )

    report = verify_dataset(src, kind="math", completion="worked_solution", gold="gold")

    if verify._HAVE_SYMPY:
        assert report.verified == 1
        assert report.failed == 0
    else:
        # Without sympy the symbolic tier is skipped, so it reads as failed.
        assert report.verified == 0
        assert report.failed == 1


def test_math_missing_gold_is_unverifiable(tmp_path):
    """A row whose gold cell is empty is counted unverifiable, not verified."""
    src = write_jsonl(
        tmp_path / "missing_gold.jsonl",
        [
            {"worked_solution": r"\boxed{42}", "gold": "42"},
            {"worked_solution": r"\boxed{99}", "gold": ""},
        ],
    )

    report = verify_dataset(src, kind="math", completion="worked_solution", gold="gold")

    assert report.verified == 1
    assert report.failed == 0
    assert report.unverifiable == 1


# ------------------------------------------------------------------------ code
def _fenced(body: str) -> str:
    return "```python\n" + body + "\n```"


def test_code_happy_path_counts_verified_and_failed(tmp_path):
    """A solution that passes its tests verifies; a wrong one fails."""
    passing = _fenced("def add(a, b):\n    return a + b")
    failing = _fenced("def add(a, b):\n    return a - b")
    src = write_jsonl(
        tmp_path / "code.jsonl",
        [
            {"output": passing, "unit_tests": json.dumps(["assert add(1, 2) == 3"])},
            {"output": failing, "unit_tests": json.dumps(["assert add(1, 2) == 3"])},
        ],
    )

    report = verify_dataset(src, kind="code", completion="output", tests="unit_tests")

    assert report.row_count == 2
    assert report.verified == 1
    assert report.failed == 1
    assert report.unverifiable == 0


def test_code_passes_helper_direct():
    code = _fenced("def add(a, b):\n    return a + b")
    assert code_passes(code, ["assert add(1, 2) == 3"])
    assert not code_passes(code, ["assert add(1, 2) == 99"])


def test_code_missing_tests_column_fails(tmp_path):
    """No resolvable tests column -> hard FAIL."""
    src = write_jsonl(
        tmp_path / "no_tests.jsonl",
        [
            {"output": _fenced("def add(a, b):\n    return a + b")},
        ],
    )

    report = verify_dataset(src, kind="code", completion="output")

    assert report.status == "FAIL"


# ------------------------------------------------------------------------- out
def test_out_file_contains_only_verified_rows(tmp_path):
    """--out writes exactly the verified rows."""
    src = write_jsonl(
        tmp_path / "math_out.jsonl",
        [
            {"worked_solution": r"\boxed{42}", "gold": "42"},
            {"worked_solution": r"\boxed{43}", "gold": "42"},
            {"worked_solution": r"\boxed{7}", "gold": "7"},
        ],
    )
    out = tmp_path / "verified.jsonl"

    report = verify_dataset(
        src, kind="math", completion="worked_solution", gold="gold", out=out
    )

    assert report.verified == 2
    assert out.exists()
    written = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(written) == report.verified
    golds = {row["gold"] for row in written}
    assert golds == {"42", "7"}


# ----------------------------------------------------------------- fail paths
def test_nonexistent_file_fails(tmp_path):
    report = verify_dataset(tmp_path / "nope.jsonl", kind="math")
    assert report.status == "FAIL"


def test_bad_kind_fails(tmp_path):
    src = write_csv(
        tmp_path / "any.csv",
        ["worked_solution", "gold"],
        [{"worked_solution": r"\boxed{1}", "gold": "1"}],
    )
    report = verify_dataset(src, kind="logic")
    assert report.status == "FAIL"
