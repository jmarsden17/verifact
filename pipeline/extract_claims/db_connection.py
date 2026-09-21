"""Holds functions for calculating embedding vectors using OpenAI's API."""
from dotenv import load_dotenv
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector


def get_connection():
    """Establish a connection to the PostgreSQL database and register the vector type."""
    load_dotenv()
    logging.info(
        "Loading environment variables and setting up database connection.")
    try:
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            dbname=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            port=os.environ['DB_PORT']
        )
        register_vector(conn)
    except Exception as e:
        logging.error(f"Error connecting to database: {e}")
        raise
    return conn


def find_most_similar_claim(query_embedding):
    """Find the most similar claim(s) to a query embedding using pgvector cosine distance."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                WITH matched_claims AS (
                    SELECT claim_id, claim, 1 - (claim_embedding <=> %s::vector) AS similarity, verdict_id, summary, technique_id
                    FROM claim

                    WHERE 1 - (claim_embedding <=> %s::vector) >= 0.8 
                    ORDER BY claim_embedding <=> %s::vector
                    LIMIT 1
                ),
                updated AS (
                    UPDATE claim
                    SET access_datetime = NOW()
                    WHERE claim_id = (SELECT claim_id FROM matched_claims)
                    RETURNING claim_id
                )

                SELECT m.claim, m.similarity, v.verdict, m.summary, t.technique
                FROM matched_claims m
                LEFT JOIN verdict v USING (verdict_id)
                LEFT JOIN technique t USING (technique_id)
                
                """,
                (query_embedding, query_embedding, query_embedding)
            )
            row = cur.fetchone()
            conn.commit()
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        raise
    finally:
        conn.close()

    if row is None:
        return None, None, None, None, None

    return row['claim'], row['similarity'], row['verdict'], row['summary'], row['technique']
