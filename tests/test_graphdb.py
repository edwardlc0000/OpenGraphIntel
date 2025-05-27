# tests/test_graphdb.py

import pytest
import logging
from unittest.mock import patch, MagicMock
from backend.data_layer.graphdb import GraphDBManager
from neomodel import config as neomodel_config

# Fixture to reset the singleton instance before each test
@pytest.fixture(autouse=True)
def reset_singleton():
    GraphDBManager._instance = None

@patch('backend.data_layer.graphdb.get_env_variable')
def test_singleton_instance(mock_get_env_variable):
    # Mock environment variable retrieval
    mock_get_env_variable.side_effect = lambda x: {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "user",
        "NEO4J_PASSWORD": "password"
    }[x]

    # Create two instances of GraphDBManager
    manager1 = GraphDBManager()
    manager2 = GraphDBManager()

    # Assert that both instances are the same
    assert manager1 is manager2

# Mock environment variables
@patch('backend.data_layer.graphdb.get_env_variable')
def test_initialize_driver_success(mock_get_env_variable):
    # Setup mock return values
    mock_get_env_variable.side_effect = lambda x: {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "user",
        "NEO4J_PASSWORD": "password"
    }[x]

    # Mock the GraphDatabase.driver method
    with patch('backend.data_layer.graphdb.GraphDatabase.driver') as mock_driver:
        mock_driver.return_value = MagicMock()

        # Create GraphDBManager instance
        manager = GraphDBManager()

        # Test if the driver was initialized correctly
        assert manager._driver is not None
        mock_driver.assert_called_once_with(
            "bolt://localhost:7687", auth=("user", "password")
        )

@patch('backend.data_layer.graphdb.get_env_variable')
def test_initialize_driver_singleton(mock_get_env_variable):
    # Setup mock return values
    mock_get_env_variable.side_effect = lambda x: {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "user",
        "NEO4J_PASSWORD": "password"
    }[x]

    # Mock the GraphDatabase.driver method
    with patch('backend.data_layer.graphdb.GraphDatabase.driver') as mock_driver:
        mock_driver.return_value = MagicMock()

        # Create first instance of GraphDBManager
        manager1 = GraphDBManager()
        assert manager1._driver is not None
        driver1 = manager1._driver

        # Create second instance of GraphDBManager
        manager1._initialize_driver()  # This should not create a new driver
        driver2 = manager1._driver

        # Assert that both instances share the same driver
        assert driver1 is driver2
        mock_driver.assert_called_with(
            "bolt://localhost:7687", auth=("user", "password")
        )

@patch('backend.data_layer.graphdb.get_env_variable')
def test_get_neo4j_config_failure(mock_get_env_variable):
    # Setup mock to raise ValueError for missing environment variable
    mock_get_env_variable.side_effect = ValueError("Missing environment variable")

    # Attempt to create GraphDBManager and expect ValueError
    with pytest.raises(ValueError, match="Missing environment variable"):
        GraphDBManager()

@patch('backend.data_layer.graphdb.get_env_variable')
def test_initialize_driver_failure(mock_get_env_variable):
    # Setup mock return values
    mock_get_env_variable.side_effect = lambda x: {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "user",
        "NEO4J_PASSWORD": "password"
    }[x]

    # Force GraphDatabase.driver to raise an exception
    with patch('backend.data_layer.graphdb.GraphDatabase.driver', side_effect=RuntimeError("Driver error")):
        with pytest.raises(RuntimeError, match="Failed to create Neo4j driver."):
            GraphDBManager()

@patch('backend.data_layer.graphdb.GraphDBManager._initialize_driver')
def test_configure_neomodel(mock_initialize_driver):
    mock_initialize_driver.return_value = None

    # Mock environment variable retrieval
    with patch('backend.data_layer.graphdb.get_env_variable') as mock_get_env_variable:
        mock_get_env_variable.side_effect = lambda x: {
            "NEO4J_URI": "localhost:7687",
            "NEO4J_USER": "user",
            "NEO4J_PASSWORD": "password"
        }[x]

        # Ensure neomodel configuration is applied correctly
        manager = GraphDBManager()
        expected_url = "bolt://user:password@localhost:7687"
        assert neomodel_config.DATABASE_URL == expected_url

