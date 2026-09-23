"""
Main handler file for the lambda function
"""
import logging
import json
import boto3
import pandas as pd
from transform import transform
from collate_results import combine_main
from load import load


def handler(event=None, context=None) -> dict:
    """Main handler function for Lambda"""
    logging.basicConfig(level=logging.INFO)

    logging.info(event)

    s3_client = boto3.client('s3')
    bucket_name = event['results'][0]['s3_reference']['bucket']
    extract_key = event['results'][0]['s3_reference']['key']

    response = s3_client.get_object(Bucket=bucket_name, Key=extract_key)

    content_bytes = response['Body'].read()
    content_string = content_bytes.decode('utf-8')

    results = json.loads(content_string)

    logging.info('Successfully loaded values from S3 Bucket')

    # Get data from extract:
    combined = combine_main(results)
    verdict_list = []
    for key in combined:
        verdicts = combined[key]['verdicts']
        for verdict in verdicts:
            verdict['claim'] = key
            verdict['summary'] = combined[key]['summary']['summary']
            verdict['confidence_score'] = combined[key]['summary']['confidence_score']
            verdict['verdict'] = combined[key]['summary']['overall_verdict']
            verdict['misinformation_type'] = combined[key]['summary']['misinformation_type']

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

    # Loads the data into the RDS
    if not data.empty:
        load(data)

    output_records = []

    output_records = data.to_dict(orient='records')

    # Getting the skipped data

    response = s3_client.get_object(
        Bucket='c25-disinformation-lambda',
        Key='extract_claims.json'
    )

    content_bytes = response['Body'].read()
    content_string = content_bytes.decode('utf-8')

    results = json.loads(content_string)

    skipped = results['body']['skipped']

    for row in skipped:
        output_records.append({
            "claim": row["text"],
            "verdict": row["verdict"],
            "similarity": float(row["similarity"]),
            "summary": row["summary"],
            "technique": row["technique"],
            "skip_etl": True,
        })

    for entry in output_records:
        entry.pop('claim_embedding', None)

    return {
        "statusCode": 200,
        "body": output_records
    }
