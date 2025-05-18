# tests/test_ingestion_main

import os
import pytest
from fastapi.testclient import TestClient
from backend.ingestion.main import app

@pytest.fixture(autouse=True)
def set_pytest_env(monkeypatch):
    # Ensure startup logic is skipped during tests
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "true")
    yield
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

@pytest.fixture
def client():
    # Use context manager to ensure lifespan events are handled
    with TestClient(app) as client:
        yield client

def test_load_sdn_data_success(mocker, client):
    mock_db = object()
    mocker.patch("backend.ingestion.main.get_db", return_value=iter([mock_db]))
    mocker.patch("backend.ingestion.main.download_sdn_files", return_value=("xml_path", "xsd_path"))
    mocker.patch("backend.ingestion.main.validate_sdn_xml", return_value=True)
    mocker.patch("backend.ingestion.main.parse_sdn_xml", return_value={"some": "data"})
    mocker.patch("backend.ingestion.main.store_sdn_data", return_value=None)

    response = client.post("/ingestion/load/sdn_data")
    assert response.status_code == 200
    assert response.json() == {"message": "SDN advanced data loaded successfully"}

def test_load_sdn_data_invalid_xml(mocker, client):
    mock_db = object()
    mocker.patch("backend.ingestion.main.get_db", return_value=iter([mock_db]))
    mocker.patch("backend.ingestion.main.download_sdn_files", return_value=("xml_path", "xsd_path"))
    mocker.patch("backend.ingestion.main.validate_sdn_xml", return_value=False)

    response = client.post("/ingestion/load/sdn_data")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid XML file"

def test_load_sdn_data_unexpected_exception(mocker, client):
    mock_db = object()
    mocker.patch("backend.ingestion.main.get_db", return_value=iter([mock_db]))
    # Force an exception in download_sdn_files
    mocker.patch("backend.ingestion.main.download_sdn_files", side_effect=Exception("Unexpected error"))
    response = client.post("/ingestion/load/sdn_data")
    assert response.status_code == 500
    assert response.json()["detail"] == "An internal server error occurred."

def test_lifespan_startup_logic(mocker, monkeypatch):
    # Unset PYTEST_CURRENT_TEST to trigger startup logic
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    # Mock all side effects in startup logic
    mocker.patch("backend.ingestion.main.init_db", return_value=None)
    mocker.patch("backend.ingestion.main.get_db", return_value=iter([object()]))
    mocker.patch("backend.ingestion.main.load_sdn_data", return_value=None)
    mocker.patch("backend.ingestion.main.scheduler.start", return_value=None)
    mocker.patch("backend.ingestion.main.scheduler.add_job", return_value=None)
    with TestClient(app):
        pass  # Just starting and stopping the app triggers lifespan

def test_lifespan_startup_exception(monkeypatch, mocker):
    # Unset PYTEST_CURRENT_TEST to trigger startup logic
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    # Patch get_db to raise an exception
    mocker.patch("backend.ingestion.main.get_db", side_effect=Exception("DB error"))
    # Patch scheduler methods to avoid side effects
    mocker.patch("backend.ingestion.main.init_db", return_value=None)
    mocker.patch("backend.ingestion.main.scheduler.start", return_value=None)
    mocker.patch("backend.ingestion.main.scheduler.add_job", return_value=None)
    # Patch logger to check error logging
    log_mock = mocker.patch("backend.ingestion.main.logger.error")
    from backend.ingestion.main import app
    with TestClient(app):
        pass
    log_mock.assert_any_call("Failed to initialize SDN data load: DB error")


def test_lifespan_shutdown_scheduler(monkeypatch, mocker):
    # Unset PYTEST_CURRENT_TEST to trigger shutdown logic
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    # Patch BackgroundScheduler.running property on the class
    mocker.patch(
        "apscheduler.schedulers.background.BackgroundScheduler.running",
        new_callable=mocker.PropertyMock,
        return_value=True
    )
    mocker.patch("backend.ingestion.main.scheduler.shutdown", return_value=None)
    # Patch startup logic to do nothing
    mocker.patch("backend.ingestion.main.init_db", return_value=None)
    mocker.patch("backend.ingestion.main.get_db", return_value=iter([object()]))
    mocker.patch("backend.ingestion.main.load_sdn_data", return_value=None)
    mocker.patch("backend.ingestion.main.scheduler.start", return_value=None)
    mocker.patch("backend.ingestion.main.scheduler.add_job", return_value=None)
    with TestClient(app):
        pass
