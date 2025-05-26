# backend/data_layer/object_store.py

# Import dependencies
import logging
import importlib

# Import custom modules
from backend.common.cloud_env import detect_env

# Configure logging
logger = logging.getLogger(__name__)

# Import environment variables
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

_object_store_instance = None

class ObjectStore:
    """
    A factory class to get an instance of the appropriate object store based on the cloud environment.
    """
    @staticmethod
    def get_object_store() -> object:
        """
        This function dynamically imports the appropriate object store module based on the cloud environment.
        It checks for an environment variable override and defaults to using the detected environment.
        Returns:
            object: An instance of the object store class for the detected cloud environment.
        """
        global _object_store_instance
        if _object_store_instance is None:
            if os.getenv("CLOUD_ENV_OVERRIDE") is not None:
                cloud_env = os.getenv("CLOUD_ENV_OVERRIDE")
            else:
                cloud_env = detect_env().lower()
            logger.info(f"Detected cloud environment: {cloud_env}")

            if "aws" in cloud_env:
                module_name = "backend.data_layer.object_store_aws"
                class_name = "ObjectStoreAWS"
            elif "azure" in cloud_env:
                module_name = "backend.data_layer.object_store_azure"
                class_name = "ObjectStoreAzure"
            elif "gcp" in cloud_env:
                module_name = "backend.data_layer.object_store_gcp"
                class_name = "ObjectStoreGCP"
            else:
                raise RuntimeError(f"Unsupported cloud environment: {cloud_env}")

            logger.info(f"Importing module {module_name}.{class_name}")
            module = importlib.import_module(module_name)
            object_store_class = getattr(module, class_name)
            _object_store_instance = object_store_class()
        return _object_store_instance