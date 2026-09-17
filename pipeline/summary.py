"""Create a summary of multiple source claims and their corresponding verdicts."""

import os

from openai import OpenAI
from dotenv import load_dotenv
from summary_models import SummaryResult


def handler(event, context) -> dict:
    """Pivot per-source verdict lists into a claim-keyed structure."""
    grouped = {}

    for branch_output in event:
        for verdict in branch_output["body"]:
            claim_text = verdict["claim"]
            grouped.setdefault(claim_text, []).append(verdict)

    return {
        "statusCode": 200,
        "body": grouped
    }


def generate_summary(claims: list[dict]) -> SummaryResult:
    """Generate a summary of multiple source claims and their corresponding verdicts using OpenAI's API."""
    load_dotenv()
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                    base_url=os.environ["OPENAI_BASE_URL"])

    grouped_claims = handler(claims, None)["body"]

    summaries = {}

    for key in grouped_claims:
        outlet_claims = grouped_claims[key]

        prompt = f"""
        Summarize the following claims and their corresponding verdicts into a concise summary
        that captures the overall consensus and key points. The summary should be clear, neutral, and informative. It should
        be clear to point out opposing verdicts and highlight any areas of agreement or disagreement. The summary should be structured
        in a way that is easy to read and understand. The 'reasoning' and 'verdict' fields should be used to inform the summary, but the
        summary should not simply repeat these fields verbatim. You should also include a 'confidence score' for the summary as a number
        between 0 and 1 which indicates the agreement level between the different sources. Verdicts that are 'Unclear / Not enough evidence' should
        be treated as neutral and not contribute to the confidence score.:

        {outlet_claims}
        """

        response = client.chat.completions.create(
            model="gpt-5.6-luna",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise summarization assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format=SummaryResult)

        summaries[0] = response.choices[0].message.parsed.model_dump()

    return summaries
