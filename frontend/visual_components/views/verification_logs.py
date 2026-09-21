"""Verification Logs page: searchable table of past claim checks."""

import streamlit as st

from database_conns import fetch_data as fn

from .. import theme
from ..components.header import render_page_header

# Database column -> label shown in the table
LOG_COLUMNS = {
    "timestamp": "Timestamp",
    "claim_statement": "Claim Statement",
    "verdict": "Verdict",
    "technique": "Disinformation Technique",
    "sources_count": "Sources Consulted",
    "tags_list": "Tags",
}


def _render_filters():
    """Render the filter bar and return (keyword, verdict)."""

    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            query = st.text_input("Filter by Keyword or Tag",
                                  placeholder="Search claims or tags...")
        with c2:
            status = st.selectbox("Verdict Filter",
                                  ["All", *theme.VERDICT_ORDER])
    return query, status


def render():
    """Filterable Data Table View matching exact ERD entities."""

    render_page_header(
        "Verification History Logs",
        "Search and review past newsroom claim checks indexed in RDS."
    )

    query, status = _render_filters()
    df = fn.get_filtered_logs(query, status)

    if df.empty:
        st.info("No verification logs match your filter criteria.")
        return

    # Only show columns that exist, so the page survives DB/fallback format changes
    valid_cols = [c for c in LOG_COLUMNS if c in df.columns]

    if valid_cols:
        st.dataframe(
            df[valid_cols].rename(columns=LOG_COLUMNS),
            width="stretch",
            hide_index=True
        )
    else:
        st.dataframe(df, width="stretch", hide_index=True)
