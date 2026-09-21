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
    return information['extract']


def get_all_relevant_information(nlp, keywords: list[str]) -> str:
    """Returns all the relevant information as a paragraph"""
    combined_text = ""
    for keyword in keywords:
        combined_text += get_wiki_article(keyword) + " "
        logging.info(
            "Successfully got information on %s from Wikipedia",
            keyword.lower()
        )
    return combined_text


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    nlp = load_spacy_model()

    text = "The moon is made of blue cheese"

    extract = extract_keywords(nlp, text)
    logging.info("Successfully extracted %s key word(s)", len(extract))

    get_all_relevant_information(nlp, extract)
    logging.info("Extraction complete")
