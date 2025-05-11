# open_graph_intel/data_layer/vectorstore.py

# Import dependencies
import logging
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
from typing import Final

# Import custom modules
from open_graph_intel.common.utils import get_env_variable

# Configure logging
logger = logging.getLogger(__name__)

# Import environment variables
import os
from dotenv import load_dotenv

load_dotenv()

# Cache for the Milvus host and port
_milvus_host = None
_milvus_grpc_port = None

# Lazy initialization for the Milvus host and port
def get_milvus_config() -> tuple[str, str]:
    """
    Retrieves the Milvus host and port from environment variables.
    Returns:
        tuple: A tuple containing the Milvus host and port.
    """
    try:
        MILVUS_HOST = get_env_variable("MILVUS_HOST")
        MILVUS_GRPC_PORT = get_env_variable("MILVUS_GRPC_PORT")
        return MILVUS_HOST, MILVUS_GRPC_PORT
    except ValueError as e:
        logger.error(f"Error retrieving environment variables: {e}")
        raise

# Lazy initialization of the Milvus host and port
def connect_to_milvus() -> None:
    """
    Connects to the Milvus server using the host and port from environment variables.
    """
    global _milvus_host, _milvus_grpc_port
    if _milvus_host is None or _milvus_grpc_port is None:
        _milvus_host, _milvus_grpc_port = get_milvus_config()
    if not connections.has_connection("default"):
        try:
            connections.connect(host=_milvus_host, port=_milvus_grpc_port)
            logger.info(f"Connected to Milvus at {_milvus_host}:{_milvus_grpc_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus at {_milvus_host}:{_milvus_grpc_port}")
            raise RuntimeError("Failed to connect to Milvus.")
    else:
        logger.info("Already connected to Milvus.")

# Define a collection schema
def create_collection(collection_name) -> Collection:
    """
    Create a collection in Milvus with the specified schema.
    Args:
        collection_name (str): The name of the collection to create.
    """
    connect_to_milvus()  # Ensure connection to Milvus
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024)
    ]
    schema = CollectionSchema(fields, description="Vector store for embeddings")
    collection = Collection(name=collection_name, schema=schema)
    logger.info(f"Collection {collection_name} created with schema: {schema}")
    return collection

# Insert vectors
def insert_vectors(collection_name, ids, embeddings) -> None:
    """
    Insert vectors into the specified collection.
    Args:
        collection_name (str): The name of the collection.
        ids (list): A list of IDs for the vectors.
        embeddings (list): A list of embeddings to insert.
    """
    connect_to_milvus()  # Ensure connection to Milvus
    if not Collection.exists(collection_name):
        create_collection(collection_name)

    collection = Collection(collection_name)
    data = [ids, embeddings]

    try:
        collection.insert(data)
        logger.info(f"Inserted {len(ids)} vectors into collection {collection_name}.")
    except Exception as e:
        logger.error(f"Error inserting vectors: {e}")
        raise
    finally:
        collection.flush()
        logger.info(f"Flushed collection {collection_name}.")

# Search vectors
def search_vectors(collection_name, query_vectors, top_k=5):
    """
    Search for similar vectors in the specified collection.
    Args:
        collection_name (str): The name of the collection.
        query_vectors (list): A list of query vectors to search for.
        top_k (int): The number of top results to return.
    """
    connect_to_milvus()  # Ensure connection to Milvus
    collection = Collection(collection_name)
    search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

    try:
        results = collection.search(
            data=query_vectors,
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=None
        )        
        logger.info(f"Search completed in collection {collection_name}.")
        return results
    except Exception as e:
        logger.error(f"Error searching vectors: {e}")
        raise