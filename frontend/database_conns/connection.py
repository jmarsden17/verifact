"""Data logic and backend handlers."""

import os
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Force loading .env file explicitly from the frontend folder
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_db_connection():
    """Establish connection to PostgreSQL RDS using environment variables."""
    host = os.getenv("DB_HOST") or os.getenv("db_host")
    port = os.getenv("DB_PORT") or os.getenv("db_port") or "5432"
    dbname = os.getenv("DB_NAME") or os.getenv("db_name")
    user = os.getenv("DB_USER") or os.getenv("db_user")
    password = os.getenv("DB_PASSWORD") or os.getenv("db_password")

    # Debug print statement
    print(f"Connecting to DB: host={host}, dbname={dbname}, user={user}")

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
