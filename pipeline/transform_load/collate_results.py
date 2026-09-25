"""Handler to collate verification results from parallel Lambdas."""
from summary import generate_summary


def combine_main(event):
    """Handler to collate verification results from parallel Lambdas."""

    # Returns dict where keys are claim texts
    # and values are lists of verdicts from different sources.
    results = aggregate_verdicts(event)["body"]

    # Returns dict where keys are claim texts and values are the corresponding summaries.
    summaries = generate_summary(results)

    combined = {}
    # Outputs a dict in the form: {
    #     claim: {
    #         "individual_verdicts": [{},{},{}],
    #         "summary": {}
    #     },
    #     claim2: {
    #         "individual_verdicts": [...],
    #         "summary": ...
    #     }
    # }
    for claim_text, verdicts in results.items():
        combined[claim_text] = {
            "verdicts": verdicts,
            "summary": summaries.get(claim_text),
        }

    return combined


def aggregate_verdicts(claims) -> dict:
    """Pivot per-source verdict lists into a claim-keyed structure."""
    grouped = {}

    for branch_output in claims:
        for verdict in branch_output["body"]:
            claim_text = verdict["claim"]
            grouped.setdefault(claim_text, []).append(verdict)

    return {
        "statusCode": 200,
        "body": grouped
    }
