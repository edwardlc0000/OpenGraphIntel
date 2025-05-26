# backend/data_layer/object_store_aws.py

import logging
from minio import Minio
from minio.error import S3Error
from backend.common.utils import get_env_variable

logger = logging.getLogger(__name__)

class ObjectStoreAWS:
    """
    A class to interact with AWS S3-compatible object storage using MinIO.
    """

    _minio_client = None

    def __init__(self):
        self.endpoint, self.access_key, self.secret_key, self.secure = self._get_minio_config()
        self._initialize_client()

    @classmethod
    def _get_minio_config(cls):
        """
        Retrieves MinIO configuration from environment variables.
        """
        try:
            endpoint = f"{get_env_variable('MINIO_FILES_HOST')}:{get_env_variable('MINIO_FILES_PORT')}"
            access_key = get_env_variable('MINIO_FILES_ROOT_USER')
            secret_key = get_env_variable('MINIO_FILES_ROOT_PASSWORD')
            secure = False  # Set to True if using HTTPS
            return endpoint, access_key, secret_key, secure
        except Exception as e:
            logger.error(f"Error retrieving MinIO config: {e}")
            raise

    def _initialize_client(self) -> None:
        """
        Initializes the MinIO client with the provided configuration.
        """
        if self._minio_client is None:
            self._minio_client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )

    @property
    def client(self) -> Minio:
        """
        Returns the MinIO client.
        """
        if self._minio_client is None:
            self._initialize_client()
        return self._minio_client

    def ensure_bucket(self, bucket_name: str) -> None:
        """
        Ensures the bucket exists. If it does not exist, it creates the bucket.
        Args:
            bucket_name (str): The name of the bucket to check or create.
        """
        found = self.client.bucket_exists(bucket_name)
        if not found:
            self.client.make_bucket(bucket_name)
            logger.info(f"Created bucket: {bucket_name}")

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
            self.client.fput_object(bucket_name, object_name, file_path)
            logger.info(f"Uploaded {file_path} to {bucket_name}/{object_name}")
        except S3Error as e:
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
            self.client.fget_object(bucket_name, object_name, file_path)
            logger.info(f"Downloaded {bucket_name}/{object_name} to {file_path}")
        except S3Error as e:
            logger.error(f"Failed to download file: {e}")
            raise

    def list_files(self, bucket_name: str, prefix: str = "") -> list[str]:
        """
        Lists files in the specified bucket.
        Args:
            bucket_name (str): The name of the bucket to list files from.
            prefix (str): Optional prefix to filter the listed files.
        """
        try:
            return [obj.object_name for obj in self.client.list_objects(bucket_name, prefix=prefix, recursive=True)]
        except S3Error as e:
            logger.error(f"Failed to list files: {e}")
            raise