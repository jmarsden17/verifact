"""
The load aspect of the ETL pipeline.
Uploads data into the DynamoDB table
"""
import os
import logging
from dotenv import load_dotenv
import boto3


def connect_to_dynamodb():
    """Connects to the DynamoDB database"""
    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=os.environ["ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["SECRET_ACCESS_KEY"]
    )
    logging.info("Successfully connected to DynamoDB")
    return dynamodb.Table('c25-disinformation-dynamo')


def dynamodb_put_item(dynamodb, item: dict):
    """Puts an item into the DynamoDB table"""
    dynamodb.put_item(
        TableName='c25-disinformation-dynamo',
        Item={
            "claim": str(item['claim']),
            "claim_link": str(item['claim_link']),
            "tags": ', '.join(item['tags']),
            "entities": item['entities'],
            "timestamp": item['timestamp'].isoformat(),
            "verification": str(item['verification']),
            "confidence": str(item['confidence']),
            "summary": str(item['summary']),
            "all_verifications": item['all_verifications']
        }
    )
    logging.info("Loaded into DynamoDB")


if __name__ == "__main__":

    # Set up file:
    logging.basicConfig(level=logging.INFO)
    load_dotenv()

    # Establish connection to DynamoDB:
    dynamodb = connect_to_dynamodb()

    # TODO: The claim should be extracted from transform.py
    # Put item into DynamoDB:
    dynamodb_put_item(dynamodb, claim)
