
# test_database.py

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
import open_graph_intel.data_layer.database as db_module

# Test construct_postgres_url
@patch("open_graph_intel.data_layer.database.get_env_variable")
def test_construct_postgres_url(mock_get_env_variable):
    mock_get_env_variable.side_effect = lambda key: {
        "POSTGRES_DB": "test_db",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "test_password",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432"
    }[key]

    expected_url = "postgresql://test_user:test_password@localhost:5432/test_db"
    assert db_module.construct_postgres_url() == expected_url

@patch("open_graph_intel.data_layer.database.get_env_variable")
def test_construct_postgres_url_missing_env_var(mock_get_env_variable):
    mock_get_env_variable.side_effect = ValueError("Missing environment variable")
    with pytest.raises(ValueError):
        db_module.construct_postgres_url()

# Test construct_engine
@patch("open_graph_intel.data_layer.database.create_engine")
@patch("open_graph_intel.data_layer.database.construct_postgres_url")
def test_construct_engine(mock_construct_postgres_url, mock_create_engine):
    """Test construct_engine with a valid database URL."""
    from open_graph_intel.data_layer.database import _engine
    _engine = None  # Reset the global _engine
    mock_construct_postgres_url.return_value = "postgresql://test_user:test_password@localhost:5432/test_db"
    mock_create_engine.return_value = MagicMock(spec=Engine)

    engine = db_module.construct_engine()
    assert engine == mock_create_engine.return_value
    mock_create_engine.assert_called_once_with("postgresql://test_user:test_password@localhost:5432/test_db")

@patch("open_graph_intel.data_layer.database.create_engine")
def test_construct_engine_creation_failure(mock_create_engine):
    """Test construct_engine when create_engine raises an exception."""
    db_module._engine = None  # Reset the global _engine
    mock_create_engine.side_effect = Exception("Engine creation failed")
    with pytest.raises(RuntimeError, match="Failed to create database engine."):
        db_module.construct_engine(database_url="postgresql://user:pass@localhost:5432/db")

@patch("open_graph_intel.data_layer.database.create_engine")
def test_construct_engine_retry_logic(mock_create_engine):
    """Test construct_engine retry logic when engine creation fails."""
    db_module._engine = None  # Reset the global _engine
    mock_create_engine.side_effect = Exception("Engine creation failed")
    with patch("open_graph_intel.data_layer.database.logger") as mock_logger:
        with pytest.raises(RuntimeError, match="Failed to create database engine."):
            db_module.construct_engine(database_url="postgresql://user:pass@localhost:5432/db", retries=3)
        assert mock_logger.info.call_count == 3  # Ensure retries are logged
        assert mock_logger.error.call_count >= 3  # Ensure errors are logged


# Test construct_session
@patch("open_graph_intel.data_layer.database.construct_engine")
def test_construct_session(mock_construct_engine):
    mock_engine = MagicMock(spec=Engine)
    mock_construct_engine.return_value = mock_engine

    session_factory = db_module.construct_session()
    assert isinstance(session_factory, sessionmaker)
    assert session_factory.kw["bind"] == mock_engine

# Test construct_base
def test_construct_base():
    base = db_module.construct_base()
    assert base.metadata is not None

# Test get_db
@patch("open_graph_intel.data_layer.database.construct_session")
def test_get_db(mock_construct_session):
    mock_session = MagicMock()
    mock_construct_session.return_value = MagicMock(return_value=mock_session)

    generator = db_module.get_db()
    db = next(generator)
    assert db == mock_session
    mock_session.close.assert_not_called()

    # Ensure the session is closed after the generator is exhausted
    with pytest.raises(StopIteration):
        next(generator)
    mock_session.close.assert_called_once()
