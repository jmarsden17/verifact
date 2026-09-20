"""Handler to verify a claim against an article from a specified fact check site."""

import logging
from dotenv import load_dotenv
from .verify_llm import compare_claims_with_article
from .firecrawl_client import extract


def handler(event, context):
    """Handler to verify a claim against an article from a specified fact check site."""
    logging.basicConfig(level=logging.INFO)
    load_dotenv()

    claims_data = event["body"]
    source_url = event.get("source_url", "")
    source_name = event.get("source_name", "")

    results = []

    logging.info(
        "Starting verification of claims against the specified fact check site.")
    for claim_item in claims_data:
        if claim_item.get("skip_etl") is True:
            verdict = {
                "claim": claim_item.get("text"),
                "similar_claim": claim_item.get("similar_claim"),
                "similarity": claim_item.get("similarity"),
                "verdict": claim_item.get("verdict"),
                "summary": claim_item.get("summary"),
                "technique": claim_item.get("technique")
            }
            results.append(verdict)
            continue

        try:
            claim = claim_item.get("text")
            extracted_article, urls = extract(claim, source_url)
            if not extracted_article.strip():
                verdict = {
                    "claim": claim,
                    "verdict": "Unclear / Not enough evidence",
                    "reasoning": "No matching article found on this source.",
                    "misinformation_type": "None",
                    "entities": [],
                    "tags": [],
                    "sources": [],
                    "source_name": source_name,
                    "claim_embedding": claim_item.get('embedding')
                }
            else:
                verdict = compare_claims_with_article(claim, extracted_article)
                verdict["sources"] = urls
                verdict["claim"] = claim
                verdict["source_name"] = source_name
                verdict['claim_embedding'] = claim_item.get('embedding')

            results.append(verdict)
        except Exception as e:
            verdict = {
                "claim": claim,
                "verdict": "Unclear / Not enough evidence",
                "reasoning": f"Error processing claim: {e}",
                "misinformation_type": "None",
                "entities": [],
                "tags": [],
                "sources": [],
                "source_name": source_name,
                "claim_embeddding": claim_item.get('embedding')
            }
            results.append(verdict)

    return {
        "statusCode": 200,
        "body": results

    }
