"""Semicircle confidence gauge component."""

import math
import streamlit as st
import streamlit.components.v1 as components
from .. import theme


def render_gauge_with_gradient(confidence: float):
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
<div style="text-align:center;font-family:sans-serif;padding-top:14px;">
  <div style="font-weight:600;color:{theme.COLOUR_TEXT_MAIN};margin-bottom:4px;">Model Confidence</div>
  <svg viewBox="-15 0 230 160" width="100%" style="max-width:360px;">
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

    components.html(gauge_html, height=270)
