"""
Extracts the content of the URL a user submits as a claim.
"""
import logging
from newspaper import Article


def extract_url(url: str) -> dict:
    """Extracts the content from the url"""
    try:
        article = Article(url)
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
