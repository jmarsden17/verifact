"""Plotly chart builders for claims analytics, latency, techniques, and NLP features."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
from .. import theme
from ._base import apply_base_layout


def build_quick_verdict_donut(df: pd.DataFrame):
    """Quick summary donut chart showing overall verdict distribution using brand colours."""

    if df.empty or "verdict" not in df.columns:
        return None

    counts = df["verdict"].value_counts().reset_index()
    counts.columns = ["Verdict", "Count"]

    fig = px.pie(
        counts,
        values="Count",
        names="Verdict",
        hole=0.6,
        color="Verdict",
        color_discrete_map=theme.VERDICT_CHART_COLOURS,
        category_orders={"Verdict": theme.VERDICT_ORDER}
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hoverinfo="label+value+percent",
        marker=dict(line=dict(color="#FFFFFF", width=2))
    )

    return apply_base_layout(
        fig,
        height=240,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
    )


def build_quick_top_tactics_bar(df: pd.DataFrame):
    """Quick summary horizontal bar chart of top 5 tactics."""

    if df.empty or "technique" not in df.columns:
        return None

    top_tactics = df["technique"].value_counts().head(5).reset_index()
    top_tactics.columns = ["Technique", "Count"]

    fig = px.bar(
        top_tactics,
        x="Count",
        y="Technique",
        orientation="h",
        color_discrete_sequence=[theme.COLOUR_PRIMARY]
    )

    return apply_base_layout(
        fig,
        height=240,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
    )


def build_quadrant_chart(df: pd.DataFrame):
    """4-Quadrant Scatter Plot: Amplification (Outlets) vs Latency (Days)."""

    if df.empty or "days_latent" not in df.columns or "outlet_count" not in df.columns:
        return None

    fig = px.scatter(
        df,
        x="days_latent",
        y="outlet_count",
        color="verdict",
        size="velocity" if "velocity" in df.columns else None,
        hover_name="claim",
        hover_data=["publisher_str",
                    "technique"] if "publisher_str" in df.columns else None,
        color_discrete_map=theme.VERDICT_CHART_COLOURS,
        title="Claim Risk Matrix: Latency vs. Outlet Amplification"
    )

    fig.add_vline(x=7, line_dash="dash", line_color="gray",
                  annotation_text="7-Day Latency Threshold")
    median_outlets = df["outlet_count"].median(
    ) if not df["outlet_count"].empty else 2
    fig.add_hline(y=median_outlets, line_dash="dash",
                  line_color="gray", annotation_text="Median Outlet Spread")

    return apply_base_layout(
        fig,
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Days Latent (Age of Claim)",
        yaxis_title="Outlets Amplifying Claim"
    )


def build_technique_breakdown(df: pd.DataFrame):
    """Stacked bar chart detailing techniques grouped by verdict."""

    if df.empty or "technique" not in df.columns or "verdict" not in df.columns:
        return None

    grouped = df.groupby(["technique", "verdict"]
                         ).size().reset_index(name="count")

    fig = px.bar(
        grouped,
        x="count",
        y="technique",
        color="verdict",
        orientation="h",
        color_discrete_map=theme.VERDICT_CHART_COLOURS,
        title="Tactical Breakdown by Verdict Impact"
    )

    return apply_base_layout(
        fig,
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        barmode="stack",
        xaxis_title="Volume of Claims",
        yaxis_title="Disinformation Technique",
        yaxis={'categoryorder': 'total ascending'}
    )


def build_technique_latency_boxplot(df: pd.DataFrame):
    """Boxplot showing Median, Interquartile Range (IQR), and Outliers for claim latency."""

    if df.empty or "days_latent" not in df.columns or "technique" not in df.columns:
        return None

    fig = px.box(
        df,
        x="technique",
        y="days_latent",
        color="technique",
        points="outliers",
        hover_data=["claim"] if "claim" in df.columns else None,
        title="Statistical Latency Spread & Outliers by Technique (Days)"
    )

    return apply_base_layout(
        fig,
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Disinformation Technique",
        yaxis_title="Days Latent (Age/Resurfacing Delay)",
        showlegend=False
    )


def build_narrative_decay_curve(df: pd.DataFrame):
    """Fits an exponential decay curve to quantify how quickly claims fade out."""

    if df.empty or "days_latent" not in df.columns:
        return None

    valid_latencies = df["days_latent"].dropna()
    if valid_latencies.empty:
        return None

    counts, bin_edges = np.histogram(valid_latencies, bins=20)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=bin_centers,
        y=counts,
        name="Observed Claims",
        marker_color=theme.COLOUR_PRIMARY,
        opacity=0.6
    ))

    if len(counts) > 0 and sum(counts) > 0:
        lambda_est = 1.0 / (valid_latencies.mean() + 1e-5)
        fit_y = max(counts) * np.exp(-lambda_est * bin_centers)

        fig.add_trace(go.Scatter(
            x=bin_centers,
            y=fit_y,
            mode="lines",
            name=f"Decay Curve Trend (λ={lambda_est:.3f})",
            line=dict(color=theme.COLOUR_DANGER_FG, width=3, dash="dash")
        ))

    return apply_base_layout(
        fig,
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Days Elapsed Since Publication",
        yaxis_title="Claim Ingestion Density",
        legend=dict(orientation="h", y=1.1)
    )


def build_tfidf_keyword_chart(df: pd.DataFrame):
    """Uses TF-IDF term weighting to isolate vocabulary overrepresented in disproven claims."""

    if df.empty or "claim" not in df.columns or "verdict" not in df.columns:
        return None

    contradicted_df = df[df["verdict"] == "Contradicted"]
    if len(contradicted_df) < 2:
        return None

    try:
        vectoriser = TfidfVectorizer(
            stop_words="english", max_features=15, ngram_range=(1, 2))
        tfidf_matrix = vectoriser.fit_transform(
            contradicted_df["claim"].dropna())

        scores = tfidf_matrix.sum(axis=0).A1
        words = vectoriser.get_feature_names_out()

        result_df = pd.DataFrame({"Term": words, "TF-IDF Score": scores}).sort_values(
            by="TF-IDF Score", ascending=True
        )

        fig = px.bar(
            result_df,
            x="TF-IDF Score",
            y="Term",
            orientation="h",
            color="TF-IDF Score",
            color_continuous_scale="Reds",
            title="High-Risk Keywords Correlated with Disproven Claims (TF-IDF)"
        )

        return apply_base_layout(
            fig,
            height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis_title="TF-IDF Statistical Weight",
            yaxis_title="Vocabulary / N-Gram"
        )
    except ValueError:
        return None
