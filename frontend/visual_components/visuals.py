"""Visual components for rendering analytics charts in the frontend."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from . import theme


def render_outlet_analytics_chart(df: pd.DataFrame):
    """Render bar chart showing claim volume per individual publisher."""
    if df.empty or "publisher" not in df.columns:
        return None

    chart_df = df.copy()

    # 1. Fill NaN values and cast strictly to string
    chart_df["publisher"] = chart_df["publisher"].fillna("Unknown").astype(str)

    # 2. Split string lists (e.g. "BBC Verify, Reuters") into lists
    chart_df["publisher"] = chart_df["publisher"].str.split(", ")

    # 3. Explode into individual rows
    exploded_df = chart_df.explode("publisher")

    # 4. Clean up whitespace safely
    exploded_df["publisher"] = exploded_df["publisher"].astype(str).str.strip()

    color_discrete_map = {
        "Supported": theme.COLOUR_SUCCESS_FG,
        "Contradicted": theme.COLOUR_DANGER_FG,
        "Missing Context": theme.COLOUR_WARNING_FG,
        "Unclear": theme.COLOUR_UNCLEAR_FG
    }

    fig = px.histogram(
        exploded_df,
        x="publisher",
        color="verdict",
        color_discrete_map=color_discrete_map,
        labels={"publisher": "Fact-Checking Publisher", "verdict": "Verdict"},
        category_orders={"verdict": [
            "Supported", "Contradicted", "Missing Context", "Unclear"]}
    )

    fig.update_layout(
        xaxis_title=None,
        yaxis_title="Volume of Claims",
        barmode="stack",
        height=320,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            title_text="Verdict",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def render_recurrence_timeline_chart(df: pd.DataFrame):
    """Map new claims vs resurfaced queries from timestamps."""

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


def render_confidence_gauge(confidence_score: float):
    """Confidence gauge with dynamic colouring."""

    # Bar colour based on confidence score
    if confidence_score >= 80:
        bar_colour = theme.COLOUR_SUCCESS_FG
    elif confidence_score >= 50:
        bar_colour = theme.COLOUR_WARNING_FG
    else:
        bar_colour = theme.COLOUR_DANGER_FG

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence_score,
        number={'suffix': "%", 'font': {
            'size': 24, 'color': theme.COLOUR_TEXT_MAIN}},
        title={'text': "Model Confidence Score", 'font': {
            'size': 13, 'color': theme.COLOUR_TEXT_MUTED}},
        gauge={
            'axis': {
                'range': [0, 100],
                'tickwidth': 1,
                'tickcolor': theme.COLOUR_TEXT_MUTED,
                'tickvals': [0, 50, 100],
                'ticktext': ["0%", "50%", "100%"]
            },
            'bar': {'color': bar_colour, 'thickness': 0.75},
            'bgcolor': theme.COLOUR_APP_BG,
            'borderwidth': 1,
            'bordercolor': theme.COLOUR_BORDER
        }
    ))

    fig.update_layout(
        height=190,
        margin=dict(l=30, r=30, t=45, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=theme.COLOUR_TEXT_MAIN)
    )

    return fig


def render_overall_accuracy_chart(supported: int, contradicted: int, missing_context: int, unclear: int):
    """Render a donut chart showing the proportion of claim verdicts."""

    data = {
        "Verdict": ["Supported", "Contradicted", "Missing Context", "Unclear"],
        "Count": [supported, contradicted, missing_context, unclear]
    }
    df = pd.DataFrame(data)
    df = df[df["Count"] > 0]  # Filter out empty

    if df.empty:
        return None

    colour_map = {
        "Supported": theme.COLOUR_SUCCESS_FG,
        "Contradicted": theme.COLOUR_DANGER_FG,
        "Missing Context": theme.COLOUR_WARNING_FG,
        "Unclear": theme.COLOUR_UNCLEAR_FG
    }

    fig = px.pie(
        df,
        values="Count",
        names="Verdict",
        color="Verdict",
        color_discrete_map=colour_map,
        hole=0.6
    )

    fig.update_layout(
        height=180,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    return fig
