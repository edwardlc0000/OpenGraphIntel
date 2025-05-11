#open_graph_intel/data_layer/database.py

# Import dependencies
import logging
from typing import Generator
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, declarative_base
from typing import Final

# Import custom modules
from open_graph_intel.common.utils import get_env_variable

# Configure logging
logger = logging.getLogger(__name__)

# Import environment variables
import os
from dotenv import load_dotenv

load_dotenv()

# Cache for the engine and session
_session_factory = None
_engine = None

# Lazy initialization for the database URL
def construct_postgres_url() -> str:
    """
    Constructs the PostgreSQL URL from environment variables.
    Returns:
        str: The PostgreSQL URL.
    """
    try:
        DB_NAME = get_env_variable("POSTGRES_DB")
        USER = get_env_variable("POSTGRES_USER")
        PASSWORD = get_env_variable("POSTGRES_PASSWORD")
        HOST = get_env_variable("POSTGRES_HOST")
        PORT = get_env_variable("POSTGRES_PORT")
        return f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
    except ValueError as e:
        logger.error(f"Error retrieving environment variables: {e}")
        raise

# Lazy intialization of the database engine
def construct_engine(database_url: str = None, retries: int = 5) -> Engine:
    """
    Creates a database engine with retry logic.
    Args:
        database_url (str): The database URL.
        retries (int): Number of retries for creating the engine.
    Returns:
        engine: The SQLAlchemy engine.
    """
    global _engine
    if _engine is None:
        if database_url is None:
            database_url = construct_postgres_url()
        for i in range(retries):
            try:
                _engine = create_engine(database_url)
                logger.info(f"Database engine created successfully: {database_url.split('@')[0]}")
                return _engine
            except Exception as e:
                logger.error(f"Error creating database engine: {e}")
                if i <= retries - 1:
                    logger.info(f"Retrying to create database engine... ({i + 1}/{retries})")
        logger.error(f"Failed to create database engine after {retries} retries.")
        raise RuntimeError("Failed to create database engine.")
    return _engine

def construct_session(engine: Engine = None) -> Session:
    """
    Creates a session for the database.
    Args:
        engine: The SQLAlchemy engine.
    Returns:
        SessionLocal: The session factory.
    """
    global _session_factory
    if _session_factory is None:
        logger.info("Creating a new session factory.")
        if engine is None:
            engine = construct_engine()
        _session_factory = sessionmaker(autocommit=False,
                                        autoflush=False,
                                        bind=engine)
    return _session_factory


# Lazy initialization for the declarative base
def construct_base() -> DeclarativeBase:
    """
    Creates a declarative base for the database models.
    Returns:
        Base: The declarative base.
    """
    return declarative_base()


# Dependency injection for the database session
def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    """
    SessionLocal = construct_session()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
