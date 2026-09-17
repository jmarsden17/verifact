"""Visual components for rendering analytics charts in the frontend."""

import pandas as pd
import plotly.express as px
from . import theme


def render_outlet_analytics_chart(df: pd.DataFrame):
    """Render stacked bar chart showing verdict breakdowns per publisher from real DB data."""
    if df.empty or "publisher" not in df or "verdict" not in df:
        return None

    # Group real data by Publisher and Verdict
    grouped = df.groupby(["publisher", "verdict"]
                         ).size().reset_index(name="Claims")

    colour_map = {
        "Supported": theme.COLOUR_SUCCESS_FG,
        "Contradicted": theme.COLOUR_DANGER_FG,
        "Missing Context": theme.COLOUR_WARNING_FG,
        "Unclear": theme.COLOUR_UNCLEAR_FG
    }

    fig = px.bar(
        grouped,
        x="publisher",
        y="Claims",
        color="verdict",
        color_discrete_map=colour_map,
        barmode="stack"
    )

    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="",
        yaxis_title="Volume of Claims",
        legend_title_text="Verdict",
        font=dict(color=theme.COLOUR_TEXT_MAIN),
        yaxis=dict(showgrid=True, gridcolor=theme.COLOUR_BORDER),
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1)
    )

    return fig


def render_recurrence_timeline_chart(df: pd.DataFrame):
    """Render timeline mapping new claims vs resurfaced queries from real DB timestamps."""
    if df.empty or "publish_datetime" not in df or "access_datetime" not in df:
        return None

    df = df.copy()
    df["publish_datetime"] = pd.to_datetime(df["publish_datetime"])
    df["access_datetime"] = pd.to_datetime(df["access_datetime"])

    # Identify resurfaced queries (>7 days between publish and last access)
    df["is_resurfaced"] = (df["access_datetime"] -
                           df["publish_datetime"]).dt.days > 7

    weekly_df = df.resample("W", on="publish_datetime").agg(
        **{
            "New Submissions": ("claim_id", "count"),
            "Resurfaced Queries": ("is_resurfaced", "sum")
        }
    ).reset_index()

    fig = px.line(
        weekly_df,
        x="publish_datetime",
        y=["New Submissions", "Resurfaced Queries"],
        color_discrete_map={
            "New Submissions": theme.COLOUR_PRIMARY,
            "Resurfaced Queries": theme.COLOUR_WARNING_FG
        }
    )

    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Date",
        yaxis_title="Claim Volume",
        legend_title_text="",
        font=dict(color=theme.COLOUR_TEXT_MAIN),
        yaxis=dict(showgrid=True, gridcolor=theme.COLOUR_BORDER),
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1)
    )

    return fig
