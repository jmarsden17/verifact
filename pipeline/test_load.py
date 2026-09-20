# pylint: skip-file

"""
Test for load file
"""
import pylint
from unittest.mock import MagicMock

from transform_load.load import (
    get_tag_mapping,
    get_verdict_mapping,
    get_technique_mapping,
    get_outlet_mapping
)
