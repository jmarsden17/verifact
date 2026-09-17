"""Firecrawl client for extracting articles from specific sites."""

import os
from firecrawl import Firecrawl


def extract(claim: str, site: str):
    """Extract articles from a specific fact check site related to the given claim."""
    firecrawl = Firecrawl(api_key=os.environ["API_KEY"])
    results = firecrawl.search(
        query=f'"{claim}" site:{site}',
        limit=1, scrape_options={"formats": ["markdown", "links"]},
    )
    output = []
    for r in results.web:
        output.append(
            f"Source URL: {r.metadata.url}\n{r.markdown or r.metadata.description}")
    return "\n".join(output)
