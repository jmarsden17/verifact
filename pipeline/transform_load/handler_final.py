"""
Main handler file for the lambda function
"""
import pandas as pd
import logging
from transform import transform
from collate_results import combine_main
from load import load


def handler(event=None, context=None) -> dict:
    """Main handler function for Lambda"""
    logging.basicConfig(level=logging.INFO)

    results = event.get("results", [])
    skipped = event.get("skipped", [])

    # Get data from extract:

    combined = combine_main(results)
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

    # Filters out data that should not be loaded into the RDS based on the 'skip_etl' flag
    logging.info("Filtering out data with 'skip_etl' set to True")

    # Loads the data into the RDS
    if not data.empty:
        load(data)

    output_records = []

    output_records = data.to_dict(orient='records')

    for row in skipped:
        output_records.append({
            "claim": row["text"],
            "verdict": row["verdict"],
            "similarity": float(row["similarity"]),
            "summary": row["summary"],
            "technique": row["technique"],
            "skip_etl": True,
        })

    return {
        "statusCode": 200,
        "body": output_records
    }
