# tests/test_objectstore_aws.py

import pytest
from unittest.mock import patch, MagicMock
import backend.data_layer.objectstore_aws as objectstore

@pytest.fixture(autouse=True)
def reset_minio_client():
    # Reset the singleton before each test
    objectstore._minio_client = None

def test_get_minio_config_success():
    with patch('backend.data_layer.objectstore_aws.get_env_variable') as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            'MINIO_FILES_HOST': 'localhost',
            'MINIO_FILES_PORT': '9000',
            'MINIO_FILES_ROOT_USER': 'user',
            'MINIO_FILES_ROOT_PASSWORD': 'pass'
        }[key]
        endpoint, access_key, secret_key, secure = objectstore.get_minio_config()
        assert endpoint == 'localhost:9000'
        assert access_key == 'user'
        assert secret_key == 'pass'
        assert secure is False

def test_get_minio_config_failure():
    with patch('backend.data_layer.objectstore_aws.get_env_variable', side_effect=Exception("env error")):
        with pytest.raises(Exception):
            objectstore.get_minio_config()

def test_get_minio_client_singleton():
    with patch('backend.data_layer.objectstore_aws.get_minio_config') as mock_conf, \
         patch('backend.data_layer.objectstore_aws.Minio') as mock_minio:
        mock_conf.return_value = ('host:9000', 'user', 'pass', False)
        client_instance = MagicMock()
        mock_minio.return_value = client_instance
        client1 = objectstore.get_minio_client()
        client2 = objectstore.get_minio_client()
        assert client1 is client2
        mock_minio.assert_called_once()

def test_ensure_bucket_exists():
    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = True
    with patch('backend.data_layer.objectstore_aws.get_minio_client', return_value=mock_client):
        objectstore.ensure_bucket('testbucket')
        mock_client.bucket_exists.assert_called_with('testbucket')
        mock_client.make_bucket.assert_not_called()

def test_ensure_bucket_not_exists():
    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = False
    with patch('backend.data_layer.objectstore_aws.get_minio_client', return_value=mock_client):
        objectstore.ensure_bucket('testbucket')
        mock_client.make_bucket.assert_called_with('testbucket')

def test_upload_file_success():
    mock_client = MagicMock()
    with patch('backend.data_layer.objectstore_aws.get_minio_client', return_value=mock_client), \
         patch('backend.data_layer.objectstore_aws.ensure_bucket'):
        objectstore.upload_file('bucket', 'obj', '/tmp/file')
        mock_client.fput_object.assert_called_with('bucket', 'obj', '/tmp/file')

def test_upload_file_failure():
    mock_client = MagicMock()
    mock_client.fput_object.side_effect = objectstore.S3Error("err", "msg", "req", "host", "id", "res")
    with patch('backend.data_layer.objectstore_aws.get_minio_client', return_value=mock_client), \
         patch('backend.data_layer.objectstore_aws.ensure_bucket'):
        with pytest.raises(objectstore.S3Error):
            objectstore.upload_file('bucket', 'obj', '/tmp/file')

def test_download_file_success():
    mock_client = MagicMock()
    with patch('backend.data_layer.objectstore_aws.get_minio_client', return_value=mock_client):
        objectstore.download_file('bucket', 'obj', '/tmp/file')
        mock_client.fget_object.assert_called_with('bucket', 'obj', '/tmp/file')

def test_download_file_failure():
    mock_client = MagicMock()
    mock_client.fget_object.side_effect = objectstore.S3Error("err", "msg", "req", "host", "id", "res")
    with patch('backend.data_layer.objectstore_aws.get_minio_client', return_value=mock_client):
        with pytest.raises(objectstore.S3Error):
            objectstore.download_file('bucket', 'obj', '/tmp/file')

def test_list_files_success():
    mock_client = MagicMock()
    mock_obj = MagicMock()
    mock_obj.object_name = 'file1.txt'
    mock_client.list_objects.return_value = [mock_obj]
    with patch('backend.data_layer.objectstore_aws.get_minio_client', return_value=mock_client):
        files = objectstore.list_files('bucket')
        assert files == ['file1.txt']
        mock_client.list_objects.assert_called_with('bucket', prefix='', recursive=True)

def test_list_files_failure():
    mock_client = MagicMock()
    mock_client.list_objects.side_effect = objectstore.S3Error("err", "msg", "req", "host", "id", "res")
    with patch('backend.data_layer.objectstore_aws.get_minio_client', return_value=mock_client):
        with pytest.raises(objectstore.S3Error):
            objectstore.list_files('bucket')
