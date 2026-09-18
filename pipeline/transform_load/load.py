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

from transform import transform
from handler_collate_results import combine_main


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


def format_claim_insert(claims: dict, verdicts: dict, techniques: dict) -> list[tuple]:
    """Returns a formatted list of tuples for insertion"""
    formatted_tuple = []
    for claim in claims:
        formatted_tuple.append((
            claim['claim'],
            claim['claim_url'],
            verdicts[claim['verdict']],
            techniques[claim['technique']],
            claim['summary'],
            claim['claim_embedding'],
            claim['confidence_score']
        ))
    return formatted_tuple


def format_claim_tags_insert(claim_tags: list[dict]) -> list[tuple]:
    """Returns a formatted list of tuples for insertion"""
    formatted_insert = []
    for item in claim_tags:
        for tag_id in item['tags_id']:
            formatted_insert.append((
                int(item['claim_id']),
                int(tag_id)
            ))
    return formatted_insert


def format_sources_insert(sources: list[dict], outlets) -> list[tuple]:
    """Returns a formatted list of tuples for insertion"""
    formatted_sources = []
    for source in sources:
        formatted_sources.append((
            source['sources'],
            source['source_reasoning'],
            outlets[source['source_name']]
        ))
    return formatted_sources


def format_claim_source_insert(claim_sources: dict) -> list[tuple]:
    """Returns a formatted list of tuples for insertion"""
    formatted_insert = []
    for item in claim_sources:
        formatted_insert.append((
            int(item['claim_id']),
            int(item['source_id'])
        ))
    return formatted_insert


def main_claim_insertion_function(conn: connection, data: pd.DataFrame) -> dict:
    """Inserts claim data and returns a dictionary with the claim and claim_id mapping"""
    verdict_map = get_verdict_mapping(conn)
    logging.info("Successfully retrieved verdict mapping")
    technique_map = get_technique_mapping(conn)
    logging.info("Successfully retrieved technique mapping")

    claims = data[['claim', 'verdict', 'technique', 'summary',
                   'claim_url', 'claim_embedding', 'confidence_score']].drop_duplicates(subset='claim')
    claims = claims.to_dict(orient='records')

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
    claim_tags_dict = claim_tags.to_dict(orient='records')

    formatted_claim_tags = format_claim_tags_insert(claim_tags_dict)
    add_claim_tags_to_database(conn, formatted_claim_tags)


def main_source_insertion_function(conn: connection, data: pd.DataFrame) -> dict:
    """Inserts source data and returns the dictionary mapping the source to its id"""
    outlet_map = get_outlet_mapping(conn)
    logging.info("Successfully retrieved outlet mapping")

    sources = data[['sources', 'source_name',
                    'source_reasoning']].to_dict(orient='records')

    formatted_sources = format_sources_insert(sources, outlet_map)
    return add_source_to_database(conn, formatted_sources)


def main_claim_source_insertion_function(conn: connection, data: pd.DataFrame) -> None:
    """Inserts the source and claim pairing into the database"""
    claim_source = data[['claim_id', 'source_id']].to_dict(orient='records')
    formatted_claim_source = format_claim_source_insert(claim_source)
    add_claim_source_to_database(conn, formatted_claim_source)


def handler(event=None, context=None) -> dict:
    """Main handler function for Lambda"""

    # Set up:
    logging.basicConfig(level=logging.INFO)
    load_dotenv()

    conn = get_db_connection()

    if conn is None:
        raise SystemExit(1)
    logging.info("Successfully connected to the database")

    # TODO: Get data from extract:
    combined = combine_main(event['body'])
    verdict_list = []
    for key in combined:
        verdicts = combined[key]['verdicts']
        for verdict in verdicts:
            verdict['claim'] = key
            verdict['summary'] = combined[key]['summary']['summary']
            verdict['confidence_score'] = combined[key]['summary']['confidence_score']
        verdict_list.append(verdicts)
        verdict_list.append(combined[key]['summary'])
    logging.info("Received data to transform")

    # Transform raw data to DataFrame
    df = transform(verdict_list)
    logging.info("Transformed data")

    # Extract records and flatten the DataFrame
    records = df.to_dict(orient='records')
    flattened_data = [
        val
        for row in records
        for key, val in row.items()
        if isinstance(val, dict) and val.get("claim")
    ]
    flattened_data = transform(flattened_data)

    # Convert flattened list back to a clean DataFrame for SQL operations
    data = pd.DataFrame(flattened_data)

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

    return {
        "statusCode": 200,
        "body": data.to_dict(orient='records')
    }


