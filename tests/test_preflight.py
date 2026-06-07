"""Tests for adaption_kit.preflight.lint_dataset.

The headline behavior is the dedup collapse warning: Adaption always applies
deduplication keyed on the prompt, so an anchor that is the same value on every
row collapses to a single row. These tests build their own tiny files under
tmp_path and assert the real status and counts.
"""

from __future__ import annotations

from conftest import write_csv

from adaption_kit.preflight import (
    FAIL,
    PASS,
    WARN,
    LintReport,
    lint_dataset,
)


def test_clean_unique_completion_only_passes(tmp_path):
    """A completion only file with all unique answers should PASS."""
    src = write_csv(
        tmp_path / "clean.csv",
        ["completion"],
        [
            {"completion": "Our SPF 50 serum absorbs in seconds."},
            {"completion": "This mascara lifts and separates every lash."},
            {"completion": "A matte lipstick that lasts through dinner."},
            {"completion": "Lightweight moisturizer for oily skin."},
        ],
    )

    report = lint_dataset(src, completion="completion")

    assert isinstance(report, LintReport)
    assert report.status == PASS
    assert report.anchor == "completion"
    assert report.anchor_column == "completion"
    assert report.row_count == 4
    assert report.unique_anchor_values == 4
    assert report.duplicate_rows == 0


def test_constant_anchor_collapses_to_one_row(tmp_path):
    """A prompt that is identical on every row is the dedup collapse trap.

    With more than one row and a single unique anchor value the report must
    FAIL (or at the very least strongly WARN); the package raises this to FAIL.
    """
    same_prompt = "Write a product description."
    src = write_csv(
        tmp_path / "templated.csv",
        ["prompt", "product"],
        [
            {"prompt": same_prompt, "product": "serum"},
            {"prompt": same_prompt, "product": "mascara"},
            {"prompt": same_prompt, "product": "lipstick"},
            {"prompt": same_prompt, "product": "toner"},
        ],
    )

    report = lint_dataset(src, prompt="prompt", context=["product"])

    assert report.status in (FAIL, WARN)
    # The package treats a constant anchor as a hard FAIL.
    assert report.status == FAIL
    assert report.unique_anchor_values == 1
    # Three of the four rows would be collapsed by dedup.
    assert report.duplicate_rows == report.row_count - 1


def test_several_duplicate_anchors_warn_with_count(tmp_path):
    """Many but not total duplicates should WARN and report a collapse count."""
    src = write_csv(
        tmp_path / "dupy.csv",
        ["prompt"],
        [
            {"prompt": "Describe the serum."},
            {"prompt": "Describe the serum."},
            {"prompt": "Describe the serum."},
            {"prompt": "Describe the mascara."},
        ],
    )

    report = lint_dataset(src, prompt="prompt")

    # 2 unique out of 4 rows -> 50 percent, below the package's thresholds.
    assert report.status == WARN
    assert report.unique_anchor_values == 2
    assert report.duplicate_rows == 2
    # The collapse count is surfaced in at least one WARN message.
    warn_messages = " ".join(msg for level, msg in report.checks if level == WARN)
    assert "2" in warn_messages


def test_bom_file_still_loads(tmp_path):
    """A file written with a UTF-8 BOM (utf-8-sig) must load correctly.

    If the BOM leaked into the first header the 'prompt' column would not be
    found and the anchor would not resolve; a clean load proves utf-8-sig.
    """
    src = write_csv(
        tmp_path / "bom.csv",
        ["prompt", "completion"],
        [
            {"prompt": "Q1", "completion": "A1"},
            {"prompt": "Q2", "completion": "A2"},
            {"prompt": "Q3", "completion": "A3"},
        ],
        bom=True,
    )

    report = lint_dataset(src, prompt="prompt", completion="completion")

    # Header read cleanly: the anchor resolved to the prompt column by name.
    assert report.anchor == "prompt"
    assert report.anchor_column == "prompt"
    assert "prompt" in report.columns
    assert report.columns[0] == "prompt"
    assert report.row_count == 3
    # No parse failure and no missing column FAILs.
    assert report.status in (PASS, WARN)
