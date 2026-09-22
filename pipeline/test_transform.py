# pylint: skip-file

"""Tests for the transform script."""


import pandas as pd
import pytest

from transform_load.transform import (
    clean_categorical_list,
    clean_categorical_value,
    clean_float_value,
    clean_list_value,
    clean_tag_list,
    clean_text_value,
    dedupe_list,
    ensure_column,
    filter_tags,
    sort_tags,
    transform,
)


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

VERDICTS = ["Supported", "Contradicted",
            "Mixed / Missing Context", "Unclear / Not enough evidence"]
TECHNIQUES = ["Deepfake", "Misleading Context", "None"]
TOPICS = ["Europe", "Media Journalism", "Technology"]
OUTLETS = ["BBC", "Wiki", "Google"]


# ---------------------------------------------------------------------------
# Simple cleaning helpers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value, expected", [
    pytest.param(["a", "b"], ["a", "b"], id="list"),
    pytest.param([], [], id="empty list"),
    pytest.param(None, [], id="none"),
    pytest.param("not a list", [], id="string"),
    pytest.param({"a": 1}, [], id="dict"),
])
def test_clean_list_value(value, expected):
    """A list is kept as is, anything else becomes an empty list."""
    assert clean_list_value(value) == expected


@pytest.mark.parametrize("value, expected", [
    pytest.param("  hello  ", "hello", id="padded string"),
    pytest.param("hello", "hello", id="clean string"),
    pytest.param("   ", "", id="only whitespace"),
    pytest.param(None, "", id="none"),
    pytest.param(123, "", id="number"),
])
def test_clean_text_value(value, expected):
    """A string is stripped, anything else becomes an empty string."""
    assert clean_text_value(value) == expected


@pytest.mark.parametrize("value, expected", [
    pytest.param(0.94, 0.94, id="float"),
    pytest.param(1, 1, id="int"),
    pytest.param(0, 0, id="zero"),
    pytest.param(None, None, id="none"),
    pytest.param("not a number", None, id="string"),
    pytest.param(True, None, id="true"),
    pytest.param(False, None, id="false"),
])
def test_clean_float_value(value, expected):
    """A real number is kept, anything else (including bools) becomes None."""
    assert clean_float_value(value) == expected


# ---------------------------------------------------------------------------
# Tag and category helpers
# ---------------------------------------------------------------------------

# filter_tags

@pytest.mark.parametrize("tags, exclude, max_tags, expected", [
    pytest.param(["fact-checking", "economy", "inflation"], ["fact-checking"], 5,
                 ["economy", "inflation"], id="removes excluded tag"),
    pytest.param(["Fact-Checking", "economy"], ["fact-checking"], 5,
                 ["economy"], id="exclusion ignores case"),
    pytest.param(["news", "economy", "inflation"], ["news"], 5,
                 ["economy", "inflation"], id="custom exclude list"),
    pytest.param(["economy", "inflation"], None, 5,
                 ["economy", "inflation"], id="no exclude list"),
    pytest.param(["a", "b", "c", "d", "e", "f", "g"], [], 5,
                 ["a", "b", "c", "d", "e"], id="limits to five"),
    pytest.param(["a", "b", "c", "d"], [], 2,
                 ["a", "b"], id="custom limit"),
    pytest.param(["skip", "a", "b", "c"], ["skip"], 2,
                 ["a", "b"], id="excludes before limiting"),
    pytest.param([], [], 5, [], id="empty list"),
])
def test_filter_tags(tags, exclude, max_tags, expected):
    """Excluded tags are removed, then the result is capped at max_tags."""
    assert filter_tags(tags, exclude=exclude, max_tags=max_tags) == expected


def test_filter_tags_uses_defaults():
    """With no exclude list or limit given, nothing is excluded and five are kept."""
    tags = ["a", "b", "c", "d", "e", "f"]

    assert filter_tags(tags) == ["a", "b", "c", "d", "e"]


# clean_categorical_value

