"""Claims Analytics page: Refactored modular layout for narrative intelligence."""

import numpy as np
import pandas as pd
import streamlit as st

from database_conns import fetch_data as fn
from ..components.header import render_page_header
from ..components.section import render_section_heading
from ..components.chart_display import show_chart

from ..charts.claims import (
    build_quadrant_chart,
    build_technique_breakdown,
    build_technique_latency_boxplot,
    build_narrative_decay_curve,
    build_tfidf_keyword_chart,
    build_quick_verdict_donut,
    build_quick_top_tactics_bar,
)


# --- DATA PREPROCESSING HELPERS ---

def _preprocess_claims_data(df: pd.DataFrame) -> pd.DataFrame:
    """Add calculated intelligence fields: days latent, outlet counts, and spread velocity."""
    df = df.copy()
    df["publish_datetime"] = pd.to_datetime(df["publish_datetime"])
    df["access_datetime"] = pd.to_datetime(df["access_datetime"])

    df["days_latent"] = (df["access_datetime"] -
                         df["publish_datetime"]).dt.total_seconds() / (24 * 3600)
    df["days_latent"] = df["days_latent"].clip(lower=0)

    df["publisher_str"] = df["publisher"].fillna("Unattributed").astype(str)
    df["outlet_list"] = df["publisher_str"].str.split(", ")
    df["outlet_count"] = df["outlet_list"].apply(len)
    df["velocity"] = np.where(
        df["days_latent"] > 0, df["outlet_count"] / (df["days_latent"] + 1), df["outlet_count"])

    return df


def _apply_keyword_filter(df: pd.DataFrame, keywords: str) -> pd.DataFrame:
    """Filter records by entity or topic keyword matches."""
    if not keywords:
        return df
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    pattern = "|".join(kw_list)
    return df[
        df["claim"].str.contains(pattern, case=False, na=False) |
        df["publisher_str"].str.contains(pattern, case=False, na=False)
    ]


def _apply_metadata_filters(df: pd.DataFrame, verdicts: list, techniques: list, min_outlets: int, latency_mode: str) -> pd.DataFrame:
    """Filter records by categorical verdicts, techniques, and temporal lifecycles."""
    filtered = df.copy()
    if verdicts:
        filtered = filtered[filtered["verdict"].isin(verdicts)]
    if techniques:
        filtered = filtered[filtered["technique"].isin(techniques)]

    filtered = filtered[filtered["outlet_count"] >= min_outlets]

    if latency_mode == "Breaking / Viral (<7 Days)":
        filtered = filtered[filtered["days_latent"] <= 7]
    elif latency_mode == "Resurfaced Myths (>7 Days)":
        filtered = filtered[filtered["days_latent"] > 7]

    return filtered


# --- UI COMPONENT FUNCTIONS ---

def _render_filter_controls(df: pd.DataFrame) -> tuple:
    """Render filter UI inputs and return raw filter selections."""
    col_search, col_verdict = st.columns([2, 1])

    with col_search:
        keywords = st.text_input(
            "Search Topics or Entities",
            placeholder="e.g. Johnny Depp, Ukraine, Taxes, Vaccines...",
            help="💡 Filter by specific public figures, conflict zones, or policy debates."
        )

    with col_verdict:
        all_verdicts = sorted(df["verdict"].dropna().unique().tolist())
        selected_verdicts = st.multiselect(
            "Fact-Check Outcome",
            options=all_verdicts,
            default=all_verdicts,
            help="💡 Focus on 'Contradicted' for proven falsehoods."
        )

    col_tech, col_outlets, col_latency = st.columns([1.5, 1, 1])

    with col_tech:
        all_techniques = sorted(df["technique"].dropna().unique().tolist())
        selected_techniques = st.multiselect(
            "Deception Tactic Used",
            options=all_techniques,
            default=[],
            help="💡 Filter by manipulation type."
        )

    with col_outlets:
        min_outlets = st.slider("Min. Outlets Carrying Claim", 1, 10, 1)

    with col_latency:
        latency_mode = st.selectbox(
            "Story Lifecycle",
            ["All Claims",
                "Breaking / Viral (<7 Days)", "Resurfaced Myths (>7 Days)"]
        )

    return keywords, selected_verdicts, selected_techniques, min_outlets, latency_mode


def _render_explained_filter_bar(df: pd.DataFrame) -> pd.DataFrame:
    """Render collapsible filter engine and return filtered dataframe."""
    with st.expander("🔍 Filter & Story Search Controls (Click to expand guidance)", expanded=True):
        kw, verdicts, techniques, min_out, latency = _render_filter_controls(
            df)

    filtered = _apply_keyword_filter(df, kw)
    filtered = _apply_metadata_filters(
        filtered, verdicts, techniques, min_out, latency)
    return filtered


