# tests/test_object_store_gcp.py

import pytest
from unittest.mock import patch, MagicMock
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
from google.api_core.exceptions import GoogleAPIError
from backend.data_layer.object_store_gcp import ObjectStoreGCP

@pytest.fixture
def mock_env_variables():
    env_vars = {
        'GCP_PROJECT_ID': 'my-project',
        'GCS_BUCKET_NAME': 'my-bucket'
    }
    with patch('backend.data_layer.object_store_gcp.get_env_variable') as mock_env:
        mock_env.side_effect = lambda key: env_vars[key]
        yield

def setup_gcs_mocks(mock_storage_client):
    mock_client = MagicMock()
    mock_storage_client.return_value = mock_client

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_get_gcs_config_success(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    store = ObjectStoreGCP()
    assert store.project_id == 'my-project'
    assert store.bucket_name == 'my-bucket'

@patch('backend.data_layer.object_store_gcp.get_env_variable', side_effect=Exception("env error"))
def test_get_gcs_config_failure(mock_env):
    with pytest.raises(Exception):
        ObjectStoreGCP()

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_gcs_client_singleton(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    store1 = ObjectStoreGCP()
    client1 = store1.client
    store2 = ObjectStoreGCP()
    client2 = store2.client
    assert client1 is client2

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_gcs_client_initialization(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    store = ObjectStoreGCP()
    assert store.client is not None
    mock_storage_client.assert_called_with(project='my-project')

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_gcs_client_initialization_singleton(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    store = ObjectStoreGCP()
    client1 = store.client
    store._initialize_client()
    client2 = store.client
    assert client1 is client2
    mock_storage_client.assert_called_once_with(project='my-project')

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_gcs_client_initialization_failure(mock_storage_client, mock_env_variables):
    mock_storage_client.side_effect = DefaultCredentialsError("Credentials error")
    with pytest.raises(DefaultCredentialsError):
        ObjectStoreGCP()

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_gcs_client_property(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    store = ObjectStoreGCP()
    store._gcs_client = None  # Force re-initialization
    client = store.client
    assert client is not None
    mock_storage_client.assert_called_with(project='my-project')

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_ensure_bucket_exists(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    mock_client = mock_storage_client.return_value
    mock_bucket = MagicMock()
    mock_client.lookup_bucket.return_value = mock_bucket
    store = ObjectStoreGCP()
    store.ensure_bucket('my-bucket')
    mock_client.lookup_bucket.assert_called_with('my-bucket')
    mock_client.create_bucket.assert_not_called()

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_ensure_bucket_not_exists(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    mock_client = mock_storage_client.return_value
    mock_client.lookup_bucket.return_value = None
    store = ObjectStoreGCP()
    store.ensure_bucket('my-bucket')
    mock_client.create_bucket.assert_called_with('my-bucket')

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_ensure_bucket_failure(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    mock_client = mock_storage_client.return_value
    mock_client.lookup_bucket.side_effect = GoogleAPIError("Bucket error")
    store = ObjectStoreGCP()
    with pytest.raises(GoogleAPIError):
        store.ensure_bucket('my-bucket')

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_upload_file_success(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    mock_client = mock_storage_client.return_value
    mock_bucket = mock_client.get_bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    mock_blob.upload_from_filename.return_value = None

    store = ObjectStoreGCP()
    store.upload_file('my-bucket', 'my-object', '/path/to/file')
    mock_bucket.blob.assert_called_with('my-object')
    mock_blob.upload_from_filename.assert_called_with('/path/to/file')

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_upload_file_failure(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    mock_client = mock_storage_client.return_value
    mock_bucket = mock_client.get_bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    mock_blob.upload_from_filename.side_effect = GoogleAPIError("Upload error")

    store = ObjectStoreGCP()
    with pytest.raises(GoogleAPIError):
        store.upload_file('my-bucket', 'my-object', '/path/to/file')

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_download_file_success(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    mock_client = mock_storage_client.return_value
    mock_bucket = mock_client.get_bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    mock_blob.download_to_filename.return_value = None

    store = ObjectStoreGCP()
    store.download_file('my-bucket', 'my-object', '/path/to/file')
    mock_bucket.blob.assert_called_with('my-object')
    mock_blob.download_to_filename.assert_called_with('/path/to/file')

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_download_file_failure(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    mock_client = mock_storage_client.return_value
    mock_bucket = mock_client.get_bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    mock_blob.download_to_filename.side_effect = GoogleAPIError("Download error")

    store = ObjectStoreGCP()
    with pytest.raises(GoogleAPIError):
        store.download_file('my-bucket', 'my-object', '/path/to/file')

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_list_files_success(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    mock_client = mock_storage_client.return_value
    mock_bucket = mock_client.get_bucket.return_value
    # Mocking blobs with names directly in the returned list
    mock_blob_1 = MagicMock()
    mock_blob_1.name = 'file1'

    mock_blob_2 = MagicMock()
    mock_blob_2.name = 'file2'

    mock_bucket.list_blobs.return_value = [mock_blob_1, mock_blob_2]

    # Instantiate ObjectStoreGCP and call list_files
    store = ObjectStoreGCP()
    files = store.list_files('my-bucket')

    # Assert that the file names are as expected
    assert files == ['file1', 'file2']
    # Verify list_blobs was called with correct parameters
    mock_bucket.list_blobs.assert_called_with(prefix='')

@patch('backend.data_layer.object_store_gcp.storage.Client')
def test_list_files_failure(mock_storage_client, mock_env_variables):
    setup_gcs_mocks(mock_storage_client)
    mock_client = mock_storage_client.return_value
    mock_bucket = mock_client.get_bucket.return_value
    mock_bucket.list_blobs.side_effect = GoogleAPIError("List error")

    store = ObjectStoreGCP()
    with pytest.raises(GoogleAPIError):
        store.list_files('my-bucket')