@pytest.mark.parametrize("value, allowed, category, expected", [
    # A valid value is returned in the allowed list's own casing
    pytest.param("supported", VERDICTS, "VERDICTS", "Supported",
                 id="verdict lowercase"),
    pytest.param("CONTRADICTED", VERDICTS, "VERDICTS", "Contradicted",
                 id="verdict uppercase"),
    pytest.param("Supported", VERDICTS, "VERDICTS", "Supported",
                 id="verdict exact match"),
    pytest.param("europe", TOPICS, "TOPIC_TAGS", "Europe",
                 id="topic"),
    pytest.param("deepfake", TECHNIQUES, "TECHNIQUE_TAGS", "Deepfake",
                 id="technique"),
    pytest.param("bbc", OUTLETS, "OUTLETS", "BBC",
                 id="outlet"),

    # An invalid value falls back to a different default for each category
    pytest.param("nonsense", VERDICTS, "VERDICTS", "Unclear / Not enough evidence",
                 id="invalid verdict"),
    pytest.param(None, VERDICTS, "VERDICTS", "Unclear / Not enough evidence",
                 id="none as verdict"),
    pytest.param("abc", TOPICS, "TOPIC_TAGS", "Other",
                 id="invalid topic"),
    pytest.param(123, TOPICS, "TOPIC_TAGS", "Other",
                 id="number as topic"),
    pytest.param("abc", TECHNIQUES, "TECHNIQUE_TAGS", "None",
                 id="invalid technique"),
    pytest.param("abc", OUTLETS, "OUTLETS", None,
                 id="invalid outlet"),
])
def test_clean_categorical_value(value, allowed, category, expected):
    """Valid values match ignoring case, invalid values use the category's fallback."""
    assert clean_categorical_value(value, allowed, category) == expected


# clean_categorical_list

@pytest.mark.parametrize("values, expected", [
    pytest.param(["Europe", "Nonsense", "Technology"], ["Europe", "Technology"],
                 id="drops invalid values"),
    pytest.param(["Nonsense"], [], id="all invalid"),
    pytest.param([1, None, "Europe"], ["Europe"], id="drops non strings"),
    pytest.param([], [], id="empty list"),
    pytest.param(None, [], id="none"),
    pytest.param("Europe", [], id="string instead of list"),
])
def test_clean_categorical_list(values, expected):
    """Only values in the allowed list are kept, and non lists become empty."""
    assert clean_categorical_list(values, TOPICS) == expected


# dedupe_list

@pytest.mark.parametrize("values, expected", [
    pytest.param(["UK", "UK", "ONS"], ["UK", "ONS"], id="exact duplicates"),
    pytest.param(["UK", "uk", "ONS"], ["UK", "ONS"], id="ignores case"),
    pytest.param(["b", "a", "b", "c"], ["b", "a", "c"], id="keeps first position"),
    pytest.param(["a", "b", "c"], ["a", "b", "c"], id="no duplicates"),
    pytest.param([], [], id="empty list"),
])
def test_dedupe_list(values, expected):
    """Case insensitive duplicates are removed and the first one keeps its place."""
    assert dedupe_list(values) == expected


# sort_tags

@pytest.mark.parametrize("tags, expected", [
    pytest.param(["inflation", "economy", "finance"],
                 ["economy", "finance", "inflation"], id="alphabetical"),
    pytest.param(["Zebra", "apple"], ["apple", "Zebra"], id="ignores case"),
    pytest.param([], [], id="empty list"),
])
def test_sort_tags(tags, expected):
    """Tags are sorted alphabetically, ignoring case."""
    assert sort_tags(tags) == expected


# clean_tag_list

@pytest.mark.parametrize("tags, exclude, expected", [
    pytest.param(["fact-checking", "Europe", "Nonsense Tag", "europe", "Media Journalism"],
                 ["fact-checking"], ["Europe", "Media Journalism"],
                 id="invalid, duplicate and excluded tags"),
    pytest.param(["Media Journalism", "Europe"], None,
                 ["Europe", "Media Journalism"], id="sorts tags"),
    pytest.param(["Nonsense"], None, [], id="all invalid"),
    pytest.param(None, [], [], id="none input"),
    pytest.param(None, None, [], id="none input and no exclude list"),
])
def test_clean_tag_list(tags, exclude, expected):
    """Invalid tags are dropped, duplicates removed, and the result sorted."""
    assert clean_tag_list(tags, exclude=exclude) == expected


# ---------------------------------------------------------------------------
# ensure_column
# ---------------------------------------------------------------------------

def test_ensure_column_adds_missing_column_with_default():
    """A missing column is added and filled with the default value."""
    df = pd.DataFrame({"a": [1, 2]})

    result = ensure_column(df, "b", "x")

    assert result["b"].tolist() == ["x", "x"]


def test_ensure_column_calls_callable_default_for_each_row():
    """A callable default is called once per row, so rows don't share one object."""
    df = pd.DataFrame({"a": [1, 2]})

    result = ensure_column(df, "b", list)

    assert result["b"].tolist() == [[], []]
    assert result["b"][0] is not result["b"][1]


