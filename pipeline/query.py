"""
Main functionalities:
- Queries the database for claims with the same category
- Queries the filtered database to look for claims with the same semantic
- If there are no similar claims:
    - Returns nothing
- If there are similar claims:
    - Returns the sources so that it can be compared
"""
from os import environ
import logging
from dotenv import load_dotenv
import pandas as pd
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


def handler(event=None, context=None):
    """Main function for the query lambda function"""
    # Set up:
    logging.basicConfig(level=logging.INFO)
    load_dotenv()

    conn = get_db_connection()

    if conn is None:
        raise SystemExit(1)

    # TODO: Complete this:
    conn.close()

    return {}


if __name__ == "__main__":

    handler()
