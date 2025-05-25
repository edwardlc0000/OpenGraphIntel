# tests/test_object_store_azure.py

import pytest
from unittest.mock import patch, MagicMock, mock_open
import backend.data_layer.object_store_azure as object_store

@pytest.fixture(autouse=True)
def reset_blob_service_client():
    object_store._blob_service_client = None

def test_get_azure_blob_config_success():
    with patch('backend.data_layer.object_store_azure.get_env_variable') as mock_env:
        mock_env.return_value = "UseDevelopmentStorage=true"
        conn_str = object_store.get_azure_blob_config()
        assert conn_str == "UseDevelopmentStorage=true"

def test_get_azure_blob_config_failure():
    with patch('backend.data_layer.object_store_azure.get_env_variable', side_effect=Exception("env error")):
        with pytest.raises(Exception):
            object_store.get_azure_blob_config()

def test_get_blob_service_client_singleton():
    with patch('backend.data_layer.object_store_azure.get_azure_blob_config') as mock_conf, \
         patch('backend.data_layer.object_store_azure.BlobServiceClient') as mock_bsc:
        mock_conf.return_value = "conn_str"
        instance = MagicMock()
        mock_bsc.from_connection_string.return_value = instance
        client1 = object_store.get_blob_service_client()
        client2 = object_store.get_blob_service_client()
        assert client1 is client2
        mock_bsc.from_connection_string.assert_called_once_with("conn_str")

def test_ensure_container_creates():
    mock_client = MagicMock()
    with patch('backend.data_layer.object_store_azure.get_blob_service_client', return_value=mock_client):
        object_store.ensure_container('testcontainer')
        mock_client.create_container.assert_called_with('testcontainer')

def test_ensure_container_exists():
    mock_client = MagicMock()
    mock_client.create_container.side_effect = object_store.ResourceExistsError("exists")
    with patch('backend.data_layer.object_store_azure.get_blob_service_client', return_value=mock_client):
        object_store.ensure_container('testcontainer')
        mock_client.create_container.assert_called_with('testcontainer')

def test_upload_file_success():
    mock_client = MagicMock()
    mock_blob_client = MagicMock()
    mock_client.get_blob_client.return_value = mock_blob_client
    with patch('backend.data_layer.object_store_azure.get_blob_service_client', return_value=mock_client), \
         patch('backend.data_layer.object_store_azure.ensure_container'), \
         patch("builtins.open", mock_open(read_data=b"data")) as m:
        object_store.upload_file('container', 'blob', '/tmp/file')
        mock_client.get_blob_client.assert_called_with(container='container', blob='blob')
        mock_blob_client.upload_blob.assert_called()
        m.assert_called_with('/tmp/file', 'rb')

def test_upload_file_failure():
    mock_client = MagicMock()
    mock_blob_client = MagicMock()
    mock_blob_client.upload_blob.side_effect = Exception("fail")
    mock_client.get_blob_client.return_value = mock_blob_client
    with patch('backend.data_layer.object_store_azure.get_blob_service_client', return_value=mock_client), \
         patch('backend.data_layer.object_store_azure.ensure_container'), \
         patch("builtins.open", mock_open(read_data=b"data")):
        with pytest.raises(Exception):
            object_store.upload_file('container', 'blob', '/tmp/file')

def test_download_file_success():
    mock_client = MagicMock()
    mock_blob_client = MagicMock()
    mock_download = MagicMock()
    mock_download.readall.return_value = b"abc"
    mock_blob_client.download_blob.return_value = mock_download
    mock_client.get_blob_client.return_value = mock_blob_client
    with patch('backend.data_layer.object_store_azure.get_blob_service_client', return_value=mock_client), \
         patch("builtins.open", mock_open()) as m:
        object_store.download_file('container', 'blob', '/tmp/file')
        mock_client.get_blob_client.assert_called_with(container='container', blob='blob')
        mock_blob_client.download_blob.assert_called()
        handle = m()
        handle.write.assert_called_with(b"abc")

def test_download_file_not_found():
    mock_client = MagicMock()
    mock_blob_client = MagicMock()
    mock_blob_client.download_blob.side_effect = object_store.ResourceNotFoundError("not found")
    mock_client.get_blob_client.return_value = mock_blob_client
    with patch('backend.data_layer.object_store_azure.get_blob_service_client', return_value=mock_client), \
         patch("builtins.open", mock_open()):
        with pytest.raises(object_store.ResourceNotFoundError):
            object_store.download_file('container', 'blob', '/tmp/file')

def test_download_file_other_error():
    mock_client = MagicMock()
    mock_blob_client = MagicMock()
    mock_blob_client.download_blob.side_effect = Exception("fail")
    mock_client.get_blob_client.return_value = mock_blob_client
    with patch('backend.data_layer.object_store_azure.get_blob_service_client', return_value=mock_client), \
         patch("builtins.open", mock_open()):
        with pytest.raises(Exception):
            object_store.download_file('container', 'blob', '/tmp/file')

def test_list_files_success():
    mock_client = MagicMock()
    mock_container_client = MagicMock()
    mock_blob = MagicMock()
    mock_blob.name = "file1.txt"
    mock_container_client.list_blobs.return_value = [mock_blob]
    mock_client.get_container_client.return_value = mock_container_client
    with patch('backend.data_layer.object_store_azure.get_blob_service_client', return_value=mock_client):
        files = object_store.list_files('container')
        assert files == ['file1.txt']
        mock_client.get_container_client.assert_called_with('container')
        mock_container_client.list_blobs.assert_called_with(name_starts_with='')

def test_list_files_failure():
    mock_client = MagicMock()
    mock_container_client = MagicMock()
    mock_container_client.list_blobs.side_effect = Exception("fail")
    mock_client.get_container_client.return_value = mock_container_client
    with patch('backend.data_layer.object_store_azure.get_blob_service_client', return_value=mock_client):
        with pytest.raises(Exception):
            object_store.list_files('container')
