"""Helpers for safely putting database / web-scraped text into HTML."""

import html
from urllib.parse import urlparse


def esc(value) -> str:
    """HTML-escape any value (None becomes an empty string)."""

    return "" if value is None else html.escape(str(value), quote=True)


def safe_url(url) -> str | None:
    """Return the URL if it is http(s), otherwise None (blocks javascript: links etc.)."""

    if not isinstance(url, str):
        return None
    url = url.strip()
    return url if urlparse(url).scheme in ("http", "https") else None


def domain_of(url: str) -> str:
    """Readable label for a link, e.g. 'fullfact.org'."""

    return urlparse(url).netloc.removeprefix("www.")
