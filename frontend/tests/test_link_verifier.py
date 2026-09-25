"""Tests for the link verifier functions."""

import socket
import ssl

import pytest

from database_conns.link_verifier import is_valid_url, ssl_check, verify_url


def test_is_valid_url():
    assert is_valid_url("https://www.example.com") is True
    assert is_valid_url("http://www.example.com") is True
    assert is_valid_url("https://example.com") is True
    assert is_valid_url("ftp://example.com") is False
    assert is_valid_url("www.example.com") is False
    assert is_valid_url("example") is False


def test_ssl_check_valid_certificate_is_true(mocker):
    mock_sock = mocker.MagicMock()
    mock_sock.__enter__.return_value = mock_sock
    mocker.patch(
        "database_conns.link_verifier.socket.create_connection",
        return_value=mock_sock,
    )
    mock_ctx = mocker.MagicMock()
    mock_ctx.wrap_socket.return_value.__enter__.return_value = mocker.MagicMock()
    mocker.patch(
        "database_conns.link_verifier.ssl.create_default_context",
        return_value=mock_ctx,
    )
    assert ssl_check("https://www.example.com") is True


def test_ssl_check_non_https_is_not_checked():
    assert ssl_check("http://www.example.com") is None


@pytest.mark.parametrize("network_error", [
    pytest.param(socket.gaierror("Name or service not known"), id="dns failure"),
    pytest.param(socket.timeout("timed out"), id="connection times out"),
    pytest.param(ConnectionRefusedError("Connection refused"), id="connection refused"),
])
def test_ssl_check_network_errors_are_inconclusive(mocker, network_error):
    mocker.patch(
        "database_conns.link_verifier.socket.create_connection",
        side_effect=network_error,
    )
    assert ssl_check("https://www.test.co.uk") is None


def test_ssl_check_bad_certificate_is_invalid(mocker):
    mock_sock = mocker.MagicMock()
    mock_sock.__enter__.return_value = mock_sock
    mocker.patch(
        "database_conns.link_verifier.socket.create_connection",
        return_value=mock_sock,
    )
    mock_ctx = mocker.MagicMock()
    mock_ctx.wrap_socket.side_effect = ssl.SSLError("certificate verify failed")
    mocker.patch(
        "database_conns.link_verifier.ssl.create_default_context",
        return_value=mock_ctx,
    )
    assert ssl_check("https://www.test.co.uk") is False


def test_ssl_check_uses_the_urls_own_port(mocker):
    mock_sock = mocker.MagicMock()
    mock_sock.__enter__.return_value = mock_sock
    mock_create_connection = mocker.patch(
        "database_conns.link_verifier.socket.create_connection",
        return_value=mock_sock,
    )
    mocker.patch("database_conns.link_verifier.ssl.create_default_context")
    ssl_check("https://www.test.co.uk:8443")
    assert mock_create_connection.call_args.args[0] == ("www.test.co.uk", 8443)


def test_verify_url_accepts_a_valid_https_url(mocker):
    mocker.patch("database_conns.link_verifier.ssl_check", return_value=True)
    assert verify_url("https://www.example.com") is True


def test_verify_url_accepts_http_without_checking_ssl():
    # http has no certificate to check; ssl_check itself would return None
    # for a non-https scheme, so nothing needs mocking here.
    assert verify_url("http://www.example.com") is True


def test_verify_url_rejects_malformed_urls():
    assert verify_url("ftp://example.com") is False
    assert verify_url("www.example.com") is False
    assert verify_url("example") is False


def test_verify_url_does_not_reject_on_an_inconclusive_check(mocker):
    mocker.patch("database_conns.link_verifier.ssl_check", return_value=None)
    assert verify_url("https://www.test.co.uk") is True


def test_verify_url_rejects_a_confirmed_bad_certificate(mocker):
    mocker.patch("database_conns.link_verifier.ssl_check", return_value=False)
    assert verify_url("https://www.test.co.uk") is False