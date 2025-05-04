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

# Retrieve the environment variables with detailed error information
try:
    MILVUS_HOST: Final[str] = get_env_variable("MILVUS_HOST")
    MILVUS_GRPC_PORT: Final[str] = get_env_variable("MILVUS_GRPC_PORT")
except ValueError as e:
    logger.error(f"Error retrieving environment variables: {e}")
    raise

# Connect to Milvus
connections.connect(host=MILVUS_HOST, port=MILVUS_GRPC_PORT)

# Define a collection schema
def create_collection(collection_name):
    """
    Create a collection in Milvus with the specified schema.
    Args:
        collection_name (str): The name of the collection to create.
    """
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024)
    ]
    schema = CollectionSchema(fields, description="Vector store for embeddings")
    collection = Collection(name=collection_name, schema=schema)
    return collection

# Insert vectors
def insert_vectors(collection_name, ids, embeddings):
    """
    Insert vectors into the specified collection.
    Args:
        collection_name (str): The name of the collection.
        ids (list): A list of IDs for the vectors.
        embeddings (list): A list of embeddings to insert.
    """
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
        logger.info(f"Flushed collection {collection_name} after insertion.")

# Search vectors
def search_vectors(collection_name, query_vectors, top_k=5):
    """
    Search for similar vectors in the specified collection.
    Args:
        collection_name (str): The name of the collection.
        query_vectors (list): A list of query vectors to search for.
        top_k (int): The number of top results to return.
    """
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
    except Exception as e:
        logger.error(f"Error searching vectors: {e}")
        raise
    finally:
        logger.info(f"Search completed in collection {collection_name}.")

    return results