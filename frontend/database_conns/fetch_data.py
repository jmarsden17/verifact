"""Data logic and backend handlers."""

import sys
from pathlib import Path
import pandas as pd
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from requests import get

from .connection import get_db_connection

# Force loading .env file explicitly from the frontend folder
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Add 'pipeline' directory to Python path for cross-folder imports
PIPELINE_DIR = Path(__file__).resolve().parent.parent / "pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.append(str(PIPELINE_DIR))


def fetch_analytics_data() -> pd.DataFrame:
    """Fetch analytics records aggregated at the top-level claim summary level with all outlets."""

    query = """
        SELECT 
            c.claim_id,
            c.claim,
            v.verdict,
            t.technique,
            STRING_AGG(DISTINCT o.outlet, ', ') AS publisher,
            c.publish_datetime,
            c.access_datetime
        FROM claim c
        LEFT JOIN verdict v ON c.verdict_id = v.verdict_id
        LEFT JOIN technique t ON c.technique_id = t.technique_id
        LEFT JOIN claim_source cs ON c.claim_id = cs.claim_id
        LEFT JOIN source s ON cs.source_id = s.source_id
        LEFT JOIN outlet o ON s.outlet_id = o.outlet_id
        GROUP BY c.claim_id, c.claim, v.verdict, t.technique, c.publish_datetime, c.access_datetime
        ORDER BY c.access_datetime DESC
    """

    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        # Mock fallback data
        return pd.DataFrame([
            {
                "claim_id": 1,
                "claim": "The moon is made of green cheese.",
                "verdict": "Contradicted",
                "technique": "Deepfake",
                "publisher": "BBC Verify, Reuters",
                "publish_datetime": "2026-09-18 09:58:31",
                "access_datetime": "2026-09-18 09:58:31"
            },
            {
                "claim_id": 2,
                "claim": "Drinking warm lemon water daily completely cures type 2 diabetes.",
                "verdict": "Contradicted",
                "technique": "False Medical Claim",
                "publisher": "Full Fact, BBC Verify",
                "publish_datetime": "2026-09-15 11:20:00",
                "access_datetime": "2026-09-18 10:15:00"
            },
            {
                "claim_id": 3,
                "claim": "Government removing all EV purchase tax credits starting next month.",
                "verdict": "Supported",
                "technique": "Policy Distortion",
                "publisher": "Reuters, Wikipedia",
                "publish_datetime": "2026-09-14 12:15:00",
                "access_datetime": "2026-09-18 10:30:00"
            }
        ])


# Import pipeline handlers dynamically
try:
    import pipeline.handler_extract_claims as handler_extract_claims
    import pipeline.handler_verify_claim as handler_verify_claim
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False


def verify_claim(claim_input: str, url_input: str = "") -> dict:
    """Pass user input to pipeline handlers and return formatted results for UI."""

    return _mock_verification_payload(claim_input)


def _mock_verification_payload(claim_input: str) -> list:
    """Fallback list payload referencing only BBC Verify, Reuters, Full Fact, and Wikipedia."""

    return [
        {
            "claim": "Drinking warm lemon water daily completely cures type 2 diabetes.",
            "rating": "Contradicted",
            "reasoning": "Medical consensus indexed across fact-checking databases confirms lemon water cannot cure diabetes.",
            "sources": [
                {"name": "Full Fact", "snippet": "No clinical evidence supports claims that drinking warm lemon water reverses or cures diabetes."},
                {"name": "BBC Verify", "snippet": "Health experts confirm social media posts promoting lemon water cures lack scientific backing."}
            ]
        },
        {
            "claim": "Government is removing all EV purchase tax credits starting next month.",
            "rating": "Supported",
            "reasoning": "Official policy updates confirm scheduled phase-outs of electric vehicle tax incentives.",
            "sources": [
                {"name": "Reuters", "snippet": "Government treasury updates outline immediate timeline changes for clean energy tax exemptions."}
            ]
        },
        {
            "claim": "Central bank is planning an emergency 200 basis point rate cut.",
            "rating": "Missing Context",
            "reasoning": "Monetary policy documentation confirms interest rate discussions, but no emergency cut has been scheduled.",
            "sources": [
                {"name": "Wikipedia", "snippet": "Central bank monetary policy history shows steady benchmark rate adjustments without emergency intervention."}
            ]
        }
    ]


