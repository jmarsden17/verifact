"""Handler to verify a claim against an article from a specified fact check site."""

from dotenv import load_dotenv
from llm_client import compare_claims_with_article
from firecrawl_client import extract


def handler(event, context):
    """Handler to verify a claim against an article from a specified fact check site."""
    load_dotenv()

    claims_data = event["body"]
    site = event.get("site", "")
    source_name = event.get("source_name", "")

    results = []

    for claim_item in claims_data:
        claim = claim_item.get("text")
        extracted_article = extract(claim, site)
        verdict = compare_claims_with_article(claim, extracted_article)

        verdict["claim"] = claim
        verdict["source_name"] = source_name

        results.append(verdict)

    return {
        "statusCode": 200,
        "body": results

    }
