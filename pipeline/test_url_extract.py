# pylint: skip-file

"""
Tests for url_extract.py.

extract_url() tries trafilatura first and falls back to Firecrawl if
trafilatura returns nothing. Each scraper's own function
(extract_with_trafilatura, extract_with_firecrawl) has three outcomes:
success, no result, or an exception. Those are parametrised so more
cases can be added as a single line each.
"""

import logging

import pytest

from url_extract import (
    extract_with_trafilatura,
    extract_with_firecrawl,
    extract_url,
)


# ---------------------------------------------------------------------------
# extract_with_trafilatura
# ---------------------------------------------------------------------------

def test_extract_with_trafilatura_success(mocker, caplog):
    """A page that fetches and extracts returns the extracted text."""
    caplog.set_level(logging.INFO)
    mock_fetch = mocker.patch(
        "url_extract.trafilatura.fetch_url", return_value="test fetch url")
    mock_extract = mocker.patch(
        "url_extract.trafilatura.extract", return_value="test extract")

    url = "www.test.co.uk"

    result = extract_with_trafilatura(url)

    assert result == "test extract"
    mock_fetch.assert_called_once_with(url)
    mock_extract.assert_called_once_with("test fetch url")
    assert "Successfully extracted URL with Trafilatura" in caplog.text


@pytest.mark.parametrize("fetch_return, extract_return", [
    pytest.param(None, None, id="fetch returns nothing"),
    pytest.param("test fetch url", None, id="extract returns nothing"),
    pytest.param("test fetch url", "", id="extract returns an empty string"),
])
def test_extract_with_trafilatura_no_result(mocker, fetch_return, extract_return):
    """No page or no extractable text returns None, without raising."""
    mocker.patch("url_extract.trafilatura.fetch_url", return_value=fetch_return)
    mocker.patch("url_extract.trafilatura.extract", return_value=extract_return)

    result = extract_with_trafilatura("www.test.co.uk")

    assert result is None


@pytest.mark.parametrize("failing_step", [
    pytest.param("fetch_url", id="fetch_url raises"),
    pytest.param("extract", id="extract raises"),
])
def test_extract_with_trafilatura_error(mocker, caplog, failing_step):
    """An exception from either trafilatura call is caught and returns None."""
    caplog.set_level(logging.INFO)
    mocker.patch("url_extract.trafilatura.fetch_url", return_value="test fetch url")
    mocker.patch(f"url_extract.trafilatura.{failing_step}",
                 side_effect=Exception("Trafilatura error"))

    result = extract_with_trafilatura("www.test.co.uk")

    assert result is None
    assert "Failed to extract with Trafilatura" in caplog.text


# ---------------------------------------------------------------------------
# extract_with_firecrawl
# ---------------------------------------------------------------------------

def test_extract_with_firecrawl_success(mocker, caplog):
    """A scrape that returns markdown gives back that markdown."""
    caplog.set_level(logging.INFO)
    mock_app = mocker.Mock()
    mock_app.scrape.return_value = {"markdown": "test markdown"}
    mocker.patch("url_extract.Firecrawl", return_value=mock_app)
    mocker.patch.dict("url_extract.environ", {"FIRECRAWL_API_KEY": "test_key"})

    url = "www.test.co.uk"

    result = extract_with_firecrawl(url)

    assert result == "test markdown"
    mock_app.scrape.assert_called_once_with(url)
    assert "Successfully extracted URL with FireCrawl" in caplog.text


def test_extract_with_firecrawl_markdown_key_is_none(mocker, caplog):
    """The 'markdown' key existing with a None value still counts as a match:
    the code only checks the key is present, not that its value is truthy,
    so the success log fires even though the returned value is None."""
    caplog.set_level(logging.INFO)
    mock_app = mocker.Mock()
    mock_app.scrape.return_value = {"markdown": None}
    mocker.patch("url_extract.Firecrawl", return_value=mock_app)
    mocker.patch.dict("url_extract.environ", {"FIRECRAWL_API_KEY": "test_key"})

    result = extract_with_firecrawl("www.test.co.uk")

    assert result is None
    assert "Successfully extracted URL with FireCrawl" in caplog.text