def _render_kpi_card_row(df: pd.DataFrame):
    """Render headline summary metrics."""
    total = len(df)
    if total == 0:
        st.warning(
            "No claims match your current filters. Broaden your search parameters.")
        return

    contradicted = len(df[df["verdict"] == "Contradicted"])
    falsehood_rate = (contradicted / total) * 100
    resurfaced_ratio = (df[df["days_latent"] > 7].shape[0] / total) * 100
    avg_velocity = df["velocity"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Claims Under Review", f"{total:,}")
    c2.metric("Proven Falsehood Rate", f"{falsehood_rate:.1f}%")
    c3.metric("Recycled Myth Ratio", f"{resurfaced_ratio:.1f}%")
    c4.metric("Spread Rate", f"{avg_velocity:.1f} outlets/day")


def _render_quick_summary_row(df: pd.DataFrame):
    """Quick, on-the-go visual summaries for journalists."""
    col1, col2 = st.columns(2)

    with col1:
        st.caption("⚡ QUICK BREAKDOWN: VERDICT DISTRIBUTION")
        show_chart(build_quick_verdict_donut(df))

    with col2:
        st.caption("⚡ QUICK BREAKDOWN: TOP 5 DECEPTION TACTICS")
        show_chart(build_quick_top_tactics_bar(df))


# --- SECTION RENDERING HELPERS ---

def _render_velocity_section(df: pd.DataFrame):
    """Render quadrant chart and tactic breakdown."""
    col_quad, col_tech = st.columns(2)

    with col_quad:
        render_section_heading(
            "Breaking Virality vs. Recycled Myths", "Quadrant breakdown of claim velocity.")
        show_chart(build_quadrant_chart(df))
        with st.expander("💡 Reporter's Field Notes: How to use these findings"):
            st.markdown("""
            * **Top-Left (Breaking Viral Hoax):** Immediate fact-check alerts needed.
            * **Top-Right (Recycled Propaganda):** Look for political triggers that resurrected an old narrative.
            """)

    with col_tech:
        render_section_heading("Deception Tactics Breakdown",
                               "Manipulation tricks linked to disproven claims.")
        show_chart(build_technique_breakdown(df))
        with st.expander("💡 Reporter's Field Notes: How to use these findings"):
            st.markdown("""
            * **Deepfake dominance:** Trace origins to fringe forums or channels.
            * **Policy Distortion dominance:** Request direct expert quotes to counter framing spin.
            """)


def _render_lifespan_section(df: pd.DataFrame):
    """Render latency boxplots and decay curves."""
    col_box, col_decay = st.columns(2)

    with col_box:
        render_section_heading("Lifespan & Outliers by Tactic",
                               "Typical claim ages and outlier zombie myths.")
        show_chart(build_technique_latency_boxplot(df))
        with st.expander("💡 Reporter's Field Notes: How to use these findings"):
            st.markdown(
                "* **Far-Right Outliers:** Zombie myths that resurface periodically. Great for 'Why this myth returns' stories.")

    with col_decay:
        render_section_heading(
            "How Fast Propaganda Dies Down", "Momentum loss over time.")
        show_chart(build_narrative_decay_curve(df))
        with st.expander("💡 Reporter's Field Notes: How to use these findings"):
            st.markdown(
                "* **Flattish Decay Curve:** Claim has taken root in search indexing. Ask platform safety teams for comment.")


def _render_keywords_section(df: pd.DataFrame):
    """Render TF-IDF keyword association chart."""
    render_section_heading("Red Flag Language in Disproven Claims",
                           "Buzzwords overrepresented in false claims.")
    show_chart(build_tfidf_keyword_chart(df))
    with st.expander("💡 Reporter's Field Notes: How to use these findings"):
        st.markdown(
            "* **Editor Tip:** Use top-ranked phrases in social monitoring tools (e.g. TweetDeck) to flag unverified claims early.")


# --- MAIN ENTRYPOINT ---

def render():
    """Main view rendering logic."""
    render_page_header(
        "Claims & Narrative Intelligence",
        "Investigative hub for spotting breaking hoaxes, identifying manipulation tactics, and exposing recycled myths."
    )

    raw_df = fn.fetch_analytics_data()
    if raw_df.empty:
        st.warning(
            "⚠️ Unable to load live database records. Please check your system connection.")
        return

    df = _preprocess_claims_data(raw_df)

    filtered_df = _render_explained_filter_bar(df)

    st.markdown("---")
    _render_kpi_card_row(filtered_df)

    st.markdown("---")
    _render_quick_summary_row(filtered_df)

    st.markdown("---")
    _render_velocity_section(filtered_df)

    st.markdown("---")
    _render_lifespan_section(filtered_df)

    st.markdown("---")
    _render_keywords_section(filtered_df)
