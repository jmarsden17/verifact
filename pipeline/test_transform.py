"""Tests for transform script."""

from transform import (
    clean_categorical_list,
    clean_categorical_value,
    clean_float_value,
    clean_list_value,
    clean_tag_list,
    clean_text_value,
    clean_verdict,
    dedupe_list,
    filter_tags,
    resolve_overall_verdict,
    sort_tags,
    transform,
)

VERDICTS = ["supported", "contradicted", "mixed / missing context", "unclear / not enough evidence"]
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


def test_clean_float_value_converts_none_to_none():
    """None stays None."""
    assert clean_float_value(None) is None


def test_clean_float_value_converts_non_numeric_to_none():
    """A non-numeric value becomes None."""
    assert clean_float_value("not a number") is None


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


def test_filter_tags_handles_empty_list():
    """An empty input returns an empty result."""
    assert not filter_tags([], exclude=[])


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


def test_clean_categorical_list_keeps_only_allowed_values():
    """Values not in the allowed list are dropped."""
    result = clean_categorical_list(["Europe", "Nonsense", "Technology"], TOPICS)
    assert result == ["Europe", "Technology"]


def test_dedupe_list_removes_exact_duplicates():
    """Exact duplicate values are removed."""
    assert dedupe_list(["UK", "UK", "ONS"]) == ["UK", "ONS"]


def test_dedupe_list_is_case_insensitive():
    """Differently-cased duplicates are treated as the same value."""
    assert dedupe_list(["UK", "uk", "ONS"]) == ["UK", "ONS"]


def test_sort_tags_sorts_alphabetically():
    """Tags are returned in alphabetical order."""
    assert sort_tags(["inflation", "economy", "finance"]) == ["economy", "finance", "inflation"]


def test_clean_tag_list_dedupes_filters_and_validates():
    """clean_tag_list drops invalid tags, dedupes, filters, and sorts."""
    tags = ["fact-checking", "Europe", "Nonsense Tag", "europe", "Media Journalism"]

    result = clean_tag_list(tags, exclude=["fact-checking"])

    assert result == ["Europe", "Media Journalism"]


def test_clean_verdict_cleans_an_individual_source_verdict():
    """clean_verdict cleans one raw per-source verdict dict."""
    raw = {
        "claim": "  Example claim.  ",
        "verdict": "Contradicted",
        "reasoning": "  Some reasoning.  ",
        "misinformation_type": "Deepfake",
        "entities": ["X", "x"],
        "tags": ["Europe", "fact-checking"],
        "sources": ["https://a.com"],
        "source_name": "  Full Fact  ",
    }

    result = clean_verdict(raw)

    assert result["claim"] == "Example claim."
    assert result["verdict"] == "contradicted"
    assert result["reasoning"] == "Some reasoning."
    assert result["technique"] == "deepfake"
    assert result["entities"] == ["X"]
    assert result["tags"] == ["Europe"]
    assert result["sources"] == ["https://a.com"]
    assert result["source_name"] == "Full Fact"


def test_clean_verdict_accepts_technique_key_as_fallback():
    """clean_verdict reads 'technique' if 'misinformation_type' isn't present."""
    raw = {"claim": "X", "verdict": "Supported", "reasoning": "Y",
           "technique": "None", "entities": [], "tags": [], "sources": []}

    result = clean_verdict(raw)

    assert result["technique"] == "none"


def test_resolve_overall_verdict_picks_majority():
    """The verdict with the most votes wins."""
    verdicts = [{"verdict": "contradicted"}, {"verdict": "contradicted"}, {"verdict": "supported"}]
    assert resolve_overall_verdict(verdicts) == "contradicted"


def test_resolve_overall_verdict_falls_back_on_tie():
    """A tie between verdicts resolves to 'unclear / not enough evidence'."""
    verdicts = [{"verdict": "contradicted"}, {"verdict": "supported"}]
    assert resolve_overall_verdict(verdicts) == "unclear / not enough evidence"


def test_resolve_overall_verdict_falls_back_on_no_data():
    """No individual verdicts resolves to 'unclear / not enough evidence'."""
    assert resolve_overall_verdict([]) == "unclear / not enough evidence"


def test_resolve_overall_verdict_ignores_unknown_votes():
    """'unknown' verdicts don't count towards the majority."""
    verdicts = [{"verdict": "unknown"}, {"verdict": "supported"}, {"verdict": "supported"}]
    assert resolve_overall_verdict(verdicts) == "supported"


def test_transform_produces_one_row_per_claim():
    """transform() cleans a claim-keyed combined dict into one row per claim."""
    combined = {
        "The Eiffel Tower was built in 1822.": {
            "verdicts": [
                {"claim": "The Eiffel Tower was built in 1822.", "verdict": "Contradicted",
                 "reasoning": "It was completed in 1889.", "misinformation_type": "None",
                 "entities": ["Eiffel Tower"], "tags": ["Europe"], "sources": ["https://fullfact.org/x"],
                 "source_name": "Full Fact"},
                {"claim": "The Eiffel Tower was built in 1822.", "verdict": "Contradicted",
                 "reasoning": "Built 1887-1889.", "misinformation_type": "None",
                 "entities": ["Eiffel Tower"], "tags": ["Europe"], "sources": ["https://bbc.co.uk/x"],
                 "source_name": "BBC Verify"},
            ],
            "summary": {
                "summary": "  Both sources agree it was 1889.  ",
                "confidence_score": 0.95,
                "misinformation_type": "None",
                "entities": ["Eiffel Tower", "eiffel tower"],
                "tags": ["History Revisionism", "fact-checking"],
                "sources": ["https://fullfact.org/x", "https://bbc.co.uk/x"],
            },
        }
    }

    df = transform(combined)

    assert len(df) == 1
    row = df.iloc[0]
    assert row["claim"] == "The Eiffel Tower was built in 1822."
    assert row["verdict"] == "contradicted"
    assert row["summary"] == "Both sources agree it was 1889."
    assert row["confidence_score"] == 0.95
    assert row["technique"] == "none"
    assert row["entities"] == ("Eiffel Tower",)
    assert row["tags"] == ("History Revisionism",)
    assert row["sources"] == ("https://fullfact.org/x", "https://bbc.co.uk/x")
    assert len(row["individual_verdicts"]) == 2


def test_transform_handles_missing_summary():
    """A claim with no summary block still produces a row, with defaults."""
    combined = {
        "Some claim.": {
            "verdicts": [
                {"claim": "Some claim.", "verdict": "Supported", "reasoning": "OK.",
                 "misinformation_type": "None", "entities": [], "tags": [], "sources": []},
            ],
            "summary": None,
        }
    }

    df = transform(combined)

    row = df.iloc[0]
    assert row["claim"] == "Some claim."
    assert row["verdict"] == "supported"
    assert row["summary"] == ""
    assert row["confidence_score"] is None
    assert row["technique"] == "unknown"


def test_transform_handles_empty_dict():
    """transform() returns an empty DataFrame for an empty input dict."""
    df = transform({})
    assert len(df) == 0