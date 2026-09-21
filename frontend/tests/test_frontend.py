"""Testing file for frontend services."""

import pytest
import pandas as pd
from streamlit.testing.v1 import AppTest
from utils import db as fn
from components import visuals as vis
from components import theme

# Successful path tests


def test_verify_claim_success():
    """Verify complete structure returned on valid input."""

    result = fn.verify_claim(
        "Lemon water cures diabetes", "https://example.com")
    assert isinstance(result, dict)
    assert "rating" in result
    assert "reasoning" in result
    assert "sources" in result
    assert len(result["sources"]) > 0


def test_get_breaking_claims_structure():
    """Ensure breaking claims returns list of non-empty claims."""

    claims = fn.get_breaking_claims()
    assert isinstance(claims, list)
    assert len(claims) > 0
    assert "title" in claims[0]
    assert "status" in claims[0]


def test_get_filtered_logs_no_filter():
    """Verify log fetching returns complete DataFrame when un-filtered."""

    df = fn.get_filtered_logs("", "All")
    assert isinstance(df, pd.DataFrame)
    assert len(df) >= 3
    assert "Claim Statement" in df.columns


# Unsuccessful path tests and edge cases

def test_verify_claim_empty_input():
    """Empty or whitespace input should return None."""

    assert fn.verify_claim("", "") is None
    assert fn.verify_claim("   ", "") is None


def test_verify_claim_extremely_long_input():
    """Extremely long text string payload handling."""

    long_claim = "Claim " * 1000
    result = fn.verify_claim(long_claim, "")
    assert result is not None
    assert isinstance(result["rating"], str)


def test_get_filtered_logs_invalid_keyword():
    """Keyword search returning zero matching records."""

    df = fn.get_filtered_logs("NON_EXISTENT_QUERY_XYZ", "All")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0


def test_get_filtered_logs_verdict_filter():
    """Test precise filtering by specific verdict type."""

    df = fn.get_filtered_logs("", "Contradicted")
    assert len(df) > 0
    assert all(df["Verdict"] == "Contradicted")


# Visual and theme tests

def test_render_confidence_gauge_variations():
    """Test gauge chart generation across all verdict rating colors."""

    ratings = ["Supported", "Contradicted", "Missing Context", "Unclear"]
    for r in ratings:
        fig = vis.render_confidence_gauge(85.5, r)
        assert fig is not None


def test_render_outlet_analytics_chart():
    """Ensure stacked analytics chart compiles without throwing exceptions."""

    fig = vis.render_outlet_analytics_chart()
    assert fig is not None


# UI integration tests

@pytest.fixture
def app():
    """Fixture to initialise AppTest instance."""

    at = AppTest.from_file(__file__.replace("test_frontend.py", "app.py"))
    at.session_state["authenticated"] = True
    at.run()
    return at


def test_app_initial_load(app):
    """Verify app loads on Claim Verification Workspace by default without exceptions."""

    assert not app.exception
    # Verify main text area is present on initial workspace load
    assert len(app.text_area) > 0


def test_navigation_switch_pages(app):
    """Test switching through all sidebar radio choices using .set_value()."""

    pages = ["Top / New Stories", "Verification Logs",
             "Outlet Analytics", "Claim Verification"]

    for page in pages:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception


def test_preset_button_click(app):
    """Test clicking a sample claim pre-fills the form."""

    # Click Lemon Water Cure preset button
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["input_claim"] != ""
    assert "lemon water" in app.session_state["input_claim"].lower()


def test_submit_valid_claim(app):
    """Test filling out and submitting the verification form."""

    app.text_area[0].input("Viral post claims tax rate cut").run()
    # Click form submit button (last button rendered in form container)
    app.button[3].click().run()
    assert not app.exception


def test_submit_empty_form_warning(app):
    """Submitting empty input triggers warning message."""

    app.session_state["input_claim"] = ""
    app.session_state["input_url"] = ""
    app.run()

    # Click submit button on empty input
    app.button[3].click().run()
    assert not app.exception
    assert len(app.warning) > 0
    assert "Please select a sample claim" in app.warning[0].value


def test_logs_filtering_ui(app):
    """Test searching and dropdown selection within the Logs view."""
    app.sidebar.radio[0].set_value("Verification Logs").run()

    app.text_input[0].input("Lemon").run()
    assert not app.exception

    app.selectbox[0].set_value("Contradicted").run()
    assert not app.exception
