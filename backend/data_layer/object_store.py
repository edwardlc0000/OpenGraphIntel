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

def get_objectstore_module() -> str:
    """
    This function dynamically imports the appropriate object store module based on the cloud environment.
    It checks for an environment variable override and defaults to using the detected environment.
    """
    if os.getenv("CLOUD_ENV_OVERRIDE") is not None:
        return os.getenv("CLOUD_ENV_OVERRIDE").lower()
    else:
        return detect_env().lower()

def get_objectstore() -> None:
    """
    This function returns the object store module based on the cloud environment.
    It raises an error if the cloud environment is unknown.
    """
    cloud_env = get_objectstore_module()

    # Log the detected cloud environment
    logger.info(f"Detected cloud environment: {cloud_env}")

    # Dynamically import the appropriate object store module
    if "aws" in cloud_env:
        objectstore = importlib.import_module('backend.data_layer.objectstore_aws')
    elif "azure" in cloud_env:
        objectstore = importlib.import_module('backend.data_layer.objectstore_azure')
    elif "gcp" in cloud_env:
        objectstore = importlib.import_module('backend.data_layer.objectstore_gcp')
    elif "unknown" in cloud_env:
        logger.error("Unknown cloud environment. Please check your configuration.")
        raise RuntimeError("Unknown cloud environment. Please check your configuration.")
