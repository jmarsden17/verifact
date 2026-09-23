"""Outlet Analytics page: Refactored modular layout for publisher reliability."""

import pandas as pd
import streamlit as st

from database_conns import fetch_data as fn
from ..components.header import render_page_header
from ..components.section import render_section_heading
from ..components.chart_display import show_chart

from ..charts.outlet import (
    _explode_publishers,
    build_falsehood_density_matrix,
    build_syndication_network,
    build_jaccard_similarity_heatmap,
    build_quick_top_outlets_bar,
    build_quick_outlet_verdict_breakdown,
)


# Data processing

def _filter_by_outlets(df: pd.DataFrame, selected_outlets: list) -> pd.DataFrame:
    """Isolate specific outlets if any are selected."""

    if not selected_outlets:
        return df
    return df[df["publisher"].isin(selected_outlets)]


def _filter_by_volume(df: pd.DataFrame, min_volume: int) -> pd.DataFrame:
    """Filter out outlets below the minimum claim volume threshold."""

    counts = df["publisher"].value_counts()
    valid_outlets = counts[counts >= min_volume].index
    return df[df["publisher"].isin(valid_outlets)]


# UI functions

def _render_publisher_filters(exploded_df: pd.DataFrame) -> tuple:
    """Render publisher dropdowns and volume thresholds."""

    col_out, col_thresh = st.columns([3, 1])

    with col_out:
        all_outlets = sorted(exploded_df["publisher"].unique().tolist())
        selected_outlets = st.multiselect(
            "Focus on Specific Outlets", options=all_outlets, default=[])

    with col_thresh:
        min_volume = st.number_input("Min. Claim Volume", min_value=1, value=1)

    return selected_outlets, min_volume


def _render_explained_filter_bar(exploded_df: pd.DataFrame) -> pd.DataFrame:
    """Render collapsible publisher filter panel and return filtered dataset."""

    with st.expander("🔍 Publisher Search & Filters (Click to expand guidance)", expanded=True):
        selected_outlets, min_volume = _render_publisher_filters(exploded_df)

    filtered = _filter_by_outlets(exploded_df, selected_outlets)
    filtered = _filter_by_volume(filtered, min_volume)
    return filtered


def _render_quick_summary_row(exploded_df: pd.DataFrame):
    """Quick, on-the-go visual summaries for journalists."""

    col1, col2 = st.columns(2)

    with col1:
        st.caption("⚡ QUICK BREAKDOWN: TOP 5 OUTLETS BY VOLUME")
        show_chart(build_quick_top_outlets_bar(exploded_df))

    with col2:
        st.caption("⚡ QUICK BREAKDOWN: TOP OUTLETS VERDICT PROFILE")
        show_chart(build_quick_outlet_verdict_breakdown(exploded_df))


# Section rendering helpers

def _render_network_risk_section(filtered_exploded: pd.DataFrame, raw_df: pd.DataFrame):
    """Render reliability scatter matrix and co-publishing network bar chart."""

    col_rel, col_net = st.columns(2)

    with col_rel:
        render_section_heading("Outlet Reliability Map",
                               "Volume vs. proportion of disproven stories.")
        show_chart(build_falsehood_density_matrix(filtered_exploded))
        with st.expander("💡 Reporter's Field Notes: How to use these findings"):
            st.markdown("""
            * **Top-Right Outlets:** High-risk hubs with high volumes and high falsehood rates.
            * **Bottom-Right Outlets:** Highly reliable news sources with strong editorial checks.
            """)

    with col_net:
        render_section_heading("Top Co-Publishing Networks",
                               "Outlets co-publishing identical claims.")
        show_chart(build_syndication_network(raw_df))
        with st.expander("💡 Reporter's Field Notes: How to use these findings"):
            st.markdown(
                "* **Investigative Lead:** Repeated pairings signal shared syndication agreements or automated scraping.")


def _render_coordination_matrix_section(raw_df: pd.DataFrame):
    """Render Jaccard media overlap heatmap."""

    render_section_heading("Media Coordination & Overlap Matrix",
                           "Clusters indicate synchronized publishing across outlets.")
    show_chart(build_jaccard_similarity_heatmap(raw_df))
    with st.expander("💡 Reporter's Field Notes: How to use these findings"):
        st.markdown(
            "* **Dark Clusters:** Indicates synchronized publishing networks covering near-identical claim portfolios.")


def _build_scorecard_dataframe(filtered_exploded: pd.DataFrame) -> pd.DataFrame:
    """Aggregate statistics to form the publisher scorecard table."""

    scorecard = filtered_exploded.groupby("publisher").agg(
        total_claims=("claim_id", "nunique"),
        contradicted=("verdict", lambda x: (x == "Contradicted").sum()),
        missing_context=("verdict", lambda x: (x == "Missing Context").sum()),
        supported=("verdict", lambda x: (x == "Supported").sum()),
        primary_tactic=("technique", lambda x: x.mode()
                        [0] if not x.empty else "None")
    ).reset_index()

    scorecard["unreliability_index"] = (
        ((scorecard["contradicted"] + scorecard["missing_context"]
          ) / scorecard["total_claims"]) * 100
    ).round(1)

    return scorecard.sort_values(by="total_claims", ascending=False)


def _render_scorecard_section(filtered_exploded: pd.DataFrame):
    """Render summary table and table field notes."""

    render_section_heading("Publisher Reliability Scorecard",
                           "Monitored media outlets ranked by volume and flagged ratio.")

    scorecard_df = _build_scorecard_dataframe(filtered_exploded)

    st.dataframe(
        scorecard_df.rename(columns={
            "publisher": "Outlet / Publisher",
            "total_claims": "Total Claims Handled",
            "contradicted": "Disproven",
            "missing_context": "Missing Context",
            "supported": "Verified True",
            "unreliability_index": "Flagged Rate (%)",
            "primary_tactic": "Main Deception Tactic"
        }),
        use_container_width=True,
        hide_index=True
    )
    with st.expander("💡 Reporter's Field Notes: How to use this table"):
        st.markdown("""
        * **Background Check:** Sort by Flagged Rate (%) to evaluate unfamiliar sources.
        * **Tactic Column:** Reveals bias styles (e.g., *Missing Context* signals misleading framing).
        """)


# Main page

def render():
    """Main view rendering logic."""

    render_page_header(
        "Outlet & Source Network Intelligence",
        "Audit media reliability, expose coordinated republishing networks, and pinpoint high-risk news sources."
    )

    raw_df = fn.fetch_analytics_data()
    if raw_df.empty:
        st.warning(
            "⚠️ Unable to load live database records. Please check your system connection.")
        return

    exploded_df = _explode_publishers(raw_df)

    filtered_exploded = _render_explained_filter_bar(exploded_df)

    st.markdown("---")
    _render_quick_summary_row(filtered_exploded)

    st.markdown("---")
    _render_network_risk_section(filtered_exploded, raw_df)

    st.markdown("---")
    _render_coordination_matrix_section(raw_df)

    st.markdown("---")
    _render_scorecard_section(filtered_exploded)
