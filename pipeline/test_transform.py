"""Tests for transform script."""

import pandas as pd

from transform import (
    clean_categorical_value,
    clean_list_value,
    clean_tag_list,
    clean_text_value,
    dedupe_list,
    filter_tags,
    sort_tags,
    transform,
)

VERDICTS = ["supported", "contradicted", "missing/mixed context", "unclear"]


def test_clean_list_value_keeps_a_list_as_is():
    """A real list is returned unchanged."""
    assert clean_list_value(["a", "b"]) == ["a", "b"]


def test_clean_list_value_converts_none_to_empty_list():
    """None becomes an empty list."""
    assert not clean_list_value(None)


def test_clean_list_value_converts_non_list_to_empty_list():
    """A non-list value becomes an empty list."""
    assert not clean_list_value("not a list")


def test_clean_text_value_strips_whitespace():
    """Leading/trailing whitespace is stripped from a string."""
    assert clean_text_value("  hello  ") == "hello"


def test_clean_text_value_converts_none_to_empty_string():
    """None becomes an empty string."""
    assert clean_text_value(None) == ""


def test_clean_text_value_converts_non_string_to_empty_string():
    """A non-string value becomes an empty string."""
    assert clean_text_value(123) == ""


def test_filter_tags_removes_excluded_tags():
    """Tags in the exclude list are removed."""
    tags = ["fact-checking", "economy", "inflation"]

    result = filter_tags(tags, exclude=["fact-checking"])

    assert result == ["economy", "inflation"]


def test_filter_tags_limits_to_five():
    """No more than five tags are returned."""
    tags = ["a", "b", "c", "d", "e", "f", "g"]

    result = filter_tags(tags, exclude=[])

    assert result == ["a", "b", "c", "d", "e"]


def test_filter_tags_is_case_insensitive_for_exclusions():
    """Exclusions match regardless of casing."""
    tags = ["Fact-Checking", "economy"]

    result = filter_tags(tags, exclude=["fact-checking"])

    assert result == ["economy"]


def test_filter_tags_accepts_custom_exclude_list():
    """A caller-supplied exclude list is respected."""
    tags = ["news", "economy", "inflation"]

    result = filter_tags(tags, exclude=["news"])

    assert result == ["economy", "inflation"]


def test_filter_tags_handles_empty_list():
    """An empty input returns an empty result."""
    assert not filter_tags([], exclude=[])


def test_filter_tags_defaults_to_no_exclusions():
    """With no exclude list given, nothing is filtered out."""
    tags = ["economy", "inflation"]

    result = filter_tags(tags)

    assert result == ["economy", "inflation"]


def test_clean_categorical_value_keeps_valid_value():
    """A valid value is returned lowercased."""
    assert clean_categorical_value("supported", VERDICTS) == "supported"


def test_clean_categorical_value_converts_invalid_value_to_unknown():
    """A value not in the allowed list becomes 'unknown'."""
    assert clean_categorical_value("nonsense", VERDICTS) == "unknown"


def test_clean_categorical_value_converts_none_to_unknown():
    """None becomes 'unknown'."""
    assert clean_categorical_value(None, VERDICTS) == "unknown"


def test_clean_categorical_value_is_case_insensitive():
    """Matching against the allowed list ignores casing."""
    assert clean_categorical_value("Contradicted", VERDICTS) == "contradicted"


def test_dedupe_list_removes_exact_duplicates():
    """Exact duplicate values are removed."""
    assert dedupe_list(["UK", "UK", "ONS"]) == ["UK", "ONS"]


def test_dedupe_list_is_case_insensitive():
    """Differently-cased duplicates are treated as the same value."""
    assert dedupe_list(["UK", "uk", "ONS"]) == ["UK", "ONS"]


def test_dedupe_list_preserves_order():
    """The first occurrence of each value keeps its original position."""
    assert dedupe_list(["b", "a", "b", "c"]) == ["b", "a", "c"]


def test_dedupe_list_handles_empty_list():
    """An empty input returns an empty result."""
    assert not dedupe_list([])


def test_sort_tags_sorts_alphabetically():
    """Tags are returned in alphabetical order."""
    assert sort_tags(["inflation", "economy", "finance"]) == ["economy", "finance", "inflation"]


def test_sort_tags_is_case_insensitive():
    """Sorting ignores casing."""
    assert sort_tags(["Zebra", "apple"]) == ["apple", "Zebra"]


def test_sort_tags_handles_empty_list():
    """An empty input returns an empty result."""
    assert not sort_tags([])


def test_clean_tag_list_dedupes_filters_and_sorts():
    """clean_tag_list combines dedupe, filter, and sort in one step."""
    tags = ["fact-checking", "Inflation", "economy", "inflation"]

    result = clean_tag_list(tags, exclude=["fact-checking"])

    assert result == ["economy", "Inflation"]


def test_clean_tag_list_handles_non_list_input():
    """A non-list value is treated as an empty tag list."""
    assert not clean_tag_list(None, exclude=[])


def test_transform_produces_clean_dataframe():
    """transform() cleans every column of a raw handler_verify_claim.py record."""
    records = [
        {
            "claim": "  The UK inflation rate rose to 4% in 2025.  ",
            "entities": ["UK", "uk"],
            "verdict": "Contradicted",
            "reasoning": "  Some reasoning.  ",
            "tags": ["fact-checking", "economy", "inflation"],
            "sources": ["https://bbc.com/a"],
            "source_name": "BBC",
        }
    ]

    df = transform(records)

    row = df.iloc[0]
    assert row["claim"] == "The UK inflation rate rose to 4% in 2025."
    assert row["entities"] == ["UK"]
    assert row["verdict"] == "contradicted"
    assert row["reasoning"] == "Some reasoning."
    assert row["tags"] == ["economy", "inflation"]
    assert row["sources"] == ["https://bbc.com/a"]
    assert row["source_name"] == "BBC"


def test_transform_handles_empty_list():
    """transform() returns an empty DataFrame for an empty input list."""
    df = transform([])
    assert len(df) == 0