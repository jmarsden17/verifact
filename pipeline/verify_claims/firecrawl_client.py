"""Firecrawl client for extracting articles from specific sites."""

import os
from urllib.parse import urlparse
from firecrawl import Firecrawl


def extract(claim: str, site: str):
    """Extract articles from a specific fact check site related to the given claim."""
    firecrawl = Firecrawl(api_key=os.environ["API_KEY"])
    domain = urlparse(site).netloc or site
    results = firecrawl.search(
        query=f'"{claim}" site:{domain}',
        limit=1, scrape_options={"formats": ["markdown", "links"]},
        timeout=30000
    )
    output = []
    urls = []

    for r in results.web or []:
        url = getattr(r.metadata, "url", None) if r.metadata else None
        description = getattr(r.metadata, "description",
                              None) if r.metadata else None
        markdown = getattr(r, "markdown", None)
        output.append(f"Source URL: {url}\n{markdown or description}")
        urls.append(url)
    return "\n".join(output), urls
