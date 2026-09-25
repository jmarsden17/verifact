"""Tests for pipeline_client.py."""

import json

import pytest

from database_conns.pipeline_client import (
    _parse_output,
    _build_input,
    _invoke_step_function,
    run_pipeline,
    PipelineError,
)


# ---------------------------------------------------------------------------
# _parse_output
# ---------------------------------------------------------------------------

def test_parse_output_unwraps_body_key():
    raw = json.dumps({"statusCode": 200, "body": [{"claim": "X"}]})
    assert _parse_output(raw) == [{"claim": "X"}]


def test_parse_output_unwraps_doubly_encoded_json():
    inner = json.dumps({"body": {"claim": "X"}})
    raw = json.dumps(inner)
    assert _parse_output(raw) == {"claim": "X"}


def test_parse_output_returns_data_as_is_when_no_body_key():
    raw = json.dumps({"claim": "X"})
    assert _parse_output(raw) == {"claim": "X"}


# ---------------------------------------------------------------------------
# _build_input
# ---------------------------------------------------------------------------

def test_build_input_url_only_valid(mocker):
    mocker.patch("database_conns.pipeline_client.verify_url", return_value=True)
    mocker.patch("database_conns.pipeline_client.extract_url", return_value="scraped text")

    result = _build_input("", "https://example.com")

    assert result == {"user_text": "scraped text"}


def test_build_input_url_only_invalid_sends_raw_url(mocker):
    mocker.patch("database_conns.pipeline_client.verify_url", return_value=False)

    result = _build_input("", "not-a-real-url")

    assert result == {"user_text": "not-a-real-url"}


def test_build_input_text_only_valid_url_extracts(mocker):
    mocker.patch("database_conns.pipeline_client.verify_url", return_value=True)
    mocker.patch("database_conns.pipeline_client.extract_url", return_value="scraped text")

    result = _build_input("https://example.com", "")

    assert result == {"user_text": "scraped text"}


def test_build_input_text_only_not_a_url_sends_as_is(mocker):
    mocker.patch("database_conns.pipeline_client.verify_url", return_value=False)

    result = _build_input("just some claim text", "")

    assert result == {"user_text": "just some claim text"}


def test_build_input_text_and_url_together():
    result = _build_input("some claim", "https://example.com")

    assert result == {"user_text": "some claim"}


def test_build_input_neither_given():
    assert _build_input("", "") == {}


# ---------------------------------------------------------------------------
# _invoke_step_function
# ---------------------------------------------------------------------------

def test_invoke_step_function_succeeds(mocker):
    mock_sfn = mocker.MagicMock()
    mock_sfn.start_execution.return_value = {"executionArn": "arn:exec"}
    mock_sfn.describe_execution.return_value = {
        "status": "SUCCEEDED",
        "output": json.dumps({"body": {"claim": "X"}}),
    }
    mocker.patch("database_conns.pipeline_client._client", return_value=mock_sfn)

    result = _invoke_step_function("arn:sm", {"user_text": "x"})

    assert result == {"claim": "X"}


def test_invoke_step_function_raises_on_failure(mocker):
    mock_sfn = mocker.MagicMock()
    mock_sfn.start_execution.return_value = {"executionArn": "arn:exec"}
    mock_sfn.describe_execution.return_value = {
        "status": "FAILED", "cause": "boom"}
    mocker.patch("database_conns.pipeline_client._client", return_value=mock_sfn)

    with pytest.raises(PipelineError, match="failed"):
        _invoke_step_function("arn:sm", {"user_text": "x"})


def test_invoke_step_function_calls_on_progress(mocker):
    mock_sfn = mocker.MagicMock()
    mock_sfn.start_execution.return_value = {"executionArn": "arn:exec"}
    mock_sfn.describe_execution.return_value = {
        "status": "SUCCEEDED", "output": json.dumps({"body": []}),
    }
    mocker.patch("database_conns.pipeline_client._client", return_value=mock_sfn)
    progress_calls = []

    _invoke_step_function("arn:sm", {}, on_progress=lambda w, m, s: progress_calls.append(s))

    assert progress_calls == ["SUCCEEDED"]


def test_invoke_step_function_times_out(mocker):
    mock_sfn = mocker.MagicMock()
    mock_sfn.start_execution.return_value = {"executionArn": "arn:exec"}
    mock_sfn.describe_execution.return_value = {"status": "RUNNING"}
    mocker.patch("database_conns.pipeline_client._client", return_value=mock_sfn)
    mocker.patch("database_conns.pipeline_client.time.sleep")
    mocker.patch("database_conns.pipeline_client.MAX_WAIT_SECONDS", 2)
    mocker.patch("database_conns.pipeline_client.POLL_INTERVAL_SECONDS", 1)

    with pytest.raises(PipelineError, match="did not finish"):
        _invoke_step_function("arn:sm", {})


# ---------------------------------------------------------------------------
# run_pipeline
# ---------------------------------------------------------------------------

def test_run_pipeline_raises_when_no_state_machine_arn(mocker):
    mocker.patch.dict("os.environ", {}, clear=True)

    with pytest.raises(PipelineError, match="STATE_MACHINE_ARN"):
        run_pipeline("a claim")


def test_run_pipeline_invokes_step_function_when_configured(mocker):
    mocker.patch.dict("os.environ", {"STATE_MACHINE_ARN": "arn:sm"})
    mock_invoke = mocker.patch(
        "database_conns.pipeline_client._invoke_step_function", return_value={"ok": True})

    result = run_pipeline("a claim")

    assert result == {"ok": True}
    mock_invoke.assert_called_once()