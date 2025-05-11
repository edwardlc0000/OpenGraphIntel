# open_graph_intel/data_layer/graphdb.py

# Import dependencies
import logging
from neo4j import Driver, GraphDatabase

# Import custom modules
from open_graph_intel.common.utils import get_env_variable

# Configure logging
logger = logging.getLogger(__name__)

# Import environment variables
import os
from dotenv import load_dotenv

load_dotenv()

# Cache for the Neo4j driver
_neo4j_driver = None

# Lazy initialization for the Neo4j configuration
def get_neo4j_config() -> tuple[str, str, str]:
    """
    Retrieves the Neo4j configuration from environment variables.
    Returns:
        tuple: A tuple containing the Neo4j URI, user, and password.
    """
    try:
        NEO4J_URI = get_env_variable("NEO4J_URI")
        NEO4J_USER = get_env_variable("NEO4J_USER")
        NEO4J_PASSWORD = get_env_variable("NEO4J_PASSWORD")
        return NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
    except ValueError as e:
        logger.error(f"Error retrieving environment variables: {e}")
        raise

# Lazy initialization for the Neo4j driver
def get_neo4j_driver() -> Driver:
    """
    Retrieves the Neo4j driver, creating it if it doesn't exist.
    Returns:
        Driver: The Neo4j driver.
    """
    global _neo4j_driver
    if _neo4j_driver is None:
        NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD = get_neo4j_config()
        try:
            _neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            logger.info(f"Neo4j driver created successfully: {NEO4J_URI}")
        except Exception as e:
            logger.error(f"Failed to create Neo4j driver: {e}")
            raise RuntimeError("Failed to create Neo4j driver.")
    return _neo4j_driver

# Create nodes
def create_node(tx, label, properties):
    """
    Create a node in the Neo4j database.
    Args:
        tx: The transaction object.
        label (str): The label for the node.
        properties (dict): A dictionary of properties for the node.
    """
    try:
        query = f"CREATE (n:{label} $properties)"
        tx.run(query, properties=properties)
        logger.info(f"Node created with label {label} and properties {properties}")
    except Exception as e:
        logger.error(f"Error creating node: {e}")
        raise
    finally:
        tx.close()

# Create relationships
def create_relationship(tx, start_node, end_node, relationship_type):
    """
    Create a relationship between two nodes in the Neo4j database.
    Args:
        tx: The transaction object.
        start_node (str): The starting node's ID.
        end_node (str): The ending node's ID.
        relationship_type (str): The type of relationship to create.
    """
    try:
        query = f"MATCH (a), (b) WHERE id(a) = $start_node AND id(b) = $end_node CREATE (a)-[r:{relationship_type}]->(b)"
        tx.run(query, start_node=start_node, end_node=end_node)
        logger.info(f"Relationship created from {start_node} to {end_node} with type {relationship_type}")
    except Exception as e:
        logger.error(f"Error creating relationship: {e}")
        raise
    finally:
        tx.close()
