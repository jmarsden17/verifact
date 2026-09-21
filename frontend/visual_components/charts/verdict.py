"""Charts about a single verification result - confidence gauge and verdict donut."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .. import theme
from ._base import apply_base_layout
from ..components.gauge import render_gauge_with_gradient

HIGH_CONFIDENCE = 80
MEDIUM_CONFIDENCE = 50


def build_confidence_gauge(confidence_score: float):
    """Gauge whose bar colour reflects how confident the model is."""

    return render_gauge_with_gradient(confidence_score)


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
