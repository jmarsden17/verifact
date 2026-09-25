"""Validate a user-submitted URL before it is scraped."""

import logging
import re
import socket
import ssl
from urllib.parse import urlparse

URL_PATTERN = (
    r"^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}"
    r"\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$"
)


def is_valid_url(url: str) -> bool:
    """Check if the given URL is a well-formed http(s) address."""

    return bool(re.match(URL_PATTERN, url))


def ssl_check(url: str, timeout: float = 5.0) -> bool | None:
    """True if valid, False if confirmed bad, None if not checkable."""

    parsed = urlparse(url)
    if parsed.scheme != "https":
        return None

    host = parsed.hostname
    if not host:
        return None

    try:
        port = parsed.port or 443
    except ValueError:
        return False

    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host):
                return True
    except ssl.SSLError:
        return False
    except OSError as e:
        logging.warning("Could not check SSL certificate for %s: %s", url, e)
        return None


def verify_url(url: str) -> bool:
    """Verify if the URL is valid and does not have a confirmed-bad certificate."""

    if not is_valid_url(url):
        return False
    if ssl_check(url) is False:
        return False
    return True
