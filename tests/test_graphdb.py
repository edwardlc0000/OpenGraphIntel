# tests/test_graphdb.py

import pytest
from unittest.mock import patch, MagicMock
from open_graph_intel.data_layer.graphdb import (
    get_neo4j_config,
    get_neo4j_driver,
    create_node,
    create_relationship,
)

# Test get_neo4j_config
@patch("open_graph_intel.data_layer.graphdb.get_env_variable")
def test_get_neo4j_config(mock_get_env_variable):
    mock_get_env_variable.side_effect = lambda key: {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
    }[key]

    config = get_neo4j_config()
    assert config == ("bolt://localhost:7687", "neo4j", "password")
    mock_get_env_variable.assert_any_call("NEO4J_URI")
    mock_get_env_variable.assert_any_call("NEO4J_USER")
    mock_get_env_variable.assert_any_call("NEO4J_PASSWORD")

# Test get_neo4j_driver
@patch("open_graph_intel.data_layer.graphdb.GraphDatabase.driver")
@patch("open_graph_intel.data_layer.graphdb.get_neo4j_config")
def test_get_neo4j_driver(mock_get_neo4j_config, mock_driver):
    mock_get_neo4j_config.return_value = ("bolt://localhost:7687", "neo4j", "password")
    mock_driver.return_value = MagicMock()

    driver = get_neo4j_driver()
    assert driver is not None
    mock_get_neo4j_config.assert_called_once()
    mock_driver.assert_called_once_with(
        "bolt://localhost:7687", auth=("neo4j", "password")
    )

# Test create_node
@patch("open_graph_intel.data_layer.graphdb.logger")
def test_create_node(mock_logger):
    mock_tx = MagicMock()
    label = "Person"
    properties = {"name": "John Doe", "age": 30}

    create_node(mock_tx, label, properties)

    mock_tx.run.assert_called_once_with(
        "CREATE (n:Person $properties)", properties=properties
    )
    mock_logger.info.assert_called_once_with(
        f"Node created with label {label} and properties {properties}"
    )

# Test create_relationship
@patch("open_graph_intel.data_layer.graphdb.logger")
def test_create_relationship(mock_logger):
    mock_tx = MagicMock()
    start_node = 1
    end_node = 2
    relationship_type = "FRIENDS"

    create_relationship(mock_tx, start_node, end_node, relationship_type)

    mock_tx.run.assert_called_once_with(
        "MATCH (a), (b) WHERE id(a) = $start_node AND id(b) = $end_node CREATE (a)-[r:FRIENDS]->(b)",
        start_node=start_node,
        end_node=end_node,
    )
    mock_logger.info.assert_called_once_with(
        f"Relationship created from {start_node} to {end_node} with type {relationship_type}"
    )

