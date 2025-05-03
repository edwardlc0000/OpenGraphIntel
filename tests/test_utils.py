# tests/test_utils.py

import pytest
from open_graph_intel.common.utils import get_env_variable

def test_get_env_variable_existing(monkeypatch):
    # Use monkeypatch to set an environment variable
    monkeypatch.setenv('TEST_VAR', 'test_value')
    
    # Assert that the function retrieves the correct value
    assert get_env_variable('TEST_VAR') == 'test_value'


def test_get_env_variable_non_existing():
    # Assert that the function raises a ValueError when the variable is not set
    with pytest.raises(ValueError, match="Environment variable NON_EXISTENT_VAR not found."):
        get_env_variable('NON_EXISTENT_VAR')


# Additional test cases can be defined as needed
