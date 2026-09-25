# Pipeline

The pipeline takes text submitted by a user and turns it into verified claims stored in the database. It is made of three Dockerised AWS Lambda functions and a few helper modules.

| Component | Folder | What it does |
|---|---|---|
| Extract | `extract_claims/` | Pulls the individual claims out of the input, embeds them, and looks for similar claims already in the database |
| Verify | `verify_claims/` | Searches one fact-checking outlet for each new claim using Firecrawl, and has an LLM compare the article with the claim |
| Transform / Load | `transform_load/` | Combines the verdicts from each outlet, writes an overall summary and confidence score, cleans the data and inserts it into Postgres |

The orchestration is not in this repository. The plan is for a Step Function to call Extract, then run one Verify per outlet in parallel, then call Transform / Load. 

## Order of events

1. The orchestrator calls Extract with the user text.
2. Extract asks the LLM for the claims. For each claim that needs an outside check, it creates an embedding and searches the database for a stored claim with similarity of 0.8 or more.
3. Extract returns the claims with their embeddings. A claim that matched a stored one is flagged `skip_etl` and carries the stored verdict.
4. The orchestrator calls Verify once per outlet, passing the claims and the outlet's name and URL.
5. Verify passes cached claims straight through. For new claims it searches the outlet with Firecrawl and asks the LLM for a verdict.
6. The orchestrator gives all the verdicts to Transform / Load.
7. Transform / Load groups them by claim, writes a summary and confidence score, cleans the data and inserts new claims into Postgres.

A claim that matches an earlier one is not verified again and not inserted again. Its stored verdict is returned and its `access_amount` goes up by one.

## 1. Extract Lambda (`extract_claims/`)

Handler: `handler_extract_claims.handler`

Input:

```json
{ "user_text": "Text, headline or article body to analyse" }
```

What it does:

1. `extract_llm.get_claims_from_user` sends the text to the LLM and parses the reply into the `InputAnalysis` model in `extract_models.py`. That holds a list of claims, 1 to 2 topic tags for the whole text and a one line summary. The prompt asks for single, self-contained claims, drops vague statements like "X rallied supporters", and treats quotes and promises as not verifiable.
2. Each claim has:
   - `text`: the claim as one checkable sentence
   - `claim_type`: `event`, `statistic`, `promise`, `opinion` or `other`
   - `verification_method`: `external_search` (needs outside sources), `context_only` (can be answered from the article itself) or `not_verifiable` (opinion, promise or too vague)
   - `entities`: people, organisations and places named in the claim
   - `tags`: 1 to 2 topic tags from the fixed list
3. Only claims marked `external_search` continue. Each gets an embedding (`text-embedding-3-small`, 1536 dimensions) from `generate_embeddings`, then `db_connection.find_most_similar_claim` runs a pgvector cosine similarity query. The best match with similarity of 0.8 or more counts as a duplicate. The query also updates that row's `access_datetime` and `access_amount`.

Output:

```json
{
  "statusCode": 200,
  "body": [
    {
      "text": "Unemployment fell to 3.1% last year.",
      "claim_type": "statistic",
      "verification_method": "external_search",
      "entities": ["Millbrook"],
      "tags": ["Economy Finance"],
      "embedding": [0.0123, "... 1536 floats ..."],
      "similar_claim": null,
      "similarity": null,
      "verdict": null,
      "summary": null,
      "technique": null,
      "skip_etl": false
    }
  ]
}
```

If a duplicate is found, `similar_claim`, `similarity`, `verdict`, `summary` and `technique` are filled in and `skip_etl` is `true`.

