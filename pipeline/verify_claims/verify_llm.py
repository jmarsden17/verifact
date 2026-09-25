"""LLM client functions for extracting and comparing claims using the OpenAI SDK."""
 
 
import logging
import os
 
from openai import OpenAI
from verify_models import VerdictResult
 
 
def compare_claims_with_article(user_text: str, article_text: str) -> dict:
    """Send text to LLM service using the official OpenAI SDK."""
    api_key = os.environ["OPENAI_API_KEY"]
    base_url = os.environ["OPENAI_BASE_URL"]
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
 
    logging.info("Comparing claim against article (%d chars): %.80s",
                len(article_text or ""), user_text)
 
    prompt = f"""
    Analyze the following verified article text in relation to the user's claim:
    1. First, ensure you ignore any irrelevant articles. The tool can sometimes return unrelated content. Ignore these if they are irrelevant for proving/disproving the claim.
    2. Compare the article's claims with the user's claim and identify any agreements or discrepancies.
    3. Return exactly one of the allowed verdicts: "Supported", "Contradicted", "Missing Context", or "Unclear".    
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
    result = response.choices[0].message.parsed.model_dump()
    logging.info("Verdict: %s", result.get("verdict"))
    return result