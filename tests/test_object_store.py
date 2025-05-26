# tests/test_object_store.py

import pytest
import os
import importlib
from unittest.mock import patch, MagicMock
from backend.data_layer.object_store import ObjectStore

# Reset and reload the ObjectStore module to ensure each test has a fresh state
@pytest.fixture(autouse=True)
def reset_object_store_instance():
    """Fixture to reset the ObjectStore instance before each test."""
    # Ensure the environment variable is not set
    os.environ.pop('CLOUD_ENV_OVERRIDE', None)
    import backend.data_layer.object_store  # Ensure proper path
    yield
    # Reset the singleton instance after each test
    ObjectStore._object_store_instance = None
    importlib.reload(importlib.import_module('backend.data_layer.object_store'))

# Test: Detecting environment and AWS import
@patch('backend.data_layer.object_store.detect_env', return_value='aws')
@patch('importlib.import_module')
def test_object_store_detect_env(mock_import_module, mock_detect_env):
    os.environ['AWS_EXECUTION_ENV'] = 'aws'  # Simulate AWS environment
    # Mocking the module and class
    mock_module = MagicMock()
    mock_class = MagicMock()
    setattr(mock_module, "ObjectStoreAWS", mock_class)
    mock_import_module.return_value = mock_module

    # Call the function to test object store instantiation
    instance = ObjectStore.get_object_store()

    # Assertions to verify behavior
    mock_import_module.assert_called_with('backend.data_layer.object_store_aws')
    mock_class.assert_called_once()
    assert instance is mock_class.return_value

# Test: Environment override and AWS import
@patch('backend.data_layer.object_store.detect_env', return_value='aws')
@patch('importlib.import_module')
def test_get_object_store_aws(mock_import_module, mock_detect_env):
    os.environ['CLOUD_ENV_OVERRIDE'] = 'aws'  # Set environment override
    mock_module = MagicMock()
    mock_class = MagicMock()
    setattr(mock_module, "ObjectStoreAWS", mock_class)
    mock_import_module.return_value = mock_module

    instance = ObjectStore.get_object_store()

    mock_import_module.assert_called_with('backend.data_layer.object_store_aws')
    mock_class.assert_called_once()
    assert instance is mock_class.return_value

    # Cleanup environment variable
    del os.environ['CLOUD_ENV_OVERRIDE']

# Test: Environment detection mechanism and Azure import
@patch('backend.data_layer.object_store.detect_env', return_value='azure')
@patch('importlib.import_module')
def test_get_object_store_azure(mock_import_module, mock_detect_env):
    os.environ['CLOUD_ENV_OVERRIDE'] = 'azure'
    mock_module = MagicMock()
    mock_class = MagicMock()
    setattr(mock_module, "ObjectStoreAzure", mock_class)
    mock_import_module.return_value = mock_module

    instance = ObjectStore.get_object_store()

    mock_import_module.assert_called_with('backend.data_layer.object_store_azure')
    mock_class.assert_called_once()
    assert instance is mock_class.return_value

    # Cleanup environment variable
    del os.environ['CLOUD_ENV_OVERRIDE']

# Test: Default behavior and GCP import with proper detection
@patch('backend.data_layer.object_store.detect_env', return_value='gcp')
@patch('importlib.import_module')
def test_get_object_store_gcp(mock_import_module, mock_detect_env):
    os.environ['CLOUD_ENV_OVERRIDE'] = 'gcp'
    mock_module = MagicMock()
    mock_class = MagicMock()
    setattr(mock_module, "ObjectStoreGCP", mock_class)
    mock_import_module.return_value = mock_module

    instance = ObjectStore.get_object_store()

    mock_import_module.assert_called_with('backend.data_layer.object_store_gcp')
    mock_class.assert_called_once()
    assert instance is mock_class.return_value

    # Cleanup environment variable
    del os.environ['CLOUD_ENV_OVERRIDE']

# Test: Unsupported environment
@patch('backend.data_layer.object_store.detect_env', return_value='unsupported')
def test_unsupported_cloud_env(mock_detect_env):
    os.environ['CLOUD_ENV_OVERRIDE'] = 'unsupported'
    with pytest.raises(RuntimeError, match="Unsupported cloud environment: unsupported"):
        ObjectStore.get_object_store()

    # Cleanup environment variable
    del os.environ['CLOUD_ENV_OVERRIDE']

# Test: Singleton behavior
@patch('backend.data_layer.object_store.detect_env', return_value='aws')
@patch('importlib.import_module')
def test_get_object_store_singleton(mock_import_module, mock_detect_env):
    os.environ['CLOUD_ENV_OVERRIDE'] = 'aws'
    mock_module = MagicMock()
    mock_class = MagicMock()
    setattr(mock_module, "ObjectStoreAWS", mock_class)
    mock_import_module.return_value = mock_module

    instance1 = ObjectStore.get_object_store()
    instance2 = ObjectStore.get_object_store()

    assert instance1 is instance2
    del os.environ['CLOUD_ENV_OVERRIDE']