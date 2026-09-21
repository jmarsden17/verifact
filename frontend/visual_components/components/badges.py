"""Verdict badge."""

import streamlit as st

from .. import theme


def render_verdict_badge(rating: str):
    """Render status indicators."""

    bg, fg, icon = theme.VERDICT_BADGES.get(rating, theme.VERDICT_BADGE_DEFAULT)

    badge_html = f"""
    <div style="
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background-color: {bg};
        color: {fg};
        padding: 6px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 12px;
    ">
        <span>{icon}</span>
        <span>VERDICT: {rating.upper()}</span>
    </div>
    """
    st.markdown(badge_html, unsafe_allow_html=True)
