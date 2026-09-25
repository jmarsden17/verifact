"""Firecrawl client for extracting articles from specific sites."""

from time import sleep
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from firecrawl import Firecrawl
from bs4 import BeautifulSoup
from requests import get


def extract(claim: str, site: str) -> tuple:
    """Extract articles from a specific fact check site related to the given claim."""
    firecrawl = Firecrawl(api_key=os.environ["API_KEY"])
    domain = urlparse(site).netloc or site

    logging.info("Searching %s for claim: %.80s", domain, claim)

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

    if not urls:
        logging.warning("No search results on %s for claim: %.80s", domain, claim)
    else:
        logging.info("Found %d result(s) on %s", len(urls), domain)

    return "\n".join(output), urls


def get_article_content(link: str) -> dict[str, str]:
    """Returns the full content of a BBC news article."""
    logging.info("Fetching article: %s", link)

    res = get(link)

    soup = BeautifulSoup(res.content, features="html.parser")

    title_tag = soup.find("h1")
    content_tag = soup.find("main")

    if title_tag is None or content_tag is None:
        logging.warning(
            "Article page missing expected h1/main elements: %s", link)

    return {
        "url": link,
        "title": title_tag.get_text().strip() if title_tag else "",
        "content": content_tag.get_text().strip() if content_tag else "",
        "published": soup.find("time")["datetime"] if soup.find("time") else ""

    }


def get_article_links(claim, site: str, source_url: str) -> list[str]:
    """Returns a list of relevant article links."""
    logging.info("Searching %s for claim: %.80s", site, claim)

    res = get(site + claim, timeout=5)

    soup = BeautifulSoup(res.content, features="html.parser")

    articles = soup.find_all("a", class_="exn3ah94")

    links = [a["href"] for a in articles
            if a["href"].startswith(source_url)]

    if not links:
        logging.warning(
            "No matching links found on %s for claim: %.80s", site, claim)
    else:
        logging.info("Found %d link(s) on %s", len(links), site)

    return links


def extract_scrape(claim: str, site: str, source_url: str) -> list[dict]:
    """Returns scraped articles."""
    claim = claim.strip()
    claim = claim.replace(" ", "%20")

    links = get_article_links(claim, site, source_url)

    articles = [get_article_content(l) for l in links]

    logging.info("Scraped %d article(s) from %d link(s)", len(articles), len(links))

    return articles