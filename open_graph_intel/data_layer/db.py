#open_graph_intel/data_layer/db.py

# Import dependencies
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Final

# Import custom modules
from open_graph_intel.common.utils import get_env_variable

# Configure logging
logger = logging.getLogger(__name__)

# Import environment variables
import os
from dotenv import load_dotenv

load_dotenv()

# Retrieve the environment variables with detailed error information
try:
    DB_NAME: Final[str] = get_env_variable("POSTGRES_DB")
    USER: Final[str] = get_env_variable("POSTGRES_USER")
    PASSWORD: Final[str] = get_env_variable("POSTGRES_PASSWORD")
    HOST: Final[str] = get_env_variable("POSTGRES_HOST")
    PORT: Final[str] = get_env_variable("POSTGRES_PORT")
except ValueError as e:
    logger.error(f"Error retrieving environment variables: {e}")
    raise

# Construct the PostgreSQL URL
DATABASE_URL: Final[str] = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

# Create the database engine
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("Database engine created successfully.")
except Exception as e:
    logger.error(f"Error creating database engine: {e}")
    raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
