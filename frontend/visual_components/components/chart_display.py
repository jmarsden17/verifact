"""One place that decides how every Plotly chart is shown in the app."""

import streamlit as st


def show_chart(fig, key: str | None = None):
    """Render a Plotly figure full width with the toolbar hidden (no-op if fig is None)."""

    if fig is None:
        return
    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
        key=key,
    )
