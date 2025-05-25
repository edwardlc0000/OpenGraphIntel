# tests/test_object_store_aws.py

import pytest
from unittest.mock import patch, MagicMock
from backend.data_layer.object_store_aws import ObjectStoreAWS, S3Error

@pytest.fixture
def mock_env_variables():
    env_vars = {
        'MINIO_FILES_HOST': 'localhost',
        'MINIO_FILES_PORT': '9000',
        'MINIO_FILES_ROOT_USER': 'user',
        'MINIO_FILES_ROOT_PASSWORD': 'pass'
    }
    with patch('backend.data_layer.object_store_aws.get_env_variable') as mock_env:
        mock_env.side_effect = lambda key: env_vars[key]
        yield

def test_get_minio_config_success():
    with patch('backend.data_layer.object_store_aws.get_env_variable') as mock_env:
        mock_env.side_effect = lambda key: {
            'MINIO_FILES_HOST': 'localhost',
            'MINIO_FILES_PORT': '9000',
            'MINIO_FILES_ROOT_USER': 'user',
            'MINIO_FILES_ROOT_PASSWORD': 'pass'
        }[key]
        store = ObjectStoreAWS()
        assert store.endpoint == 'localhost:9000'
        assert store.access_key == 'user'
        assert store.secret_key == 'pass'
        assert store.secure is False

def test_get_minio_config_failure():
    with patch('backend.data_layer.object_store_aws.get_env_variable', side_effect=Exception("env error")):
        with pytest.raises(Exception):
            ObjectStoreAWS()

def test_minio_client_singleton(mock_env_variables):
    with patch('backend.data_layer.object_store_aws.ObjectStoreAWS._get_minio_config', return_value=('host:9000', 'user', 'pass', False)), \
         patch('backend.data_layer.object_store_aws.Minio') as mock_minio:
        client_instance = MagicMock()
        mock_minio.return_value = client_instance
        store1 = ObjectStoreAWS()
        client1 = store1.client
        store2 = ObjectStoreAWS()
        client2 = store2.client
        assert client1 is client2


def test_ensure_bucket_exists(mock_env_variables):
    # Specific mock for Minio client
    with patch('backend.data_layer.object_store_aws.Minio') as mock_minio:
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_minio.return_value = mock_client
        store = ObjectStoreAWS()
        store.ensure_bucket('testbucket')
        mock_client.bucket_exists.assert_called_with('testbucket')
        mock_client.make_bucket.assert_not_called()

def test_ensure_bucket_not_exists(mock_env_variables):
    with patch('backend.data_layer.object_store_aws.Minio') as mock_minio:
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False
        mock_minio.return_value = mock_client
        store = ObjectStoreAWS()
        store.ensure_bucket('testbucket')
        mock_client.make_bucket.assert_called_with('testbucket')

def test_upload_file_success(mock_env_variables):
    with patch('backend.data_layer.object_store_aws.Minio') as mock_minio:
        # Configure the mock Minio client
        mock_client = MagicMock()
        mock_minio.return_value = mock_client

        # Prepare store instance after patching
        store = ObjectStoreAWS()

        # Call the method under test
        store.upload_file('bucket', 'obj', '/tmp/file')

        # Assert interactions with the mock client
        mock_client.fput_object.assert_called_with('bucket', 'obj', '/tmp/file')
        mock_client.bucket_exists.assert_called_with('bucket')

def test_upload_file_failure(mock_env_variables):
    with patch('backend.data_layer.object_store_aws.Minio') as mock_minio:
        mock_client = MagicMock()
        mock_minio.return_value = mock_client

        # Set up the client to raise an error on fput_object call
        mock_client.fput_object.side_effect = S3Error("err", "msg", "req", "host", "id", "res")

        # Prepare store instance after patching
        store = ObjectStoreAWS()

        # Execute the upload and expect an S3Error
        with pytest.raises(S3Error):
            store.upload_file('bucket', 'obj', '/tmp/file')

        # Ensure the function attempted the call, causing the side effect
        mock_client.fput_object.assert_called_with('bucket', 'obj', '/tmp/file')

def test_download_file_success(mock_env_variables):
    with patch('backend.data_layer.object_store_aws.Minio') as mock_minio:
        mock_client = MagicMock()
        mock_client.fget_object.return_value = None
        mock_minio.return_value = mock_client
        store = ObjectStoreAWS()
        store.download_file('bucket', 'obj', '/tmp/file')
        mock_client.fget_object.assert_called_with('bucket', 'obj', '/tmp/file')

def test_download_file_failure(mock_env_variables):
    with patch('backend.data_layer.object_store_aws.Minio') as mock_minio:
        mock_client = MagicMock()
        mock_client.fget_object.side_effect = S3Error("err", "msg", "req", "host", "id", "res")
        mock_minio.return_value = mock_client
        store = ObjectStoreAWS()
        with pytest.raises(S3Error):
            store.download_file('bucket', 'obj', '/tmp/file')
        mock_client.fget_object.assert_called_with('bucket', 'obj', '/tmp/file')

def test_list_files_success(mock_env_variables):
    with patch('backend.data_layer.object_store_aws.Minio') as mock_minio:
        mock_client = MagicMock()
        mock_client.list_objects.return_value = [MagicMock(object_name='file1'), MagicMock(object_name='file2')]
        mock_minio.return_value = mock_client
        store = ObjectStoreAWS()
        files = store.list_files('bucket')
        assert files == ['file1', 'file2']
        mock_client.list_objects.assert_called_with('bucket', prefix='', recursive=True)

def test_list_files_failure(mock_env_variables):
    with patch('backend.data_layer.object_store_aws.Minio') as mock_minio:
        mock_client = MagicMock()
        mock_client.list_objects.side_effect = S3Error("err", "msg", "req", "host", "id", "res")
        mock_minio.return_value = mock_client
        store = ObjectStoreAWS()
        with pytest.raises(S3Error):
            store.list_files('bucket')
        mock_client.list_objects.assert_called_with('bucket', prefix='', recursive=True)