"""Holds functions for calculating embedding vectors using OpenAI's API."""
from openai import OpenAI
from dotenv import load_dotenv
import os


def generate_embeddings(claim: str) -> list[int]:
    """Generate embedding vector for a given claim using OpenAI's API."""
    load_dotenv()
    api_key = os.environ["OPENAI_API_KEY"]

    client = OpenAI(api_key=api_key)

    response = client.embeddings.create(
        input=claim,
        model="text-embedding-3-small"
    )
    embedding_vector = response.data[0].embedding
    return embedding_vector
