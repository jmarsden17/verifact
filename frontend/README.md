# Frontend

The dashboard for the Disinformation Verifier, built with [Streamlit](https://streamlit.io/). Journalists use it to submit claims and to look through claims that have already been checked. It is password protected and reads its data from the PostgreSQL database.

## Views

The sidebar has four pages.

| View | What it shows | Data source |
|---|---|---|
| Claim Verification | A text box for a statement or headline, an optional URL, and a demo button that fills in a paragraph with several claims. Results show a summary (counts of supported, contradicted and missing context claims, an accuracy percentage and a donut chart), then a report for each claim with a verdict badge, reasoning, a confidence gauge and the source evidence. | Mock data at the moment |
| Top Disproven Claims | The 10 most recent claims rated Contradicted or Missing Context, with outlet names and timestamps. | RDS, with sample data if the query fails |
| Verification Logs | A searchable table of past checks with timestamp, claim, verdict, technique, number of sources and tags. Has a keyword box and a verdict filter. | RDS |
| Outlet Analytics | Metric cards (total claims checked, main outlet, top technique, resurfaced myths older than 7 days) and two charts: verdicts by outlet, and new submissions against resurfacing queries by week. | RDS, with sample data if the query fails |

The sidebar footer has an "Engine Status" box. It is static text describing ECS Fargate and RDS.

## Structure

```
frontend/
├── app.py                      entry point: page config, theme, password gate, navigation
├── database_conns/
│   ├── connection.py           psycopg2 connection from environment variables
│   └── fetch_data.py           SQL queries, verify_claim() and the mock fallbacks
├── visual_components/
│   ├── ui.py                   page layouts and reusable UI pieces
│   ├── visuals.py              Plotly charts
│   ├── theme.py                colours and injected CSS
│   └── graphs.py               empty
├── tests/
│   └── test_frontend.py        out of date
├── .streamlit/config.toml      Streamlit theme
├── Dockerfile
└── requirements.txt
```

## Configuration

Settings come from environment variables. For local work, put them in `frontend/.env`. It is loaded automatically and is already in `.gitignore`.

| Variable | Required | Description |
|---|---|---|
| `DB_HOST` | yes | Postgres host |
| `DB_PORT` | no, defaults to 5432 | Postgres port |
| `DB_NAME` | yes | Database name (`disinformation` if you used `database/schema.sql`) |
| `DB_USER` | yes | Database user |
| `DB_PASSWORD` | yes | Database password |
| `DASHBOARD_PASSWORD` | yes | Login password. If it isn't set, `check_password()` in `app.py` uses a default from the code, which is not safe for a deployed instance. |

`connection.py` also accepts the lowercase names (`db_host` and so on).

Example `frontend/.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=disinformation
DB_USER=postgres
DB_PASSWORD=change-me
DASHBOARD_PASSWORD=choose-a-strong-password
```

## Run locally

You need Python 3.12 and a database created from [database/schema.sql](../database/README.md).

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r frontend/requirements.txt
cd frontend
streamlit run app.py
```

Open http://localhost:8501. You can also run `streamlit run frontend/app.py` from the repository root.

With an empty database, the Logs view says no logs match, and the other views show an empty message or sample data.

## Run with Docker

The Dockerfile copies the whole repository into the image, so build it from the repository root:

```bash
docker build -f frontend/Dockerfile -t verifact-dashboard .
docker run -p 8501:8501 --env-file frontend/.env verifact-dashboard
```

The container serves Streamlit on port 8501. In AWS it runs as an ECS Fargate service with a health check on `/_stcore/health`. See [terraform/README.md](../terraform/README.md).

## Data layer

`database_conns/fetch_data.py` is the only file that talks to the database.

| Function | Purpose | If the database call fails |
|---|---|---|
| `fetch_analytics_data()` | One row per claim with verdict, technique, outlets and dates, for the analytics view | Returns sample data |
| `get_filtered_logs(search_query, verdict_filter)` | History table with an optional keyword and verdict filter (parameterised SQL) | Raises the exception, so the page errors |
| `get_top_disproven_claims()` | Latest 10 Contradicted or Missing Context claims | Returns sample data |
| `verify_claim(claim_input, url_input)` | Meant to call the pipeline and return one result per claim | Always returns mock data for now |

Each result in the Claim Verification view is expected to look like this:

```python
{
    "claim": "Drinking warm lemon water daily completely cures type 2 diabetes.",
    "rating": "Contradicted",   # Supported, Contradicted, Missing Context or Unclear
    "reasoning": "Plain English explanation.",
    "sources": [{"name": "Full Fact", "snippet": "..."}],
}
```

## Theme

Colours are in `visual_components/theme.py`: a primary blue (`#6A8EAE`) plus green, red, amber and grey for Supported, Contradicted, Missing Context and Unclear. They are injected as CSS on every page, and `.streamlit/config.toml` sets the matching base theme. Change a colour in `theme.py` and both the badges and the charts follow.

