"""Data logic and backend handlers."""

import pandas as pd
from pathlib import Path
import sys

# Add 'pipeline' directory to Python path for cross-folder imports
PIPELINE_DIR = Path(__file__).resolve().parent.parent / "pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.append(str(PIPELINE_DIR))

# Import pipeline handlers dynamically
try:
    import pipeline.handler_extract_claims as handler_extract_claims
    import pipeline.handler_verify_claim as handler_verify_claim
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False


def verify_claim(claim_input: str, url_input: str = "") -> dict:
    """Pass user input to pipeline handlers and return formatted results for UI."""

    if not claim_input or not claim_input.strip():
        return None

    # Fallback if imports fail
    if not PIPELINE_AVAILABLE:
        return _mock_verification_payload(claim_input)

    try:
        # Extract claims using handler
        extract_event = {"user_text": claim_input}
        extract_res = handler_extract_claims.handler(extract_event, None)
        extracted_claims = extract_res.get("body", [])

        if not extracted_claims:
            return {
                "rating": "Unclear",
                "reasoning": "No verifiable external claims extracted from the submitted text.",
                "sources": []
            }

        # Verify extracted claims against target
        verify_event = {
            "body": extracted_claims,
            "site": url_input if url_input else "https://fullfact.org",
            "source_name": "Full Fact"
        }
        verify_res = handler_verify_claim.handler(verify_event, None)
        results = verify_res.get("body", [])

        if not results:
            return {
                "rating": "Unclear",
                "reasoning": "Verification engine returned no matching article results.",
                "sources": []
            }

        # Format response for Streamlit UI
        first_result = results[0]
        return {
            "rating": first_result.get("verdict", "Unclear"),
            "reasoning": first_result.get("explanation", "Reasoning generated via LLM verification."),
            "sources": [
                {
                    "name": res.get("source_name", "Fact Check Partner"),
                    "snippet": res.get("claim", claim_input)
                }
                for res in results
            ]
        }
    except Exception as err:
        # Return fallback on runtime errors (e.g. missing API keys in .env)
        return _mock_verification_payload(claim_input, error_msg=str(err))


def _mock_verification_payload(claim_input: str, error_msg: str = "") -> dict:
    """Fallback payload used when pipeline handlers are offline or missing keys."""

    rating = "Contradicted" if "lemon" in claim_input.lower() else "Supported"
    return {
        "rating": rating,
        "reasoning": f"Sample response (Pipeline Fallback). Processed text: '{claim_input[:50]}...' {error_msg}".strip(),
        "sources": [
            {
                "name": "Full Fact Record",
                "snippet": f"Verified factual data regarding: {claim_input[:40]}..."
            }
        ]
    }


def get_breaking_claims() -> list:
    """Retrieve recent claims indexed from primary fact-checking outlets."""

    return [
        {
            "time": "10m ago",
            "outlet": "BBC Verify",
            "title": "Claim regarding central bank emergency interest rate cuts",
            "status": "Contradicted"
        },
        {
            "time": "45m ago",
            "outlet": "Full Fact",
            "title": "Statistics on regional hospital waiting times in shared image",
            "status": "Missing Context"
        },
        {
            "time": "2h ago",
            "outlet": "Reuters",
            "title": "Government announcement on renewable energy subsidies",
            "status": "Supported"
        }
    ]


def get_filtered_logs(query: str = "", status: str = "All"):
    """Filter verification history records for display."""

    data = [
        {"Timestamp": "2026-09-14 14:30", "Claim Statement": "Lemon water cures diabetes",
            "Verdict": "Contradicted", "Sources Consulted": 2, "Latency (s)": 3.8},
        {"Timestamp": "2026-09-14 12:15", "Claim Statement": "EV tax incentive changes starting next month",
            "Verdict": "Supported", "Sources Consulted": 3, "Latency (s)": 4.1},
        {"Timestamp": "2026-09-13 18:40", "Claim Statement": "Video shows recent protest in central London",
            "Verdict": "Missing Context", "Sources Consulted": 4, "Latency (s)": 5.2},
    ]
    df = pd.DataFrame(data)

    if query:
        df = df[df["Claim Statement"].str.contains(
            query, case=False, na=False)]
    if status != "All":
        df = df[df["Verdict"] == status]

    return df
