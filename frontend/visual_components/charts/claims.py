"""Visual components for claim-related charts."""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from .. import theme
from sklearn.feature_extraction.text import TfidfVectorizer


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

    # Reference lines for Quadrant Analysis
    fig.add_vline(x=7, line_dash="dash", line_color="gray",
                  annotation_text="7-Day Latency Threshold")
    median_outlets = df["outlet_count"].median(
    ) if not df["outlet_count"].empty else 2
    fig.add_hline(y=median_outlets, line_dash="dash",
                  line_color="gray", annotation_text="Median Outlet Spread")

    fig.update_layout(
        xaxis_title="Days Latent (Age of Claim)",
        yaxis_title="Outlets Amplifying Claim",
        height=400
    )
    return fig


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
    fig.update_layout(
        barmode="stack",
        xaxis_title="Volume of Claims",
        yaxis_title="Disinformation Technique",
        height=400,
        yaxis={'categoryorder': 'total ascending'}
    )
    return fig


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

    fig.update_layout(
        xaxis_title="Disinformation Technique",
        yaxis_title="Days Latent (Age/Resurfacing Delay)",
        showlegend=False,
        height=400
    )
    return fig


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
        marker_color="#3366CC",
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
            line=dict(color="#DC3912", width=3, dash="dash")
        ))

    fig.update_layout(
        title="Propaganda Persistence & Decay Curve",
        xaxis_title="Days Elapsed Since Publication",
        yaxis_title="Claim Ingestion Density",
        height=400,
        legend=dict(orientation="h", y=1.1)
    )
    return fig


def build_tfidf_keyword_chart(df: pd.DataFrame):
    """Uses TF-IDF term weighting to isolate vocabulary overrepresented in disproven claims."""
    if df.empty or "claim" not in df.columns or "verdict" not in df.columns:
        return None

    contradicted_df = df[df["verdict"] == "Contradicted"]
    if len(contradicted_df) < 2:
        return None

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english", max_features=15, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(
            contradicted_df["claim"].dropna())

        scores = tfidf_matrix.sum(axis=0).A1
        words = vectorizer.get_feature_names_out()

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

        fig.update_layout(
            xaxis_title="TF-IDF Statistical Weight",
            yaxis_title="Vocabulary / N-Gram",
            height=400
        )
        return fig
    except ValueError:
        # Handles cases where text corpus is empty or contains only stop words
        return None
