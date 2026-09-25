"""Extracts the content of the URL a user submits as a claim."""

from os import environ
import logging
from dotenv import load_dotenv
import trafilatura
from trafilatura.settings import use_config
from firecrawl import Firecrawl


TRAFILATURA_TIMEOUT_SECONDS = 10


def extract_with_trafilatura(url: str) -> str | None:
    """Scrapes web content with trafilatura."""

    try:
        config = use_config()
        config.set("DEFAULT", "DOWNLOAD_TIMEOUT",
                   str(TRAFILATURA_TIMEOUT_SECONDS))
        downloaded = trafilatura.fetch_url(url, config=config)
        result = trafilatura.extract(downloaded)
        if result:
            logging.info('Successfully extracted URL with Trafilatura')
            return result
    except Exception as e:
        logging.warning('Failed to extract with Trafilatura: %s', e)
    return None


def extract_with_firecrawl(url: str) -> str | None:
    """Scrapes web content using FireCrawl."""

    api_key = environ.get('FIRECRAWL_API_KEY')
    if not api_key:
        logging.error(
            'FIRECRAWL_API_KEY is not set; skipping FireCrawl extraction')
        return None

    try:
        app = Firecrawl(api_key=api_key)
        result = app.scrape(url)
        markdown = result.get('markdown') if isinstance(result, dict) else None
        if markdown:
            logging.info("Successfully extracted URL with FireCrawl")
            return markdown
    except Exception as e:
        logging.warning('Failed to extract with FireCrawl: %s', e)
    return None


def extract_url(url: str) -> str | None:
    """Extracts information from URL."""

    logging.info("Attempt extraction with Trafilatura")
    extraction = extract_with_trafilatura(url)
    if extraction:
        return extraction

    logging.info("Attempt extraction with FireCrawl")
    extraction = extract_with_firecrawl(url)
    if extraction:
        return extraction

    logging.warning('Error: Cannot extract content with any scraper')
    return None


if __name__ == "__main__":

    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    web = 'https://www.bbc.co.uk/news/articles/c6y0z4gv0le4o'

    extract_url(web)
