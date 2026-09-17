"""Handler to extract claims from user-provided text."""

import os
from openai import OpenAI
from dotenv import load_dotenv
from llm_client import get_claims_from_user
from db_connection import find_most_similar_claim


def handler(event, context):
    """Handler to extract claims from user-provided text."""
    load_dotenv()
    input_text = event.get("user_text", "")
    analysis = get_claims_from_user(input_text)
    claims = []
    for claim in analysis["claims"]:
        if claim["verification_method"] == "external_search":
            claim["embedding"] = generate_embeddings(claim["text"])
            similar_claim, similarity = find_most_similar_claim(
                claim["embedding"])
            claim["similar_claim"] = similar_claim
            claim["similarity"] = similarity
            claims.append(claim)

    for claim in claims:
        if claim["similar_claim"] is not None:
            claim["skip_etl"] = True
        else:
            claim["skip_etl"] = False

    return {
        "statusCode": 200,
        "body": claims
    }


def generate_embeddings(claim: str) -> list[int]:
    """Generate embedding vector for a given claim using OpenAI's API."""
    load_dotenv()
    api_key = os.environ["OPENAI_API_KEY"]

    client = OpenAI(api_key=api_key)

    response = client.embeddings.create(
        input=claim,
        model="text-embedding-3-small"
    )
    embedding_vector = response.data[0].embedding
    return embedding_vector
