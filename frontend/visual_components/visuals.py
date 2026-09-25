"""Wrapper module for visual components used in testing and the main app."""

import plotly.graph_objects as go
import pandas as pd
from .charts.verdict import build_confidence_gauge, build_accuracy_donut
from .charts.outlet import build_outlet_chart
from . import theme


def render_confidence_gauge(confidence: float, rating: str):
    """Render a confidence gauge chart for a given confidence score and rating.

    Args:
        confidence: Confidence score (0-100)
        rating: Verdict rating (e.g., "Supported", "Contradicted", etc.)

    Returns:
        A plotly figure representing the gauge chart
    """
    # Create a simple gauge figure using Plotly
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=confidence,
        title={'text': f"Confidence - {rating}"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': theme.VERDICT_CHART_COLOURS.get(rating, "#999999")},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 100], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    return fig


def render_outlet_analytics_chart():
    """Render outlet analytics chart with sample data.

    Returns:
        A plotly figure representing outlet analytics
    """
    # Create sample data for outlet analytics
    sample_data = pd.DataFrame({
        'publisher': ['BBC Verify', 'Reuters', 'Full Fact', 'Wikipedia', 'BBC Verify', 'Reuters'],
        'verdict': ['Supported', 'Supported', 'Contradicted', 'Missing Context', 'Contradicted', 'Missing Context'],
        'count': [3, 2, 4, 1, 2, 1]
    })

    # Use the existing build_outlet_chart function
    fig = build_outlet_chart(sample_data)
    return fig if fig is not None else go.Figure()
