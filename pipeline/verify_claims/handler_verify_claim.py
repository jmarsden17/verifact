"""Handler to verify a claim against an article from a specified fact check site."""

import logging
import json
from dotenv import load_dotenv
import boto3
from verify_llm import compare_claims_with_article
from firecrawl_client import extract


def handler(event=None, context=None):
    """Handler to verify a claim against an article from a specified fact check site."""
    logging.basicConfig(level=logging.INFO)
    load_dotenv()

    source_url = event.get("source_url", "")
    source_name = event.get("source_name", "")

    s3_client = boto3.client('s3')
    bucket_name = event['s3_reference']['bucket']
    extract_key = event['s3_reference']['key']
    unique_folder = event['s3_reference']['folder_name']

    response = s3_client.get_object(Bucket=bucket_name, Key=extract_key)

    content_bytes = response['Body'].read()
    content_string = content_bytes.decode('utf-8')

    new_event = json.loads(content_string)

    logging.info('Successfully loaded values from S3 Bucket')

    claims_data = new_event["body"]["to_process"]
    source_url = new_event.get("source_url", "")
    source_name = new_event.get("source_name", "")

    results = []

    logging.info(
        "Starting verification of claims against the specified fact check site.")
    for claim_item in claims_data:
        if claim_item.get("skip_etl") is True:
            verdict = {
                "claim": claim_item.get("text"),
                "similar_claim": claim_item.get("similar_claim"),
                "similarity": claim_item.get("similarity"),
                "verdict": claim_item.get("verdict"),
                "summary": claim_item.get("summary"),
                "technique": claim_item.get("technique")
            }
            results.append(verdict)
            continue

        try:
            claim = claim_item.get("text")
            extracted_article, urls = extract(claim, source_url)
            if not extracted_article.strip():
                verdict = {
                    "claim": claim,
                    "verdict": "Unclear / Not enough evidence",
                    "reasoning": "No matching article found on this source.",
                    "misinformation_type": "None",
                    "entities": [],
                    "tags": [],
                    "sources": [],
                    "source_name": source_name,
                    "claim_embedding": claim_item.get('embedding')
                }
            else:
                verdict = compare_claims_with_article(claim, extracted_article)
                verdict["sources"] = urls
                verdict["claim"] = claim
                verdict["source_name"] = source_name
                verdict['claim_embedding'] = claim_item.get('embedding')

            results.append(verdict)
        except Exception as e:
            verdict = {
                "claim": claim,
                "verdict": "Unclear / Not enough evidence",
                "reasoning": f"Error processing claim: {e}",
                "misinformation_type": "None",
                "entities": [],
                "tags": [],
                "sources": [],
                "source_name": source_name,
                "claim_embeddding": claim_item.get('embedding')
            }
            results.append(verdict)

    return_values = json.dumps({
        "statusCode": 200,
        "body": results
    })

    # Read from S3 Bucket
    bucket_name = 'c25-disinformation-lambda'
    extract_key = 'verify_claim.json'

    response = s3_client.get_object(Bucket=bucket_name, Key=extract_key)

    verify_content_bytes = response['Body'].read()
    verify_content_bytes = verify_content_bytes.decode('utf-8')

    new_event = json.loads(verify_content_bytes)
    new_event.append(json.loads(return_values))

    # Upload to S3
    s3_client = boto3.client('s3')
    key = f'{unique_folder}/verify_claim.json'
    s3_client.put_object(
        Bucket='c25-disinformation-lambda',
        Key=key,
        Body=json.dumps(new_event),
        ContentType='application/json'
    )

    logging.info('Successfully loaded values into S3 Bucket')

    return {
        "statusCode": 200,
        "s3_reference": {
            "bucket": "c25-disinformation-lambda",
            "key": key,
            "folder_name": unique_folder
        }
    }