def test_ensure_column_keeps_existing_column():
    """A column that already exists is left alone."""
    df = pd.DataFrame({"a": [1, 2]})

    result = ensure_column(df, "a", 0)

    assert result["a"].tolist() == [1, 2]


# ---------------------------------------------------------------------------
# transform
# ---------------------------------------------------------------------------

# One column at a time
# Each case changes one field of an otherwise valid record, runs transform(),
# and checks the cleaned value in the resulting column.

def make_record(**overrides):
    """A valid verdict record, with any fields replaced by the overrides."""
    record = {
        "claim": "A claim.",
        "verdict": "Supported",
        "reasoning": "A reason.",
        "misinformation_type": "None",
        "entities": [],
        "tags": [],
        "sources": [],
        "source_name": "Full Fact",
    }
    record.update(overrides)
    return record


@pytest.mark.parametrize("field, value, column, expected", [
    # verdict
    pytest.param("verdict", "supported", "verdict", "Supported",
                 id="verdict casing"),
    pytest.param("verdict", "nonsense", "verdict", "Unclear / Not enough evidence",
                 id="invalid verdict"),
    pytest.param("verdict", None, "verdict", "Unclear / Not enough evidence",
                 id="none verdict"),

    # technique (comes from misinformation_type)
    pytest.param("misinformation_type", "deepfake", "technique", "Deepfake",
                 id="technique casing"),
    pytest.param("misinformation_type", "Not A Real Technique", "technique", "None",
                 id="invalid technique"),
    pytest.param("misinformation_type", None, "technique", "None",
                 id="none technique"),

    # text columns
    pytest.param("claim", "  padded claim  ", "claim", "padded claim",
                 id="claim stripped"),
    pytest.param("reasoning", "  padded reason  ", "source_reasoning", "padded reason",
                 id="reasoning renamed and stripped"),
    pytest.param("summary", None, "summary", "",
                 id="none summary"),

    # entities
    pytest.param("entities", ["UK", "uk", "ONS"], "entities", ("UK", "ONS"),
                 id="entities deduped"),
    pytest.param("entities", "not a list", "entities", (),
                 id="entities not a list"),

    # tags
    pytest.param("tags", ["Media Journalism", "Europe"], "tags",
                 ("Europe", "Media Journalism"), id="tags sorted"),
    pytest.param("tags", ["Nonsense"], "tags", (),
                 id="invalid tags"),
    pytest.param("tags", None, "tags", (),
                 id="none tags"),

    # sources
    pytest.param("sources", ["https://a.com", "https://b.com"], "sources",
                 "https://a.com", id="first source kept"),
    pytest.param("sources", [], "sources", None,
                 id="no sources"),
    pytest.param("sources", None, "sources", None,
                 id="none sources"),

    # source_name
    pytest.param("source_name", "  BBC Verify  ", "source_name", "BBC Verify",
                 id="outlet stripped"),
    pytest.param("source_name", "full fact", "source_name", "Full Fact",
                 id="outlet casing"),
    pytest.param("source_name", "Google", "source_name", None,
                 id="invalid outlet"),

    # claim_url
    pytest.param("claim_url", "https://example.com", "claim_url",
                 "https://example.com", id="valid claim url"),
    pytest.param("claim_url", "   ", "claim_url", None,
                 id="blank claim url"),
    pytest.param("claim_url", 123, "claim_url", None,
                 id="number as claim url"),

    # claim_embedding
    pytest.param("claim_embedding", [0.1, 0.2], "claim_embedding", [0.1, 0.2],
                 id="valid embedding"),
    pytest.param("claim_embedding", "not a list", "claim_embedding", None,
                 id="invalid embedding"),

    # numbers
    pytest.param("confidence_score", 0.5, "confidence_score", 0.5,
                 id="valid confidence score"),
    pytest.param("confidence_score", "high", "confidence_score", None,
                 id="invalid confidence score"),
    pytest.param("similarity", 0.9, "similarity", 0.9,
                 id="valid similarity"),
    pytest.param("similarity", "high", "similarity", None,
                 id="invalid similarity"),
])
def test_transform_cleans_column(field, value, column, expected):
    """Each column of a record is cleaned the way its rules say."""
    df = transform([make_record(**{field: value})])

    assert df.iloc[0][column] == expected


# Whole records

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