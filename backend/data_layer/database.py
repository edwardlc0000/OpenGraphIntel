#backend/data_layer/database.py

# Import dependencies
import logging
from typing import Generator
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from typing import Final

# Import custom modules
from backend.common.utils import get_env_variable
from backend.models.base import Base

# Configure logging
logger = logging.getLogger(__name__)

# Import environment variables
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    """
    A class to manage the database connection and session.
    """
    _instance = None

    def __new__(cls, database_url=None):
        """
        Singleton pattern to ensure only one instance of DatabaseManager exists.
        """
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._engine = None
            cls._instance._session_factory = None
            cls._instance._base = None
            cls._instance._db_url = database_url or cls._instance._construct_postgres_url()
            cls._instance._engine = cls._instance._construct_engine(cls._instance._db_url)
            cls._instance._session_factory = cls._instance._construct_session(cls._instance._engine)
            cls._instance._base = cls._instance._construct_base()
        return cls._instance

    def _construct_postgres_url(self) -> str:
        """
        Constructs the PostgreSQL URL from environment variables.
        Returns:
            str: The PostgreSQL URL.
        """
        try:
            DB_NAME: Final[str] = get_env_variable("POSTGRES_DB")
            USER: Final[str] = get_env_variable("POSTGRES_USER")
            PASSWORD: Final[str] = get_env_variable("POSTGRES_PASSWORD")
            HOST: Final[str] = get_env_variable("POSTGRES_HOST")
            PORT: Final[str] = get_env_variable("POSTGRES_PORT")
            return f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
        except ValueError as e:
            logger.error(f"Error retrieving environment variables: {e}")
            raise

    def _construct_engine(self, database_url: str = None, retries: int = 5) -> Engine:
        """
        Creates a database engine with retry logic.
        Args:
            database_url (str): The database URL.
            retries (int): Number of retries for creating the engine.
        Returns:
            engine: The SQLAlchemy engine.
        """
        if self._engine is None:
            for i in range(retries):
                try:
                    self._engine = create_engine(database_url)
                    logger.info(f"Database engine created successfully: {database_url.split('@')[0]}")
                    return self._engine
                except Exception as e:
                    logger.error(f"Error creating database engine: {e}")
                    logger.info(f"Retrying to create database engine... ({i + 1}/{retries})")
            logger.error(f"Failed to create database engine after {retries} retries.")
            raise RuntimeError("Failed to create database engine.")
        return self._engine

    def _construct_session(self, engine: Engine = None) -> sessionmaker:
        """
        Creates a session factory for the database.
        Args:
            engine: The SQLAlchemy engine.
        Returns:
            SessionLocal: The session factory.
        """
        if self._session_factory is None:
            logger.info("Creating a new session factory.")
            self._session_factory = sessionmaker(autocommit=False,
                                                 autoflush=False,
                                                 bind=engine)
        return self._session_factory

    def _construct_base(self):
        """
        Creates a declarative base for the database models.
        Returns:
            Base: The declarative base.
        """
        if self._base is None:
            self._base = Base
        return self._base

    def get_db(self) -> Generator[Session, None, None]:
        """
        Dependency that provides a database session.
        """
        SessionLocal = self._construct_session()
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def init_db(self) -> None:
        """
        Initializes the database by creating the tables.
        """
        logger.info("Initializing the database.")
        self._base.metadata.create_all(bind=self._engine)
        logger.info("Database initialized successfully.")