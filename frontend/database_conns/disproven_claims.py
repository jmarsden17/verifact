"""Data logic for the Latest Disproven Claims feed."""

import pandas as pd
from .connection import get_db_connection

SORT_ORDERS = {
    "newest": "c.publish_datetime DESC NULLS LAST, c.access_datetime DESC NULLS LAST",
    "most_checked": "c.access_amount DESC NULLS LAST, c.publish_datetime DESC NULLS LAST",
}

QUERY = """
    SELECT
        c.claim_id,
        c.claim AS claim_text,
        c.summary,
        v.verdict,
        t.technique,
        c.publish_datetime,
        c.access_datetime,
        c.access_amount,
        STRING_AGG(DISTINCT o.outlet, ', ') AS publishers,
        JSONB_AGG(DISTINCT JSONB_BUILD_OBJECT('outlet', o.outlet, 'url', s.source_url))
            FILTER (WHERE s.source_url IS NOT NULL) AS source_links
    FROM claim c
    JOIN verdict v ON c.verdict_id = v.verdict_id
    LEFT JOIN technique t ON c.technique_id = t.technique_id
    LEFT JOIN claim_source cs ON c.claim_id = cs.claim_id
    LEFT JOIN source s ON cs.source_id = s.source_id
    LEFT JOIN outlet o ON s.outlet_id = o.outlet_id
    WHERE LOWER(v.verdict) IN ('contradicted', 'missing context')
    {verdict_clause}
    GROUP BY c.claim_id, c.claim, c.summary, v.verdict, t.technique,
             c.publish_datetime, c.access_datetime, c.access_amount
    ORDER BY {order_by}
    LIMIT %s
"""


def get_disproven_claims(sort: str = "newest", verdict: str = "All",
                         limit: int = 10) -> pd.DataFrame:
    """Contradicted / Missing Context claims, newest (by publish date) first by default."""

    order_by = SORT_ORDERS.get(sort, SORT_ORDERS["newest"])
    params = []

    verdict_clause = ""
    if verdict != "All":
        verdict_clause = "AND LOWER(v.verdict) = LOWER(%s)"
        params.append(verdict)

    params.append(limit)
    query = QUERY.format(verdict_clause=verdict_clause, order_by=order_by)

    try:
        conn = get_db_connection()
        try:
            return pd.read_sql(query, conn, params=tuple(params))
        finally:
            conn.close()
    except Exception as e:
        print(f"⚠️ Disproven claims query failed: {e}")
        return _sample_claims(sort, verdict, limit)


def _sample_claims(sort: str, verdict: str, limit: int) -> pd.DataFrame:
    """Placeholder rows used only when the database is unreachable."""

    today = pd.Timestamp.now().normalize()

    df = pd.DataFrame([
        {
            "claim_id": 1,
            "claim_text": "Central bank is planning an emergency 200 basis point rate cut.",
            "summary": "Monetary policy documents confirm interest rate discussions, but no emergency cut has been scheduled.",
            "verdict": "Missing Context",
            "technique": "Policy Distortion",
            "publish_datetime": today - pd.Timedelta(days=1),
            "access_datetime": today,
            "access_amount": 8,
            "publishers": "Wikipedia",
            "source_links": [{"outlet": "Wikipedia", "url": "https://en.wikipedia.org"}],
        },
        {
            "claim_id": 2,
            "claim_text": "Drinking warm lemon water daily completely cures type 2 diabetes.",
            "summary": "No clinical evidence supports claims that lemon water reverses or cures diabetes.",
            "verdict": "Contradicted",
            "technique": "False Medical Claim",
            "publish_datetime": today - pd.Timedelta(days=3),
            "access_datetime": today - pd.Timedelta(days=1),
            "access_amount": 42,
            "publishers": "BBC Verify, Full Fact",
            "source_links": [
                {"outlet": "Full Fact", "url": "https://fullfact.org"},
                {"outlet": "BBC Verify", "url": "https://www.bbc.co.uk/news/bbcverify"},
            ],
        },
        {
            "claim_id": 3,
            "claim_text": "The moon is made of green cheese.",
            "summary": None,
            "verdict": "Contradicted",
            "technique": "Deepfake",
            "publish_datetime": today - pd.Timedelta(days=9),
            "access_datetime": today - pd.Timedelta(days=2),
            "access_amount": 5,
            "publishers": "BBC Verify, Reuters",
            "source_links": None,
        },
    ])

    if verdict != "All":
        df = df[df["verdict"].str.lower() == verdict.lower()]

    sort_column = "access_amount" if sort == "most_checked" else "publish_datetime"
    df = df.sort_values(sort_column, ascending=False).head(
        limit).reset_index(drop=True)
    df.attrs["is_sample"] = True
    return df
