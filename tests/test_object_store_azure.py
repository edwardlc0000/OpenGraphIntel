# tests/test_object_store_azure.py

import pytest
from unittest.mock import patch, MagicMock, mock_open
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError, AzureError
from backend.data_layer.object_store_azure import ObjectStoreAzure  # Adjust based on your module path

@pytest.fixture
def mock_env_variables():
    env_vars = {
        'AZURE_BLOB_CONNECTION_STRING': 'DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;'
    }
    with patch('backend.data_layer.object_store_azure.get_env_variable') as mock_env:
        mock_env.side_effect = lambda key: env_vars[key]
        yield

@patch('backend.data_layer.object_store_azure.get_env_variable')
def test_get_azure_blob_config_success(mock_env):
    mock_env.side_effect = lambda key: {
        'AZURE_BLOB_CONNECTION_STRING': 'DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;'
    }[key]
    store = ObjectStoreAzure()
    assert store.connection_string == 'DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;'

@patch('backend.data_layer.object_store_azure.get_env_variable', side_effect=Exception("env error"))
def test_get_azure_blob_config_failure(mock_env):
    with pytest.raises(Exception):
        ObjectStoreAzure()

@patch('backend.data_layer.object_store_azure.BlobServiceClient.from_connection_string')
def test_blob_client_singleton(mock_blob_service_client, mock_env_variables):
    mock_instance = MagicMock()
    mock_blob_service_client.return_value = mock_instance
    store1 = ObjectStoreAzure()
    client1 = store1.client
    store2 = ObjectStoreAzure()
    client2 = store2.client
    assert client1 is client2

@patch('backend.data_layer.object_store_azure.BlobServiceClient.from_connection_string')
def test_blob_client_initialization(mock_blob_service_client, mock_env_variables):
    mock_instance = MagicMock()
    mock_blob_service_client.return_value = mock_instance
    # Create a store instance
    store = ObjectStoreAzure()
    store._initialize_client()
    # Ensure the client is initialized
    assert store.client is not None
    assert store.client is mock_instance

@patch('backend.data_layer.object_store_azure.BlobServiceClient.from_connection_string')
def test_blob_client_initialization_singleton(mock_blob_service_client, mock_env_variables):
    mock_instance = MagicMock()
    mock_blob_service_client.return_value = mock_instance
    store1 = ObjectStoreAzure()
    client1 = store1.client
    store2 = ObjectStoreAzure()
    client2 = store2.client
    assert client1 is client2

@patch('backend.data_layer.object_store_azure.BlobServiceClient.from_connection_string')
def test_blob_client_property(mock_blob_service_client, mock_env_variables):
    mock_instance = MagicMock()
    mock_blob_service_client.return_value = mock_instance
    store = ObjectStoreAzure()
    store._blob_service_client = None  # Simulate the client not being initialized
    assert store._blob_service_client is None
    client = store.client  # This should trigger initialization
    assert store._blob_service_client is not None
    assert client is mock_instance

@patch('backend.data_layer.object_store_azure.BlobServiceClient')
def test_ensure_container_exists(mock_blob_service_client, mock_env_variables):
    object_store = ObjectStoreAzure()
    mock_client_instance = mock_blob_service_client.from_connection_string.return_value
    mock_create_container = mock_client_instance.create_container
    mock_create_container.side_effect = ResourceExistsError
    container_name = "existing-container"
    object_store.ensure_container(container_name)
    mock_create_container.assert_called_once_with(container_name)

@patch('backend.data_layer.object_store_azure.BlobServiceClient')
def test_ensure_container_not_exists(mock_blob_service_client, mock_env_variables):
    object_store = ObjectStoreAzure()
    mock_client_instance = mock_blob_service_client.from_connection_string.return_value
    mock_create_container = mock_client_instance.create_container
    mock_create_container.side_effect = lambda name: None  # Simulate successful container creation
    container_name = "test-container"
    object_store.ensure_container(container_name)
    mock_create_container.assert_called_once_with(container_name)

@patch('backend.data_layer.object_store_azure.BlobServiceClient')
def test_upload_file_success(mock_blob_service_client, mock_env_variables):
    # Arrange
    object_store = ObjectStoreAzure()
    mock_client_instance = mock_blob_service_client.from_connection_string.return_value
    mock_blob_client = mock_client_instance.get_blob_client.return_value
    mock_blob_client.upload_blob = MagicMock()

    container_name = "test-container"
    blob_name = "blob.txt"
    file_path = "path/to/file.txt"

    # Mock opening a file
    with patch('builtins.open', mock_open(read_data="data")) as mock_file:
        # Act
        object_store.upload_file(container_name, blob_name, file_path)

    # Assert
    object_store.ensure_container(container_name)
    mock_blob_client.upload_blob.assert_called_once()
    mock_file.assert_called_once_with(file_path, "rb")


@patch('backend.data_layer.object_store_azure.BlobServiceClient')
def test_upload_file_failure(mock_blob_service_client, mock_env_variables):
    # Arrange
    object_store = ObjectStoreAzure()
    mock_client_instance = mock_blob_service_client.from_connection_string.return_value
    mock_blob_client = mock_client_instance.get_blob_client.return_value
    mock_blob_client.upload_blob = MagicMock(side_effect=AzureError("Upload failed"))

    container_name = "test-container"
    blob_name = "blob.txt"
    file_path = "path/to/file.txt"

    # Mock opening a file
    with patch('builtins.open', mock_open(read_data="data")):
        # Act & Assert
        with pytest.raises(AzureError, match="Upload failed"):
            object_store.upload_file(container_name, blob_name, file_path)

@patch('backend.data_layer.object_store_azure.BlobServiceClient')
def test_download_file_success(mock_blob_service_client, mock_env_variables):
    mock_client = MagicMock()
    mock_blob_client = MagicMock()
    mock_client.get_blob_client.return_value = mock_blob_client

    # Mock the download_blob process
    mock_blob_data = MagicMock()
    mock_blob_data.readall.return_value = b"data"
    mock_blob_client.download_blob.return_value = mock_blob_data

    with patch('backend.data_layer.object_store_azure.BlobServiceClient.from_connection_string',
               return_value=mock_client), \
            patch("builtins.open", mock_open()) as mock_file:
        object_store = ObjectStoreAzure()
        object_store.download_file('container', 'blob', '/tmp/file')

        mock_client.get_blob_client.assert_called_with(container='container', blob='blob')
        mock_blob_client.download_blob.assert_called_once()
        mock_file().write.assert_called_once_with(b"data")

@patch('backend.data_layer.object_store_azure.BlobServiceClient')
def test_download_file_not_found(mock_blob_service_client, mock_env_variables):
    mock_client = MagicMock()
    mock_blob_client = MagicMock()
    mock_blob_client.download_blob.side_effect = ResourceNotFoundError("Blob not found")
    mock_client.get_blob_client.return_value = mock_blob_client

    with patch('backend.data_layer.object_store_azure.BlobServiceClient.from_connection_string',
               return_value=mock_client), \
            patch("builtins.open", mock_open()), \
            pytest.raises(ResourceNotFoundError, match="Blob not found"):
        object_store = ObjectStoreAzure()
        object_store.download_file('container', 'blob', '/tmp/file')

@patch('backend.data_layer.object_store_azure.BlobServiceClient')
def test_download_file_failure(mock_blob_service_client, mock_env_variables):
    mock_client = MagicMock()
    mock_blob_client = MagicMock()
    mock_blob_client.download_blob.side_effect = AzureError("Download failed")
    mock_client.get_blob_client.return_value = mock_blob_client

    with patch('backend.data_layer.object_store_azure.BlobServiceClient.from_connection_string',
               return_value=mock_client), \
            patch("builtins.open", mock_open()), \
            pytest.raises(AzureError, match="Download failed"):
        object_store = ObjectStoreAzure()
        object_store.download_file('container', 'blob', '/tmp/file')

@patch('backend.data_layer.object_store_azure.BlobServiceClient')
def test_list_files_success(mock_blob_service_client, mock_env_variables):
    # Mock the Azure client and container interactions
    mock_client = MagicMock()
    mock_container_client = MagicMock()

    # Create a mock blob with a name attribute
    mock_blob1 = MagicMock()
    mock_blob1.name = 'file1.txt'
    mock_blob2 = MagicMock()
    mock_blob2.name = 'file2.txt'

    # Mock list_blobs return value
    mock_container_client.list_blobs.return_value = [mock_blob1, mock_blob2]
    mock_client.get_container_client.return_value = mock_container_client

    # Use the mock client when the BlobServiceClient is initialized
    with patch('backend.data_layer.object_store_azure.BlobServiceClient.from_connection_string',
               return_value=mock_client):
        object_store = ObjectStoreAzure()
        files = object_store.list_files('container')

        # Check if the files returned match the mock setup
        assert files == ['file1.txt', 'file2.txt']
        mock_client.get_container_client.assert_called_with('container')
        mock_container_client.list_blobs.assert_called_with(name_starts_with='')


@patch('backend.data_layer.object_store_azure.BlobServiceClient')
def test_list_files_failure(mock_blob_service_client, mock_env_variables):
    # Mock the Azure client and container interactions
    mock_client = MagicMock()
    mock_container_client = MagicMock()

    # Simulate an exception when list_blobs is called
    mock_container_client.list_blobs.side_effect = Exception("fail")
    mock_client.get_container_client.return_value = mock_container_client

    # Use the mock client when the BlobServiceClient is initialized
    with patch('backend.data_layer.object_store_azure.BlobServiceClient.from_connection_string',
               return_value=mock_client):
        object_store = ObjectStoreAzure()

        # Check that an exception is raised with the expected message
        with pytest.raises(Exception, match="fail"):
            object_store.list_files('container')