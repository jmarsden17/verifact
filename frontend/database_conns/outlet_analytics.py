"""Data logic for the Outlet Analytics page."""

import pandas as pd

from .connection import get_db_connection

TIME_BUCKETS = {
    "Day": "day",
    "Week": "week",
    "Month": "month",
}

# Outlet-level: claims checked, false-claim rate, and how many other outlets
# also covered the same claims (a rough cross-verification signal).
OUTLET_SUMMARY_QUERY = """
    SELECT
        o.outlet_id,
        o.outlet,
        COUNT(DISTINCT c.claim_id) AS claims_checked,
        COUNT(DISTINCT c.claim_id) FILTER (
            WHERE LOWER(v.verdict) IN ('contradicted', 'missing context')
        ) AS false_claims,
        ROUND(
            COUNT(DISTINCT c.claim_id) FILTER (
                WHERE LOWER(v.verdict) IN ('contradicted', 'missing context')
            )::numeric / NULLIF(COUNT(DISTINCT c.claim_id), 0) * 100,
            1
        ) AS false_claim_rate
    FROM outlet o
    JOIN source s ON s.outlet_id = o.outlet_id
    JOIN claim_source cs ON cs.source_id = s.source_id
    JOIN claim c ON c.claim_id = cs.claim_id
    LEFT JOIN verdict v ON v.verdict_id = c.verdict_id
    GROUP BY o.outlet_id, o.outlet
    HAVING COUNT(DISTINCT c.claim_id) >= %s
    ORDER BY claims_checked DESC
"""

# How many outlets independently covered each claim - the "variety" signal.
CROSS_VERIFICATION_QUERY = """
    SELECT
        c.claim_id,
        COUNT(DISTINCT o.outlet_id) AS outlet_count
    FROM claim c
    JOIN claim_source cs ON cs.claim_id = c.claim_id
    JOIN source s ON s.source_id = cs.source_id
    JOIN outlet o ON o.outlet_id = s.outlet_id
    GROUP BY c.claim_id
"""

# Claims checked per outlet over time, for the top N outlets by volume.
OUTLET_TIMELINE_QUERY = """
    SELECT
        o.outlet,
        DATE_TRUNC(%s, COALESCE(c.publish_datetime, c.access_datetime)) AS period,
        COUNT(DISTINCT c.claim_id) AS claims_checked
    FROM outlet o
    JOIN source s ON s.outlet_id = o.outlet_id
    JOIN claim_source cs ON cs.source_id = s.source_id
    JOIN claim c ON c.claim_id = cs.claim_id
    WHERE o.outlet = ANY(%s)
    GROUP BY o.outlet, period
    ORDER BY period
"""


def get_outlet_summary(min_claims: int = 1) -> pd.DataFrame:
    """One row per outlet: claims checked, false-claim rate, ordered by volume.

    min_claims: drop outlets below this claim count (avoids a single false
    claim looking like a "100% false" outlet on 1 data point).

    If the database can't be reached, returns clearly-marked sample data
    (df.attrs["is_sample"] is True) so the page can warn the user.
    """

    try:
        conn = get_db_connection()
        try:
            return pd.read_sql(OUTLET_SUMMARY_QUERY, conn, params=(min_claims,))
        finally:
            conn.close()
    except Exception as e:
        print(f"⚠️ Outlet summary query failed: {e}")
        return _sample_outlet_summary(min_claims)


def get_cross_verification_counts() -> pd.DataFrame:
    """One row per claim: how many distinct outlets covered it.

    Feeds a histogram of "how many outlets typically check the same claim" -
    the variety-in-outlets signal from the design notes.
    """

    try:
        conn = get_db_connection()
        try:
            return pd.read_sql(CROSS_VERIFICATION_QUERY, conn)
        finally:
            conn.close()
    except Exception as e:
        print(f"⚠️ Cross-verification query failed: {e}")
        return _sample_cross_verification()


def get_outlet_timeline(outlets: list, bucket: str = "Week") -> pd.DataFrame:
    """Claims-checked-over-time, one series per outlet in `outlets`.

    bucket: one of TIME_BUCKETS keys ("Day", "Week", "Month").
    """

    trunc = TIME_BUCKETS.get(bucket, "week")

    if not outlets:
        return pd.DataFrame(columns=["outlet", "period", "claims_checked"])

    try:
        conn = get_db_connection()
        try:
            return pd.read_sql(
                OUTLET_TIMELINE_QUERY, conn, params=(trunc, outlets)
            )
        finally:
            conn.close()
    except Exception as e:
        print(f"⚠️ Outlet timeline query failed: {e}")
        return _sample_outlet_timeline(outlets, bucket)


def _sample_outlet_summary(min_claims: int) -> pd.DataFrame:
    df = pd.DataFrame([
        {"outlet_id": 1, "outlet": "BBC Verify", "claims_checked": 42,
            "false_claims": 30, "false_claim_rate": 71.4},
        {"outlet_id": 2, "outlet": "Reuters", "claims_checked": 35,
            "false_claims": 12, "false_claim_rate": 34.3},
        {"outlet_id": 3, "outlet": "Full Fact", "claims_checked": 28,
            "false_claims": 22, "false_claim_rate": 78.6},
        {"outlet_id": 4, "outlet": "Wikipedia", "claims_checked": 15,
            "false_claims": 4, "false_claim_rate": 26.7},
    ])
    df = df[df["claims_checked"] >= min_claims].reset_index(drop=True)
    df.attrs["is_sample"] = True
    return df


def _sample_cross_verification() -> pd.DataFrame:
    df = pd.DataFrame(
        [{"claim_id": i, "outlet_count": n} for i, n in
         enumerate([1, 1, 1, 2, 2, 2, 2, 3, 3, 4], start=1)]
    )
    df.attrs["is_sample"] = True
    return df


def _sample_outlet_timeline(outlets: list, bucket: str) -> pd.DataFrame:
    periods = pd.date_range(
        end=pd.Timestamp.now().normalize(), periods=6, freq="W")
    rows = []
    for outlet in outlets:
        for i, period in enumerate(periods):
            rows.append({
                "outlet": outlet,
                "period": period,
                "claims_checked": 3 + (i * 2) % 7,
            })
    df = pd.DataFrame(rows)
    df.attrs["is_sample"] = True
    return df
