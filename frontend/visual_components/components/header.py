"""Page header with the brand icon."""

import streamlit as st

from .. import theme


def render_page_header(title: str, description: str):
    """Render section headers with brand icon."""

    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 6px;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50" width="48" height="48" style="flex-shrink: 0;">
            <!-- Document Shield Base -->
            <rect x="2" y="4" width="36" height="42" rx="5" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="2.5"/>
            <!-- Accent Lines -->
            <line x1="9" y1="14" x2="24" y2="14" stroke="{theme.COLOUR_PRIMARY_DARK}" stroke-width="2.5" stroke-linecap="round"/>
            <line x1="9" y1="20" x2="31" y2="20" stroke="#E2E8F0" stroke-width="2.5" stroke-linecap="round"/>
            <!-- Check Badge -->
            <circle cx="32" cy="35" r="11" fill="{theme.COLOUR_PRIMARY}"/>
            <path d="M 28 35 L 30 37 L 36 32" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <h1 style="margin: 0 !important; font-size: 36px !important; font-weight: 800 !important; color: {theme.COLOUR_TEXT_MAIN}; line-height: 1.1;">{title}</h1>
    </div>
    <p style="margin-bottom: 24px; color: {theme.COLOUR_TEXT_MUTED}; font-size: 15px; margin-left: 62px;">{description}</p>
    """, unsafe_allow_html=True)
