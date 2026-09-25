# Database

This folder has the PostgreSQL schema for the Disinformation Verifier. `schema.sql` creates the database and tables and adds the seed data (topic tags, outlets, verdicts and techniques).

The RDS database is the main data store in the project:

- The pipeline writes checked claims, their sources and their embeddings to it.
- The extract Lambda searches it for similar claims that were already checked.
- The dashboard reads it for history, disproven claims, analytics, etc. 

## Requirements

- PostgreSQL 15 or later. The RDS instance in Terraform runs Postgres 17.
- The [pgvector](https://github.com/pgvector/pgvector) extension. It is available on Amazon RDS for PostgreSQL. Locally you may need to install it (for example `brew install pgvector`) or use the `pgvector/pgvector` Docker image.
- The `psql` client. The script uses the `\c` meta-command, so it has to be run with `psql`.

## Setup


Local set up:

```bash
psql postgres -f schema.sql
```

AWS RDS set up:

```bash
psql -h <db_hostname> -p <db_port> -U <db_username> postgres -f schema.sql
```

The script connects to the default `postgres` database, creates `disinformation`, switches to it, creates the tables and inserts the seed data.

The seed inserts use `ON CONFLICT ... DO NOTHING`, so those parts can be run again safely.

## Data model


There are eight tables. `claim` is the main table that we will be frequently querying from. `verdict`, `technique`, `tags` and `outlet` are lookup tables. `claim_tags` and `claim_source` link claims to their tags and sources, and each `source` belongs to an `outlet`.


### Tables

| Table | Columns | Purpose |
|---|---|---|
| `claim` | `claim_id`, `claim`, `publish_datetime`, `access_datetime`, `verdict_id`, `technique_id`, `summary`, `claim_embedding`, `confidence_score`, `access_amount` | One row per checked claim. This is the main table. |
| `verdict` | `verdict_id`, `verdict` | Lookup table: Supported, Contradicted, Mixed / Missing Context, Unclear / Not enough evidence. |
| `technique` | `technique_id`, `technique` | Lookup table of 16 disinformation techniques, for example Deepfake, Cherry Picking, Outdated Content and None. |
| `tags` | `tag_id`, `tags` | Lookup table of 49 topic tags, for example Politics UK, Healthcare, Climate Change and Other. |
| `claim_tags` | `claim_tag_id`, `claim_id`, `tag_id` | Links claims to topic tags (many to many). |
| `outlet` | `outlet_id`, `outlet` | Lookup table of the four outlets: Reuters Fact Check, BBC Verify, Full Fact, Wikipedia API. |
| `source` | `source_id`, `source_url`, `source_reasoning`, `outlet_id` | An article or URL used as evidence, with the LLM's reasoning for that source and the outlet it came from. |
| `claim_source` | `claim_source_id`, `claim_id`, `source_id` | Links claims to their sources (many to many). This is the evidence trail. |
