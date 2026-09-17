"""Firecrawl client for extracting articles from specific sites."""

import os
from firecrawl import Firecrawl
from urllib.parse import urlparse


def extract(claim: str, site: str):
    """Extract articles from a specific fact check site related to the given claim."""
    firecrawl = Firecrawl(api_key=os.environ["API_KEY"])
    domain = urlparse(site).netloc or site
    results = firecrawl.search(
        query=f'"{claim}" site:{domain}',
        limit=1, scrape_options={"formats": ["markdown", "links"]},
        timeout=30
    )
    output = []
    urls = []
    for r in results.web:
        output.append(
            f"Source URL: {r.metadata.url}\n{r.markdown or r.metadata.description}")
        urls.append(r.metadata.url)
    return "\n".join(output), urls
