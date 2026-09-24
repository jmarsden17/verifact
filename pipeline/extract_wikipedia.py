"""
A file that scrapes Wikipedia
"""

import logging
import requests
from requests import get
from bs4 import BeautifulSoup


def get_article_titles(claim: str) -> list[str]:
    """Returns a list of article titles from Wikipedia search results"""
    wiki_url = "https://en.wikipedia.org/w/index.php?search="
    headers = {
        "User-Agent": "VeriFact"
    }

    res = get(wiki_url + claim, headers=headers, timeout=5)
    soup = BeautifulSoup(res.content, features="html.parser")

    # Target links specifically inside search result headings
    search_heading_links = soup.select(".mw-search-result-heading a")

    return [
        a["title"]
        for a in search_heading_links
        if a.has_attr("title")
    ]


def get_wiki_article(title: str) -> tuple:
    """Returns the full wiki article based on keyword."""
    wiki_url_api = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|info",
        "inprop": "url",
        "explaintext": True,
        "titles": title,
        "redirects": 1,
    }
    headers = {
        "User-Agent": "VeriFact"
    }

    try:
        response = requests.get(wiki_url_api, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id != "-1" and "extract" in page_data:
                content = page_data["extract"]
                url = page_data.get("fullurl")
                return [content], [url]

    except requests.RequestException as e:
        logging.error("Failed to retrieve article for %s: %s", title, e)

    logging.warning("No information found for %s", title.lower())
    return [], []


def wiki_search(claim: str) -> list[dict]:
    """Returns scraped articles."""

    titles = get_article_titles(claim)

    if len(titles) > 0:
        title = titles[0]
        return get_wiki_article(title)

    return [], []


if __name__ == "__main__":

    print(wiki_search('moon is made of cheese.'))
