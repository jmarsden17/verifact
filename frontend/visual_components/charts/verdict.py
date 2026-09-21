"""Charts about a single verification result - confidence gauge and verdict donut."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .. import theme
from ._base import apply_base_layout

HIGH_CONFIDENCE = 80
MEDIUM_CONFIDENCE = 50


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def make_gradient_steps(vmin, vmax, hex_colors, n_segments=60):
    """Build Plotly gauge 'steps' that blend smoothly across the given hex colors."""
    stops = [_hex_to_rgb(c) for c in hex_colors]
    steps = []
    for i in range(n_segments):
        seg_min = vmin + (vmax - vmin) * i / n_segments
        seg_max = vmin + (vmax - vmin) * (i + 1) / n_segments
        t = i / (n_segments - 1)
        scaled = t * (len(stops) - 1)
        idx = min(int(scaled), len(stops) - 2)
        local_t = scaled - idx
        r = int(stops[idx][0] + (stops[idx + 1][0] - stops[idx][0]) * local_t)
        g = int(stops[idx][1] + (stops[idx + 1][1] - stops[idx][1]) * local_t)
        b = int(stops[idx][2] + (stops[idx + 1][2] - stops[idx][2]) * local_t)
        steps.append({"range": [seg_min, seg_max],
                     "color": f"rgb({r},{g},{b})"})
    return steps


def build_confidence_gauge(confidence_score: float):
    """Gauge whose bar colour reflects how confident the model is."""

    if confidence_score >= HIGH_CONFIDENCE:
        bar_colour = theme.GRADIENT_HIGH_SCORE
    elif confidence_score >= MEDIUM_CONFIDENCE:
        bar_colour = theme.GRADIENT_MID_SCORE
    else:
        bar_colour = theme.GRADIENT_LOW_SCORE

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
            "steps": make_gradient_steps(
                0, 100,
                [theme.GRADIENT_LOW_SCORE, theme.GRADIENT_MID_SCORE,
                    theme.GRADIENT_HIGH_SCORE]
            ),
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
