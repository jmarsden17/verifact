"""Verdict badge."""

import streamlit as st

from .. import theme


def render_verdict_badge(rating: str):
    """Render status indicators."""

    fg, bg, icon = theme.VERDICT_BADGES.get(
        rating, theme.VERDICT_BADGE_DEFAULT)

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
        <span style="
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background-color: #ffffff;
            width: 24px;
            height: 24px;
            border-radius: 50%;
        ">{icon}</span>
        <span>VERDICT: {rating.upper()}</span>
    </div>
    """

    st.markdown(badge_html, unsafe_allow_html=True)
