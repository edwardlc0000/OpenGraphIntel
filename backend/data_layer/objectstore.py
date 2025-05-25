# backend/data_layer/objectstore.py

# Import dependencies
import logging

# Import custom modules
from backend.common.cloud_env import detect_env

# Configure logging
logger = logging.getLogger(__name__)

# Import environment variables
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

cloud_env: str = os.getenv("CLOUD_ENV_OVERRIDE", default=detect_env()).lower()

try:
    if "aws" in cloud_env:
        import backend.data_layer.objectstore_aws
    elif "azure" in cloud_env:
        import backend.data_layer.objectstore_azure
    elif "gcp" in cloud_env:
        import backend.data_layer.objectstore_gcp
    elif "unknown" in cloud_env:
        logger.error("Unknown cloud environment. Please check your configuration.")
        raise RuntimeError("Unknown cloud environment. Please check your configuration.")
except RuntimeError:
    logger.error("Error importing object store module. Please check your cloud environment configuration.")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
