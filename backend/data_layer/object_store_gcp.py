# backend/data_layer/object_store_gcp.py

import logging
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
from google.api_core.exceptions import GoogleAPIError
from dotenv import load_dotenv
from backend.common.utils import get_env_variable

load_dotenv()
logger = logging.getLogger(__name__)

# Lazy initialization for GCS client
_gcs_client = None

def get_gcs_config():
    """
    Retrieves Google Cloud Storage configuration from environment variables.
    """
    try:
        project_id = get_env_variable("GCP_PROJECT_ID")
        bucket_name = get_env_variable("GCS_BUCKET_NAME")
        return project_id, bucket_name
    except Exception as e:
        logger.error(f"Error retrieving GCS config: {e}")
        raise

def get_gcs_client():
    """
    Returns a singleton Google Cloud Storage client.
    If the client is not already created, it initializes it.
    Returns:
        gcs_client: The GCS client.
    """
    global _gcs_client
    if _gcs_client is None:
        try:
            project_id, _ = get_gcs_config()
            # Initialize the GCS client with the project ID
            _gcs_client = storage.Client(project=project_id)
        except DefaultCredentialsError as e:
            logger.error(f"Could not initialize GCS client: {e}")
            raise
    return _gcs_client

def ensure_bucket(bucket_name: str):
    """
    Ensures the bucket exists.
    If it does not exist, it creates the bucket.
    Args:
        bucket_name (str): The name of the bucket to check or create.
    """
    client = get_gcs_client()
    try:
        bucket = client.lookup_bucket(bucket_name)
        if bucket is None:
            bucket = client.create_bucket(bucket_name)
            logger.info(f"Created bucket: {bucket_name}")
    except GoogleAPIError as e:
        logger.error(f"Failed to ensure bucket: {e}")
        raise

def upload_file(bucket_name: str, object_name: str, file_path: str):
    """
    Uploads a file to the specified bucket.
    """
    client = get_gcs_client()
    ensure_bucket(bucket_name)
    try:
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_filename(file_path)
        logger.info(f"Uploaded {file_path} to {bucket_name}/{object_name}")
    except GoogleAPIError as e:
        logger.error(f"Failed to upload file: {e}")
        raise

def download_file(bucket_name: str, object_name: str, file_path: str):
    """
    Downloads a file from the specified bucket.
    """
    client = get_gcs_client()
    try:
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.download_to_filename(file_path)
        logger.info(f"Downloaded {bucket_name}/{object_name} to {file_path}")
    except GoogleAPIError as e:
        logger.error(f"Failed to download file: {e}")
        raise

def list_files(bucket_name: str, prefix: str = ""):
    """
    Lists files in the specified bucket.
    """
    client = get_gcs_client()
    try:
        bucket = client.get_bucket(bucket_name)
        return [blob.name for blob in bucket.list_blobs(prefix=prefix)]
    except GoogleAPIError as e:
        logger.error(f"Failed to list files: {e}")
        raise