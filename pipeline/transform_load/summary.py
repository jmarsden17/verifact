"""Create a summary of multiple source claims and their corresponding verdicts."""

import logging
import os

from openai import OpenAI
from dotenv import load_dotenv
from summary_models import SummaryResult

logger = logging.getLogger(__name__)


def generate_summary(grouped_claims: list[dict]) -> SummaryResult:
    """
    Generate a summary of multiple source claims and their corresponding 
    verdicts using OpenAI's API.
    """
    load_dotenv()
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                    base_url=os.environ["OPENAI_BASE_URL"])
    summaries = {}

    logger.info("Summarizing %d claim group(s)", len(grouped_claims))

    for key in grouped_claims:
        outlet_claims = grouped_claims[key]
        logger.info("Summarizing claim: %.80s", key)

        prompt = f"""
        Summarize the following claims and their corresponding verdicts into a concise, neutral summary.

        AGGREGATION RULES (apply before writing anything):
        - Treat "Unclear / Not enough evidence" as an ABSTENTION, not a data point that pulls the
        consensus toward "unclear". It means that source has no opinion — it does not count as
        evidence against the claim being supported or contradicted.
        - Determine the overall consensus using only the sources that took a clear position
        (Supported/Contradicted/Misleading context/etc.). If a majority of those sources agree, state that as the
        consensus, and separately note how many sources abstained.
        - Only describe the overall picture as "unclear/not enough evidence" if the sources that DID
        take a position are themselves split or contradictory (e.g., one says Supported, one says Contradicted).
        Abstentions alone should never be the reason you call something unclear UNLESS all sources abstained.
        - If sources disagree, explicitly say so and describe the disagreement — don't average it
        into a mushy middle verdict.

        CONFIDENCE SCORE RULES:
        - Base confidence on agreement among sources that took a clear position.
        - Abstentions ("Unclear / Not enough evidence") should modestly lower confidence, since they
        reduce the amount of corroborating evidence — but should not lower it as much as an actual
        contradicting verdict would.
        - Only score above 0.9 if every source that took a position agrees, AND there are few or no
        abstentions.

        The 'reasoning' and 'verdict' fields should inform the summary, but do not repeat them verbatim.

        Claims and verdicts:
        {outlet_claims}
        """

        try:
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
            logger.info("Summarized claim: %.80s", key)
        except Exception as e:
            logger.error("Failed to summarize claim %.80r: %s", key, e)

    logger.info("Finished summarizing %d of %d claim group(s)",
                len(summaries), len(grouped_claims))

    return summaries
