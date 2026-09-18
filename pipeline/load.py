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
import pandas as pd


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


def get_tag_mapping(conn: connection) -> dict:
    """Returns a dictionary mapping all the tags and their ID"""
    with conn.cursor() as cursor:
        query = """
            SELECT tag, tag_id
            FROM tags;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
    return {row["tag"]: row["tag_id"] for row in rows}


def get_verdict_mapping(conn: connection) -> dict:
    """Returns a dictionary mapping all the verdict and their ID"""
    with conn.cursor() as cursor:
        query = """
            SELECT verdict, verdict_id
            FROM verdict;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
    return {row["verdict"]: row["verdict_id"] for row in rows}


def get_technique_mapping(conn: connection) -> dict:
    """Returns a dictionary mapping all the technique and their ID"""
    with conn.cursor() as cursor:
        query = """
            SELECT technique, technique_id
            FROM technique;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
    return {row["technique"]: row["technique_id"] for row in rows}


def get_outlet_mapping(conn: connection) -> dict:
    """Returns a dictionary mapping all the outlet and their ID"""
    with conn.cursor() as cursor:
        query = """
            SELECT outlet, outlet_id
            FROM outlet;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
    return {row["outlet"]: row["outlet_id"] for row in rows}


def add_claims_to_database(conn: connection, data: list[tuple]) -> dict:
    """Inserts claims to the database"""
    with conn.cursor() as cursor:
        query = """
            INSERT INTO claim (
                claim, 
                claim_url, 
                publish_datetime, 
                access_datetime, 
                verdict_id, 
                technique_id, 
                summary, 
                claim_embedding
            )
            VALUES %s
            ON CONFLICT (claim, publish_datetime, access_datetime)
            DO NOTHING
            RETURNING claim, claim_id;
        """

        rows = execute_values(cursor, query, data, fetchall=True)
        conn.commit()
    return dict(rows)


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


def add_source_to_database(conn: connection, data: list[tuple]) -> list[int]:
    """Inserts source to the database"""
    with conn.cursor() as cursor:
        query = """
            INSERT INTO source
                (source_url, source_verification, outlet_id)
            VALUES %s
            RETURNING source, source_id;;
        """

        rows = execute_values(cursor, query, data, fetchall=True)
        conn.commit()
    return dict(rows)


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


def format_claim_insert(claims: dict, verdicts: dict, techniques: dict) -> list[tuple]:
    """Returns a formatted list of tuples for insertion"""
    formatted_tuple = []
    for claim in claims:
        formatted_tuple.append((
            claim['claim'],
            claim['claim_url'],
            verdicts[claim['verdict']],
            techniques[claim['technique']],
            claim['summary']
        ))
    return formatted_tuple


def format_claim_tags_insert(claim_tags: list[dict]) -> list[tuple]:
    """Returns a formatted list of tuples for insertion"""
    formatted_insert = []
    for item in claim_tags:
        for id in item['tags_id']:
            formatted_insert.append((
                item['claims'], id
            ))
    return formatted_insert


def format_sources_insert(sources: list[dict], outlets) -> list[tuple]:
    """Returns a formatted list of tuples for insertion"""
    formatted_sources = []
    for source in sources:
        formatted_sources.append((
            source['sources'],
            # TODO: Missing source verification -> ask what it is and add it in
            outlets[source['source_name']]
        ))


def format_claim_source_insert(claim_sources: dict) -> list[tuple]:
    """Returns a formatted list of tuples for insertion"""
    formatted_insert = []
    for item in claim_sources:
        formatted_insert.append((
            item['claim_id'],
            item['source_id']
        ))
    return formatted_insert


def handler(event=None, context=None):

    # Set up:
    logging.basicConfig(level=logging.INFO)
    load_dotenv()

    conn = get_db_connection()

    if conn is None:
        raise SystemExit(1)
    logging.info("Successfully connected to the database")

    # Get dictionary mappings:
    tag_map = get_tag_mapping(conn)
    verdict_map = get_verdict_mapping(conn)
    technique_map = get_technique_mapping(conn)
    outlet_map = get_outlet_mapping(conn)
    logging.info("Successfully extracted all the relevant mappings")

    # TODO: Get data from transform:
    data = pd.DataFrame()
    logging.info("Received data from transform")

    # Insert into claim table:
    claims = data[['claim', 'verdict',
                   'technique', 'summary']].drop_duplicates()
    claims = claims.to_dict(orient='records')
    formatted_claims = format_claim_insert(claims)
    claim_map = add_claims_to_database(claims)
    logging.info("Successfully added claims to database")

    data['claim_id'] = data['claim'].map(claim_map)

    # Insert into tags table
    claim_tags = data[['claim_id', 'tags']].drop_duplicates()
    claim_tags["tags_id"] = claim_tags["tags"].apply(
        lambda tags: [tag_map[tag] for tag in tags]
    )
    claim_tags_dict = claim_tags.to_dict(orient='records')
    formatted_claim_tags = format_claim_tags_insert(claim_tags_dict)
    add_claim_tags_to_database(formatted_claim_tags)
    logging.info("Successfully added claim_tags to database")

    # TODO: Missing source verification
    # Insert into source table:
    sources = data[['sources', 'source_name']]
    formatted_sources = format_sources_insert(sources, outlet_map)
    source_map = add_source_to_database(formatted_sources)
    logging.info("Successfully added source to database")

    data['source_id'] = data['sources'].map(source_map)

    # Insert into claim_source table:
    claim_source = data[['claim_id', 'source_id']].to_dict(orient='records')
    formatted_claim_source = format_claim_source_insert(claim_source)
    add_claim_source_to_database(formatted_claim_source)
    logging.info("Successfully added claim_source to database")


if __name__ == "__main__":

    handler()
