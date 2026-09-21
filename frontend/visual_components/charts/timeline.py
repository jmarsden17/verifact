"""Line chart - new claims vs resurfaced queries over time."""

import pandas as pd
import plotly.express as px

from .. import theme
from ._base import TOP_RIGHT_LEGEND, apply_base_layout

# A claim counts as "resurfaced" if it is accessed this many days after publication
RESURFACED_AFTER_DAYS = 7


def build_recurrence_chart(df: pd.DataFrame):
    """Build the weekly new-vs-resurfaced chart, or None if data is missing."""

    if df.empty or "publish_datetime" not in df or "access_datetime" not in df:
        return None

    df = df.copy()
    df["publish_datetime"] = pd.to_datetime(df["publish_datetime"])
    df["access_datetime"] = pd.to_datetime(df["access_datetime"])

    df["is_resurfaced"] = (
        df["access_datetime"] - df["publish_datetime"]
    ).dt.days > RESURFACED_AFTER_DAYS

    weekly_df = df.resample("W", on="publish_datetime").agg(
        **{
            "New Submissions": ("claim_id", "count"),
            "Resurfaced Queries": ("is_resurfaced", "sum"),
        }
    ).reset_index()

    fig = px.line(
        weekly_df,
        x="publish_datetime",
        y=["New Submissions", "Resurfaced Queries"],
        color_discrete_map={
            "New Submissions": theme.COLOUR_PRIMARY,
            "Resurfaced Queries": theme.COLOUR_WARNING_FG,
        },
    )

    return apply_base_layout(
        fig,
        height=360,
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis_title="Date",
        yaxis_title="Claim Volume",
        legend_title_text="",
        font=dict(color=theme.COLOUR_TEXT_MAIN),
        yaxis=dict(showgrid=True, gridcolor=theme.COLOUR_BORDER),
        legend=TOP_RIGHT_LEGEND,
    )