if __name__ == "__main__":

    parallel_output = [
        # Branch 1: Reuters
        {
            "statusCode": 200,
            "body": [
                {
                    "claim": "The unemployment rate fell to 3.8% in August, the lowest in six months.",
                    "verdict": "Supported",
                    "reasoning": "Reuters' labour market report confirms the 3.8% figure, matching the official BLS release for August.",
                    "misinformation_type": "None",
                    "entities": ["Bureau of Labor Statistics"],
                    "tags": ["Economy Finance"],
                    "sources": ["reuters.com/markets/us-unemployment-august-2026"],
                    "source_name": "Reuters Fact Check",
                    "claim_embedding": [0.12, -0.45, 0.89],
                    "claim_url": "www.xxx.com",
                    "confidence_score": 0.8
                },
                {
                    "claim": "The new trade agreement will eliminate all tariffs between the two countries by 2027.",
                    "verdict": "Mixed / Missing Context",
                    "reasoning": "The agreement phases out most tariffs by 2027 but explicitly excludes steel and agricultural products, which the claim omits.",
                    "misinformation_type": "Misleading Context",
                    "entities": ["Ministry of Trade"],
                    "tags": ["Trade Tariffs"],
                    "sources": ["reuters.com/business/trade-deal-tariffs-2026"],
                    "source_name": "Reuters Fact Check",
                    "claim_embedding": [0.12, -0.45, 0.89],
                    "claim_url": "www.xxx.com",
                    "confidence_score": 0.8
                },
            ],
        },
        # Branch 2: AP
        {
            "statusCode": 200,
            "body": [
                {
                    "claim": "The unemployment rate fell to 3.8% in August, the lowest in six months.",
                    "verdict": "Supported",
                    "reasoning": "AP's coverage of the jobs report independently corroborates the 3.8% figure and the six-month low framing.",
                    "misinformation_type": "None",
                    "entities": ["Bureau of Labor Statistics"],
                    "tags": ["Economy Finance"],
                    "sources": ["apnews.com/article/jobs-report-august-2026"],
                    "source_name": "Reuters Fact Check",
                    "claim_embedding": [0.12, -0.45, 0.89],
                    "claim_url": "www.xxx.com",
                    "confidence_score": 0.8
                },
                {
                    "claim": "The new trade agreement will eliminate all tariffs between the two countries by 2027.",
                    "verdict": "Contradicted",
                    "reasoning": "AP reports the deal retains a 12% tariff on steel imports indefinitely, directly contradicting the 'all tariffs' claim.",
                    "misinformation_type": "Statistical Distortion",
                    "entities": ["Ministry of Trade"],
                    "tags": ["Trade Tariffs"],
                    "sources": ["apnews.com/article/trade-deal-steel-tariffs"],
                    "source_name": "Reuters Fact Check",
                    "claim_embedding": [0.12, -0.45, 0.89],
                    "claim_url": "www.xxx.com",
                    "confidence_score": 0.8
                },
            ],
        },
        # Branch 3: BBC
        {
            "statusCode": 200,
            "body": [
                # {
                #     "claim": "The unemployment rate fell to 3.8% in August, the lowest in six months.",
                #     "verdict": "Unclear / Not enough evidence",
                #     "reasoning": "No matching article found on this source.",
                #     "misinformation_type": "None",
                #     "entities": [],
                #     "tags": [],
                #     "sources": [],
                #     "source_name": "Reuters Fact Check",
                #     "claim_embedding": [0.12, -0.45, 0.89],
                #     "claim_url": "www.xxx.com",
                #     "confidence_score": 0.8
                # },
                {
                    "claim": "The new trade agreement will eliminate all tariffs between the two countries by 2027.",
                    "verdict": "Contradicted",
                    "reasoning": "BBC's analysis piece states agricultural tariffs remain untouched under the deal, contradicting the blanket elimination claim.",
                    "misinformation_type": "Misleading Context",
                    "entities": ["Ministry of Trade"],
                    "tags": ["Trade Tariffs"],
                    "sources": ["bbc.co.uk/news/business-trade-deal-analysis"],
                    "source_name": "Reuters Fact Check",
                    "claim_embedding": [0.12, -0.45, 0.89],
                    "claim_url": "www.xxx.com",
                    "confidence_score": 0.8
                },
            ],
        },
    ]

    input = {
        'status': 200,
        'body': parallel_output
    }

    handler(event=input, context=None)
