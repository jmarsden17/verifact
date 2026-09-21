"""Charts about a single verification result - confidence gauge and verdict donut."""

import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
from streamlit import html
from .. import theme
from ._base import apply_base_layout

HIGH_CONFIDENCE = 80
MEDIUM_CONFIDENCE = 50


def build_confidence_gauge(confidence: float):
    """Render the semicircle confidence gauge with a gradient."""

    cx, cy, r = 100, 110, 80
    circumference = math.pi * r
    dash_offset = circumference * (1 - confidence / 100)

    tick_radius = r + 16
    tick_labels = []
    for value in (0, 20, 40, 60, 80, 100):
        angle = math.radians(180 - 1.8 * value)
        tick_labels.append(
            (cx + tick_radius * math.cos(angle), cy -
             tick_radius * math.sin(angle), value)
        )
    tick_svg = "\n".join(
        f'    <text x="{x:.1f}" y="{y:.1f}" font-size="10" fill="{theme.COLOUR_PRIMARY_DARK}" '
        f'text-anchor="middle">{value}</text>'
        for x, y, value in tick_labels
    )

    gauge_html = f"""
    <html>
    <body style="margin:0;background:transparent;">
    <div style="text-align:center;font-family:sans-serif;padding-top:6px;">
      <div style="font-weight:600;font-size:13px;color:{theme.COLOUR_TEXT_MAIN};margin-bottom:2px;">Model Confidence</div>
      <svg viewBox="-15 0 230 160" width="100%" style="max-width:220px;">
        <defs>
          <linearGradient id="barGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="{theme.GRADIENT_LOW_SCORE}" />
            <stop offset="50%" stop-color="{theme.GRADIENT_MID_SCORE}" />
            <stop offset="100%" stop-color="{theme.GRADIENT_HIGH_SCORE}" />
          </linearGradient>
        </defs>
        <path d="M20,{cy} A{r},{r} 0 0 1 180,{cy}"
              fill="none" stroke="#eaeaea" stroke-width="14" stroke-linecap="round" />
        <path d="M20,{cy} A{r},{r} 0 0 1 180,{cy}"
              fill="none" stroke="url(#barGradient)" stroke-width="14"
              stroke-linecap="round"
              stroke-dasharray="{circumference}"
              stroke-dashoffset="{dash_offset}" />
    {tick_svg}
        <text x="{cx}" y="{cy - 15}" font-size="16" font-weight="700" fill="{theme.COLOUR_PRIMARY_DARK}" text-anchor="middle">{confidence}%</text>
      </svg>
    </div>
    </body>
    </html>
    """

    components.html(gauge_html, height=145)


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
