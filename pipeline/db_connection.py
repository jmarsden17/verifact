"""Holds functions for calculating embedding vectors using OpenAI's API."""
from openai import OpenAI
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import register_vector


def get_connection():
    load_dotenv()
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        port=os.environ['DB_PORT']
    )
    register_vector(conn)
    return conn


def find_most_similar_claim(query_embedding):
    """Find the most similar claim(s) to a query embedding using pgvector cosine distance."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, claim_text, 1 - (embedding <=> %s) AS similarity
            FROM claims
            ORDER BY embedding <=> %s
            WHERE 1 - (embedding <=> %s) >= 0.8 
            LIMIT 1
            """,
            (query_embedding, query_embedding, query_embedding)
        )
        embedding = cur.fetchall()
    claim = embedding[0]['claim_text'] if embedding else None
    similarity = embedding[0]['similarity'] if embedding else None
    return claim, similarity
