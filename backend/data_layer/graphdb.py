# backend/data_layer/graphdb.py

# Import dependencies
import logging
from neo4j import Driver, GraphDatabase
from neomodel import config as neomodel_config

# Import custom modules
from backend.common.utils import get_env_variable

# Configure logging
logger = logging.getLogger(__name__)

class GraphDBManager:
    """
    A class to manage the Neo4j database connection and operations.
    This class is designed to be a singleton, ensuring that only one instance of the Neo4j driver is created.
    """
    _instance = None

    def __new__(cls):
        """
        Singleton pattern to ensure only one instance of GraphDBManager exists.
        """
        if cls._instance is None:
            cls._instance = super(GraphDBManager, cls).__new__(cls)
            cls._instance._driver = None
            cls._instance._initialize_driver()
            cls._instance._configure_neomodel()
        return cls._instance

    def get_neo4j_config(self) -> tuple[str, str, str]:
        """
        Retrieves the Neo4j configuration from environment variables.
        Returns:
            tuple: A tuple containing the Neo4j URI, user, and password
        """
        try:
            NEO4J_URI = get_env_variable("NEO4J_URI")
            NEO4J_USER = get_env_variable("NEO4J_USER")
            NEO4J_PASSWORD = get_env_variable("NEO4J_PASSWORD")
            return NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
        except ValueError as e:
            logger.error(f"Error retrieving environment variables: {e}")
            raise

    def _initialize_driver(self) -> None:
        """Initialize the Neo4j driver with the provided credentials."""
        NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD = self.get_neo4j_config()
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
                logger.info(f"Neo4j driver created successfully: {NEO4J_URI}")
            except Exception as e:
                logger.error(f"Failed to create Neo4j driver: {e}")
                raise RuntimeError("Failed to create Neo4j driver.") from e

    def _configure_neomodel(self) -> None:
        """Configure neomodel with the Neo4j driver."""
        if self._driver is None:
            self._initialize_driver()
        NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD = self.get_neo4j_config()
        neomodel_config.DATABASE_URL = f'bolt://{NEO4J_USER}:{NEO4J_PASSWORD}@{NEO4J_URI}'
        logger.info("neomodel configured successfully.")

    def close_driver(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver is not None:
            try:
                self._driver.close()
                logger.info("Neo4j driver closed successfully.")
            except Exception as e:
                logger.error(f"Error closing Neo4j driver: {e}")
                raise RuntimeError("Failed to close Neo4j driver.") from e
        else:
            logger.warning("No Neo4j driver to close.")

    def execute_query(self, query: str, parameters: dict = None) -> list:
        """
        Execute a Cypher query against the Neo4j database.
        Args:
            query (str): The Cypher query to execute.
            parameters (dict): Optional parameters for the query.
        Returns:
            list: The results of the query.
        """
        if self._driver is None:
            self._initialize_driver()

        with self._driver.session() as session:
            try:
                result = session.run(query, parameters or {})
                return [record for record in result]
            except Exception as e:
                logger.error(f"Query failed: {query} with parameters {parameters}. Error: {e}")
                raise
