"""Handler to collate verification results from parallel Lambdas."""


def handler(event, context):
    """Handler to collate verification results from parallel Lambdas."""

    results = event["body"]

    collated_results = []
    for claim in results:
        collated_results.append(claim)

    return {
        "statusCode": 200,
        "body": collated_results
    }
