"""
Extract information from the Wikipedia API
"""
import logging
import requests
import spacy
import pytextrank


def load_spacy_model():
    """Load spacy model"""
    nlp = spacy.load("en_core_web_md")
    logging.info("Successfully loaded the SpaCy model")
    nlp.add_pipe("textrank")
    return nlp


def extract_keywords(nlp, claim: str) -> list[str]:
    """Returns an extracted list of keywords from a claim"""
    extracted_phrases = []
    doc = nlp(claim)
    for phrase in doc._.phrases[:10]:
        extracted_phrases.append(phrase.text.capitalize())
    return extracted_phrases


def get_wiki_article(keyword: str) -> str:
    """Returns the first paragraph of the wiki article based on key word"""
    wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}"
    headers = {
        "User-Agent": "VeriFact"
    }
    information = requests.get(wiki_url, headers=headers).json()
    if 'extract' in information:
        return information['extract']
    else:
        logging.warning("No information for %s", keyword.lower())
        return None


def get_all_relevant_information(nlp, keywords: list[str]) -> str:
    """Returns all the relevant information as a paragraph"""
    combined_text = ""
    for keyword in keywords:
        extract = get_wiki_article(keyword)
        if extract is not None:
            combined_text += extract + " "
            logging.info(
                "Successfully got information on %s from Wikipedia",
                keyword.lower()
            )
    return combined_text


def handler(event=None, context=None):
    """Main handler function for Lambda"""
    logging.basicConfig(level=logging.INFO)
    nlp = load_spacy_model()

    # TODO: Change this to the claims
    text = "The moon is made of blue cheese"

    extract = extract_keywords(nlp, text)
    logging.info(
        "Successfully extracted %s key word(s)",
        len(extract)
    )

    get_all_relevant_information(nlp, extract)
    logging.info("Extraction complete")

    # TODO: Add a return to pass data to the next Lambda
