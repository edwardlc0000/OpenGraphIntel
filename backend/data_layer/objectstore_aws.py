# backend/data_layer/blobstore.py

import logging
import os
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
from backend.common.utils import get_env_variable

load_dotenv()
logger = logging.getLogger(__name__)

# Lazy initialization for MinIO client
_minio_client = None

def get_minio_config():
    """
    Retrieves MinIO configuration from environment variables.
    """
    try:
        endpoint = f"{get_env_variable('MINIO_FILES_HOST', 'minio-files')}:{get_env_variable('MINIO_FILES_PORT')}"
        access_key = get_env_variable('MINIO_FILES_ROOT_USER')
        secret_key = get_env_variable('MINIO_FILES_ROOT_PASSWORD')
        secure = False  # Set to True if using HTTPS
        return endpoint, access_key, secret_key, secure
    except Exception as e:
        logger.error(f"Error retrieving MinIO config: {e}")
        raise

def get_minio_client():
    """
    Returns a singleton MinIO client.
    """
    global _minio_client
    if _minio_client is None:
        endpoint, access_key, secret_key, secure = get_minio_config()
        _minio_client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    return _minio_client

def ensure_bucket(bucket_name: str):
    """
    Ensures the bucket exists.
    """
    client = get_minio_client()
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)
        logger.info(f"Created bucket: {bucket_name}")

def upload_file(bucket_name: str, object_name: str, file_path: str):
    """
    Uploads a file to the specified bucket.
    """
    client = get_minio_client()
    ensure_bucket(bucket_name)
    try:
        client.fput_object(bucket_name, object_name, file_path)
        logger.info(f"Uploaded {file_path} to {bucket_name}/{object_name}")
    except S3Error as e:
        logger.error(f"Failed to upload file: {e}")
        raise

def download_file(bucket_name: str, object_name: str, file_path: str):
    """
    Downloads a file from the specified bucket.
    """
    client = get_minio_client()
    try:
        client.fget_object(bucket_name, object_name, file_path)
        logger.info(f"Downloaded {bucket_name}/{object_name} to {file_path}")
    except S3Error as e:
        logger.error(f"Failed to download file: {e}")
        raise

def list_files(bucket_name: str, prefix: str = ""):
    """
    Lists files in the specified bucket.
    """
    client = get_minio_client()
    try:
        return [obj.object_name for obj in client.list_objects(bucket_name, prefix=prefix, recursive=True)]
    except S3Error as e:
        logger.error(f"Failed to list files: {e}")
        raise
