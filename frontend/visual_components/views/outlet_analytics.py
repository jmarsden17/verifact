"""Outlet Analytics page: headline metrics and charts from RDS."""

import pandas as pd
import streamlit as st
from database_conns import fetch_data as fn
from ..charts.outlet import build_outlet_chart
from ..charts.timeline import RESURFACED_AFTER_DAYS, build_recurrence_chart
from ..components.chart_display import show_chart
from ..components.header import render_page_header
from ..components.section import render_section_heading


def _most_common(df: pd.DataFrame, column: str) -> str:
    """Most frequent value in a column, or "N/A" when there is nothing to count."""

    if column in df and not df[column].dropna().empty:
        return df[column].mode()[0]
    return "N/A"


def _headline_metrics(df: pd.DataFrame) -> dict:
    """Numbers for the metric cards at the top of the page."""

    days_to_resurface = (df["access_datetime"] -
                         df["publish_datetime"]).dt.days
    return {
        "total_claims": len(df),
        "resurfaced": int((days_to_resurface > RESURFACED_AFTER_DAYS).sum()),
        # NOTE: "publisher" holds combined strings like "BBC Verify, Reuters",
        # so this is the most common *combination*, not the top single outlet.
        "top_publisher": _most_common(df, "publisher"),
        "top_technique": _most_common(df, "technique"),
    }


def _render_metric_row(metrics: dict):
    """Render the row of headline metric cards."""

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(label="Total Claims Checked",
              value=f"{metrics['total_claims']:,}")
    m2.metric(label="Primary Outlet Source", value=metrics["top_publisher"])
    m3.metric(label="Top Technique Used", value=metrics["top_technique"])
    m4.metric(label="Resurfaced Myths (>7d)",
              value=f"{metrics['resurfaced']:,}")


def render():
    """Live metric cards & relational data analytics powered by RDS."""

    render_page_header(
        "Outlet Source Analytics",
        "Live distribution metrics across ingested fact-checking partners and techniques."
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

    col_publisher, col_recurrence = st.columns(2)

    with col_publisher:
        render_section_heading(
            "Verifications by Fact-Checking Publisher",
            "Live volume of claims indexed across verified primary partners.",
        )
        show_chart(build_outlet_chart(df))

    with col_recurrence:
        render_section_heading(
            "Claim Ingestion & Recurrence Rate",
            "Comparing new claims against queries resurfacing long after publication.",
        )
        show_chart(build_recurrence_chart(df))

    st.markdown("---")
