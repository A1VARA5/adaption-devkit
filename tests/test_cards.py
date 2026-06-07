"""Tests for adaption_kit.cards.

Covers Kaggle tag validation against the KAGGLE_VALID_TAGS surface and the
dataset card generator. No files needed; these are pure string functions.
"""

from __future__ import annotations

import pytest

from adaption_kit.cards import (
    KAGGLE_VALID_TAGS,
    InvalidKaggleTag,
    generate_dataset_card,
    validate_kaggle_tags,
)


def test_valid_kaggle_tags_pass():
    """Tags drawn from the accepted taxonomy are returned cleaned."""
    # Use real entries from the package's own valid set.
    tags = [KAGGLE_VALID_TAGS[0], KAGGLE_VALID_TAGS[1]]
    cleaned = validate_kaggle_tags(tags)
    assert cleaned == [KAGGLE_VALID_TAGS[0], KAGGLE_VALID_TAGS[1]]


def test_valid_kaggle_tags_are_lowercased_and_deduped():
    """Case is normalized and duplicates are dropped."""
    tag = KAGGLE_VALID_TAGS[0]
    cleaned = validate_kaggle_tags([tag.upper(), tag])
    assert cleaned == [tag]


def test_invalid_kaggle_tag_rejected():
    """A tag outside the taxonomy raises InvalidKaggleTag."""
    bad = "not-a-real-kaggle-tag"
    assert bad not in KAGGLE_VALID_TAGS
    with pytest.raises(InvalidKaggleTag):
        validate_kaggle_tags([bad])


def test_generate_dataset_card_is_non_empty_string():
    """The dataset card generator returns a non empty markdown string."""
    card = generate_dataset_card(
        title="BrandVoice Marketing Set",
        summary="Adapted marketing copy for a consistent brand voice.",
        tags=[KAGGLE_VALID_TAGS[0]],
        improvement_percent=12.5,
        row_count=200,
    )

    assert isinstance(card, str)
    assert card.strip()
    # Front matter and the title both land in the output.
    assert card.startswith("---")
    assert "BrandVoice Marketing Set" in card
