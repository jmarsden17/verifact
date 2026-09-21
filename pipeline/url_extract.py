"""
Extracts the content of the URL a user submits as a claim.
"""
import logging
from newspaper import Article
import requests
from bs4 import BeautifulSoup


def extract_url(url: str) -> dict:
    """Extracts the content from the url"""
    try:
        header = {
            'User-Agent': 'Disinformation'
        }
        article = Article(url, headers=header, request_timeout=10)
        article.download()
        article.parse()

        logging.info("Successfully extracted from URL")

        return {
            "title": article.title,
            "text": article.text
        }

    except Exception as e:
        logging.error("Cannot extract from URL")
        return {
            "error": e
        }


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    web = 'https://www.ft.com/content/697c5196-3aa4-4c59-bad9-a455bcc1858f?syn-25a6b1a6=1'

    print(extract_url(web))
