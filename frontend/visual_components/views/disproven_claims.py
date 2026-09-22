"""Latest Disproven Claims page: newest false / misleading claims, with source links."""

import streamlit as st
from database_conns import disproven_claims as data
from ..components.claim_card import render_disproven_claim_card
from ..components.header import render_page_header

FEED_LIMIT = 10

SORT_OPTIONS = {
    "Newest first": "newest",
    "Most checked": "most_checked",
}
SORT_CAPTIONS = {
    "newest": "Sorted by publish date, newest first.",
    "most_checked": "Sorted by how many times each claim has been checked.",
}
VERDICT_OPTIONS = ["All", "Contradicted", "Missing Context"]


def _render_controls():
    """Sort and verdict filters. Returns (sort_key, verdict)."""

    col_sort, col_verdict = st.columns(2)

    with col_sort:
        sort_label = st.segmented_control(
            "Sort by", list(SORT_OPTIONS), default="Newest first", key="disproven_sort"
        ) or "Newest first"  # segmented controls can be un-clicked, which returns None

    with col_verdict:
        verdict = st.segmented_control(
            "Verdict", VERDICT_OPTIONS, default="All", key="disproven_verdict"
        ) or "All"

    return SORT_OPTIONS[sort_label], verdict


def _render_feed_stats(df):
    """Three headline numbers for the claims currently shown."""

    contradicted = int((df["verdict"].str.lower() == "contradicted").sum())
    techniques = df["technique"].dropna() if "technique" in df else []
    top_technique = techniques.mode()[0] if len(techniques) else "N/A"

    c1, c2, c3 = st.columns(3)
    c1.metric("Claims shown", len(df))
    c2.metric("Contradicted", contradicted)
    c3.metric("Most common technique", top_technique)


def render():
    """Feed of the latest disproven and misleading claims from RDS."""

    render_page_header(
        "Latest Disproven Claims",
        "The newest false and misleading claims indexed across partner outlets, with links to the fact-checks."
    )

    sort_key, verdict = _render_controls()
    df = data.get_disproven_claims(sort_key, verdict, FEED_LIMIT)

    if df.attrs.get("is_sample"):
        st.warning(
            "Showing sample data because the database couldn't be reached. "
            "Check your RDS settings in .env."
        )

    if df.empty:
        st.info("No disproven claims match these filters.")
        return

    _render_feed_stats(df)
    st.caption(SORT_CAPTIONS[sort_key])

    for _, row in df.iterrows():
        render_disproven_claim_card(row)
