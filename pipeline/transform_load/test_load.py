# pylint: skip-file

"""
Test for load file
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from psycopg2 import OperationalError

from load import (
    get_db_connection,
    get_tag_mapping,
    get_verdict_mapping,
    get_technique_mapping,
    get_outlet_mapping,
    format_claim_insert,
    format_claim_tags_insert,
    format_sources_insert,
    format_claim_source_insert,
    add_claim_source_to_database,
    add_claim_tags_to_database,
    add_claims_to_database,
    add_source_to_database,
    main_claim_insertion_function,
    main_claim_source_insertion_function,
    main_claim_tags_insertion_function,
    main_source_insertion_function
)


@pytest.fixture
def tag_mapping():
    return {
        'tag 1': 1,
        'tag 2': 2,
        'tag 3': 3
    }


@pytest.fixture
def verdict_mapping():
    return {
        'verdict 1': 1,
        'verdict 2': 2,
        'verdict 3': 3
    }


@pytest.fixture
def technique_mapping():
    return {
        'technique 1': 1,
        'technique 2': 2,
        'technique 3': 3
    }


@pytest.fixture
def outlet_mapping():
    return {
        'outlet 1': 1,
        'outlet 2': 2,
        'outlet 3': 3
    }


def test_get_tag_mapping(tag_mapping):
    mock_conn = MagicMock()

    mock_conn.cursor().__enter__().fetchall.return_value = [
        {'tag_id': 1, 'tag': 'tag 1'},
        {'tag_id': 2, 'tag': 'tag 2'},
        {'tag_id': 3, 'tag': 'tag 3'}
    ]

    result = get_tag_mapping(mock_conn)

    assert isinstance(result, dict)
    assert result == tag_mapping


def test_get_verdict_mapping(verdict_mapping):
    mock_conn = MagicMock()

    mock_conn.cursor().__enter__().fetchall.return_value = [
        {'verdict_id': 1, 'verdict': 'verdict 1'},
        {'verdict_id': 2, 'verdict': 'verdict 2'},
        {'verdict_id': 3, 'verdict': 'verdict 3'}
    ]

    result = get_verdict_mapping(mock_conn)

    assert isinstance(result, dict)
    assert result == verdict_mapping


def test_get_technique_mapping(technique_mapping):
    mock_conn = MagicMock()

    mock_conn.cursor().__enter__().fetchall.return_value = [
        {'technique_id': 1, 'technique': 'technique 1'},
        {'technique_id': 2, 'technique': 'technique 2'},
        {'technique_id': 3, 'technique': 'technique 3'}
    ]

    result = get_technique_mapping(mock_conn)

    assert isinstance(result, dict)
    assert result == technique_mapping


def test_get_outlet_mapping(outlet_mapping):
    mock_conn = MagicMock()

    mock_conn.cursor().__enter__().fetchall.return_value = [
        {'outlet_id': 1, 'outlet': 'outlet 1'},
        {'outlet_id': 2, 'outlet': 'outlet 2'},
        {'outlet_id': 3, 'outlet': 'outlet 3'}
    ]

    result = get_outlet_mapping(mock_conn)

    assert isinstance(result, dict)
    assert result == outlet_mapping


def test_format_claim_insert_valid(verdict_mapping, technique_mapping):
    claims = [
        {
            "claim": "claim 1",
            "verdict": "verdict 1",
            "technique": "technique 1",
            "summary": "summary 1",
            "claim_embedding": [0.1, 0.2, 0.3],
            "confidence_score": 0.85,
        },
        {
            "claim": "claim 2",
            "verdict": "verdict 2",
            "technique": "technique 2",
            "summary": "summary 2",
            "claim_embedding": [0.4, 0.5, 0.6],
            "confidence_score": 0.25,
        }
    ]

    result = format_claim_insert(claims, verdict_mapping, technique_mapping)

    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], tuple)
    assert result[0] == (
        "claim 1",
        1,
        1,
        "summary 1",
        [0.1, 0.2, 0.3],
        0.85,
    )
    assert isinstance(result[1], tuple)
    assert result[1] == (
        "claim 2",
        2,
        2,
        "summary 2",
        [0.4, 0.5, 0.6],
        0.25,
    )


def test_format_claim_insert_invalid(verdict_mapping, technique_mapping):
    claims = [
        {
            "claim": "claim 1",
            "verdict": "no verdict",
            "technique": "technique 1",
            "summary": "summary 1",
            "claim_embedding": [0.1, 0.2, 0.3],
            "confidence_score": 0.85,
        },
        {
            "claim": "claim 2",
            "verdict": "verdict 2",
            "technique": "no technique",
            "summary": "summary 2",
            "claim_embedding": [0.4, 0.5, 0.6],
            "confidence_score": 0.25,
        },
        {
            "claim": "claim 3",
            "verdict": "no verdict ",
            "technique": "no technique",
            "summary": "summary 2",
            "claim_embedding": [0.7, 0.8, 0.9],
            "confidence_score": 0.5,
        }
    ]

    result = format_claim_insert(claims, verdict_mapping, technique_mapping)

    assert isinstance(result, list)
    assert len(result) == 0


def test_format_claim_tags_insert_valid():
    claim_tags = [
        {
            'claim_id': '1',
            'tags_id': ['1', '2', '3']
        },
        {
            'claim_id': '2',
            'tags_id': []
        }
    ]

    result = format_claim_tags_insert(claim_tags)

    assert isinstance(result, list)
    assert len(result) == 3
    assert isinstance(result[0], tuple)
    assert result[0] == (1, 1)
    assert isinstance(result[1], tuple)
    assert result[1] == (1, 2)
    assert isinstance(result[2], tuple)
    assert result[2] == (1, 3)


def test_format_claim_tags_insert_invalid():
    claim_tags = [
        {
            'claim_id': '1',
            'tags_id': ['a', '!', '1.2', '', None]
        }
    ]

    result = format_claim_tags_insert(claim_tags)

    assert isinstance(result, list)
    assert len(result) == 0


def test_format_sources_insert_valid(outlet_mapping):
    sources = [
        {
            'sources': 'source 1',
            'source_reasoning': 'reasoning 1',
            'source_name': 'outlet 1'
        },
        {
            'sources': 'source 2',
            'source_reasoning': 'reasoning 2',
            'source_name': 'outlet 2'
        },
    ]

    result = format_sources_insert(sources, outlet_mapping)

    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], tuple)
    assert result[0] == (
        'source 1',
        'reasoning 1',
        1
    )
    assert isinstance(result[1], tuple)
    assert result[1] == (
        'source 2',
        'reasoning 2',
        2
    )


def test_format_sources_insert_invalid(outlet_mapping):
    sources = [
        {
            'sources': 'source 1',
            'source_reasoning': 'reasoning 1',
            'source_name': 'no outlet'
        },
        {
            'sources': 'source 2',
            'source_reasoning': 'reasoning 2',
            'source_name': None
        },
    ]

    result = format_sources_insert(sources, outlet_mapping)

    assert isinstance(result, list)
    assert len(result) == 0


def test_format_claim_source_insert_valid():
    claim_source = [
        {
            'claim_id': '1',
            'source_id': '1'
        },
        {
            'claim_id': '2',
            'source_id': '2'
        },
    ]

    result = format_claim_source_insert(claim_source)

    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], tuple)
    assert result[0] == (1, 1)
    assert isinstance(result[1], tuple)
    assert result[1] == (2, 2)


def test_format_claim_source_insert_invalid():
    claim_source = [
        {
            'claim_id': '1',
            'source_id': 'a'
        },
        {
            'claim_id': '2',
            'source_id': '!'
        },
        {
            'claim_id': '3',
            'source_id': '1.2'
        },
        {
            'claim_id': '4',
            'source_id': ''
        },
        {
            'claim_id': '5',
            'source_id': None
        },
    ]

    result = format_claim_source_insert(claim_source)

    assert isinstance(result, list)
    assert len(result) == 0


# ---------------------------------------------------------------------------
# db connection
# ---------------------------------------------------------------------------

@pytest.fixture
def db_env(monkeypatch):
    monkeypatch.setenv("DATABASE_NAME", "test_db")
    monkeypatch.setenv("DATABASE_IP", "localhost")
    monkeypatch.setenv("DATABASE_PASSWORD", "test_password")
    monkeypatch.setenv("DATABASE_USERNAME", "test_user")
    monkeypatch.setenv("DATABASE_PORT", "5432")


@patch("load.connect")
def test_get_db_connection_success(mock_connect, db_env):
    result = get_db_connection()

    assert result == mock_connect.return_value
    kwargs = mock_connect.call_args.kwargs
    assert kwargs["dbname"] == "test_db"
    assert kwargs["host"] == "localhost"
    assert kwargs["password"] == "test_password"
    assert kwargs["user"] == "test_user"
    assert kwargs["port"] == "5432"


@patch("load.connect", side_effect=OperationalError("connection failed"))
def test_get_db_connection_failure_returns_none(mock_connect, db_env):
    assert get_db_connection() is None


# ---------------------------------------------------------------------------
# add to database
# ---------------------------------------------------------------------------
 
@patch("load.execute_values")
def test_add_claims_to_database(mock_execute_values):
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor().__enter__()
    mock_cursor.fetchall.return_value = [
        {"claim": "claim 1", "claim_id": 1},
        {"claim": "claim 2", "claim_id": 2}
    ]
    data = [
        ("claim 1", 1, 1, "summary 1", [0.1, 0.2], 0.85),
        ("claim 2", 2, 2, "summary 2", [0.3, 0.4], 0.25)
    ]
 
    result = add_claims_to_database(mock_conn, data)
 
    assert result == {"claim 1": 1, "claim 2": 2}
    mock_execute_values.assert_called_once()
    assert mock_execute_values.call_args.args[0] == mock_cursor
    assert mock_execute_values.call_args.args[2] == data
    mock_conn.commit.assert_called_once()
 
 
@patch("load.execute_values")
def test_add_source_to_database(mock_execute_values):
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor().__enter__()
    mock_cursor.fetchall.return_value = [
        {"source_url": "source 1", "source_id": 10},
        {"source_url": "source 2", "source_id": 11}
    ]
    data = [
        ("source 1", "reasoning 1", 1),
        ("source 2", "reasoning 2", 2)
    ]
 
    result = add_source_to_database(mock_conn, data)
 
    assert result == {"source 1": 10, "source 2": 11}
    assert mock_execute_values.call_args.args[2] == data
    mock_conn.commit.assert_called_once()
 
 
@pytest.mark.parametrize("add_function", [
    add_claim_tags_to_database,
    add_claim_source_to_database
])
@patch("load.execute_values")
def test_add_link_tables_to_database(mock_execute_values, add_function):
    mock_conn = MagicMock()
    data = [(1, 1), (1, 2)]
 
    result = add_function(mock_conn, data)
 
    assert result is None
    assert mock_execute_values.call_args.args[2] == data
    mock_conn.commit.assert_called_once()



# ---------------------------------------------------------------------------
# main insertion functions
# ---------------------------------------------------------------------------
 
@patch("load.add_claims_to_database")
@patch("load.get_technique_mapping")
@patch("load.get_verdict_mapping")
def test_main_claim_insertion_function(mock_verdicts, mock_techniques, mock_add,
                                       verdict_mapping, technique_mapping):
    mock_verdicts.return_value = verdict_mapping
    mock_techniques.return_value = technique_mapping
    mock_add.return_value = {"claim 1": 10, "claim 2": 20}
    conn = MagicMock()
    data = pd.DataFrame({
        "claim": ["claim 1", "claim 1", "claim 2"],
        "verdict": ["verdict 1", "verdict 1", "verdict 2"],
        "technique": ["technique 1", "technique 1", "technique 2"],
        "summary": ["summary 1", "summary 1", "summary 2"],
        "claim_embedding": [[0.1, 0.2], [0.1, 0.2], [0.3, 0.4]],
        "confidence_score": [0.8, 0.8, 0.4]
    })
 
    result = main_claim_insertion_function(conn, data)
 
    assert result == {"claim 1": 10, "claim 2": 20}
    assert mock_add.call_args.args[0] == conn
    assert mock_add.call_args.args[1] == [
        ("claim 1", 1, 1, "summary 1", [0.1, 0.2], 0.8),
        ("claim 2", 2, 2, "summary 2", [0.3, 0.4], 0.4)
    ]
 
 
@patch("load.add_claims_to_database")
@patch("load.get_technique_mapping")
@patch("load.get_verdict_mapping")
def test_main_claim_insertion_function_drops_missing_values(
        mock_verdicts, mock_techniques, mock_add, verdict_mapping, technique_mapping):
    mock_verdicts.return_value = verdict_mapping
    mock_techniques.return_value = technique_mapping
    data = pd.DataFrame({
        "claim": ["claim 1", "claim 2"],
        "verdict": ["verdict 1", "verdict 2"],
        "technique": ["technique 1", "technique 2"],
        "summary": ["summary 1", None],
        "claim_embedding": [[0.1, 0.2], [0.3, 0.4]],
        "confidence_score": [0.8, 0.4]
    })
 
    main_claim_insertion_function(MagicMock(), data)
 
    assert mock_add.call_args.args[1] == [
        ("claim 1", 1, 1, "summary 1", [0.1, 0.2], 0.8)
    ]
 
 
@patch("load.add_claim_tags_to_database")
@patch("load.get_tag_mapping")
def test_main_claim_tags_insertion_function(mock_tags, mock_add, tag_mapping):
    mock_tags.return_value = tag_mapping
    conn = MagicMock()
    data = pd.DataFrame({
        "claim_id": [1, 1, 2],
        "tags": [("tag 1", "tag 2"), ("tag 1", "tag 2"), ("tag 3",)]
    })
 
    main_claim_tags_insertion_function(conn, data)
 
    mock_add.assert_called_once()
    assert mock_add.call_args.args[0] == conn
    assert mock_add.call_args.args[1] == [(1, 1), (1, 2), (2, 3)]
 
 
@patch("load.add_claim_tags_to_database")
@patch("load.get_tag_mapping")
def test_main_claim_tags_insertion_function_skips_missing_claim_id(
        mock_tags, mock_add, tag_mapping):
    mock_tags.return_value = tag_mapping
    data = pd.DataFrame({
        "claim_id": [1.0, None],
        "tags": [("tag 1",), ("tag 2",)]
    })
 
    main_claim_tags_insertion_function(MagicMock(), data)
 
    assert mock_add.call_args.args[1] == [(1, 1)]
 
 
@patch("load.add_source_to_database")
@patch("load.get_outlet_mapping")
def test_main_source_insertion_function(mock_outlets, mock_add, outlet_mapping):
    mock_outlets.return_value = outlet_mapping
    mock_add.return_value = {"source 1": 5, "source 2": 6}
    conn = MagicMock()
    data = pd.DataFrame({
        "sources": ["source 1", "source 2", None],
        "source_name": ["outlet 1", "outlet 2", "outlet 3"],
        "source_reasoning": ["reasoning 1", "reasoning 2", "reasoning 3"]
    })
 
    result = main_source_insertion_function(conn, data)
 
    assert result == {"source 1": 5, "source 2": 6}
    assert mock_add.call_args.args[0] == conn
    # the row with no source is dropped
    assert mock_add.call_args.args[1] == [
        ("source 1", "reasoning 1", 1),
        ("source 2", "reasoning 2", 2)
    ]
 
 
@patch("load.add_claim_source_to_database")
def test_main_claim_source_insertion_function(mock_add):
    conn = MagicMock()
    data = pd.DataFrame({
        "claim_id": [1.0, 2.0, None],
        "source_id": [10.0, None, 30.0]
    })
 
    main_claim_source_insertion_function(conn, data)
 
    assert mock_add.call_args.args[0] == conn
    assert mock_add.call_args.args[1] == [(1, 10)]
 