# backend/data_layer/object_store_gcp.py

import logging
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
from google.api_core.exceptions import GoogleAPIError
from dotenv import load_dotenv
from backend.common.utils import get_env_variable

load_dotenv()
logger = logging.getLogger(__name__)

class ObjectStoreGCP:
    """
    A class to interact with Google Cloud Storage.
    """

    _gcs_client = None

    def __init__(self):
        self.project_id, self.bucket_name = self._get_gcs_config()
        self._initialize_client()

    @classmethod
    def _get_gcs_config(cls):
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

    def _initialize_client(self):
        """
        Initializes the GCS client if not already done.
        """
        if self._gcs_client is None:
            try:
                self._gcs_client = storage.Client(project=self.project_id)
            except DefaultCredentialsError as e:
                logger.error(f"Could not initialize GCS client: {e}")
                raise

    @property
    def client(self):
        """
        Returns the GCS client.
        """
        if self._gcs_client is None:
            self._initialize_client()
        return self._gcs_client

    def ensure_bucket(self, bucket_name: str) -> None:
        """
        Ensures the bucket exists. If it does not exist, it creates the bucket.
        Args:
            bucket_name (str): The name of the bucket to ensure.
        """
        try:
            bucket = self.client.lookup_bucket(bucket_name)
            if bucket is None:
                self.client.create_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
        except GoogleAPIError as e:
            logger.error(f"Failed to ensure bucket: {e}")
            raise

    def upload_file(self, bucket_name: str, object_name: str, file_path: str) -> None:
        """
        Uploads a file to the specified bucket.
        Args:
            bucket_name (str): The name of the bucket to upload to.
            object_name (str): The name of the object in the bucket.
            file_path (str): The local path of the file to upload.
        """
        self.ensure_bucket(bucket_name)
        try:
            bucket = self.client.get_bucket(bucket_name)
            blob = bucket.blob(object_name)
            blob.upload_from_filename(file_path)
            logger.info(f"Uploaded {file_path} to {bucket_name}/{object_name}")
        except GoogleAPIError as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    def download_file(self, bucket_name: str, object_name: str, file_path: str) -> None:
        """
        Downloads a file from the specified bucket.
        Args:
            bucket_name (str): The name of the bucket to download from.
            object_name (str): The name of the object to download.
            file_path (str): The local path where the file will be saved.
        """
        try:
            bucket = self.client.get_bucket(bucket_name)
            blob = bucket.blob(object_name)
            blob.download_to_filename(file_path)
            logger.info(f"Downloaded {bucket_name}/{object_name} to {file_path}")
        except GoogleAPIError as e:
            logger.error(f"Failed to download file: {e}")
            raise

    def list_files(self, bucket_name: str, prefix: str = "") -> list[str]:
        """
        Lists files in the specified bucket.
        Args:
            bucket_name (str): The name of the bucket to list files from.
            prefix (str): Optional prefix to filter the files.
        """
        try:
            bucket = self.client.get_bucket(bucket_name)
            return [blob.name for blob in bucket.list_blobs(prefix=prefix)]
        except GoogleAPIError as e:
            logger.error(f"Failed to list files: {e}")
            raise