Environment: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`. It runs inside the VPC so it can reach RDS.

Files: `handler_extract_claims.py` (handler and embeddings), `extract_llm.py` (LLM call), `extract_models.py` (Pydantic models and tag lists), `db_connection.py` (connection and similarity query).

## 2. Verify Lambda (`verify_claims/`)

Handler: `handler_verify_claim.handler`

One run checks one outlet. Run it once per outlet with a different `source_url` and `source_name`.

Input:

```json
{
  "body": [ "the body list returned by the Extract Lambda" ],
  "source_url": "https://www.bbc.co.uk/news/bbcverify",
  "source_name": "BBC Verify"
}
```

`source_name` is one of Reuters Fact Check, BBC Verify, Full Fact or Wikipedia API, which are the values in the `outlet` table. Only the domain of `source_url` is used, to limit the search to that site. The URL above is only an example. The real URLs are supplied by the parallel step function flow.

What it does for each claim:

- If `skip_etl` is true, the cached verdict is passed straight through.
- Otherwise `firecrawl_client.extract` runs a Firecrawl search for `"<claim>" site:<domain>`. It takes the top 1 result as markdown with a 30 second timeout.
  - If nothing is found, the verdict is `Unclear / Not enough evidence` with the reasoning "No matching article found on this source."
  - If an article is found, `verify_llm.compare_claims_with_article` asks the LLM to compare it with the claim and return a `VerdictResult` (defined in `verify_models.py`).
- If anything fails for a claim, the error is caught and the claim gets an `Unclear / Not enough evidence` verdict with the error in `reasoning`, so one failure doesn't fail the whole batch.

Output, one entry per claim:

```json
{
  "statusCode": 200,
  "body": [
    {
      "claim": "Unemployment fell to 3.1% last year.",
      "verdict": "Contradicted",
      "reasoning": "Official statistics show 4.2%, not 3.1%.",
      "misinformation_type": "Statistical Distortion",
      "entities": ["Millbrook", "Millbrook Labor Office"],
      "tags": ["Economy Finance"],
      "sources": ["https://example.org/fact-check/..."],
      "source_name": "BBC Verify",
      "claim_embedding": [0.0123, "..."]
    }
  ]
}
```

`verdict` is one of Supported, Contradicted, Mixed / Missing Context or Unclear / Not enough evidence. For cached claims the entry has `claim`, `similar_claim`, `similarity`, `verdict`, `summary` and `technique` instead.

Environment: `OPENAI_API_KEY`, `OPENAI_BASE_URL` and the Firecrawl key. The code reads the Firecrawl key from `API_KEY` (in `firecrawl_client.py`), but Terraform sets `FIRECRAWL_API_KEY`. One of them needs to change.

Files: `handler_verify_claim.py`, `firecrawl_client.py`, `verify_llm.py`, `verify_models.py`.

## 3. Transform / Load Lambda (`transform_load/`)

Handler: `handler_final.handler`

Input: an event like `{"statusCode": 200, "body": [ ...verdicts from the Verify Lambda... ]}`. `handler_final` treats the incoming event as a single branch, so the verdicts from all outlets need to be merged into one `body` list first, or `handler_final` needs changing to accept a list of branch outputs.

Steps:

1. Collate (`collate_results.py`): `aggregate_verdicts` regroups the verdicts by claim text, so each claim has one entry per outlet.
2. Summarise (`summary.py`, `summary_models.py`): for each claim the LLM returns a `SummaryResult` with:
   - `summary`: a short, neutral explanation that points out where outlets agree or disagree
   - `confidence_score`: 0 to 1, how much the outlets agree. `Unclear / Not enough evidence` lowers it less than a direct contradiction does, and only full agreement should go over 0.9
   - `misinformation_type`: one technique tag, or `None`
   - `entities`, `tags` (1 to 2 topic tags) and `sources`
3. Transform (`transform.py`): builds a DataFrame and cleans each column. It trims text, converts numbers, removes duplicate tags and sorts them, keeps only allowed topic, technique, verdict and outlet values (matched ignoring case and put back into the standard casing), renames `reasoning` to `source_reasoning`, and adds any missing columns with defaults.
4. Load (`load.py`): rows where `skip_etl` is false are inserted into `claim` (with embedding and confidence score), then `claim_tags`, `source` and `claim_source`. Names are turned into IDs using the lookup tables. Inserts use `ON CONFLICT DO NOTHING` where there is a unique constraint.

Output: `{"statusCode": 200, "body": [ ...all records, including cached ones... ]}`.

Environment: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and the database settings, which this Lambda reads as `DATABASE_NAME`, `DATABASE_IP`, `DATABASE_USERNAME`, `DATABASE_PASSWORD` and `DATABASE_PORT`. These are different from the names the Extract Lambda uses. It also needs network access to RDS, and the Terraform for this Lambda doesn't set that up yet.

## Tags

There are 49 topic tags, 16 techniques, 4 verdicts and 4 outlets, all as fixed lists. They are used in three places: as `Literal` types in the Pydantic models (so the LLM can only return allowed values), in `transform.py` (for validation), and as seed data in `database/schema.sql`. The lists are copied into `extract_models.py`, `summary_models.py`, `verify_models.py` and `transform.py`, so change them together, or better, move them into one shared module.

## Prompt injection

Scraped web pages can't be trusted. The code keeps the instructions in the system message and passes article text as data in the user message. It also forces structured output using Pydantic models with fixed allowed values. This lowers the risk of hidden instructions in a scraped page affecting the result, but it doesn't remove it. Keep that in mind if you change the prompts.

## Running locally

Run a Lambda from inside its own folder so the imports work:

```bash
cd pipeline/extract_claims
pip install -r requirements.txt
# create a .env in this folder with the variables listed above (OPENAI_*, DB_*)
python -c "from handler_extract_claims import handler; import json; print(json.dumps(handler({'user_text': 'Your text here'}, None), default=str)[:2000])"
```

You need a reachable Postgres database with the schema loaded, plus valid LLM and Firecrawl credentials.

## Build and deploy

Each Lambda folder has a Dockerfile based on `public.ecr.aws/lambda/python:3.12`. Build from inside that folder.

```bash
cd pipeline/extract_claims
docker build --platform linux/amd64 -t <ecr-repo-url>:latest .
docker push <ecr-repo-url>:latest
```

Then set the Lambda's `image_uri` in Terraform. See [terraform/README.md](../terraform/README.md).

## Tests

```bash
pip install -r requirements.txt
cd pipeline
pytest
pytest --cov
```
