"""Renders a verdict banner indicating the status of a claim."""

import streamlit as st
from .. import theme
from .html_utils import esc

VERDICT_MESSAGES = {
    "Contradicted": ("✕", "Evidence shows this claim is false."),
    "Supported": ("✓", "Evidence supports this claim."),
    "Missing Context": ("!", "Contains some truth, but is misleading without more context."),
    "Unclear": ("?", "Not enough evidence to reach a verdict."),
}

# (Background Soft Tint, Dark Text/Icon, Border Tint)
VERDICT_THEMES = {
    "Contradicted": (theme.COLOUR_DANGER_BG, theme.COLOUR_DANGER_FG, "#FECDD3"),
    "Supported": (theme.COLOUR_SUCCESS_BG, theme.COLOUR_SUCCESS_FG, "#A7F3D0"),
    "Missing Context": (theme.COLOUR_WARNING_BG, theme.COLOUR_WARNING_FG, "#FDE68A"),
    "Unclear": (theme.COLOUR_UNCLEAR_BG, theme.COLOUR_UNCLEAR_FG, "#CBD5E1"),
}


def render_verdict_banner(rating: str):
    rating_key = rating if rating in VERDICT_MESSAGES else "Unclear"
    bg, fg, border = VERDICT_THEMES.get(rating_key, VERDICT_THEMES["Unclear"])
    glyph, message = VERDICT_MESSAGES[rating_key]

    st.markdown(
        f'<div class="verdict-banner" style="--banner-bg: {bg}; --banner-fg: {fg}; --banner-border: {border};">'
        f'<div class="verdict-banner__icon">{glyph}</div>'
        '<div>'
        '<div class="verdict-banner__label">VERDICT</div>'
        f'<div class="verdict-banner__verdict">{esc(rating.upper())}</div>'
        f'<div class="verdict-banner__text">{esc(message)}</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
