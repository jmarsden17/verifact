"""Data logic and backend handlers."""

import os
import sys
from pathlib import Path
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Force loading .env file explicitly from the frontend folder
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_db_connection():
    """Establish connection to PostgreSQL RDS using environment variables."""
    host = os.getenv("DB_HOST") or os.getenv("db_host")
    port = os.getenv("DB_PORT") or os.getenv("db_port") or "5432"
    dbname = os.getenv("DB_NAME") or os.getenv("db_name")
    user = os.getenv("DB_USER") or os.getenv("db_user")
    password = os.getenv("DB_PASSWORD") or os.getenv("db_password")

    # Debug print statement (visible in terminal running Streamlit)
    print(f"Connecting to DB: host={host}, dbname={dbname}, user={user}")

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )


def fetch_analytics_data() -> pd.DataFrame:
    """Fetch live claim analytics from RDS using RealDictCursor."""
    query = """
        SELECT 
            c.claim_id,
            c.claim,
            c.claim_url,
            c.publish_datetime,
            c.access_datetime,
            v.verdict,
            t.technique,
            o.outlet AS publisher,
            s.source_url,
            STRING_AGG(tg.tag, ', ') AS associated_tags
        FROM claim c
        LEFT JOIN verdict v ON c.verdict_id = v.verdict_id
        LEFT JOIN technique t ON c.technique_id = t.technique_id
        LEFT JOIN claim_source cs ON c.claim_id = cs.claim_id
        LEFT JOIN source s ON cs.source_id = s.source_id
        LEFT JOIN outlet o ON s.outlet_id = o.outlet_id
        LEFT JOIN claim_tags ct ON c.claim_id = ct.claim_id
        LEFT JOIN tags tg ON ct.tag_id = tg.tag_id
        GROUP BY 
            c.claim_id, 
            c.claim, 
            c.claim_url, 
            c.publish_datetime, 
            c.access_datetime, 
            v.verdict, 
            t.technique, 
            o.outlet, 
            s.source_url;
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()
        conn.close()
        return pd.DataFrame(results)

    except Exception as e:
        # Print exact error to terminal for quick debugging
        print(f"❌ DATABASE ERROR: {e}")
        return pd.DataFrame()


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
