"""Handler to extract claims from user-provided text."""

import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from extract_llm import get_claims_from_user
from db_connection import find_most_similar_claim


def handler(event, context):
    """Handler to extract claims from user-provided text and find similar claims in the database."""
    logging.basicConfig(level=logging.INFO)

    load_dotenv()
    input_text = event.get("user_text", "")

    logging.info("Extracting claims from inputted text.")
    analysis = get_claims_from_user(input_text)
    claims = []
    logging.info(
        "Processing each claim to find similar claims in the database.")
    for claim in analysis["claims"]:
        if claim["verification_method"] == "external_search":
            logging.info("Generating embedding for claim: %s", claim["text"])
            claim["embedding"] = generate_embeddings(claim["text"])

            logging.info("Finding most similar claim in the database.")
            similar_claim, similarity, verdict, summary, technique = find_most_similar_claim(
                claim["embedding"])

            logging.info(
                "Most similar claim found: %s with similarity: %s", similar_claim, similarity)
            claim["similar_claim"] = similar_claim
            claim["similarity"] = similarity
            claim["verdict"] = verdict
            claim["summary"] = summary
            claim["technique"] = technique
            claims.append(claim)

    for claim in claims:
        if claim["similar_claim"] is not None:
            claim["skip_etl"] = True
        else:
            claim["skip_etl"] = False

    return {
        "statusCode": 200,
        "body": {
            "to_process": [c for c in claims if not c.get("skip_etl")],
            "skipped":    [c for c in claims if c.get("skip_etl")],
        }
    }


def generate_embeddings(claim: str) -> list[float]:
    """Generate embedding vector for a given claim using OpenAI's API."""
    load_dotenv()

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                    base_url=os.environ["OPENAI_BASE_URL"])

    response = client.embeddings.create(
        input=claim,
        model="text-embedding-3-small",
        dimensions=1536
    )
    embedding_vector = response.data[0].embedding

    logging.info("Generated embedding vector for claim: %s", claim)
    return embedding_vector
