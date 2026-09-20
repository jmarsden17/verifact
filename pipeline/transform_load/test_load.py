# pylint: skip-file

"""
Test for load file
"""
import pytest
from unittest.mock import MagicMock

from load import (
    get_tag_mapping,
    get_verdict_mapping,
    get_technique_mapping,
    get_outlet_mapping,
    format_claim_insert
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
