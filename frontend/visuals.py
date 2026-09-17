"""Analytics visualisations and chart renderers."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import theme


def render_outlet_analytics_chart():
    """Render an interactive stacked bar chart showing verdict breakdowns per publisher."""
    # Data breakdown for each fact-checking partner
    data = [
        {"Publisher": "Full Fact", "Verdict": "Supported", "Claims": 240},
        {"Publisher": "Full Fact", "Verdict": "Contradicted", "Claims": 130},
        {"Publisher": "Full Fact", "Verdict": "Missing Context", "Claims": 42},
        {"Publisher": "FactCheck.org", "Verdict": "Supported", "Claims": 180},
        {"Publisher": "FactCheck.org", "Verdict": "Contradicted", "Claims": 110},
        {"Publisher": "FactCheck.org", "Verdict": "Missing Context", "Claims": 38},
        {"Publisher": "PolitiFact", "Verdict": "Supported", "Claims": 95},
        {"Publisher": "PolitiFact", "Verdict": "Contradicted", "Claims": 120},
        {"Publisher": "PolitiFact", "Verdict": "Missing Context", "Claims": 30},
        {"Publisher": "Reuters", "Verdict": "Supported", "Claims": 115},
        {"Publisher": "Reuters", "Verdict": "Contradicted", "Claims": 45},
        {"Publisher": "Reuters", "Verdict": "Missing Context", "Claims": 20},
        {"Publisher": "AP Fact Check", "Verdict": "Supported", "Claims": 50},
        {"Publisher": "AP Fact Check", "Verdict": "Contradicted", "Claims": 25},
        {"Publisher": "AP Fact Check", "Verdict": "Missing Context", "Claims": 8},
    ]

    df = pd.DataFrame(data)

    # Map brand theme colors to each verdict type
    colour_map = {
        "Supported": theme.COLOUR_SUCCESS_FG,
        "Contradicted": theme.COLOUR_DANGER_FG,
        "Missing Context": theme.COLOUR_WARNING_FG
    }

    fig = px.bar(
        df,
        x="Publisher",
        y="Claims",
        color="Verdict",
        color_discrete_map=colour_map,
        title="",
        barmode="stack"
    )

    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="",
        yaxis_title="Volume of Claims",
        legend_title_text="Verdict Breakdown",
        font=dict(color=theme.COLOUR_TEXT_MAIN),
        yaxis=dict(showgrid=True, gridcolor=theme.COLOUR_BORDER),
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1)
    )

    return fig


def render_confidence_gauge(confidence_score: float, rating: str):
    """Render an enterprise confidence chart."""

    # Pick indicator color based on verdict rating
    if rating == "Supported":
        bar_color = theme.COLOUR_SUCCESS_FG
    elif rating == "Contradicted":
        bar_color = theme.COLOUR_DANGER_FG
    elif rating == "Missing Context":
        bar_color = theme.COLOUR_WARNING_FG
    else:
        bar_color = theme.COLOUR_PRIMARY

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence_score,
        number={'suffix': "%", 'font': {
            'color': theme.COLOUR_TEXT_MAIN, 'size': 32}},
        title={'text': "Model Confidence", 'font': {
            'color': theme.COLOUR_TEXT_MUTED, 'size': 14}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': theme.COLOUR_BORDER},
            'bar': {'color': bar_color},
            'bgcolor': "#FFFFFF",
            'borderwidth': 1,
            'borderwidth': 1,
            'bordercolor': theme.COLOUR_BORDER,
            'steps': [
                {'range': [0, 50], 'color': "#F8FAFC"},
                {'range': [50, 100], 'color': "#F1F5F9"}
            ],
        }
    ))

    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=50, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig
