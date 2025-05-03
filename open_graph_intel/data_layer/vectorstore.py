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
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024)
    ]
    schema = CollectionSchema(fields, description="Vector store for embeddings")
    collection = Collection(name=collection_name, schema=schema)
    return collection

# Insert vectors
def insert_vectors(collection_name, ids, embeddings):
    collection = Collection(collection_name)
    data = [ids, embeddings]
    collection.insert(data)

# Search vectors
def search_vectors(collection_name, query_vectors, top_k=5):
    collection = Collection(collection_name)
    search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
    results = collection.search(
        data=query_vectors,
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        expr=None
    )
    return results