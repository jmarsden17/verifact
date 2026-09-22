"""Visual components for outlet-related charts."""

from ._base import TOP_RIGHT_LEGEND, apply_base_layout
from .. import theme
import plotly.express as px
import numpy as np
import pandas as pd


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


def build_falsehood_density_matrix(exploded_df: pd.DataFrame):
    """Scatter chart mapping total claim volume vs falsehood rate per outlet."""
    if exploded_df.empty or "publisher" not in exploded_df.columns:
        return None

    stats = exploded_df.groupby("publisher").agg(
        total_claims=("claim_id", "nunique"),
        contradicted=("verdict", lambda x: (x == "Contradicted").sum()),
        missing_context=("verdict", lambda x: (x == "Missing Context").sum()),
        techniques_used=("technique", "nunique")
    ).reset_index()

    if stats.empty:
        return None

    stats["falsehood_rate"] = (
        (stats["contradicted"] + stats["missing_context"]) / stats["total_claims"]) * 100

    fig = px.scatter(
        stats,
        x="total_claims",
        y="falsehood_rate",
        size="techniques_used",
        text="publisher",
        color="falsehood_rate",
        color_continuous_scale="Reds",
        title="Publisher Falsehood Density vs. Total Volume"
    )

    fig.update_traces(textposition="top center")
    fig.update_layout(
        xaxis_title="Total Claims Associated with Outlet",
        yaxis_title="Unreliable Claims Rate (%)",
        height=420,
        showlegend=False
    )
    return fig


def build_syndication_network(df: pd.DataFrame):
    """Identifies outlets frequently sharing or co-publishing identical claims."""
    if df.empty or "publisher" not in df.columns:
        return None

    # Filter claims associated with multi-outlet strings
    multi = df[df["publisher"].fillna("").str.contains(",")]
    if multi.empty:
        return None

    co_occurrences = {}
    for pub_str in multi["publisher"]:
        pubs = sorted(
            list(set([p.strip() for p in pub_str.split(",") if p.strip()])))
        for i in range(len(pubs)):
            for j in range(i + 1, len(pubs)):
                pair = f"{pubs[i]} ↔ {pubs[j]}"
                co_occurrences[pair] = co_occurrences.get(pair, 0) + 1

    if not co_occurrences:
        return None

    network_df = pd.DataFrame([
        {"Syndicate Pair": k, "Shared Claims": v}
        for k, v in co_occurrences.items()
    ]).sort_values(by="Shared Claims", ascending=True)

    fig = px.bar(
        network_df.tail(10),
        x="Shared Claims",
        y="Syndicate Pair",
        orientation="h",
        color="Shared Claims",
        color_continuous_scale="Viridis",
        title="Top 10 Outlet Co-Publishing Networks"
    )

    fig.update_layout(
        xaxis_title="Shared Disproven/Verified Claims",
        yaxis_title="Outlet Pair",
        height=420
    )
    return fig


def build_jaccard_similarity_heatmap(df: pd.DataFrame):
    """
    Calculates Jaccard Similarity Index J(A,B) = |A ∩ B| / |A ∪ B|
    between pairs of outlets based on the exact claims they cover.
    A score close to 1.0 indicates synchronized publication behavior.
    """
    if df.empty or "publisher" not in df.columns:
        return None

    exploded = _explode_publishers(df)

    # Filter top publishers for matrix readability
    top_publishers = exploded["publisher"].value_counts().head(
        12).index.tolist()
    filtered = exploded[exploded["publisher"].isin(top_publishers)]

    if filtered.empty:
        return None

    # Pivot into binary presence matrix (Claims x Outlets)
    basket = (filtered.groupby(["claim_id", "publisher"])["claim"]
              .count().unstack().fillna(0)
              .map(lambda x: 1 if x > 0 else 0))

    if basket.shape[1] < 2:
        return None

    cols = basket.columns
    n = len(cols)
    jaccard_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i == j:
                jaccard_matrix[i][j] = 1.0
            else:
                intersection = np.logical_and(
                    basket.iloc[:, i], basket.iloc[:, j]).sum()
                union = np.logical_or(
                    basket.iloc[:, i], basket.iloc[:, j]).sum()
                jaccard_matrix[i][j] = intersection / \
                    union if union != 0 else 0

    sim_df = pd.DataFrame(jaccard_matrix, index=cols, columns=cols)

    fig = px.imshow(
        sim_df,
        labels=dict(x="Outlet A", y="Outlet B", color="Jaccard Index"),
        color_continuous_scale="Purples",
        title="Cross-Outlet Co-occurrence Matrix (Jaccard Similarity Index)"
    )
    fig.update_layout(height=420)
    return fig
