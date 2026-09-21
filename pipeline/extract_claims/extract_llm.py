"""LLM client functions for extracting claims using the OpenAI SDK."""
import os
import logging

from openai import OpenAI, APIConnectionError, AuthenticationError, APIStatusError
from extract_models import InputAnalysis, Claim


def get_claims_from_user(text: str) -> dict:
    """Send text to LLM service using the official OpenAI SDK."""
    print("handler invoked", flush=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    api_key = os.environ["OPENAI_API_KEY"]
    if not api_key:
        logger.error("OPENAI_API_KEY is not set")
        return False

    if api_key != api_key.strip():
        logger.warning(
            "OPENAI_API_KEY has leading/trailing whitespace or a newline")

    logger.info(
        "OPENAI_API_KEY loaded: length=%d, prefix=%s, suffix=%s",
        len(api_key), api_key[:3], api_key[-4:],
    )

    base_url = os.environ["OPENAI_BASE_URL"]

    if check_openai_connection() == False:
        logger.error("OpenAI connection check failed")
        return False
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    prompt = f"""
    Analyze the following article text:
    1. Extract specific key claims and statements from the article, ensuring each claim is individual and atomic.
    2. Assign relevant topic tags to each claim based on its content.
    3. Assign a type to each claim based on its content.
    4. Determine if the claim is checkable.
    5. Return the extracted claims and statements in a structured JSON format.

    Note:
    Discard vague summarizing statements like "X promoted their accomplishments" or "X rallied supporters" — these have no checkable content.
    For claims about what someone said or promised, mark them as "opinion" or "promise" rather than treating them as claims requiring external verification.

    Text:
    {text}
    """
    response = client.beta.chat.completions.parse(
        model="gpt-5.6-luna",
        messages=[
            {
                "role": "system",
                "content": "You are a precise data extraction and assignment assistant working to extract claims to be used in a disinformation verifier.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format=InputAnalysis,
    )
    return response.choices[0].message.parsed.model_dump()


def check_openai_connection() -> bool:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # Layer 3: authenticated call
    try:
        client = OpenAI(timeout=10, max_retries=0)
        models = client.models.list()
        logger.info("Authenticated OK, %d models visible", len(list(models)))
        return True
    except AuthenticationError as e:
        logger.error("Key rejected (401): %s", e)
    except APIConnectionError as e:
        logger.error("Connection error: %s | cause: %r", e, e.__cause__)
    except APIStatusError as e:
        logger.error("API returned %s: %s", e.status_code, e.message)
    return False
