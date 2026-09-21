"""Claims Analytics page: verdict outcomes and technique trends across all claims."""

import pandas as pd
import streamlit as st
from database_conns import fetch_data as fn
from ..components.header import render_page_header
from ..components.section import render_section_heading

VERDICTS = ("Contradicted", "Supported", "Missing Context", "Unclear")


def _headline_metrics(df: pd.DataFrame) -> dict:
    """Numbers for the metric cards at the top of the page."""

    verdict_counts = df["verdict"].value_counts()
    return {
        "total_claims": len(df),
        "contradicted": int(verdict_counts.get("Contradicted", 0)),
        "supported": int(verdict_counts.get("Supported", 0)),
        "needs_context": int(
            verdict_counts.get("Missing Context", 0) +
            verdict_counts.get("Unclear", 0)
        ),
    }


def _render_metric_row(metrics: dict):
    """Render the row of headline metric cards."""

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(label="Total Claims Checked",
              value=f"{metrics['total_claims']:,}")
    m2.metric(label="Contradicted", value=f"{metrics['contradicted']:,}")
    m3.metric(label="Supported", value=f"{metrics['supported']:,}")
    m4.metric(label="Missing Context / Unclear",
              value=f"{metrics['needs_context']:,}")


def render():
    """Live claim-level analytics: verdict outcomes and disinformation techniques."""

    render_page_header(
        "Claims Analytics",
        "Verdict breakdowns and technique trends across all verified claims."
    )

    df = fn.fetch_analytics_data()

    if df.empty:
        st.warning(
            "⚠️ Unable to load live database records. Please verify your RDS connection settings in your environment.")
        return

    df["publish_datetime"] = pd.to_datetime(df["publish_datetime"])
    df["access_datetime"] = pd.to_datetime(df["access_datetime"])

    _render_metric_row(_headline_metrics(df))

    st.markdown("---")

    col_verdicts, col_techniques = st.columns(2)

    with col_verdicts:
        render_section_heading(
            "Verdict Distribution Over Time",
            "Breakdown of claim outcomes as they are verified.",
        )
        st.info("📊 Chart coming soon.")

    with col_techniques:
        render_section_heading(
            "Disinformation Technique Trends",
            "Most frequently used techniques across checked claims.",
        )
        st.info("📊 Chart coming soon.")

    st.markdown("---")
