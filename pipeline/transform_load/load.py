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
                verdict_id, 
                technique_id, 
                summary, 
                claim_embedding,
                confidence_score
            )
            VALUES %s
            ON CONFLICT (claim, publish_datetime, access_datetime)
            DO NOTHING
            RETURNING claim, claim_id;
        """

        execute_values(cursor, query, data)
        rows = cursor.fetchall()
        conn.commit()
    return {row["claim"]: row["claim_id"] for row in rows}


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
                (source_url, source_reasoning, outlet_id)
            VALUES %s
            RETURNING source_url, source_id;;
        """

        execute_values(cursor, query, data)
        rows = cursor.fetchall()
        conn.commit()
    return {row["source_url"]: row["source_id"] for row in rows}


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


def format_claim_insert(claims: list[dict], verdicts: dict, techniques: dict) -> list[tuple]:
    """Returns a formatted list of tuples for insertion"""
    formatted_tuple = []
    for claim in claims:
        verdict = claim['verdict']
        technique = claim['technique']
        if verdict in verdicts and technique in techniques:
            formatted_tuple.append((
                claim['claim'],
                verdicts[verdict],
                techniques[technique],
                claim['summary'],
                claim['claim_embedding'],
                claim['confidence_score']
            ))
        else:
            logging.warning("Skipping claim value: %s", claim)
    return formatted_tuple


def format_claim_tags_insert(claim_tags: list[dict]) -> list[tuple]:
    """Returns a formatted list of tuples for insertion"""
    formatted_insert = []
    for item in claim_tags:
        for tag_id in item['tags_id']:
            try:
                formatted_insert.append((
                    int(item['claim_id']),
                    int(tag_id)
                ))
            except (TypeError, ValueError) as e:
                logging.warning(
                    "Skipping claim source value:\nclaim_id=%r, tag_id=%r\nError: %r",
                    item['claim_id'],
                    tag_id,
                    e
                )
    return formatted_insert


def format_sources_insert(sources: list[dict], outlets) -> list[tuple]:
    """Returns a formatted list of tuples for insertion"""
    formatted_sources = []
    for source in sources:
        outlet_name = source['source_name']
        if outlet_name in outlets:
            formatted_sources.append((
                source['sources'],
                source['source_reasoning'],
                outlets[outlet_name]
            ))
    return formatted_sources


def format_claim_source_insert(claim_sources: list[dict]) -> list[tuple]:
    """Returns a formatted list of tuples for insertion"""
    formatted_insert = []
    for item in claim_sources:
        try:
            formatted_insert.append((
                int(item['claim_id']),
                int(item['source_id'])
            ))
        except (TypeError, ValueError) as e:
            logging.warning(
                "Skipping claim source value:\nclaim_id=%r, source_id=%r\nError: %r",
                item['claim_id'],
                item['source_id'],
                e
            )
    return formatted_insert


def main_claim_insertion_function(conn: connection, data: pd.DataFrame) -> dict:
    """Inserts claim data and returns a dictionary with the claim and claim_id mapping"""
    verdict_map = get_verdict_mapping(conn)
    logging.info("Successfully retrieved verdict mapping")
    technique_map = get_technique_mapping(conn)
    logging.info("Successfully retrieved technique mapping")

    claims = data[['claim', 'verdict', 'technique', 'summary',
                   'claim_embedding', 'confidence_score']].drop_duplicates(subset='claim')
    claims = claims.dropna().to_dict(orient='records')

    formatted_claims = format_claim_insert(claims, verdict_map, technique_map)
    return add_claims_to_database(conn, formatted_claims)


def main_claim_tags_insertion_function(conn: connection, data: pd.DataFrame) -> None:
    """Inserts the claim tag pairing int the database"""
    tag_map = get_tag_mapping(conn)
    logging.info("Successfully retrieved tags mapping")

    claim_tags = data[['claim_id', 'tags']].drop_duplicates()
    claim_tags["tags_id"] = claim_tags["tags"].apply(
        lambda tags: [tag_map[tag] for tag in tags]
    )
    claim_tags_dict = claim_tags.dropna().to_dict(orient='records')

    formatted_claim_tags = format_claim_tags_insert(claim_tags_dict)
    add_claim_tags_to_database(conn, formatted_claim_tags)


def main_source_insertion_function(conn: connection, data: pd.DataFrame) -> dict:
    """Inserts source data and returns the dictionary mapping the source to its id"""
    outlet_map = get_outlet_mapping(conn)
    logging.info("Successfully retrieved outlet mapping")

    sources = data[['sources', 'source_name',
                    'source_reasoning']].dropna().to_dict(orient='records')

    formatted_sources = format_sources_insert(sources, outlet_map)
    return add_source_to_database(conn, formatted_sources)


def main_claim_source_insertion_function(conn: connection, data: pd.DataFrame) -> None:
    """Inserts the source and claim pairing into the database"""
    claim_source = data[['claim_id', 'source_id']
                        ].dropna().to_dict(orient='records')

    formatted_claim_source = format_claim_source_insert(claim_source)
    add_claim_source_to_database(conn, formatted_claim_source)


def load(data: pd.DataFrame) -> None:
    """Loads data into the pipeline"""
    # Set up:
    logging.basicConfig(level=logging.INFO)
    load_dotenv()

    conn = get_db_connection()

    if conn is None:
        raise SystemExit(1)
    logging.info("Successfully connected to the database")

    # Insert into claim table:
    claim_map = main_claim_insertion_function(conn, data)
    logging.info("Successfully added claims to database")

    data['claim_id'] = data['claim'].map(claim_map)

    # Insert into claim_tags table
    main_claim_tags_insertion_function(conn, data)
    logging.info("Successfully added claim_tags to database")

    # Insert into source table:
    source_map = main_source_insertion_function(conn, data)
    logging.info("Successfully added source to database")

    data['source_id'] = data['sources'].map(source_map)

    # Insert into claim_source table:
    main_claim_source_insertion_function(conn, data)
    logging.info("Successfully added claim_source to database")
