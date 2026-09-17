# pylint: skip-file

"""
Test for the url_extract.py file
"""
import pytest
import logging
from url_extract import extract_url


def test_extract_url_valid(mocker, caplog):
    caplog.set_level(logging.INFO)
    mock_article = mocker.Mock()

    mock_article.title = "Test Title"
    mock_article.text = "Test Text"

    mock_article_class = mocker.patch(
        "url_extract.Article",
        return_value=mock_article,
    )

    url = "www.test.co.uk"

    result = {
        "title": "Test Title",
        "text": "Test Text"
    }

    assert extract_url(url) == result
    mock_article_class.assert_called_once_with(url)
    mock_article.download.assert_called_once_with()
    mock_article.parse.assert_called_once_with()
    assert "Successfully extracted from URL" in caplog.text


def test_extract_url_invalid(mocker, caplog):
    mock_article = mocker.Mock()

    message = Exception("Failed")
    mock_article.download.side_effect = message

    mock_article_class = mocker.patch(
        "url_extract.Article",
        return_value=mock_article,
    )

    url = "www.test_invalid.co.uk"

    result = {
        "error": message
    }

    assert extract_url(url) == result
    assert "Cannot extract from URL" in caplog.text
