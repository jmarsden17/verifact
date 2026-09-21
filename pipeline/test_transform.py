# pylint: skip-file

"""Tests for transform script."""

from transform_load.transform import (
    clean_categorical_list,
    clean_categorical_value,
    clean_float_value,
    clean_list_value,
    clean_tag_list,
    clean_text_value,
    dedupe_list,
    filter_tags,
    sort_tags,
    transform,
)

VERDICTS = ["Supported", "Contradicted",
            "Mixed / Missing Context", "Unclear / Not enough evidence"]
TECHNIQUES = ["Deepfake", "Misleading Context", "None"]
TOPICS = ["Europe", "Media Journalism", "Technology"]


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


def test_clean_float_value_keeps_a_float():
    """A real float is returned unchanged."""
    assert clean_float_value(0.94) == 0.94


def test_clean_float_value_keeps_an_int():
    """An int is returned unchanged."""
    assert clean_float_value(1) == 1


def test_clean_float_value_converts_none_to_none():
    """None stays None."""
    assert clean_float_value(None) is None


def test_clean_float_value_converts_non_numeric_to_none():
    """A non-numeric value becomes None."""
    assert clean_float_value("not a number") is None


def test_clean_float_value_converts_bool_to_none():
    """A bool (technically an int subclass in Python) is rejected."""
    assert clean_float_value(True) is None


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


def test_clean_categorical_value_keeps_real_casing():
    """A valid value is returned in its real (allowed-list) casing, not lowercased."""
    assert clean_categorical_value("supported", VERDICTS) == "Supported"


def test_clean_categorical_value_converts_invalid_value_to_unknown():
    """A value not in the allowed list becomes 'unknown'."""
    assert clean_categorical_value("nonsense", VERDICTS) == "unknown"


def test_clean_categorical_value_converts_none_to_unknown():
    """None becomes 'unknown'."""
    assert clean_categorical_value(None, VERDICTS) == "unknown"


def test_clean_categorical_value_is_case_insensitive():
    """Matching against the allowed list ignores input casing, but returns the allowed list's own casing."""
    assert clean_categorical_value(
        "Contradicted".lower(), VERDICTS) == "Contradicted"


def test_clean_categorical_list_keeps_only_allowed_values():
    """Values not in the allowed list are dropped."""
    result = clean_categorical_list(
        ["Europe", "Nonsense", "Technology"], TOPICS)
    assert result == ["Europe", "Technology"]


def test_clean_categorical_list_handles_non_list_input():
    """A non-list value is treated as an empty list."""
    assert not clean_categorical_list(None, TOPICS)


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
    assert sort_tags(["inflation", "economy", "finance"]) == [
        "economy", "finance", "inflation"]


def test_sort_tags_is_case_insensitive():
    """Sorting ignores casing."""
    assert sort_tags(["Zebra", "apple"]) == ["apple", "Zebra"]


def test_sort_tags_handles_empty_list():
    """An empty input returns an empty result."""
    assert not sort_tags([])


def test_clean_tag_list_dedupes_filters_and_validates():
    """clean_tag_list drops invalid tags, dedupes, filters, and sorts."""
    tags = ["fact-checking", "Europe",
            "Nonsense Tag", "europe", "Media Journalism"]

    result = clean_tag_list(tags, exclude=["fact-checking"])

    assert result == ["Europe", "Media Journalism"]


def test_clean_tag_list_handles_non_list_input():
    """A non-list value is treated as an empty tag list."""
    assert not clean_tag_list(None, exclude=[])


