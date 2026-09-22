"""Sidebar branding and status panel."""

import streamlit as st
from .. import theme


def render_sidebar_logo():
    """Render the logo inside the sidebar."""

    logo_svg = f"""
    <div style="padding: 4px 0px 16px 0px;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 80" width="100%">
            <g transform="translate(0, 5)">
                <!-- Document Container -->
                <rect x="4" y="6" width="44" height="56" rx="6" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="2.5"/>
                <!-- Document Lines -->
                <line x1="12" y1="18" x2="30" y2="18" stroke="{theme.COLOUR_PRIMARY_DARK}" stroke-width="2.5" stroke-linecap="round"/>
                <line x1="12" y1="26" x2="40" y2="26" stroke="#E2E8F0" stroke-width="2.5" stroke-linecap="round"/>
                <line x1="12" y1="34" x2="36" y2="34" stroke="#E2E8F0" stroke-width="2.5" stroke-linecap="round"/>
                <!-- Pulse Check Badge -->
                <circle cx="38" cy="46" r="14" fill="{theme.COLOUR_PRIMARY}"/>
                <path d="M 33 46 L 36 49 L 43 42" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </g>
            <!-- Brand Text -->
            <text x="64" y="32" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-weight="700" font-size="15" fill="#0F172A" letter-spacing="0.5">DISINFORMATION</text>
            <text x="64" y="48" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-weight="700" font-size="15" fill="{theme.COLOUR_PRIMARY}" letter-spacing="0.5">VERIFIER</text>
            <text x="64" y="62" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-weight="500" font-size="8.5" fill="#64748B" letter-spacing="1.2">FAST CLAIM AUDIT</text>
        </svg>
    </div>
    """
    st.sidebar.markdown(logo_svg, unsafe_allow_html=True)


def render_system_status():
    """Render a live architecture status indicator pinned to the sidebar footer."""

    st.sidebar.markdown(f"""
    <div style="margin-top: auto; padding-top: 20px;">
        <hr style="margin-bottom: 16px; border: 0; border-top: 1px solid {theme.COLOUR_BORDER};">
        <div style="background-color: #F8FAFC; border: 1px solid {theme.COLOUR_BORDER}; padding: 12px; border-radius: 8px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <span style="font-size: 12px; font-weight: 600; color: {theme.COLOUR_TEXT_MAIN};">Engine Status</span>
                <span style="font-size: 11px; font-weight: 600; color: {theme.COLOUR_SUCCESS_FG}; background-color: {theme.COLOUR_SUCCESS_BG}; padding: 2px 6px; border-radius: 4px;">● ONLINE</span>
            </div>
            <div style="font-size: 11px; color: {theme.COLOUR_TEXT_MUTED}; line-height: 1.4;">
                • <strong>Compute:</strong> AWS ECS Fargate<br>
                • <strong>Database:</strong> PostgreSQL RDS<br>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
