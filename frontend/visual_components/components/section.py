"""Section headings used inside pages."""

import streamlit as st

from .. import theme


def render_section_heading(title: str, description: str = "", level: int = 3):
    """Render a heading (### by default) with an optional muted description underneath."""

    st.markdown(f"{'#' * level} {title}")
    if description:
        st.markdown(
            f"<p style='font-size: 13px; color: {theme.COLOUR_TEXT_MUTED}; margin-bottom: 16px;'>"
            f"{description}</p>",
            unsafe_allow_html=True,
        )
