"""Bar chart - claim volume per fact-checking publisher, stacked by verdict."""

import pandas as pd
import plotly.express as px
from .. import theme
from ._base import TOP_RIGHT_LEGEND, apply_base_layout


def _explode_publishers(df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per (claim, publisher)."""

    chart_df = df.copy()
    chart_df["publisher"] = (
        chart_df["publisher"].fillna("Unknown").astype(str).str.split(", ")
    )

    exploded_df = chart_df.explode("publisher")
    exploded_df["publisher"] = exploded_df["publisher"].astype(str).str.strip()
    return exploded_df


def build_outlet_chart(df: pd.DataFrame):
    """Build the publisher volume chart, or None if there is nothing to plot."""

    if df.empty or "publisher" not in df.columns:
        return None

    fig = px.histogram(
        _explode_publishers(df),
        x="publisher",
        color="verdict",
        color_discrete_map=theme.VERDICT_CHART_COLOURS,
        labels={"publisher": "Fact-Checking Publisher", "verdict": "Verdict"},
        category_orders={"verdict": theme.VERDICT_ORDER},
    )

    return apply_base_layout(
        fig,
        height=320,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title=None,
        yaxis_title="Volume of Claims",
        barmode="stack",
        legend=dict(TOP_RIGHT_LEGEND, title_text="Verdict"),
    )
