# backend/data_layer/objectstore_azure.py

import logging
import os
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from dotenv import load_dotenv
from backend.common.utils import get_env_variable

load_dotenv()
logger = logging.getLogger(__name__)

_blob_service_client = None

def get_azure_blob_config():
    """
    Retrieves Azure Blob Storage configuration from environment variables.
    """
    try:
        # For Azurite, use the default connection string if not set
        conn_str = get_env_variable(
            "AZURE_BLOB_CONNECTION_STRING",
            "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFeqCnf2P==;BlobEndpoint=http://azurite:10000/devstoreaccount1;"
        )
        return conn_str
    except Exception as e:
        logger.error(f"Error retrieving Azure Blob config: {e}")
        raise

def get_blob_service_client():
    """
    Returns a singleton Azure BlobServiceClient.
    """
    global _blob_service_client
    if _blob_service_client is None:
        conn_str = get_azure_blob_config()
        _blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    return _blob_service_client

def ensure_container(container_name: str):
    """
    Ensures the container exists.
    """
    client = get_blob_service_client()
    try:
        client.create_container(container_name)
        logger.info(f"Created container: {container_name}")
    except ResourceExistsError:
        pass

def upload_file(container_name: str, blob_name: str, file_path: str):
    """
    Uploads a file to the specified container.
    """
    client = get_blob_service_client()
    ensure_container(container_name)
    try:
        with open(file_path, "rb") as data:
            client.get_blob_client(container=container_name, blob=blob_name).upload_blob(data, overwrite=True)
        logger.info(f"Uploaded {file_path} to {container_name}/{blob_name}")
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise

def download_file(container_name: str, blob_name: str, file_path: str):
    """
    Downloads a file from the specified container.
    """
    client = get_blob_service_client()
    try:
        blob_client = client.get_blob_client(container=container_name, blob=blob_name)
        with open(file_path, "wb") as file:
            data = blob_client.download_blob()
            file.write(data.readall())
        logger.info(f"Downloaded {container_name}/{blob_name} to {file_path}")
    except ResourceNotFoundError:
        logger.error(f"Blob {blob_name} not found in container {container_name}")
        raise
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        raise

def list_files(container_name: str, prefix: str = ""):
    """
    Lists blobs in the specified container.
    """
    client = get_blob_service_client()
    try:
        container_client = client.get_container_client(container_name)
        return [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise
