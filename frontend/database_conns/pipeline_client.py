"""Calls the claim-verification pipeline."""

import json
import os
import time
import boto3

AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "eu-west-2")

# How long the frontend will wait for a STANDARD (async) Step Function run.
POLL_INTERVAL_SECONDS = 2
MAX_WAIT_SECONDS = 50


class PipelineError(Exception):
    """Raised when the pipeline can't be reached, times out, or fails."""


def _parse_output(raw: str) -> dict:
    """Step Functions execution output, unwrapped."""

    data = json.loads(raw)
    while isinstance(data, str):
        data = json.loads(data)

    if isinstance(data, dict) and "body" in data:
        return data["body"]
    return data


def _client(service: str):
    return boto3.client(service, region_name=AWS_REGION)


def _build_input(claim_input: str, url_input: str) -> dict:
    """Payload sent to the pipeline: {"user_text": "..."}."""

    text = claim_input.strip()
    if url_input:
        text = f"{text}\n\nSource URL: {url_input.strip()}"

    return {"user_text": text}


def _invoke_step_function(state_machine_arn: str, payload: dict) -> dict:
    """Starts a STANDARD execution and polls until it finishes or times out."""

    sfn = _client("stepfunctions")
    execution = sfn.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps(payload),
    )
    execution_arn = execution["executionArn"]

    waited = 0
    while waited < MAX_WAIT_SECONDS:
        result = sfn.describe_execution(executionArn=execution_arn)
        status = result["status"]

        if status == "SUCCEEDED":
            return _parse_output(result["output"])
        if status in ("FAILED", "TIMED_OUT", "ABORTED"):
            raise PipelineError(
                f"Pipeline execution {status.lower()}: {result.get('cause', 'no cause given')}")

        time.sleep(POLL_INTERVAL_SECONDS)
        waited += POLL_INTERVAL_SECONDS

    raise PipelineError(
        f"Pipeline did not finish within {MAX_WAIT_SECONDS}s (execution: {execution_arn})")


def run_pipeline(claim_input: str, url_input: str = "") -> dict:
    """Send a claim through the real pipeline. Raises PipelineError on any failure."""

    payload = _build_input(claim_input, url_input)

    state_machine_arn = os.getenv("STATE_MACHINE_ARN")

    if state_machine_arn:
        return _invoke_step_function(state_machine_arn, payload)

    raise PipelineError(
        "STATE_MACHINE_ARN is not set - add STATE_MACHINE_ARN to .env"
    )
