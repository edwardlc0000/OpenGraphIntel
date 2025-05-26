# tests/test_database.py

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.orm import sessionmaker
from backend.data_layer.database import DatabaseManager


@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure a fresh instance of DatabaseManager before each test."""
    DatabaseManager._instance = None

@pytest.fixture
def sqlite_manager():
    """Fixture for DatabaseManager using an in-memory SQLite database."""
    manager = DatabaseManager('sqlite:///:memory:')
    manager._engine = create_engine('sqlite:///:memory:')  # Use in-memory SQLite for testing
    manager._session_factory = sessionmaker(bind=manager._engine)
    manager._base = manager._construct_base()
    return manager

# Test construct_postgres_url
@patch("backend.data_layer.database.get_env_variable")
def test_construct_postgres_url(mock_get_env_variable):
    mock_get_env_variable.side_effect = lambda key: {
        "POSTGRES_DB": "test_db",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "test_password",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432"
    }[key]

    manager = DatabaseManager()
    expected_url = "postgresql://test_user:test_password@localhost:5432/test_db"
    assert manager._construct_postgres_url() == expected_url


@patch("backend.data_layer.database.get_env_variable")
def test_construct_postgres_url_missing_env_var(mock_get_env_variable):
    mock_get_env_variable.side_effect = ValueError("Missing environment variable")
    with pytest.raises(ValueError):
        manager = DatabaseManager()
        manager._construct_postgres_url()


# Test construct_engine
@patch("backend.data_layer.database.create_engine")
@patch("backend.data_layer.database.DatabaseManager._construct_postgres_url")
def test_construct_engine(mock_construct_postgres_url, mock_create_engine):
    """Test construct_engine with a valid database URL."""
    mock_construct_postgres_url.return_value = "postgresql://test_user:test_password@localhost:5432/test_db"
    mock_create_engine.return_value = MagicMock(spec=Engine)

    manager = DatabaseManager()
    engine = manager._engine
    assert engine == mock_create_engine.return_value
    mock_create_engine.assert_called_once_with("postgresql://test_user:test_password@localhost:5432/test_db")


@patch("backend.data_layer.database.create_engine")
@patch("backend.data_layer.database.DatabaseManager._construct_postgres_url")
def test_construct_engine_with_existing_engine(mock_construct_postgres_url, mock_create_engine):
    """Test construct_engine with a valid database URL."""
    mock_construct_postgres_url.return_value = "postgresql://test_user:test_password@localhost:5432/test_db"
    mock_create_engine.return_value = MagicMock(spec=Engine)

    manager = DatabaseManager()
    engine = manager._engine
    engine = manager._engine  # Access again to check for existing engine
    assert engine == mock_create_engine.return_value
    mock_construct_postgres_url.assert_called_once()


@patch("backend.data_layer.database.create_engine")
def test_construct_engine_creation_failure(mock_create_engine):
    """Test construct_engine when create_engine raises an exception."""
    mock_create_engine.side_effect = Exception("Engine creation failed")
    with pytest.raises(RuntimeError, match="Failed to create database engine."):
        manager = DatabaseManager()
        manager._engine


@patch("backend.data_layer.database.create_engine")
def test_construct_engine_retry_logic(mock_create_engine):
    """Test construct_engine retry logic when engine creation fails."""
    mock_create_engine.side_effect = Exception("Engine creation failed")
    with patch("backend.data_layer.database.logger") as mock_logger:
        with pytest.raises(RuntimeError, match="Failed to create database engine."):
            manager = DatabaseManager()
            manager._construct_engine("postgresql://user:pass@localhost:5432/db", retries=5)
        assert mock_logger.info.call_count == 5  # Ensure retries are logged
        assert mock_logger.error.call_count >= 5  # Ensure errors are logged


# Test construct_session
@patch("backend.data_layer.database.DatabaseManager._construct_engine")
def test_construct_session(mock_construct_engine):
    mock_engine = MagicMock(spec=Engine)
    mock_construct_engine.return_value = mock_engine

    manager = DatabaseManager()
    session_factory = manager._session_factory
    assert isinstance(session_factory, sessionmaker)
    assert session_factory.kw["bind"] == mock_engine


@patch("backend.data_layer.database.DatabaseManager._construct_engine")
def test_construct_session_with_existing_factory(mock_construct_engine):
    mock_engine = MagicMock(spec=Engine)
    mock_construct_engine.return_value = mock_engine

    manager = DatabaseManager()
    session_factory1 = manager._session_factory
    session_factory2 = manager._session_factory
    assert session_factory1 == session_factory2


# Test construct_base
def test_construct_base():
    manager = DatabaseManager()
    base = manager._base
    assert base.metadata is not None


# Test get_db
@patch("backend.data_layer.database.DatabaseManager._construct_session")
def test_get_db(mock_construct_session):
    mock_session = MagicMock()
    mock_construct_session.return_value = MagicMock(return_value=mock_session)

    manager = DatabaseManager()
    generator = manager.get_db()
    db = next(generator)
    assert db == mock_session
    mock_session.close.assert_not_called()

    # Ensure the session is closed after the generator is exhausted
    with pytest.raises(StopIteration):
        next(generator)
    mock_session.close.assert_called_once()

@patch("backend.data_layer.database.DatabaseManager._construct_session")
def test_get_db_close_on_exception(mock_construct_session):
    mock_session = MagicMock()
    mock_construct_session.return_value = MagicMock(return_value=mock_session)

    manager = DatabaseManager()
    generator = manager.get_db()
    db = next(generator)
    assert db == mock_session

    # Simulate exception after yielding
    try:
        generator.throw(Exception("Test exception"))
    except Exception:
        pass
    mock_session.close.assert_called_once()

def test_construct_base_sqlite(sqlite_manager):
    base = sqlite_manager._base
    assert base.metadata is not None

def test_init_db_sqlite(sqlite_manager):
    sqlite_manager.init_db()
    # Assuming SDNEntity is a table, check if it has been created
    inspector = inspect(sqlite_manager._engine)
    assert 'sdn_entities' in inspector.get_table_names()

def test_get_db_sqlite(sqlite_manager):
    session_factory = sqlite_manager._session_factory
    session = session_factory()

    generator = sqlite_manager.get_db()
    db = next(generator)
    assert isinstance(db, session.__class__)  # Check if the session is as expected

    db.close()  # Close the session explicitly
    with pytest.raises(StopIteration):
        next(generator)