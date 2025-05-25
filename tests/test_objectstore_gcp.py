# tests/test_objectstore_gcp.py

import pytest
from unittest.mock import patch, MagicMock
import backend.data_layer.objectstore_gcp as objectstore

@pytest.fixture(autouse=True)
def reset_gcs_client():
    # Reset the singleton before each test
    objectstore._gcs_client = None

def test_get_gcs_config_success():
    with patch('backend.data_layer.objectstore_gcp.get_env_variable') as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            'GCP_PROJECT_ID': 'test-project',
            'GCS_BUCKET_NAME': 'test-bucket'
        }[key]
        project_id, bucket_name = objectstore.get_gcs_config()
        assert project_id == 'test-project'
        assert bucket_name == 'test-bucket'

def test_get_gcs_config_failure():
    with patch('backend.data_layer.objectstore_gcp.get_env_variable', side_effect=Exception("env error")):
        with pytest.raises(Exception):
            objectstore.get_gcs_config()

def test_get_gcs_client_singleton():
    with patch('backend.data_layer.objectstore_gcp.get_gcs_config') as mock_conf, \
         patch('backend.data_layer.objectstore_gcp.storage.Client') as mock_client:
        mock_conf.return_value = ('test-project', 'test-bucket')
        client_instance = MagicMock()
        mock_client.return_value = client_instance
        client1 = objectstore.get_gcs_client()
        client2 = objectstore.get_gcs_client()
        assert client1 is client2
        mock_client.assert_called_once_with(project='test-project')

def test_get_gcs_client_initialization_failure():
    with patch('backend.data_layer.objectstore_gcp.get_gcs_config', side_effect=objectstore.DefaultCredentialsError("error")):
        with pytest.raises(objectstore.DefaultCredentialsError):
            objectstore.get_gcs_client()

def test_ensure_bucket_exists():
    mock_client = MagicMock()
    mock_client.lookup_bucket.return_value = MagicMock()
    with patch('backend.data_layer.objectstore_gcp.get_gcs_client', return_value=mock_client):
        objectstore.ensure_bucket('test-bucket')
        mock_client.lookup_bucket.assert_called_with('test-bucket')
        mock_client.create_bucket.assert_not_called()

def test_ensure_bucket_not_exists():
    mock_client = MagicMock()
    mock_client.lookup_bucket.return_value = None
    with patch('backend.data_layer.objectstore_gcp.get_gcs_client', return_value=mock_client):
        objectstore.ensure_bucket('test-bucket')
        mock_client.create_bucket.assert_called_with('test-bucket')

def test_ensure_bucket_failure():
    mock_client = MagicMock()
    mock_client.lookup_bucket.side_effect = objectstore.GoogleAPIError("error")
    with patch('backend.data_layer.objectstore_gcp.get_gcs_client', return_value=mock_client):
        with pytest.raises(objectstore.GoogleAPIError):
            objectstore.ensure_bucket('test-bucket')

def test_upload_file_success():
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client.get_bucket.return_value = mock_bucket
    with patch('backend.data_layer.objectstore_gcp.get_gcs_client', return_value=mock_client), \
         patch('backend.data_layer.objectstore_gcp.ensure_bucket'):
        objectstore.upload_file('bucket', 'obj', '/tmp/file')
        mock_bucket.blob.assert_called_with('obj')
        mock_blob.upload_from_filename.assert_called_with('/tmp/file')

def test_upload_file_failure():
    mock_client = MagicMock()
    mock_client.get_bucket.side_effect = objectstore.GoogleAPIError("error")
    with patch('backend.data_layer.objectstore_gcp.get_gcs_client', return_value=mock_client):
        with pytest.raises(objectstore.GoogleAPIError):
            objectstore.upload_file('bucket', 'obj', '/tmp/file')

def test_download_file_success():
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client.get_bucket.return_value = mock_bucket
    with patch('backend.data_layer.objectstore_gcp.get_gcs_client', return_value=mock_client):
        objectstore.download_file('bucket', 'obj', '/tmp/file')
        mock_bucket.blob.assert_called_with('obj')
        mock_blob.download_to_filename.assert_called_with('/tmp/file')

def test_download_file_failure():
    mock_client = MagicMock()
    mock_client.get_bucket.side_effect = objectstore.GoogleAPIError("error")
    with patch('backend.data_layer.objectstore_gcp.get_gcs_client', return_value=mock_client):
        with pytest.raises(objectstore.GoogleAPIError):
            objectstore.download_file('bucket', 'obj', '/tmp/file')

def test_list_files_success():
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob1 = MagicMock()
    mock_blob1.name = 'file1.txt'
    mock_client.get_bucket.return_value = mock_bucket
    mock_bucket.list_blobs.return_value = [mock_blob1]
    with patch('backend.data_layer.objectstore_gcp.get_gcs_client', return_value=mock_client):
        files = objectstore.list_files('bucket')
        assert files == ['file1.txt']
        mock_bucket.list_blobs.assert_called_with(prefix='')

def test_list_files_failure():
    mock_client = MagicMock()
    mock_client.get_bucket.side_effect = objectstore.GoogleAPIError("error")
    with patch('backend.data_layer.objectstore_gcp.get_gcs_client', return_value=mock_client):
        with pytest.raises(objectstore.GoogleAPIError):
            objectstore.list_files('bucket')