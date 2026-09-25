"""Tests for connection.py."""

from database_conns.connection import get_db_connection


def test_get_db_connection_uses_uppercase_env_vars(mocker):
    mocker.patch.dict("os.environ", {
        "DB_HOST": "myhost", "DB_PORT": "5433", "DB_NAME": "mydb",
        "DB_USER": "myuser", "DB_PASSWORD": "mypass",
    }, clear=True)
    mock_connect = mocker.patch("database_conns.connection.psycopg2.connect")

    get_db_connection()

    mock_connect.assert_called_once_with(
        host="myhost", port="5433", dbname="mydb",
        user="myuser", password="mypass")


def test_get_db_connection_falls_back_to_lowercase_env_vars(mocker):
    mocker.patch.dict("os.environ", {
        "db_host": "myhost", "db_name": "mydb",
        "db_user": "myuser", "db_password": "mypass",
    }, clear=True)
    mock_connect = mocker.patch("database_conns.connection.psycopg2.connect")

    get_db_connection()

    mock_connect.assert_called_once_with(
        host="myhost", port="5432", dbname="mydb",
        user="myuser", password="mypass")


def test_get_db_connection_defaults_port_to_5432(mocker):
    mocker.patch.dict("os.environ", {"DB_HOST": "h", "DB_NAME": "d",
                                     "DB_USER": "u", "DB_PASSWORD": "p"}, clear=True)
    mock_connect = mocker.patch("database_conns.connection.psycopg2.connect")

    get_db_connection()

    assert mock_connect.call_args.kwargs["port"] == "5432"