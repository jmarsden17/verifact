"""Charts about a single verification result - confidence gauge and verdict donut."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .. import theme
from ._base import apply_base_layout

HIGH_CONFIDENCE = 80
MEDIUM_CONFIDENCE = 50


def build_confidence_gauge(confidence_score: float):
    """Gauge whose bar colour reflects how confident the model is."""

    if confidence_score >= HIGH_CONFIDENCE:
        bar_colour = theme.COLOUR_SUCCESS_FG
    elif confidence_score >= MEDIUM_CONFIDENCE:
        bar_colour = theme.COLOUR_WARNING_FG
    else:
        bar_colour = theme.COLOUR_DANGER_FG

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence_score,
        number={"suffix": "%", "font": {
            "size": 24, "color": theme.COLOUR_TEXT_MAIN}},
        title={"text": "Model Confidence Score", "font": {
            "size": 13, "color": theme.COLOUR_TEXT_MUTED}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": theme.COLOUR_TEXT_MUTED,
                "tickvals": [0, 50, 100],
                "ticktext": ["0%", "50%", "100%"],
            },
            "bar": {"color": bar_colour, "thickness": 0.75},
            "bgcolor": theme.COLOUR_APP_BG,
            "borderwidth": 1,
            "bordercolor": theme.COLOUR_BORDER,
        },
    ))

    return apply_base_layout(
        fig,
        height=190,
        margin=dict(l=30, r=30, t=45, b=10),
        font=dict(color=theme.COLOUR_TEXT_MAIN),
    )


def build_accuracy_donut(supported: int, contradicted: int,
                         missing_context: int, unclear: int):
    """Donut showing the share of each verdict, or None if there are no claims."""

    df = pd.DataFrame({
        "Verdict": theme.VERDICT_ORDER,
        "Count": [supported, contradicted, missing_context, unclear],
    })
    df = df[df["Count"] > 0]

    if df.empty:
        return None

    fig = px.pie(
        df,
        values="Count",
        names="Verdict",
        color="Verdict",
        color_discrete_map=theme.VERDICT_CHART_COLOURS,
        hole=0.6,
    )

    return apply_base_layout(
        fig,
        height=180,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
    )
