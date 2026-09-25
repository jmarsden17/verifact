"""Tests for the analytics views, chart builders, and claim card."""
import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

import frontend.visual_components.charts.claims as claims_chart
import frontend.visual_components.charts.outlet as outlet_chart
import frontend.visual_components.components.claim_card as claim_card
import frontend.visual_components.views.claims_analytics as claims_analytics
import frontend.visual_components.views.outlet_analytics as outlet_analytics
import frontend.visual_components.views.disproven_claims as disproven_claims_view


# ---------------------------------------------------------------------------
# Shared fixtures / stubs
# ---------------------------------------------------------------------------

def _make_raw_claims_df(n_extra=0):
    """Raw claims data shaped like fn.fetch_analytics_data()'s return value."""
    now = datetime(2026, 9, 20)
    rows = [
        dict(claim_id=1, claim="Lemon water cures diabetes overnight", verdict="Contradicted",
             technique="Deepfake", publisher="CNN, BBC",
             publish_datetime=now - timedelta(days=2), access_datetime=now, access_amount=5),
        dict(claim_id=2, claim="New vaccine causes infertility in mice", verdict="Contradicted",
             technique="Policy Distortion", publisher="Fox, CNN",
             publish_datetime=now - timedelta(days=20), access_datetime=now, access_amount=12),
        dict(claim_id=3, claim="City council approves new park funding", verdict="Supported",
             technique="Policy Distortion", publisher="BBC",
             publish_datetime=now - timedelta(days=1), access_datetime=now, access_amount=2),
        dict(claim_id=4, claim="Election results were manipulated by software", verdict="Missing Context",
             technique="Deepfake", publisher="CNN",
             publish_datetime=now - timedelta(days=10), access_datetime=now, access_amount=8),
        dict(claim_id=5, claim="Local bakery wins national award for bread", verdict="Supported",
             technique=None, publisher="Fox",
             publish_datetime=now - timedelta(days=3), access_datetime=now, access_amount=1),
        dict(claim_id=6, claim="Politician caught in fabricated audio scandal", verdict="Contradicted",
             technique="Deepfake", publisher="CNN, Fox, BBC",
             publish_datetime=now - timedelta(days=30), access_datetime=now, access_amount=20),
    ]
    for i in range(n_extra):
        rows.append(dict(
            claim_id=100 + i, claim=f"Extra filler claim number {i} about taxes",
            verdict="Missing Context", technique="Policy Distortion", publisher="BBC",
            publish_datetime=now - timedelta(days=i + 1), access_datetime=now, access_amount=i,
        ))
    return pd.DataFrame(rows)


def _make_processed_claims_df():
    return claims_analytics._preprocess_claims_data(_make_raw_claims_df())


