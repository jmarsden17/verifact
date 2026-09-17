"""LLM client functions for extracting and comparing claims using the OpenAI SDK."""


import os

from openai import OpenAI
from models import InputAnalysis, VerdictResult, Claim


def get_claims_from_user(text: str) -> dict:
    """Send text to LLM service using the official OpenAI SDK."""
    api_key = os.environ["OPENAI_API_KEY"]
    base_url = os.environ["OPENAI_BASE_URL"]
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


def compare_claims_with_article(user_text: str, article_text: str) -> dict:
    """Send text to LLM service using the official OpenAI SDK."""
    api_key = os.environ["OPENAI_API_KEY"]
    base_url = os.environ["OPENAI_BASE_URL"]
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    prompt = f"""
    Analyze the following verified article text in relation to the user's claim:
    1. Compare the article's claims with the user's claim and identify any agreements or discrepancies.
    2. Return exactly one of the allowed verdicts: "Supported", "Contradicted", "Missing Context", or "Unclear".    
    User Claim:
    {user_text}
    Article Text:
    {article_text}
    """
    response = client.beta.chat.completions.parse(
        model="gpt-5.6-luna",
        messages=[
            {
                "role": "system",
                "content": "You are a precise text comparison assistant.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format=VerdictResult,
    )
    return response.choices[0].message.parsed.model_dump()
