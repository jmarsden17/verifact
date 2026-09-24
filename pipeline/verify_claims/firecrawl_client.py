"""Firecrawl client for extracting articles from specific sites."""

from dotenv import load_dotenv
from time import sleep
import os
from urllib.parse import urlparse
from firecrawl import Firecrawl
from bs4 import BeautifulSoup
from requests import get


def extract(claim: str, site: str) -> tuple:
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


def get_article_content(link: str) -> dict[str, str]:
    """Returns the full content of a BBC news article."""

    res = get(link)

    soup = BeautifulSoup(res.content, features="html.parser")

    return {
        "url": link,
        "title": soup.find("h1").get_text().strip(),
        "content": soup.find("main").get_text().strip(),
        "published": soup.find("time")["datetime"] if soup.find("time") else ""

    }


def get_article_links(claim, site: str, source_url: str) -> list[str]:
    """Returns a list of relevant article links."""
    res = get(site + claim, timeout=5)

    soup = BeautifulSoup(res.content, features="html.parser")

    articles = soup.find_all("a", class_="exn3ah94")

    return [a["href"] for a in articles
            if a["href"].startswith(source_url)]


def extract_scrape(claim: str, site: str, source_url: str) -> list[dict]:
    """Returns scraped articles."""
    claim = claim.strip()
    claim = claim.replace(" ", "%20")

    links = get_article_links(claim, site, source_url)

    return [get_article_content(l) for l in links]
