"""
The load aspect of the ETL pipeline.
Uploads data into the RDS table
"""
from os import environ
import logging
from dotenv import load_dotenv
from psycopg2 import connect, OperationalError
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.extensions import connection


def get_db_connection() -> connection:
    """Returns a live connection from the database."""
    try:
        return connect(
            cursor_factory=RealDictCursor,
            dbname=environ["DATABASE_NAME"],
            host=environ["DATABASE_IP"],
            password=environ["DATABASE_PASSWORD"],
            user=environ["DATABASE_USERNAME"],
            port=environ["DATABASE_PORT"]
        )
    except OperationalError as e:
        logging.error(e)
        return None


def add_claims_to_database(conn: connection, data: list[tuple]) -> None:
    """Inserts claims to the database"""
    with conn.cursor() as cursor:
        query = """
            INSERT INTO claim
                (claim, claim_url, publish_datetime, access_datetime, verdict_id, technique_id, summary, claim_embedding)
            VALUES %s
            ON CONFLICT (claim, publish_datetime, access_datetime)
            DO NOTHING;
        """

        execute_values(cursor, query, data)
        conn.commit()


def add_claim_tags_to_database(conn: connection, data: list[tuple]) -> None:
    """Inserts claim and tags to the database"""
    with conn.cursor() as cursor:
        query = """
            INSERT INTO claim_tags
                (claim_id, tag_id)
            VALUES %s
            ON CONFLICT (claim_id, tag_id)
            DO NOTHING;
        """

        execute_values(cursor, query, data)
        conn.commit()


def add_source_to_database(conn: connection, data: list[tuple]) -> None:
    """Inserts source to the database"""
    with conn.cursor() as cursor:
        query = """
            INSERT INTO source
                (source_url, source_verification, outlet_id)
            VALUES %s;
        """

        execute_values(cursor, query, data)
        conn.commit()


def add_claim_source_to_database(conn: connection, data: list[tuple]) -> None:
    """Inserts claim and source to the database"""
    with conn.cursor() as cursor:
        query = """
            INSERT INTO claim_source
                (claim_id, source_id)
            VALUES %s
            ON CONFLICT (claim_id, source_id)
            DO NOTHING;
        """

        execute_values(cursor, query, data)
        conn.commit()


if __name__ == "__main__":

    # Set up:
    logging.basicConfig(level=logging.INFO)
    load_dotenv()

    conn = get_db_connection()

    if conn is None:
        raise SystemExit(1)
    logging.info("Successfully connected to the database")

    conn.close()
