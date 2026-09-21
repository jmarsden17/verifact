"""Create a summary of multiple source claims and their corresponding verdicts."""

import os

from openai import OpenAI
from dotenv import load_dotenv
from summary_models import SummaryResult


def generate_summary(grouped_claims: list[dict]) -> SummaryResult:
    """Generate a summary of multiple source claims and their corresponding verdicts using OpenAI's API."""
    load_dotenv()
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                    base_url=os.environ["OPENAI_BASE_URL"])
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
        reduce confidence, however not as significantly as directly contradicting verdicts. Only when all sources agree should the confidence score be
        over 0.9.:

        {outlet_claims}
        """

        response = client.chat.completions.parse(
            model="gpt-5.6-luna",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise summarization assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format=SummaryResult)

        summaries[key] = response.choices[0].message.parsed.model_dump()

    return summaries
