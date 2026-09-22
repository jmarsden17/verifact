# pylint: skip-file

"""
Tests for url_extract.py.

extract_url() has two paths: a successful download and parse, or an
exception caught and returned as an error dict. Both are parametrised
so more cases can be added as a single line each.
"""

import logging

import pytest

from url_extract import extract_url


@pytest.mark.parametrize("title, text", [
    pytest.param("Test Title", "Test Text", id="normal title and text"),
    pytest.param("", "", id="empty title and text"),
    pytest.param("Título con acentos", "Contenido áéíóú", id="non ascii text"),
])
def test_extract_url_success(mocker, caplog, title, text):
    """A successful download and parse returns the article's title and text."""
    caplog.set_level(logging.INFO)
    mock_article = mocker.Mock()
    mock_article.title = title
    mock_article.text = text

    mock_article_class = mocker.patch(
        "url_extract.Article",
        return_value=mock_article,
    )

    url = "www.test.co.uk"

    result = extract_url(url)

    assert result == {"title": title, "text": text}
    mock_article_class.assert_called_once_with(url)
    mock_article.download.assert_called_once_with()
    mock_article.parse.assert_called_once_with()
    assert "Successfully extracted from URL" in caplog.text


@pytest.mark.parametrize("failing_step, error", [
    pytest.param("download", Exception("Connection failed"),
                 id="download fails"),
    pytest.param("parse", Exception("Malformed article"),
                 id="parse fails"),
    pytest.param("download", ValueError("Invalid URL"),
                 id="download raises a different exception type"),
])
def test_extract_url_failure(mocker, caplog, failing_step, error):
    """A failure in download or parse is caught and returned as an error dict."""
    mock_article = mocker.Mock()
    getattr(mock_article, failing_step).side_effect = error

    mock_article_class = mocker.patch(
        "url_extract.Article",
        return_value=mock_article,
    )

    url = "www.test-invalid.co.uk"

    result = extract_url(url)

    assert result == {"error": error}
    mock_article_class.assert_called_once_with(url)
    assert f"Cannot extract from URL: {error}" in caplog.text

    # if download fails, parse should never be reached
    if failing_step == "download":
        mock_article.parse.assert_not_called()