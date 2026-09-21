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
    format_claim_insert,
    format_claim_tags_insert,
    format_sources_insert,
    format_claim_source_insert
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