def test_transform_produces_clean_dataframe_for_normal_branch():
    """transform() cleans every column of a normal (non-skip_etl) verdict record."""
    records = [
        {
            "claim": "  The Eiffel Tower is in London.  ",
            "verdict": "Contradicted",
            "reasoning": "  It's actually in Paris.  ",
            "misinformation_type": "Misleading Context",
            "entities": ["Eiffel Tower", "eiffel tower", "London"],
            "tags": ["fact-checking", "Europe", "Nonsense Tag"],
            "sources": ["https://fullfact.org/x"],
            "source_name": "  Full Fact  ",
            "confidence_score": 0.8,
        }
    ]

    df = transform(records)

    row = df.iloc[0]
    assert row["claim"] == "The Eiffel Tower is in London."
    assert row["verdict"] == "Contradicted"
    assert row["source_reasoning"] == "It's actually in Paris."
    assert row["technique"] == "Misleading Context"
    assert row["entities"] == ("Eiffel Tower", "London")
    assert isinstance(row["entities"], tuple)
    assert row["tags"] == ("Europe",)
    assert isinstance(row["tags"], tuple)
    assert row["sources"] == "https://fullfact.org/x"
    assert not isinstance(row["sources"], (list, tuple))
    assert row["source_name"] == "Full Fact"
    assert row["summary"] == ""
    assert row["similar_claim"] == ""
    assert row["similarity"] is None
    assert row["confidence_score"] == 0.8
    assert row["claim_url"] is None
    assert row["claim_embedding"] is None


def test_transform_handles_invalid_technique():
    """An unrecognised technique becomes 'unknown'."""
    records = [
        {
            "claim": "Example.",
            "verdict": "Supported",
            "reasoning": "Example.",
            "misinformation_type": "Not A Real Technique",
            "entities": [],
            "tags": [],
            "sources": [],
        }
    ]

    df = transform(records)

    assert df.iloc[0]["technique"] == "unknown"


def test_transform_produces_clean_dataframe_for_skip_etl_branch():
    """transform() cleans a skip_etl record's own summary/technique/similarity fields."""
    records = [
        {
            "claim": "  The Eiffel Tower was built in 1889.  ",
            "similar_claim": "  The Eiffel Tower was completed in 1889.  ",
            "similarity": 0.97,
            "verdict": "Supported",
            "summary": "  Confirmed by a previous check.  ",
            "technique": "None",
        }
    ]

    df = transform(records)

    row = df.iloc[0]
    assert row["claim"] == "The Eiffel Tower was built in 1889."
    assert row["verdict"] == "Supported"
    assert row["summary"] == "Confirmed by a previous check."
    assert row["technique"] == "None"
    assert row["similar_claim"] == "The Eiffel Tower was completed in 1889."
    assert row["similarity"] == 0.97
    assert row["source_reasoning"] == ""
    assert not row["entities"]
    assert not row["tags"]
    assert row["sources"] is None


def test_transform_handles_mixed_batch_without_crashing():
    """A batch mixing normal and skip_etl records doesn't create duplicate columns."""
    records = [
        {
            "claim": "Normal claim.",
            "verdict": "Contradicted",
            "reasoning": "Per this source, false.",
            "misinformation_type": "Deepfake",
            "entities": [],
            "tags": [],
            "sources": [],
            "source_name": "Full Fact",
        },
        {
            "claim": "Cached claim.",
            "similar_claim": "Similar claim.",
            "similarity": 0.95,
            "verdict": "Supported",
            "summary": "Overall summary from prior check.",
            "technique": "None",
        },
    ]

    df = transform(records)

    assert not df.columns.duplicated().any()
    assert df.iloc[0]["source_reasoning"] == "Per this source, false."
    assert df.iloc[0]["technique"] == "Deepfake"
    assert df.iloc[1]["summary"] == "Overall summary from prior check."
    assert df.iloc[1]["technique"] == "None"


def test_transform_adds_claim_url_embedding_confidence_columns_when_missing():
    """claim_url, claim_embedding, confidence_score exist even when not in the input records."""
    records = [{"claim": "A", "verdict": "Supported", "reasoning": "x",
                "misinformation_type": "None", "entities": [], "tags": [], "sources": []}]

    df = transform(records)

    assert "claim_url" in df.columns
    assert "claim_embedding" in df.columns
    assert "confidence_score" in df.columns
    assert df.iloc[0]["claim_url"] is None
    assert df.iloc[0]["claim_embedding"] is None
    assert df.iloc[0]["confidence_score"] is None


def test_transform_handles_empty_list():
    """transform() returns an empty DataFrame for an empty input list."""
    df = transform([])
    assert len(df) == 0
