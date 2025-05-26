# backend/data_layer/object_store_azure.py

import logging
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from backend.common.utils import get_env_variable

logger = logging.getLogger(__name__)

class ObjectStoreAzure:
    """
    A class to interact with Azure Blob Storage.
    """

    _blob_service_client = None

    def __init__(self):
        self.connection_string = self._get_azure_blob_config()
        self._initialize_client()

    @classmethod
    def _get_azure_blob_config(cls):
        """
        Retrieves Azure Blob Storage configuration from environment variables.
        """
        try:
            conn_str = get_env_variable("AZURE_BLOB_CONNECTION_STRING")
            return conn_str
        except Exception as e:
            logger.error(f"Error retrieving Azure Blob config: {e}")
            raise

    def _initialize_client(self):
        """
        Initializes the BlobServiceClient.
        """
        if self._blob_service_client is None:
            self._blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)

    @property
    def client(self):
        """
        Returns the BlobServiceClient.
        """
        if self._blob_service_client is None:
            self._initialize_client()
        return self._blob_service_client

    def ensure_container(self, container_name: str) -> None:
        """
        Ensures the container exists.
        Args:
            container_name (str): The name of the container to ensure.
        """
        try:
            self.client.create_container(container_name)
            logger.info(f"Created container: {container_name}")
        except ResourceExistsError:
            pass

    def upload_file(self, container_name: str, blob_name: str, file_path: str) -> None:
        """
        Uploads a file to the specified container.
        Args:
            container_name (str): The name of the container to upload to.
            blob_name (str): The name of the blob in the container.
            file_path (str): The local path of the file to upload.
        """
        self.ensure_container(container_name)
        try:
            with open(file_path, "rb") as data:
                self.client.get_blob_client(container=container_name, blob=blob_name).upload_blob(data, overwrite=True)
            logger.info(f"Uploaded {file_path} to {container_name}/{blob_name}")
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    def download_file(self, container_name: str, blob_name: str, file_path: str) -> None:
        """
        Downloads a file from the specified container.
        Args:
            container_name (str): The name of the container to download from.
            blob_name (str): The name of the blob in the container.
            file_path (str): The local path where the file will be saved.
        """
        try:
            blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
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

    def list_files(self, container_name: str, prefix: str = "") -> list[str]:
        """
        Lists blobs in the specified container.
        Args:
            container_name (str): The name of the container to list blobs from.
            prefix (str): Optional prefix to filter the listed blobs.
        """
        try:
            container_client = self.client.get_container_client(container_name)
            return [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise