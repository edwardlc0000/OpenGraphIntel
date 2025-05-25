# tests/test_vector_store.py

import pytest
from unittest.mock import patch, MagicMock
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
import backend.data_layer.vector_store as vector_store

@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global variables before each test."""
    vector_store._milvus_host = None
    vector_store._milvus_grpc_port = None
    pass

# Test get_milvus_config
@patch("backend.data_layer.vector_store.get_env_variable")
def test_get_milvus_config(mock_get_env_variable):
    # Mock environment variables
    mock_get_env_variable.side_effect = lambda key: "mock_host" if key == "MILVUS_HOST" else "mock_port"

    host, port = vector_store.get_milvus_config()

    assert host == "mock_host"
    assert port == "mock_port"
    mock_get_env_variable.assert_any_call("MILVUS_HOST")
    mock_get_env_variable.assert_any_call("MILVUS_GRPC_PORT")

@patch("backend.data_layer.vector_store.get_env_variable")
def test_get_milvus_config_fail(mock_get_env_variable):
    # Simulate missing environment variable
    mock_get_env_variable.side_effect = ValueError("Environment variable not found")

    with pytest.raises(ValueError, match="Environment variable not found"):
        vector_store.get_milvus_config()

# Test connect_to_milvus
@patch("backend.data_layer.vector_store.connections")
@patch("backend.data_layer.vector_store.get_milvus_config")
def test_connect_to_milvus(mock_get_milvus_config, mock_connections):
    # Mock Milvus connection
    mock_get_milvus_config.return_value = ("mock_host", "mock_port")
    mock_connections.has_connection.return_value = False

    vector_store.connect_to_milvus()

    mock_get_milvus_config.assert_called_once()
    mock_connections.connect.assert_called_once_with(host="mock_host", port="mock_port")
    mock_connections.has_connection.assert_called_once_with("default")

@patch("backend.data_layer.vector_store.connections")
@patch("backend.data_layer.vector_store.get_milvus_config")
def test_connect_to_milvus_with_existing_connection(mock_get_milvus_config, mock_connections):
    # Mock Milvus connection
    mock_get_milvus_config.return_value = ("mock_host", "mock_port")
    mock_connections.has_connection.return_value = False

    vector_store.connect_to_milvus()
    vector_store.connect_to_milvus()  # Call again to check for existing connection

    mock_get_milvus_config.assert_called_once()
    mock_connections.connect.assert_called_with(host="mock_host", port="mock_port")
    mock_connections.has_connection.assert_called_with("default")

@patch("backend.data_layer.vector_store.connections")
@patch("backend.data_layer.vector_store.get_milvus_config")
def test_connect_to_milvus_already_connected(mock_get_milvus_config, mock_connections):
    # Simulate that the connection already exists
    mock_get_milvus_config.return_value = ("mock_host", "mock_port")
    mock_connections.has_connection.return_value = True

    # Call the function
    import backend.data_layer.vector_store as vector_store
    vector_store._milvus_host = None
    vector_store._milvus_grpc_port = None
    vector_store.connect_to_milvus()

    # Should not call connect
    mock_connections.connect.assert_not_called()
    # Should call has_connection
    mock_connections.has_connection.assert_called_once_with("default")


@patch("backend.data_layer.vector_store.get_milvus_config")
@patch("backend.data_layer.vector_store.connections")
def test_connect_to_milvus_failure(mock_connections, mock_get_milvus_config):
    # Mock Milvus connection failure
    mock_get_milvus_config.return_value = ("mock_host", "mock_port")
    mock_connections.has_connection.return_value = False
    mock_connections.connect.side_effect = Exception("Connection failed")
    with pytest.raises(RuntimeError, match="Failed to connect to Milvus."):
        vector_store.connect_to_milvus()
    mock_connections.connect.assert_called_once_with(
        host="mock_host", port="mock_port")
    mock_connections.has_connection.assert_called_once_with("default")

# Test create_collection
@patch("backend.data_layer.vector_store.Collection")
@patch("backend.data_layer.vector_store.connect_to_milvus")
@patch("backend.data_layer.vector_store.CollectionSchema")
@patch("backend.data_layer.vector_store.FieldSchema")
def test_create_collection(mock_field_schema, mock_collection_schema, mock_connect_to_milvus, mock_collection):
    # Predefine consistent MagicMock objects for FieldSchema
    field_id_mock = MagicMock(name="FieldSchema(id)")
    field_embedding_mock = MagicMock(name="FieldSchema(embedding)")

    # Configure the FieldSchema mock to return the predefined objects
    mock_field_schema.side_effect = lambda name, dtype, is_primary=False, auto_id=False, dim=None: (
        field_id_mock if name == "id" else field_embedding_mock
    )

    # Mock CollectionSchema to return a MagicMock object
    mock_collection_schema.return_value = MagicMock()

    # Mock collection creation
    mock_collection.return_value = MagicMock()

    collection_name = "test_collection"
    collection = vector_store.create_collection(collection_name)

    # Assert that connect_to_milvus is called
    mock_connect_to_milvus.assert_called_once()

    # Assert that FieldSchema is called with correct parameters
    mock_field_schema.assert_any_call(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False)
    mock_field_schema.assert_any_call(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024)

    # Assert that CollectionSchema is created with the correct fields
    expected_fields = [field_id_mock, field_embedding_mock]
    mock_collection_schema.assert_called_once_with(expected_fields, description="Vector store for embeddings")

    # Assert that Collection is created with the correct name and schema
    mock_collection.assert_called_once_with(
        name=collection_name,
        schema=mock_collection_schema.return_value
    )

    # Assert that the returned collection is not None
    assert collection is not None

@patch("backend.data_layer.vector_store.Collection")
@patch("backend.data_layer.vector_store.connect_to_milvus")
@patch("backend.data_layer.vector_store.CollectionSchema")
@patch("backend.data_layer.vector_store.FieldSchema")
def test_create_collection_failure(mock_field_schema, mock_collection_schema, mock_connect_to_milvus, mock_collection):
    # Mock Milvus connection
    mock_connect_to_milvus.return_value = None
    # Mock Collection creation to raise an exception
    mock_collection.side_effect = Exception("Collection creation failed")
    collection_name = "test_collection"
    with pytest.raises(Exception, match="Collection creation failed"):
        vector_store.create_collection(collection_name)
    # Assert that connect_to_milvus is called
    mock_connect_to_milvus.assert_called_once()
    # Assert that Collection is attempted to be created
    mock_collection.assert_called_once_with(
        name=collection_name, schema=mock_collection_schema.return_value)

# Test insert_vectors
@patch("backend.data_layer.vector_store.Collection")
@patch("backend.data_layer.vector_store.connect_to_milvus")
def test_insert_vectors(mock_connect_to_milvus, mock_collection):
    # Mock vector insertion
    mock_collection.exists.return_value = False
    mock_collection.return_value = MagicMock()

    collection_name = "test_collection"
    ids = [1, 2, 3]
    embeddings = [[0.1] * 1024, [0.2] * 1024, [0.3] * 1024]

    vector_store.insert_vectors(collection_name, ids, embeddings)

    # Verify that connect_to_milvus is called (but not necessarily only once)
    assert mock_connect_to_milvus.call_count > 0

    # Verify that the collection is checked for existence
    mock_collection.exists.assert_called_once_with(collection_name)

    # Verify that the vectors are inserted
    mock_collection.return_value.insert.assert_called_once_with([ids, embeddings])

    # Verify that the collection is flushed
    mock_collection.return_value.flush.assert_called_once()

@patch("backend.data_layer.vector_store.Collection")
@patch("backend.data_layer.vector_store.connect_to_milvus")
def test_insert_vectors_failure(mock_connect_to_milvus, mock_collection):
    # Mock collection existence and instance
    mock_collection.exists.return_value = True
    collection_instance = MagicMock()
    collection_instance.insert.side_effect = Exception("Insertion failed")
    mock_collection.return_value = collection_instance

    collection_name = "test_collection"
    ids = [1, 2, 3]
    embeddings = [[0.1] * 1024, [0.2] * 1024, [0.3] * 1024]

    with pytest.raises(Exception, match="Insertion failed"):
        vector_store.insert_vectors(collection_name, ids, embeddings)

    mock_connect_to_milvus.assert_called_once()
    mock_collection.exists.assert_called_once_with(collection_name)
    collection_instance.insert.assert_called_once_with([ids, embeddings])
    collection_instance.flush.assert_called_once()

# Test search_vectors
@patch("backend.data_layer.vector_store.Collection")
@patch("backend.data_layer.vector_store.connect_to_milvus")
def test_search_vectors(mock_connect_to_milvus, mock_collection):
    # Mock vector search
    mock_collection.return_value = MagicMock()
    mock_collection.return_value.search.return_value = "mock_results"

    collection_name = "test_collection"
    query_vectors = [[0.1] * 1024]
    top_k = 5

    results = vector_store.search_vectors(collection_name, query_vectors, top_k)

    mock_connect_to_milvus.assert_called_once()
    mock_collection.assert_called_once_with(collection_name)
    mock_collection.return_value.search.assert_called_once_with(
        data=query_vectors,
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"nprobe": 10}},
        limit=top_k,
        expr=None
    )
    assert results == "mock_results"

@patch("backend.data_layer.vector_store.Collection")
@patch("backend.data_layer.vector_store.connect_to_milvus")
def test_search_vectors_failure(mock_connect_to_milvus, mock_collection):
    # Mock collection instance and make search raise an exception
    collection_instance = MagicMock()
    collection_instance.search.side_effect = Exception("Search failed")
    mock_collection.return_value = collection_instance

    collection_name = "test_collection"
    query_vectors = [[0.1] * 1024]
    top_k = 5

    with pytest.raises(Exception, match="Search failed"):
        vector_store.search_vectors(collection_name, query_vectors, top_k)

    mock_connect_to_milvus.assert_called_once()
    mock_collection.assert_called_once_with(collection_name)
    collection_instance.search.assert_called_once_with(
        data=query_vectors,
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"nprobe": 10}},
        limit=top_k,
        expr=None
    )

