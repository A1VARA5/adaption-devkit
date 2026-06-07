"""Tests for adaption_kit.suggest.suggest_mapping.

These confirm the anchor recommendation for the two cases the docs care about:
a single answer column becomes completion only, and an instruction plus a
response column become both. Files are built under tmp_path.
"""

from __future__ import annotations

from conftest import write_csv

from adaption_kit.suggest import SuggestResult, suggest_mapping


def test_answer_only_recommends_completion(tmp_path):
    """A file with only an answer column is a high quality answers corpus."""
    src = write_csv(
        tmp_path / "answers.csv",
        ["answer"],
        [
            {"answer": "Our serum hydrates without a greasy finish."},
            {"answer": "The mascara is smudge proof for twelve hours."},
            {"answer": "This toner balances oily and dry zones alike."},
            {"answer": "A balm that doubles as an overnight mask."},
        ],
    )

    result = suggest_mapping(src)

    assert isinstance(result, SuggestResult)
    assert result.anchor == "completion"
    assert result.confident is True
    assert result.completion_col == "answer"
    assert result.prompt_col is None
    assert result.mapping() == {"completion": "answer"}


def test_completion_column_recommends_completion(tmp_path):
    """A single 'completion' header is also recommended as completion only."""
    src = write_csv(
        tmp_path / "completion.csv",
        ["completion"],
        [
            {"completion": "First high quality answer here."},
            {"completion": "Second distinct answer here."},
            {"completion": "Third distinct answer here."},
        ],
    )

    result = suggest_mapping(src)

    assert result.anchor == "completion"
    assert result.completion_col == "completion"
    assert result.mapping() == {"completion": "completion"}


def test_instruction_and_response_recommends_both(tmp_path):
    """An instruction column plus a response column maps to both."""
    src = write_csv(
        tmp_path / "pairs.csv",
        ["instruction", "response"],
        [
            {
                "instruction": "Write a tagline for a sunscreen.",
                "response": "Block the rays, keep the play.",
            },
            {
                "instruction": "Write a tagline for a mascara.",
                "response": "Lashes that speak before you do.",
            },
            {
                "instruction": "Write a tagline for a lip balm.",
                "response": "Soft lips, no slips.",
            },
        ],
    )

    result = suggest_mapping(src)

    assert result.anchor == "both"
    assert result.confident is True
    assert result.prompt_col == "instruction"
    assert result.completion_col == "response"
    mapping = result.mapping()
    assert mapping.get("prompt") == "instruction"
    assert mapping.get("completion") == "response"
