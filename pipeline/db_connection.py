"""Holds functions for calculating embedding vectors using OpenAI's API."""
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import register_vector


def get_connection():
    """Establish a connection to the PostgreSQL database and register the vector type."""
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
            SELECT claim_id, claim, 1 - (embedding <=> %s) AS similarity, verdict.verdict, summary, technique.technique
            FROM claims
            LEFT JOIN verdict USING (verdict_id)
            LEFT JOIN technique USING (technique_id)

            ORDER BY embedding <=> %s
            WHERE 1 - (embedding <=> %s) >= 0.8 
            LIMIT 1
            """,
            (query_embedding, query_embedding, query_embedding)
        )
        embedding = cur.fetchall()
    claim = embedding[0]['claim'] if embedding else None
    similarity = embedding[0]['similarity'] if embedding else None
    verdict = embedding[0]['verdict'] if embedding else None
    summary = embedding[0]['summary'] if embedding else None
    technique = embedding[0]['technique'] if embedding else None
    return claim, similarity, verdict, summary, technique
