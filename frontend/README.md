# Frontend

The dashboard for the Disinformation Verifier, built with [Streamlit](https://streamlit.io/). Journalists use it to submit claims for verification, access a breaking recent disproven claims page, see our database and use our advanced outlet and claim analytics pages. It is password protected and reads its data from the PostgreSQL database via relevant queries.

## Views

The sidebar has five pages.

| View | What it shows | Data source |
|---|---|---|
| Claim Verification | A text box for a statement or headline, an optional URL, and a demo button that fills in a paragraph with several claims. Results show a summary (counts of supported, contradicted and missing context claims, an accuracy percentage and a donut chart), then a report for each claim with a verdict badge, reasoning, a confidence gauge and the source evidence. | RDS database, appropriate error messages if input is too vague |
| Top Disproven Claims | The most recent claims rated Contradicted or Missing Context, with outlet names and timestamps. | RDS, with sample data if the query fails |
| Verification Logs | A searchable table of past checks with timestamp, claim, verdict, technique, number of sources and tags. Has a keyword box and a verdict filter. | Direct from RDS |
| Outlet Analytics | Outlet and minimum claim filters, quick breakdown of top outlets by verdict and by volume, advanced statistical analytics and a publisher rundown table. | RDS, with sample data if the query fails |
| Claim Analytics | Keyword, verdict, tactic, minimum outlets and latency filters, key claim metrics, quick breakdown charts of verdict distribution and top deception tactics and advanced statistical analytics. | RDS, with sample data if the query fails |


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
| `STATE_MACHINE_ARN` | yes | The state machine that links the step function to the frontend, enables the verification service to run. |

`connection.py` also accepts the lowercase names (`db_host` and so on).

Example `frontend/.env`:

```env
DB_HOST={Your RDS endpoint}
DB_PORT="5432"
DB_NAME={Your database name}
DB_USER={Your database user}
DB_PASSWORD={Your database password}
DASHBOARD_PASSWORD={Set your dashboard password here}
STATE_MACHINE_ARN="arn:aws:states..."
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

## Run with Docker

The Dockerfile copies the whole repository into the image, so build it from the repository root:

```bash
docker build -f frontend/Dockerfile -t verifact-dashboard .
docker run -p 8501:8501 --env-file frontend/.env verifact-dashboard
```

The container serves Streamlit on port 8501. In AWS it runs as an ECS Fargate service with a health check on `/_stcore/health`. See [terraform/README.md](../terraform/README.md).


## Theme

Colours are in `visual_components/theme.py` and `.streamlit/config.toml`, to customise your branding you can edit these using hex codes.

