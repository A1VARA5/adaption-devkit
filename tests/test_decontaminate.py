"""Tests for adaption_kit.decontaminate.decontaminate and its helpers.

These build tiny training/benchmark files under tmp_path. Contamination is
triggered by sharing a phrase that is clearly longer than the 13-token n-gram
window, so the default 13-gram overlap check fires; unrelated rows are kept.
"""

from __future__ import annotations

import json

from conftest import write_jsonl

from adaption_kit.decontaminate import (
    DecontamReport,
    Decontaminator,
    decontaminate,
    ngrams,
)

# A phrase well over 13 tokens so a 13-gram window is shared verbatim.
SHARED = (
    "a train leaves the station traveling north at forty miles per hour "
    "for three hours then stops"
)


# --------------------------------------------------------------------- helpers
def test_ngrams_basic_behavior():
    # Punctuation stripped, lowercased; a 3-gram over 5 tokens -> 3 shingles.
    grams = ngrams("The Quick Brown Fox Jumps!", n=3)
    assert grams == {"the quick brown", "quick brown fox", "brown fox jumps"}
    # Text shorter than n collapses to a single whole-text shingle.
    assert ngrams("two words", n=13) == {"two words"}
    # Empty text -> empty set.
    assert ngrams("", n=13) == set()


def test_decontaminator_is_contaminated_true_and_false():
    decon = Decontaminator(n=13)
    decon.add_text(SHARED + " somewhere far away beyond the river and the hills")
    assert decon.is_contaminated("Question: " + SHARED + " how far did it travel?")
    assert not decon.is_contaminated(
        "an entirely different sentence about baking sourdough bread at home"
    )


# ----------------------------------------------------------------- end to end
def test_contaminated_removed_unrelated_kept(tmp_path):
    train = write_jsonl(
        tmp_path / "train.jsonl",
        [
            {"prompt": "Word problem: " + SHARED + " what is its average speed?"},
            {"prompt": "Describe a lightweight moisturizer for oily combination skin."},
        ],
    )
    bench = write_jsonl(
        tmp_path / "bench.jsonl",
        [
            {"prompt": SHARED + " calculate the total distance covered overall."},
        ],
    )

    report = decontaminate(train, [bench])

    assert isinstance(report, DecontamReport)
    assert report.status == "WARN"  # contamination present -> WARN
    assert report.row_count == 2
    assert report.benchmark_rows == 1
    assert report.contaminated == 1
    assert report.kept == 1
    assert report.column == "prompt"


def test_out_writes_kept_rows(tmp_path):
    train = write_jsonl(
        tmp_path / "train.jsonl",
        [
            {"prompt": "Q: " + SHARED + " find the speed.", "id": "dirty"},
            {"prompt": "How do I store fresh basil so it lasts longer?", "id": "clean"},
        ],
    )
    bench = write_jsonl(
        tmp_path / "bench.jsonl",
        [{"prompt": SHARED + " and then it returns home."}],
    )
    out = tmp_path / "clean.jsonl"

    report = decontaminate(train, [bench], out=out)

    assert report.kept == 1
    assert out.exists()
    written = [
        json.loads(line)
        for line in out.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(written) == report.kept
    assert written[0]["id"] == "clean"


def test_explicit_column_resolution_across_differing_names(tmp_path):
    """Training uses 'problem', benchmark uses 'question'; pass both explicitly."""
    train = write_jsonl(
        tmp_path / "train.jsonl",
        [
            {"problem": "Setup: " + SHARED + " determine the elapsed time."},
            {"problem": "An unrelated note about choosing a good running shoe size."},
        ],
    )
    bench = write_jsonl(
        tmp_path / "bench.jsonl",
        [{"question": SHARED + " then it parks for the night."}],
    )

    report = decontaminate(
        train, [bench], column="problem", benchmark_column="question"
    )

    assert report.column == "problem"
    assert report.contaminated == 1
    assert report.kept == 1


def test_no_anchor_column_fails(tmp_path):
    train = write_jsonl(
        tmp_path / "train.jsonl",
        [{"foo": "bar", "baz": "qux"}],
    )
    bench = write_jsonl(
        tmp_path / "bench.jsonl",
        [{"prompt": SHARED}],
    )

    report = decontaminate(train, [bench])

    assert report.status == "FAIL"


def test_nonexistent_file_fails(tmp_path):
    report = decontaminate(tmp_path / "nope.jsonl", [tmp_path / "bench.jsonl"])
    assert report.status == "FAIL"
