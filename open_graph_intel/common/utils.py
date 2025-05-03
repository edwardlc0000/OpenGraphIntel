# open_graph_intel/common/utils.py

import os
import logging
from typing import Final
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def get_env_variable(var_name: str) -> Final[str]:
    """
    Retrieve an environment variable value.
    
    Args:
        var_name (str): The name of the environment variable.
    
    Returns:
        str: The value of the environment variable.
    """
    value: str = os.getenv(var_name)
    if value is None:
        logger.error(f"Environment variable {var_name} not found.")
        raise ValueError(f"Environment variable {var_name} not found.")

    logger.info(f"Environment variable {var_name} retrieved successfully.")
    return value