@pytest.mark.parametrize("scrape_return", [
    pytest.param({}, id="no markdown key"),
    pytest.param("not a dict", id="result is not a dict"),
    pytest.param(None, id="result is none"),
])
def test_extract_with_firecrawl_no_result(mocker, caplog, scrape_return):
    """A response with no 'markdown' key returns None silently: no success
    log, and no exception raised (which would otherwise be swallowed by the
    broad except and look the same as this path from the return value alone)."""
    caplog.set_level(logging.INFO)
    mock_app = mocker.Mock()
    mock_app.scrape.return_value = scrape_return
    mocker.patch("url_extract.Firecrawl", return_value=mock_app)
    mocker.patch.dict("url_extract.environ", {"FIRECRAWL_API_KEY": "test_key"})

    result = extract_with_firecrawl("www.test.co.uk")

    assert result is None
    assert "Successfully extracted URL with FireCrawl" not in caplog.text
    assert "Failed to extract with FireCrawl" not in caplog.text


@pytest.mark.parametrize("failing_call", [
    pytest.param("client", id="creating the Firecrawl client raises"),
    pytest.param("scrape", id="scrape raises"),
])
def test_extract_with_firecrawl_error(mocker, caplog, failing_call):
    """An exception creating the client or scraping is caught and returns None."""
    caplog.set_level(logging.INFO)
    mocker.patch.dict("url_extract.environ", {"FIRECRAWL_API_KEY": "test_key"})

    if failing_call == "client":
        mocker.patch("url_extract.Firecrawl",
                     side_effect=Exception("Firecrawl error"))
    else:
        mock_app = mocker.Mock()
        mock_app.scrape.side_effect = Exception("Firecrawl error")
        mocker.patch("url_extract.Firecrawl", return_value=mock_app)

    result = extract_with_firecrawl("www.test.co.uk")

    assert result is None
    assert "Failed to extract with FireCrawl" in caplog.text


def test_extract_with_firecrawl_missing_api_key(mocker, caplog):
    """A missing FIRECRAWL_API_KEY is caught the same way as any other error."""
    caplog.set_level(logging.INFO)
    mocker.patch.dict("url_extract.environ", {}, clear=True)

    result = extract_with_firecrawl("www.test.co.uk")

    assert result is None
    assert "Failed to extract with FireCrawl" in caplog.text


# ---------------------------------------------------------------------------
# extract_url: the fallback behaviour
# ---------------------------------------------------------------------------

def test_extract_url_uses_trafilatura_when_it_succeeds(mocker, caplog):
    """If trafilatura returns text, Firecrawl is never tried."""
    caplog.set_level(logging.INFO)
    mocker.patch("url_extract.extract_with_trafilatura", return_value="from trafilatura")
    mock_firecrawl = mocker.patch("url_extract.extract_with_firecrawl")

    result = extract_url("www.test.co.uk")

    assert result == "from trafilatura"
    mock_firecrawl.assert_not_called()


def test_extract_url_falls_back_to_firecrawl(mocker, caplog):
    """If trafilatura returns nothing, Firecrawl is tried next."""
    caplog.set_level(logging.INFO)
    mocker.patch("url_extract.extract_with_trafilatura", return_value=None)
    mocker.patch("url_extract.extract_with_firecrawl", return_value="from firecrawl")

    result = extract_url("www.test.co.uk")

    assert result == "from firecrawl"


def test_extract_url_returns_none_when_both_fail(mocker, caplog):
    """If neither scraper returns anything, extract_url returns None and warns."""
    caplog.set_level(logging.INFO)
    mocker.patch("url_extract.extract_with_trafilatura", return_value=None)
    mocker.patch("url_extract.extract_with_firecrawl", return_value=None)

    result = extract_url("www.test.co.uk")

    assert result is None
    assert "Error: Cannot extract content with any scraper" in caplog.text