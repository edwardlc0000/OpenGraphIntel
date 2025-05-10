# tests/test_vectorstore.py

import pytest
from unittest.mock import patch, MagicMock
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
from open_graph_intel.data_layer.vectorstore import (
    get_milvus_config,
    connect_to_milvus,
    create_collection,
    insert_vectors,
    search_vectors,
)

# Test get_milvus_config
@patch("open_graph_intel.data_layer.vectorstore.get_env_variable")
def test_get_milvus_config(mock_get_env_variable):
    # Mock environment variables
    mock_get_env_variable.side_effect = lambda key: "mock_host" if key == "MILVUS_HOST" else "mock_port"
    
    host, port = get_milvus_config()
    
    assert host == "mock_host"
    assert port == "mock_port"
    mock_get_env_variable.assert_any_call("MILVUS_HOST")
    mock_get_env_variable.assert_any_call("MILVUS_GRPC_PORT")

@patch("open_graph_intel.data_layer.vectorstore.get_env_variable")
def test_get_milvus_config_fail(mock_get_env_variable):
    # Simulate missing environment variable
    mock_get_env_variable.side_effect = ValueError("Environment variable not found")
    
    with pytest.raises(ValueError, match="Environment variable not found"):
        get_milvus_config()

# Test connect_to_milvus
@patch("open_graph_intel.data_layer.vectorstore.connections")
@patch("open_graph_intel.data_layer.vectorstore.get_milvus_config")
def test_connect_to_milvus(mock_get_milvus_config, mock_connections):
    # Mock Milvus connection
    mock_get_milvus_config.return_value = ("mock_host", "mock_port")
    mock_connections.has_connection.return_value = False
    
    connect_to_milvus()
    
    mock_get_milvus_config.assert_called_once()
    mock_connections.connect.assert_called_once_with(host="mock_host", port="mock_port")
    mock_connections.has_connection.assert_called_once_with("default")

# Test create_collection
@patch("open_graph_intel.data_layer.vectorstore.Collection")
@patch("open_graph_intel.data_layer.vectorstore.connect_to_milvus")
@patch("open_graph_intel.data_layer.vectorstore.CollectionSchema")
@patch("open_graph_intel.data_layer.vectorstore.FieldSchema")
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
    collection = create_collection(collection_name)

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

# Test insert_vectors
@patch("open_graph_intel.data_layer.vectorstore.Collection")
@patch("open_graph_intel.data_layer.vectorstore.connect_to_milvus")
def test_insert_vectors(mock_connect_to_milvus, mock_collection):
    # Mock vector insertion
    mock_collection.exists.return_value = False
    mock_collection.return_value = MagicMock()
    
    collection_name = "test_collection"
    ids = [1, 2, 3]
    embeddings = [[0.1] * 1024, [0.2] * 1024, [0.3] * 1024]
    
    insert_vectors(collection_name, ids, embeddings)
    
    # Verify that connect_to_milvus is called (but not necessarily only once)
    assert mock_connect_to_milvus.call_count > 0

    # Verify that the collection is checked for existence
    mock_collection.exists.assert_called_once_with(collection_name)

    # Verify that the vectors are inserted
    mock_collection.return_value.insert.assert_called_once_with([ids, embeddings])

    # Verify that the collection is flushed
    mock_collection.return_value.flush.assert_called_once()

# Test search_vectors
@patch("open_graph_intel.data_layer.vectorstore.Collection")
@patch("open_graph_intel.data_layer.vectorstore.connect_to_milvus")
def test_search_vectors(mock_connect_to_milvus, mock_collection):
    # Mock vector search
    mock_collection.return_value = MagicMock()
    mock_collection.return_value.search.return_value = "mock_results"
    
    collection_name = "test_collection"
    query_vectors = [[0.1] * 1024]
    top_k = 5
    
    results = search_vectors(collection_name, query_vectors, top_k)
    
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

