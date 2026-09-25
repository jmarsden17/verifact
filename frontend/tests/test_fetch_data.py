"""Tests for fetch_data.py."""

import pandas as pd
import pytest

from database_conns.fetch_data import (
    _canonical_verdict,
    _source_url,
    _group_by_claim,
    _normalise_pipeline_output,
    verify_claim,
    fetch_analytics_data,
    get_filtered_logs,
    get_top_disproven_claims,
)


# ---------------------------------------------------------------------------
# _canonical_verdict
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    pytest.param("Supported", "Supported", id="supported"),
    pytest.param("Contradicted", "Contradicted", id="contradicted"),
    pytest.param("Mixed / Missing Context", "Missing Context",
                 id="mixed missing context"),
    pytest.param("Unclear / Not enough evidence", "Unclear", id="unclear"),
    pytest.param(None, "Unclear", id="none"),
    pytest.param("something else entirely", "Unclear", id="unrecognised"),
])
def test_canonical_verdict(raw, expected):
    assert _canonical_verdict(raw) == expected


# ---------------------------------------------------------------------------
# _source_url
# ---------------------------------------------------------------------------

def test_source_url_returns_string_value():
    assert _source_url({"sources": "https://example.com"}
                       ) == "https://example.com"


def test_source_url_returns_none_for_missing_or_non_string():
    assert _source_url({}) is None
    assert _source_url({"sources": float("nan")}) is None
    assert _source_url({"sources": ""}) is None


# ---------------------------------------------------------------------------
# _group_by_claim
# ---------------------------------------------------------------------------

def test_group_by_claim_groups_by_claim_id():
    rows = [{"claim_id": 1, "x": "a"}, {
        "claim_id": 1, "x": "b"}, {"claim_id": 2, "x": "c"}]
    grouped = _group_by_claim(rows)
    assert list(grouped.keys()) == [1, 2]
    assert len(grouped[1]) == 2


def test_group_by_claim_falls_back_to_claim_text_when_no_id():
    rows = [{"claim": "same text"}, {"claim": "same text"}]
    grouped = _group_by_claim(rows)
    assert list(grouped.keys()) == ["same text"]
    assert len(grouped["same text"]) == 2


# ---------------------------------------------------------------------------
# _normalise_pipeline_output
# ---------------------------------------------------------------------------

def test_normalise_pipeline_output_single_dict():
    raw = {"claim": "X", "verdict": "Supported", "summary": "ok",
           "source_name": "BBC", "source_reasoning": "r", "sources": "http://a"}
    result = _normalise_pipeline_output(raw)
    assert len(result) == 1
    assert result[0]["claim"] == "X"
    assert result[0]["rating"] == "Supported"
    assert result[0]["sources"][0]["url"] == "http://a"


def test_normalise_pipeline_output_groups_multiple_outlets_per_claim():
    raw = [
        {"claim_id": 1, "claim": "X", "verdict": "Supported", "source_name": "BBC"},
        {"claim_id": 1, "claim": "X", "verdict": "Supported", "source_name": "Reuters"},
    ]
    result = _normalise_pipeline_output(raw)
    assert len(result) == 1
    assert len(result[0]["sources"]) == 2


def test_normalise_pipeline_output_includes_confidence_when_numeric():
    raw = [{"claim": "X", "verdict": "Supported", "confidence_score": 0.9}]
    result = _normalise_pipeline_output(raw)
    assert result[0]["confidence"] == 90


def test_normalise_pipeline_output_omits_confidence_when_not_numeric():
    raw = [{"claim": "X", "verdict": "Supported", "confidence_score": None}]
    result = _normalise_pipeline_output(raw)
    assert "confidence" not in result[0]


# ---------------------------------------------------------------------------
# verify_claim
# ---------------------------------------------------------------------------

def test_verify_claim_uses_mock_when_no_state_machine_configured(mocker):
    mocker.patch.dict("os.environ", {}, clear=True)
    result = verify_claim("any claim")
    assert isinstance(result, list) and len(result) > 0


def test_verify_claim_uses_mock_for_the_hardcoded_demo_text(mocker):
    mocker.patch.dict("os.environ", {"STATE_MACHINE_ARN": "arn:aws:..."})
    demo_text = (
        "Viral social media posts claim that drinking warm lemon water daily completely cures type 2 diabetes. "
        "Meanwhile, policy reports suggest the government is removing all EV purchase tax credits starting next month, "
        "and leaked internal memos claim the central bank is planning an emergency 200 basis point rate cut."
    )
    mock_run = mocker.patch(
        "database_conns.fetch_data.pipeline_client.run_pipeline")

    verify_claim(demo_text)

    mock_run.assert_not_called()


def test_verify_claim_calls_real_pipeline_when_configured(mocker):
    mocker.patch.dict("os.environ", {"STATE_MACHINE_ARN": "arn:aws:..."})
    mocker.patch("database_conns.fetch_data.pipeline_client.run_pipeline",
                 return_value=[{"claim": "X", "verdict": "Supported"}])

    result = verify_claim("a real user claim")

    assert result[0]["claim"] == "X"


def test_verify_claim_falls_back_to_mock_on_pipeline_error(mocker):
    mocker.patch.dict("os.environ", {"STATE_MACHINE_ARN": "arn:aws:..."})
    mocker.patch("database_conns.fetch_data.pipeline_client.run_pipeline",
                 side_effect=Exception("pipeline down"))

    result = verify_claim("a real user claim")

    assert isinstance(result, list) and len(result) > 0


# ---------------------------------------------------------------------------
# fetch_analytics_data / get_filtered_logs / get_top_disproven_claims
# ---------------------------------------------------------------------------

def test_fetch_analytics_data_success(mocker):
    mock_conn = mocker.MagicMock()
    mocker.patch("database_conns.fetch_data.get_db_connection",
                 return_value=mock_conn)
    expected = pd.DataFrame([{"claim_id": 1}])
    mocker.patch("database_conns.fetch_data.pd.read_sql",
                 return_value=expected)

    result = fetch_analytics_data()

    assert result is expected
    mock_conn.close.assert_called_once()


def test_fetch_analytics_data_falls_back_on_error(mocker):
    mocker.patch("database_conns.fetch_data.get_db_connection",
                 side_effect=Exception("down"))

    result = fetch_analytics_data()

    assert len(result) > 0


def test_get_filtered_logs_success(mocker):
    mock_conn = mocker.MagicMock()
    mocker.patch("database_conns.fetch_data.get_db_connection",
                 return_value=mock_conn)
    expected = pd.DataFrame([{"claim_statement": "x"}])
    mocker.patch("database_conns.fetch_data.pd.read_sql",
                 return_value=expected)

    result = get_filtered_logs(search_query="foo", verdict_filter="Supported")

    assert result is expected


def test_get_top_disproven_claims_success(mocker):
    mock_conn = mocker.MagicMock()
    mocker.patch("database_conns.fetch_data.get_db_connection",
                 return_value=mock_conn)
    expected = pd.DataFrame([{"claim_text": "x"}])
    mocker.patch("database_conns.fetch_data.pd.read_sql",
                 return_value=expected)

    result = get_top_disproven_claims()

    assert result is expected


def test_get_top_disproven_claims_falls_back_on_error(mocker):
    mocker.patch("database_conns.fetch_data.get_db_connection",
                 side_effect=Exception("down"))

    result = get_top_disproven_claims()

    assert len(result) > 0
