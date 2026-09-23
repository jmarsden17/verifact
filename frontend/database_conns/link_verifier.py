import re
import ssl
import socket
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    url_pattern = "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"

    """Check if the given URL is valid."""
    if re.match(url_pattern, url):

        return True

    return False


def ssl_check(url: str, timeout: float = 5.0) -> str | None:
    """Return an error string if the SSL certificate is invalid/expired, else None."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return None
    host = parsed.netloc
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host):
                return True
        return None
    except Exception as e:
        return False


def verify_url(url: str) -> bool:
    """Verify if the URL is valid and has a valid SSL certificate."""
    if not is_valid_url(url):
        return False
    ssl_result = ssl_check(url)
    if ssl_result is False:
        return False
    return True
