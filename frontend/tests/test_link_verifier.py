"""Tests for the link verifier functions."""

from database_conns.link_verifier import is_valid_url, ssl_check, verify_url


def test_is_valid_url():
    assert is_valid_url("https://www.example.com") is True
    assert is_valid_url("http://www.example.com") is True
    assert is_valid_url("https://example.com") is True
    assert is_valid_url("ftp://example.com") is False
    assert is_valid_url("www.example.com") is False
    assert is_valid_url("example") is False


def test_verify_url():
    assert verify_url("https://www.example.com") is True
    assert verify_url("http://www.example.com") is True
    assert verify_url("ftp://example.com") is False
    assert verify_url("www.example.com") is False
    assert verify_url("example") is False