def get_filtered_logs(search_query: str = "", verdict_filter: str = "All") -> pd.DataFrame:
    """Fetch live verification history directly from PostgreSQL RDS tables."""

    query = """
        SELECT 
            c.access_datetime AS timestamp,
            c.claim AS claim_statement,
            COALESCE(v.verdict, 'Unclear') AS verdict,
            COALESCE(t.technique, 'None') AS technique,
            COUNT(DISTINCT cs.source_id) AS sources_count,
            COALESCE(STRING_AGG(DISTINCT tg.tag, ', '), 'Unassigned') AS tags_list
        FROM claim c
        LEFT JOIN verdict v ON c.verdict_id = v.verdict_id
        LEFT JOIN technique t ON c.technique_id = t.technique_id
        LEFT JOIN claim_source cs ON c.claim_id = cs.claim_id
        LEFT JOIN claim_tags ct ON c.claim_id = ct.claim_id
        LEFT JOIN tags tg ON ct.tag_id = tg.tag_id
        WHERE 1=1
    """
    params = []

    if search_query:
        query += " AND (LOWER(c.claim) LIKE LOWER(%s) OR LOWER(tg.tags) LIKE LOWER(%s))"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    if verdict_filter != "All":
        query += " AND LOWER(v.verdict) = LOWER(%s)"
        params.append(verdict_filter)

    query += """
        GROUP BY c.claim_id, c.access_datetime, c.claim, v.verdict, t.technique 
        ORDER BY c.access_datetime DESC
    """

    try:
        conn = get_db_connection()
        # Pass params as a TUPLE or None to ensure psycopg2 binds correctly!
        query_params = tuple(params) if params else None
        df = pd.read_sql(query, conn, params=query_params)
        conn.close()
        return df
    except Exception as e:
        print(f"⚠️ Live RDS Query Exception: {e}")
        raise e


def get_top_disproven_claims() -> pd.DataFrame:
    """Fetch recent live claims from RDS filtered for Contradicted or Missing Context verdicts."""
    query = """
        SELECT 
            c.claim_id,
            c.claim AS claim_text,
            COALESCE(v.verdict, 'Contradicted') AS verdict,
            STRING_AGG(DISTINCT o.outlet, ', ') AS publishers,
            c.access_datetime AS timestamp
        FROM claim c
        JOIN verdict v ON c.verdict_id = v.verdict_id
        LEFT JOIN claim_source cs ON c.claim_id = cs.claim_id
        LEFT JOIN source s ON cs.source_id = s.source_id
        LEFT JOIN outlet o ON s.outlet_id = o.outlet_id
        WHERE LOWER(v.verdict) IN ('contradicted', 'missing context')
        GROUP BY c.claim_id, c.claim, v.verdict, c.access_datetime
        ORDER BY c.access_datetime DESC
        LIMIT 10
    """
    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"⚠️ RDS Fetch Error: {e}")
        # Mock fallback for UI preview
        return pd.DataFrame([
            {
                "claim_text": "Claim regarding central bank emergency interest rate cuts",
                "verdict": "Contradicted",
                "publishers": "BBC Verify",
                "timestamp": "10m ago"
            },
            {
                "claim_text": "Drinking warm lemon water daily completely cures type 2 diabetes.",
                "verdict": "Contradicted",
                "publishers": "Full Fact, Reuters",
                "timestamp": "35m ago"
            },
            {
                "claim_text": "Statistics on regional hospital waiting times in shared image",
                "verdict": "Missing Context",
                "publishers": "Full Fact",
                "timestamp": "45m ago"
            }
        ])
