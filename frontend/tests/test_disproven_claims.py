"""Tests for disproven_claims.py."""

import pandas as pd
import pytest

from database_conns.disproven_claims import get_disproven_claims


def test_get_disproven_claims_success(mocker):
    mock_conn = mocker.MagicMock()
    mocker.patch("database_conns.disproven_claims.get_db_connection",
                return_value=mock_conn)
    expected = pd.DataFrame([{"claim_id": 1}])
    mocker.patch("database_conns.disproven_claims.pd.read_sql",
                return_value=expected)

    result = get_disproven_claims()

    assert result is expected
    mock_conn.close.assert_called_once()


def test_get_disproven_claims_with_verdict_filter_adds_param(mocker):
    mock_conn = mocker.MagicMock()
    mocker.patch("database_conns.disproven_claims.get_db_connection",
                return_value=mock_conn)
    mock_read_sql = mocker.patch(
        "database_conns.disproven_claims.pd.read_sql", return_value=pd.DataFrame())

    get_disproven_claims(verdict="Contradicted", limit=5)

    params = mock_read_sql.call_args.kwargs["params"]
    assert params == ("Contradicted", 5)


def test_get_disproven_claims_most_checked_sort(mocker):
    mock_conn = mocker.MagicMock()
    mocker.patch("database_conns.disproven_claims.get_db_connection",
                return_value=mock_conn)
    mock_read_sql = mocker.patch(
        "database_conns.disproven_claims.pd.read_sql", return_value=pd.DataFrame())

    get_disproven_claims(sort="most_checked")

    query = mock_read_sql.call_args.args[0]
    assert "access_amount DESC" in query


def test_get_disproven_claims_falls_back_to_sample_data_on_db_error(mocker):
    mocker.patch("database_conns.disproven_claims.get_db_connection",
                side_effect=Exception("connection refused"))

    result = get_disproven_claims()

    assert result.attrs.get("is_sample") is True
    assert len(result) > 0


def test_sample_claims_filters_by_verdict(mocker):
    mocker.patch("database_conns.disproven_claims.get_db_connection",
                side_effect=Exception("db down"))

    result = get_disproven_claims(verdict="Contradicted", limit=10)

    assert (result["verdict"] == "Contradicted").all()


def test_sample_claims_respects_limit(mocker):
    mocker.patch("database_conns.disproven_claims.get_db_connection",
                side_effect=Exception("db down"))

    result = get_disproven_claims(limit=1)

    assert len(result) == 1


def test_sample_claims_most_checked_sort_orders_by_access_amount(mocker):
    mocker.patch("database_conns.disproven_claims.get_db_connection",
                side_effect=Exception("db down"))

    result = get_disproven_claims(sort="most_checked", limit=3)

    assert list(result["access_amount"]) == sorted(
        result["access_amount"], reverse=True)