"""One expandable report per extracted claim: verdict up top, sources underneath."""

import streamlit as st

from .. import theme
from ..charts.verdict import build_confidence_gauge
from .badges import render_verdict_badge
from .chart_display import show_chart
from .source_evidence import render_source_evidence

# TODO: replace with the real claim.confidence_score from the database
CONFIDENT_RATINGS = ("Supported", "Contradicted")
PLACEHOLDER_CONFIDENCE_HIGH = 94.2
PLACEHOLDER_CONFIDENCE_LOW = 68.5

TITLE_MAX_CHARS = 80


def _expander_title(idx: int, claim_text: str, rating: str) -> str:
    """Verdict icon first so results can be scanned at a glance."""

    icon = theme.VERDICT_BADGES.get(rating, theme.VERDICT_BADGE_DEFAULT)[2]
    shortened = claim_text[:TITLE_MAX_CHARS]
    if len(claim_text) > TITLE_MAX_CHARS:
        shortened += "..."
    return f"{icon} Claim {idx+1}: \"{shortened}\" — {rating.upper()}"


def _render_claim_top(item: dict, claim_text: str, rating: str, idx: int):
    """Statement, verdict badge and reasoning on the left, confidence gauge on the right."""

    col_verdict, col_gauge = st.columns([1.2, 1])

    with col_verdict:
        st.markdown("**Extracted Statement:**")
        st.info(f"\"{claim_text}\"")
        render_verdict_badge(rating)
        st.markdown("**Reasoning Explanation:**")
        st.write(item.get("reasoning", "No explanation provided."))

    with col_gauge:
        confidence = (PLACEHOLDER_CONFIDENCE_HIGH
                      if rating in CONFIDENT_RATINGS
                      else PLACEHOLDER_CONFIDENCE_LOW)
        show_chart(build_confidence_gauge(confidence),
                   key=f"gauge_chart_{idx}")


def render_claim_reports(results: list):
    """One dropdown per claim. Sources sit inside it, always visible (no nested dropdowns)."""

    st.markdown("### 🔍 Individual Extracted Claim Reports")

    for idx, item in enumerate(results):
        claim_text = item.get("claim", f"Extracted Claim #{idx+1}")
        rating = item.get("rating", "Unclear")

        with st.expander(_expander_title(idx, claim_text, rating), expanded=(idx == 0)):
            _render_claim_top(item, claim_text, rating, idx)

            if item.get("sources"):
                render_source_evidence(item["sources"])
