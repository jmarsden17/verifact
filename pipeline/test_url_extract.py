# pylint: skip-file

"""
Test for the url_extract.py file
"""
import pytest
import logging
from url_extract import (
    extract_with_trafilatura,
    extract_with_firecrawl,
    extract_url
)


def test_extract_with_trafilatura_valid(mocker, caplog):
    caplog.set_level(logging.INFO)

    mock_trafilatura_fetch_url = mocker.patch(
        "url_extract.trafilatura.fetch_url", return_value="test fetch url")
    mock_trafilatura_extract = mocker.patch(
        "url_extract.trafilatura.extract", return_value="test extract")

    url = "www.test.co.uk"
    result = extract_with_trafilatura(url)

    assert result == "test extract"
    mock_trafilatura_fetch_url.assert_called_once_with(url)
    mock_trafilatura_extract.assert_called_once_with("test fetch url")
    assert "Successfully extracted URL with Trafilatura" in caplog.text


def test_extract_with_trafilatura_none(mocker, caplog):
    caplog.set_level(logging.INFO)

    mocker.patch("url_extract.trafilatura.fetch_url", return_value=None)

    url = "www.invalid_test.co.uk"
    result = extract_with_trafilatura(url)

    assert result is None


def test_extract_with_trafilatura_error(mocker, caplog):
    caplog.set_level(logging.INFO)

    mocker.patch(
        "url_extract.trafilatura.fetch_url",
        side_effect=Exception("Error")
    )

    url = "www.invalid_test.co.uk"
    result = extract_with_trafilatura(url)

    assert result is None
    assert "Failed to extract with Trafilatura" in caplog.text


def test_extract_with_firecrawl_valid(mocker, caplog):
    caplog.set_level(logging.INFO)

    mock_firecrawl_app = mocker.Mock()
    mock_firecrawl_app.scrape.return_value = {
        "markdown": "test markdown"
    }
    mocker.patch("url_extract.Firecrawl", return_value=mock_firecrawl_app)
    mocker.patch.dict("url_extract.environ", {"FIRECRAWL_API_KEY": "test_key"})

    url = "www.test.co.uk"
    result = extract_with_firecrawl(url)

    assert result == "test markdown"
    mock_firecrawl_app.scrape.assert_called_once_with(url)
    assert "Successfully extracted URL with FireCrawl" in caplog.text


def test_extract_with_firecrawl_none(mocker, caplog):
    caplog.set_level(logging.INFO)

    mock_firecrawl_app = mocker.Mock()
    mock_firecrawl_app.scrape.return_value = {
        "markdown": None
    }
    mocker.patch("url_extract.Firecrawl", return_value=mock_firecrawl_app)
    mocker.patch.dict("url_extract.environ", {"FIRECRAWL_API_KEY": "test_key"})

    url = "www.invalid_test.co.uk"
    result = extract_with_firecrawl(url)

    assert result is None


def test_extract_with_firecrawl_error(mocker, caplog):
    caplog.set_level(logging.INFO)

    mocker.patch("url_extract.Firecrawl", side_effect=Exception("Error"))
    mocker.patch.dict("url_extract.environ", {"FIRECRAWL_API_KEY": "test_key"})

    url = "www.invalid_test.co.uk"
    result = extract_with_firecrawl(url)

    assert result is None
    assert "Failed to extract with FireCrawl" in caplog.text


def test_extract_url_trafilatura_success(mocker, caplog):
    caplog.set_level(logging.INFO)

    mock_trafilatura_fetch = mocker.patch(
        "url_extract.trafilatura.fetch_url", return_value="test fetch")
    mock_trafilatura_extract = mocker.patch(
        "url_extract.trafilatura.extract", return_value="test extract")
    mock_firecrawl = mocker.patch("url_extract.extract_with_firecrawl")

    url = "www.test.co.uk"
    result = extract_url(url)

    assert result == "test extract"
    mock_trafilatura_fetch.assert_called_once_with(url)
    mock_trafilatura_extract.assert_called_once_with("test fetch")
    mock_firecrawl.assert_not_called()
    assert "Successfully extracted URL with Trafilatura" in caplog.text


def test_extract_url_trafilatura_fail_firecrawl_success(mocker, caplog):
    caplog.set_level(logging.INFO)

    mocker.patch("url_extract.trafilatura.fetch_url", return_value=None)

    mock_firecrawl_app = mocker.Mock()
    mock_firecrawl_app.scrape.return_value = {
        "markdown": "test markdown"
    }
    mocker.patch("url_extract.Firecrawl", return_value=mock_firecrawl_app)
    mocker.patch.dict("url_extract.environ", {"FIRECRAWL_API_KEY": "test_key"})

    url = "www.test.co.uk"
    result = extract_url(url)

    assert result == "test markdown"
    mock_firecrawl_app.scrape.assert_called_once_with(url)
    assert "Successfully extracted URL with FireCrawl" in caplog.text


def test_extract_url_all_fail(mocker, caplog):
    caplog.set_level(logging.INFO)

    mocker.patch("url_extract.trafilatura.fetch_url", return_value=None)

    mocker.patch("url_extract.Firecrawl", side_effect=Exception("Error"))
    mocker.patch.dict("url_extract.environ", {"FIRECRAWL_API_KEY": "test_key"})

    url = "www.test.co.uk"
    result = extract_url(url)

    assert result is None
    assert "Error: Cannot extract content with any scraper" in caplog.text
