"""Handler to extract claims from user-provided text."""

from dotenv import load_dotenv
from llm_client import get_claims_from_user


def handler(event, context):
    """Handler to extract claims from user-provided text."""
    load_dotenv()
    input_text = event.get("user_text", "")
    analysis = get_claims_from_user(input_text)
    claims = []
    for claim in analysis["claims"]:
        if claim["verification_method"] == "external_search":
            claims.append(claim)

    return {
        "statusCode": 200,
        "body": claims
    }
