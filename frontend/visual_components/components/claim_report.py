"""One expandable report per extracted claim: verdict up top, sources underneath."""

import streamlit as st

from ..charts.verdict import build_confidence_gauge
from .chart_display import show_chart
from .html_utils import esc
from .source_evidence import render_source_evidence
from .verdict_banner import render_verdict_banner

# TODO: replace with the real claim.confidence_score from the database
CONFIDENT_RATINGS = ("Supported", "Contradicted")
PLACEHOLDER_CONFIDENCE_HIGH = 94.2
PLACEHOLDER_CONFIDENCE_LOW = 68.5

TITLE_MAX_CHARS = 80


def _render_claim_heading(idx: int, total: int, claim_text: str):
    """'CLAIM 1 OF 3' label with the statement being checked underneath."""

    st.markdown(
        f'<div class="claim-label">Claim {idx+1} of {total}</div>'
        f'<div class="claim-statement">“{esc(claim_text)}”</div>',
        unsafe_allow_html=True,
    )


def _render_reasoning_and_confidence(item: dict, rating: str, idx: int):
    # Expanded text column ratio to balance the gauge
    col_reasoning, col_gauge = st.columns(
        [2.2, 1], vertical_alignment="top")

    with col_reasoning:
        st.markdown("**Reasoning Explanation**")
        st.write(item.get("reasoning", "No explanation provided."))

    with col_gauge:
        confidence = (
            PLACEHOLDER_CONFIDENCE_HIGH
            if rating in CONFIDENT_RATINGS
            else PLACEHOLDER_CONFIDENCE_LOW
        )
        show_chart(build_confidence_gauge(
            confidence), key=f"gauge_chart_{idx}")


def render_claim_reports(results: list):
    """Claim -> verdict banner -> reasoning + confidence -> source dropdown, per claim."""

    st.markdown("### 🔍 Individual Extracted Claim Reports")

    for idx, item in enumerate(results):
        claim_text = item.get("claim", f"Extracted Claim #{idx+1}")
        rating = item.get("rating", "Unclear")

        with st.container(border=True):
            _render_claim_heading(idx, len(results), claim_text)
            render_verdict_banner(rating)
            _render_reasoning_and_confidence(item, rating, idx)

            if item.get("sources"):
                render_source_evidence(item["sources"])
