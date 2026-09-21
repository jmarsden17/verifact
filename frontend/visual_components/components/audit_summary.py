"""Overview card for a multi-claim paragraph audit."""

import streamlit as st

from ..charts.verdict import build_accuracy_donut
from .chart_display import show_chart


def _count(results: list, rating: str) -> int:
    return sum(1 for r in results if r.get("rating") == rating)


def render_audit_summary(results: list):
    """Render totals, overall accuracy and the verdict donut."""

    st.markdown("### 📊 Paragraph Audit Overview")

    total_claims = len(results)
    supported = _count(results, "Supported")
    contradicted = _count(results, "Contradicted")
    missing_ctx = _count(results, "Missing Context")
    unclear = _count(results, "Unclear")

    accuracy_pct = round((supported / total_claims) * 100) if total_claims > 0 else 0

    with st.container(border=True):
        col_stats, col_chart = st.columns([1.5, 1])

        with col_stats:
            st.markdown(f"**Total Claims Extracted:** `{total_claims}`")
            st.markdown(f"✅ **Supported Claims:** `{supported}`")
            st.markdown(f"❌ **Disproved (Contradicted):** `{contradicted}`")
            st.markdown(
                f"⚠️ **Missing Context / Unclear:** `{missing_ctx + unclear}`")
            st.markdown(f"🎯 **Overall Accuracy Score:** **{accuracy_pct}%**")

        with col_chart:
            st.markdown(
                "<p style='text-align: center; font-size: 13px; font-weight: 600;'>Accuracy Breakdown</p>",
                unsafe_allow_html=True)
            show_chart(build_accuracy_donut(
                supported, contradicted, missing_ctx, unclear))
