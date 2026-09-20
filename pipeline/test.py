from extract_claims import db_connection, extract_llm, extract_models, handler_extract_claims

from verify_claims import handler_verify_claim, firecrawl_client, verify_llm, verify_models

from transform_load import handler_collate_results, load, transform, summary, summary_models

if __name__ == "__main__":
    event = {
        'user_text': 'Harry and Megan are going back to America'
        ''
    }
    event = handler_extract_claims.handler(event, None)
    event['source_name'] = 'Full Fact'
    event['source_url'] = 'https://www.bbc.co.uk/news/articles'

    event = handler_verify_claim.handler(event, None)
    event = load.handler(event, None)
    print(event)