class _DummyBlock:
    """Stands in for a Streamlit DeltaGenerator (column / expander)."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def metric(self, *a, **k):
        pass

    def caption(self, *a, **k):
        pass


@pytest.fixture
def stub_streamlit(monkeypatch):
    """Patch the streamlit widget calls used by the views under test."""
    import streamlit as st

    def fake_columns(spec, **kwargs):
        n = len(spec) if isinstance(spec, (list, tuple)) else spec
        return [_DummyBlock() for _ in range(n)]

    monkeypatch.setattr(st, "columns", fake_columns)
    monkeypatch.setattr(st, "expander", lambda *a, **k: _DummyBlock())
    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "warning", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "dataframe", lambda *a, **k: None)
    monkeypatch.setattr(st, "multiselect",
                        lambda label, options=None, default=None, **k: default if default is not None else [])
    monkeypatch.setattr(st, "text_input", lambda *a, **k: "")
    monkeypatch.setattr(st, "slider", lambda label, mn, mx,
                        val=None, **k: val if val is not None else mn)
    monkeypatch.setattr(st, "selectbox", lambda label,
                        options, **k: options[0])
    monkeypatch.setattr(st, "segmented_control",
                        lambda label, options, default=None, **k: default)
    monkeypatch.setattr(st, "number_input", lambda label,
                        min_value=1, value=1, **k: value)
    return st


# ---------------------------------------------------------------------------
# claims_analytics.py -- data processing
# ---------------------------------------------------------------------------

def test_preprocess_claims_data_adds_fields():
    df = claims_analytics._preprocess_claims_data(_make_raw_claims_df())
    for col in ("days_latent", "publisher_str", "outlet_list", "outlet_count", "velocity"):
        assert col in df.columns
    assert (df["days_latent"] >= 0).all()
    assert df.loc[df["claim_id"] == 1, "outlet_count"].iloc[0] == 2
    assert df.loc[df["claim_id"] == 6, "outlet_count"].iloc[0] == 3


def test_preprocess_claims_data_handles_missing_publisher():
    raw = _make_raw_claims_df()
    raw.loc[0, "publisher"] = None
    df = claims_analytics._preprocess_claims_data(raw)
    assert df.loc[0, "publisher_str"] == "Unattributed"
    assert df.loc[0, "outlet_count"] == 1


def test_apply_keyword_filter_matches_claim_or_publisher():
    df = _make_processed_claims_df()
    result = claims_analytics._apply_keyword_filter(df, "lemon")
    assert len(result) == 1
    assert "lemon" in result.iloc[0]["claim"].lower()

    result_pub = claims_analytics._apply_keyword_filter(df, "Fox")
    assert (result_pub["publisher_str"].str.contains("Fox")).all()


def test_apply_keyword_filter_multiple_terms_and_empty():
    df = _make_processed_claims_df()
    result = claims_analytics._apply_keyword_filter(df, "lemon, bakery")
    assert len(result) == 2

    unfiltered = claims_analytics._apply_keyword_filter(df, "")
    assert len(unfiltered) == len(df)


def test_apply_metadata_filters_verdict_and_technique():
    df = _make_processed_claims_df()
    result = claims_analytics._apply_metadata_filters(
        df, verdicts=["Contradicted"], techniques=[], min_outlets=1, latency_mode="All Claims")
    assert (result["verdict"] == "Contradicted").all()

    result_tech = claims_analytics._apply_metadata_filters(
        df, verdicts=[], techniques=["Deepfake"], min_outlets=1, latency_mode="All Claims")
    assert (result_tech["technique"] == "Deepfake").all()


def test_apply_metadata_filters_min_outlets_and_latency():
    df = _make_processed_claims_df()
    result = claims_analytics._apply_metadata_filters(
        df, verdicts=[], techniques=[], min_outlets=3, latency_mode="All Claims")
    assert (result["outlet_count"] >= 3).all()

    breaking = claims_analytics._apply_metadata_filters(
        df, verdicts=[], techniques=[], min_outlets=1, latency_mode="Breaking / Viral (<7 Days)")
    assert (breaking["days_latent"] <= 7).all()

    resurfaced = claims_analytics._apply_metadata_filters(
        df, verdicts=[], techniques=[], min_outlets=1, latency_mode="Resurfaced Myths (>7 Days)")
    assert (resurfaced["days_latent"] > 7).all()


# ---------------------------------------------------------------------------
# claims_analytics.py -- UI helpers / render()
# ---------------------------------------------------------------------------

def test_render_kpi_card_row_empty_df_warns(stub_streamlit, monkeypatch):
    warned = {}
    monkeypatch.setattr(stub_streamlit, "warning",
                        lambda msg: warned.setdefault("msg", msg))
    claims_analytics._render_kpi_card_row(pd.DataFrame())
    assert "msg" in warned


def test_render_kpi_card_row_with_data(stub_streamlit):
    df = _make_processed_claims_df()
    claims_analytics._render_kpi_card_row(df)  # should not raise


def test_render_quick_summary_row(stub_streamlit):
    df = _make_processed_claims_df()
    claims_analytics._render_quick_summary_row(df)  # should not raise


def test_render_velocity_and_lifespan_and_keywords_sections(stub_streamlit):
    df = _make_processed_claims_df()
    claims_analytics._render_velocity_section(df)
    claims_analytics._render_lifespan_section(df)
    claims_analytics._render_keywords_section(df)


def test_claims_analytics_render_full_page(stub_streamlit, monkeypatch):
    monkeypatch.setattr(claims_analytics.fn, "fetch_analytics_data",
                        lambda: _make_raw_claims_df())
    monkeypatch.setattr(
        claims_analytics, "render_page_header", lambda *a, **k: None)
    claims_analytics.render()  # exercises the full happy path


def test_claims_analytics_render_empty_data_warns(stub_streamlit, monkeypatch):
    monkeypatch.setattr(claims_analytics.fn,
                        "fetch_analytics_data", lambda: pd.DataFrame())
    monkeypatch.setattr(
        claims_analytics, "render_page_header", lambda *a, **k: None)
    warned = {}
    monkeypatch.setattr(stub_streamlit, "warning",
                        lambda msg: warned.setdefault("msg", msg))
    claims_analytics.render()
    assert "msg" in warned


# ---------------------------------------------------------------------------
# claims.py -- chart builders
# ---------------------------------------------------------------------------

def test_build_quick_verdict_donut():
    df = _make_processed_claims_df()
    fig = claims_chart.build_quick_verdict_donut(df)
    assert fig is not None
    assert claims_chart.build_quick_verdict_donut(pd.DataFrame()) is None


def test_build_quick_top_tactics_bar():
    df = _make_processed_claims_df()
    assert claims_chart.build_quick_top_tactics_bar(df) is not None
    assert claims_chart.build_quick_top_tactics_bar(pd.DataFrame()) is None


def test_build_quadrant_chart():
    df = _make_processed_claims_df()
    fig = claims_chart.build_quadrant_chart(df)
    assert fig is not None
    assert claims_chart.build_quadrant_chart(pd.DataFrame()) is None


def test_build_technique_breakdown():
    df = _make_processed_claims_df()
    assert claims_chart.build_technique_breakdown(df) is not None
    assert claims_chart.build_technique_breakdown(pd.DataFrame()) is None


def test_build_technique_latency_boxplot():
    df = _make_processed_claims_df()
    assert claims_chart.build_technique_latency_boxplot(df) is not None
    assert claims_chart.build_technique_latency_boxplot(pd.DataFrame()) is None


def test_build_narrative_decay_curve():
    df = _make_processed_claims_df()
    fig = claims_chart.build_narrative_decay_curve(df)
    assert fig is not None
    assert claims_chart.build_narrative_decay_curve(pd.DataFrame()) is None

    empty_latency = df.copy()
    empty_latency["days_latent"] = np.nan
    assert claims_chart.build_narrative_decay_curve(empty_latency) is None


def test_build_tfidf_keyword_chart():
    df = _make_processed_claims_df()
    fig = claims_chart.build_tfidf_keyword_chart(df)
    assert fig is not None
    # Fewer than 2 contradicted claims -> None
    only_supported = df[df["verdict"] == "Supported"]
    assert claims_chart.build_tfidf_keyword_chart(only_supported) is None
    assert claims_chart.build_tfidf_keyword_chart(pd.DataFrame()) is None


# ---------------------------------------------------------------------------
# outlet.py -- chart builders
# ---------------------------------------------------------------------------

def test_explode_publishers():
    raw = _make_raw_claims_df()
    exploded = outlet_chart._explode_publishers(raw)
    assert len(exploded) > len(raw)
    assert "CNN" in exploded["publisher"].values


def test_build_outlet_chart():
    raw = _make_raw_claims_df()
    assert outlet_chart.build_outlet_chart(raw) is not None
    assert outlet_chart.build_outlet_chart(pd.DataFrame()) is None


def test_build_quick_top_outlets_bar():
    exploded = outlet_chart._explode_publishers(_make_raw_claims_df())
    assert outlet_chart.build_quick_top_outlets_bar(exploded) is not None
    assert outlet_chart.build_quick_top_outlets_bar(pd.DataFrame()) is None


def test_build_quick_outlet_verdict_breakdown():
    exploded = outlet_chart._explode_publishers(_make_raw_claims_df())
    assert outlet_chart.build_quick_outlet_verdict_breakdown(
        exploded) is not None
    assert outlet_chart.build_quick_outlet_verdict_breakdown(
        pd.DataFrame()) is None


def test_build_falsehood_density_matrix():
    exploded = outlet_chart._explode_publishers(_make_raw_claims_df())
    assert outlet_chart.build_falsehood_density_matrix(exploded) is not None
    assert outlet_chart.build_falsehood_density_matrix(pd.DataFrame()) is None


def test_build_syndication_network():
    raw = _make_raw_claims_df()
    assert outlet_chart.build_syndication_network(raw) is not None
    assert outlet_chart.build_syndication_network(pd.DataFrame()) is None

    # No comma-separated publishers anywhere -> no co-occurrences -> None
    solo = raw.copy()
    solo["publisher"] = "SoloOutlet"
    assert outlet_chart.build_syndication_network(solo) is None


def test_build_jaccard_similarity_heatmap():
    raw = _make_raw_claims_df(n_extra=3)
    fig = outlet_chart.build_jaccard_similarity_heatmap(raw)
    assert fig is not None
    assert outlet_chart.build_jaccard_similarity_heatmap(
        pd.DataFrame()) is None

    # Single publisher only -> basket has <2 columns -> None
    solo = raw.copy()
    solo["publisher"] = "OnlyOneOutlet"
    assert outlet_chart.build_jaccard_similarity_heatmap(solo) is None


# ---------------------------------------------------------------------------
# outlet_analytics.py -- data processing + render()
# ---------------------------------------------------------------------------

def test_filter_by_outlets_and_volume():
    exploded = outlet_chart._explode_publishers(_make_raw_claims_df())

    filtered = outlet_analytics._filter_by_outlets(exploded, ["CNN"])
    assert (filtered["publisher"] == "CNN").all()

    unfiltered = outlet_analytics._filter_by_outlets(exploded, [])
    assert len(unfiltered) == len(exploded)

    by_volume = outlet_analytics._filter_by_volume(exploded, 3)
    counts = exploded["publisher"].value_counts()
    assert set(by_volume["publisher"].unique()) == set(
        counts[counts >= 3].index)


def test_build_scorecard_dataframe():
    exploded = outlet_chart._explode_publishers(_make_raw_claims_df())
    scorecard = outlet_analytics._build_scorecard_dataframe(exploded)
    assert "unreliability_index" in scorecard.columns
    assert set(["total_claims", "contradicted", "missing_context",
               "supported"]).issubset(scorecard.columns)
    # sorted descending by total_claims
    assert list(scorecard["total_claims"]) == sorted(
        scorecard["total_claims"], reverse=True)


def test_outlet_analytics_render_full_page(stub_streamlit, monkeypatch):
    monkeypatch.setattr(outlet_analytics.fn, "fetch_analytics_data",
                        lambda: _make_raw_claims_df())
    monkeypatch.setattr(
        outlet_analytics, "render_page_header", lambda *a, **k: None)
    outlet_analytics.render()


def test_outlet_analytics_render_empty_data_warns(stub_streamlit, monkeypatch):
    monkeypatch.setattr(outlet_analytics.fn,
                        "fetch_analytics_data", lambda: pd.DataFrame())
    monkeypatch.setattr(
        outlet_analytics, "render_page_header", lambda *a, **k: None)
    warned = {}
    monkeypatch.setattr(stub_streamlit, "warning",
                        lambda msg: warned.setdefault("msg", msg))
    outlet_analytics.render()
    assert "msg" in warned


# ---------------------------------------------------------------------------
# claim_card.py -- helpers
# ---------------------------------------------------------------------------

def test_clean_handles_none_nan_and_values():
    assert claim_card._clean(None) is None
    assert claim_card._clean(float("nan")) is None
    assert claim_card._clean("") is None
    assert claim_card._clean("hello") == "hello"
    assert claim_card._clean(5) == 5
    assert claim_card._clean([]) is None
    assert claim_card._clean([1, 2]) == [1, 2]


def test_relative_date_variants():
    today = pd.Timestamp.now().normalize()
    assert claim_card._relative_date(today) == "today"
    assert claim_card._relative_date(
        today - pd.Timedelta(days=1)) == "yesterday"
    assert claim_card._relative_date(
        today - pd.Timedelta(days=5)) == "5 days ago"
    older = today - pd.Timedelta(days=30)
    assert claim_card._relative_date(older) == older.strftime("%d %b %Y")
    assert claim_card._relative_date(None) is None
    assert claim_card._relative_date("not-a-date") == "not-a-date"


def test_as_link_list_variants():
    links = [{"outlet": "BBC", "url": "https://bbc.com"}]
    assert claim_card._as_link_list(links) == links
    assert claim_card._as_link_list(json.dumps(links)) == links
    assert claim_card._as_link_list("not json") == []
    assert claim_card._as_link_list(None) == []
    assert claim_card._as_link_list(42) == []


def test_sources_html_with_links_and_fallback():
    links = [{"outlet": "BBC", "url": "https://bbc.com/story"}]
    html = claim_card._sources_html(links, None)
    assert "bbc.com/story" in html
    assert "BBC" in html

    fallback = claim_card._sources_html(None, "Reuters, AP")
    assert "Reuters" in fallback and "AP" in fallback

    assert claim_card._sources_html(None, None) == ""


def test_meta_text_combines_parts():
    row = {"publish_datetime": pd.Timestamp.now().normalize(),
           "access_amount": 3}
    text = claim_card._meta_text(row)
    assert "Published today" in text
    assert "Checked 3 times" in text

    single = claim_card._meta_text(
        {"publish_datetime": None, "access_amount": 1})
    assert "Checked 1 time" in single
    assert "times" not in single


def test_render_disproven_claim_card(monkeypatch):
    import streamlit as st
    captured = {}
    monkeypatch.setattr(st, "markdown", lambda html, **
                        k: captured.setdefault("html", html))

    row = {
        "verdict": "Contradicted",
        "technique": "Deepfake",
        "summary": "A" * 300,  # forces truncation branch
        "source_links": json.dumps([{"outlet": "BBC", "url": "https://bbc.com"}]),
        "publishers": None,
        "claim_text": "Lemon water cures diabetes",
        "publish_datetime": pd.Timestamp.now().normalize(),
        "access_amount": 4,
    }
    claim_card.render_disproven_claim_card(row)
    assert "CONTRADICTED" in captured["html"]
    assert "Deepfake" in captured["html"]
    assert "..." in captured["html"]  # summary truncated
    assert "Lemon water cures diabetes" in captured["html"]


def test_render_disproven_claim_card_unknown_verdict_style(monkeypatch):
    import streamlit as st
    captured = {}
    monkeypatch.setattr(st, "markdown", lambda html, **
                        k: captured.setdefault("html", html))
    row = {
        "verdict": "Unclear",
        "technique": None,
        "summary": None,
        "source_links": None,
        "publishers": None,
        "claim_text": "Some unverified claim",
        "publish_datetime": None,
        "access_amount": None,
    }
    claim_card.render_disproven_claim_card(row)
    assert "UNCLEAR" in captured["html"]


# ---------------------------------------------------------------------------
# disproven_claims.py (view) -- controls, stats, render()
# ---------------------------------------------------------------------------

def _make_disproven_df(is_sample=False):
    df = pd.DataFrame([
        dict(claim_id=1, verdict="Contradicted",
             technique="Deepfake", claim_text="Claim A"),
        dict(claim_id=2, verdict="Missing Context",
             technique="Deepfake", claim_text="Claim B"),
        dict(claim_id=3, verdict="Contradicted",
             technique="Policy Distortion", claim_text="Claim C"),
    ])
    df.attrs["is_sample"] = is_sample
    return df


def test_render_controls_returns_defaults(stub_streamlit):
    sort_key, verdict = disproven_claims_view._render_controls()
    assert sort_key == "newest"
    assert verdict == "All"


def test_render_feed_stats(stub_streamlit):
    df = _make_disproven_df()
    disproven_claims_view._render_feed_stats(df)  # should not raise


def test_render_feed_stats_no_technique_column(stub_streamlit):
    df = _make_disproven_df().drop(columns=["technique"])
    disproven_claims_view._render_feed_stats(df)  # falls back to "N/A" branch


def test_disproven_claims_render_happy_path(stub_streamlit, monkeypatch):
    monkeypatch.setattr(disproven_claims_view,
                        "render_page_header", lambda *a, **k: None)
    monkeypatch.setattr(disproven_claims_view.data, "get_disproven_claims",
                        lambda sort_key, verdict, limit: _make_disproven_df())
    rendered = []
    monkeypatch.setattr(disproven_claims_view, "render_disproven_claim_card",
                        lambda row: rendered.append(row))
    disproven_claims_view.render()
    assert len(rendered) == 3


def test_disproven_claims_render_sample_data_warns(stub_streamlit, monkeypatch):
    monkeypatch.setattr(disproven_claims_view,
                        "render_page_header", lambda *a, **k: None)
    monkeypatch.setattr(disproven_claims_view.data, "get_disproven_claims",
                        lambda sort_key, verdict, limit: _make_disproven_df(is_sample=True))
    monkeypatch.setattr(disproven_claims_view,
                        "render_disproven_claim_card", lambda row: None)
    warned = {}
    monkeypatch.setattr(stub_streamlit, "warning",
                        lambda msg: warned.setdefault("msg", msg))
    disproven_claims_view.render()
    assert "msg" in warned


def test_disproven_claims_render_empty_shows_info(stub_streamlit, monkeypatch):
    monkeypatch.setattr(disproven_claims_view,
                        "render_page_header", lambda *a, **k: None)
    empty = pd.DataFrame()
    empty.attrs["is_sample"] = False
    monkeypatch.setattr(disproven_claims_view.data, "get_disproven_claims",
                        lambda sort_key, verdict, limit: empty)
    informed = {}
    monkeypatch.setattr(stub_streamlit, "info",
                        lambda msg: informed.setdefault("msg", msg))
    disproven_claims_view.render()
    assert "msg" in informed
