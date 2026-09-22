"""
Extracts the content of the URL a user submits as a claim.
"""
from os import environ
import logging
from dotenv import load_dotenv
import trafilatura
from firecrawl import Firecrawl


def extract_with_trafilatura(url: str) -> str:
    """Scrapes web content with trafilatura"""
    try:
        downloaded = trafilatura.fetch_url(url)
        result = trafilatura.extract(downloaded)
        if result:
            logging.info('Successfully extracted URL with Trafilatura')
            return result
    except Exception as e:
        logging.warning('Failed to extract with Trafilatura: %s', e)
    return None


def extract_with_firecrawl(url: str) -> str:
    """Scrapes web content using FireCrawl"""
    try:
        app = Firecrawl(api_key=environ['FIRECRAWL_API_KEY'])
        result = app.scrape(url)
        if isinstance(result, dict) and 'markdown' in result:
            logging.info("Successfully extracted URL with Firecrawl")
            return result['markdown']
    except Exception as e:
        logging.warning('Failed to extract with FireCrawl: %s', e)
    return None


def extract_url(url: str) -> str:
    """Extracts information from URL"""
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