@patch('backend.data_layer.graphdb.GraphDBManager._initialize_driver')
def test_close_driver(mock_initialize_driver):
    # Mock driver and its methods
    mock_driver = MagicMock()
    mock_initialize_driver.return_value = None

    with patch('backend.data_layer.graphdb.GraphDatabase.driver', return_value=mock_driver):
        manager = GraphDBManager()
        manager._driver = mock_driver

        # Close driver and verify
        manager.close_driver()
        mock_driver.close.assert_called_once()


@patch('backend.data_layer.graphdb.GraphDBManager._initialize_driver')
def test_close_driver_no_driver(mock_initialize_driver, caplog):
    mock_initialize_driver.return_value = None

    manager = GraphDBManager()
    manager._driver = None

    with caplog.at_level(logging.WARNING):  # Specify log level to capture
        manager.close_driver()

    # Assert that the expected warning message was logged
    assert any("No Neo4j driver to close" in record.message for record in caplog.records)

@patch('backend.data_layer.graphdb.GraphDatabase.driver')
def test_close_driver_failure(mock_driver):
    # Mock the driver to raise an exception on close
    mock_driver_instance = MagicMock()
    mock_driver_instance.close.side_effect = RuntimeError("Failed to close Neo4j driver.")
    mock_driver.return_value = mock_driver_instance
    manager = GraphDBManager()
    manager._driver = mock_driver_instance
    # Attempt to close the driver and expect an exception
    with pytest.raises(RuntimeError, match="Failed to close Neo4j driver."):
        manager.close_driver()

@patch('backend.data_layer.graphdb.GraphDBManager._initialize_driver')
def test_execute_query_success(mock_initialize_driver):
    # Mock a successful query run
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_result = MagicMock()

    mock_session.run.return_value = [mock_result]
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_initialize_driver.return_value = None

    with patch('backend.data_layer.graphdb.GraphDatabase.driver', return_value=mock_driver):
        manager = GraphDBManager()
        manager._driver = mock_driver

        # Execute the query and verify results
        query = "MATCH (n) RETURN n"
        results = manager.execute_query(query)
        assert results == [mock_result]
        mock_session.run.assert_called_once_with(query, {})

@patch('backend.data_layer.graphdb.GraphDBManager._initialize_driver')
@patch('backend.data_layer.graphdb.GraphDatabase.driver')
def test_execute_query_no_driver(mock_driver_class, mock_initialize_driver):
    # Mock the Neo4j driver behavior
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_result = MagicMock()

    # Define the query execution result
    mock_session.run.return_value = [mock_result]
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_driver_class.return_value = mock_driver  # Ensure the mock driver is used as needed

    # Make manager accessible outside initialization
    manager = GraphDBManager()
    manager._driver = None  # Simulate that the driver is not initialized

    # Now adjust _initialize_driver to simulate setting the driver
    def initialize_driver_side_effect():
        # Assign mock_driver to the GraphDBManager's _driver attribute
        GraphDBManager._instance._driver = mock_driver

    # Set the side effect
    mock_initialize_driver.side_effect = initialize_driver_side_effect

    # Execute the query
    query = "MATCH (n) RETURN n"
    results = manager.execute_query(query)

    # Assertions
    mock_initialize_driver.assert_called()  # Ensure _initialize_driver was called
    mock_session.run.assert_called_once_with(query, {})  # Verify the query run call
    assert results == [mock_result]  # Ensure the return value is as expected

@patch('backend.data_layer.graphdb.GraphDBManager._initialize_driver')
def test_execute_query_failure(mock_initialize_driver):
    # Mock a query failure
    mock_driver = MagicMock()
    mock_session = MagicMock()

    mock_session.run.side_effect = RuntimeError("Query failed")
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_initialize_driver.return_value = None

    with patch('backend.data_layer.graphdb.GraphDatabase.driver', return_value=mock_driver):
        manager = GraphDBManager()
        manager._driver = mock_driver

        # Execute the query and expect failure
        query = "MATCH (n) RETURN n"
        with pytest.raises(RuntimeError):
            manager.execute_query(query)