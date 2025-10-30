import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import sys

# Add the service's root directory to the path to allow for relative imports
service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if service_root not in sys.path:
    sys.path.insert(0, service_root)

# Mock environment variables before importing the app
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {"INTERNAL_SERVICE_SECRET": "test-secret-key"}):
        yield

# Now import the app
from api.main import app
from config.celery_config import celery_app

@pytest.fixture
def client():
    """A test client for the FastAPI app."""    
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_headers():
    return {"X-API-KEY": "test-secret-key"}

@pytest.fixture(autouse=True)
def mock_celery_task():
    """Mock the celery app send_task method."""
    # Patch the method on the client class that is used by the application
    with patch('api.infrastructure.celery_client.CeleryClient.send_task') as mock_send_task:
        mock_task = MagicMock()
        mock_task.id = "test-task-id-123"
        mock_send_task.return_value = mock_task
        yield mock_send_task

@pytest.fixture
def mock_async_result():
    """Mock the AsyncResult from Celery."""
    # Patch AsyncResult where it is used in the celery_client
    with patch('api.infrastructure.celery_client.AsyncResult') as mock_async:
        yield mock_async

# --- Test Cases ---

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_catalog_intake_success(client, mock_celery_task, auth_headers):
    """Test the catalog intake endpoint with a successful file upload."""
    dummy_content = b"this is a dummy image"
    files = {'file': ('test_image.jpg', dummy_content, 'image/jpeg')}
    
    # Also patch the file system operations to avoid actual file writes
    with patch('api.infrastructure.file_storage.LocalFileStorage.save_file') as mock_save:
        mock_save.return_value = "/app/uploads/dummy_path.jpg"
        response = client.post("/api/ai/catalog-intake", files=files, headers=auth_headers)
    
    assert response.status_code == 202
    assert response.json() == {"task_id": "test-task-id-123", "status": "PENDING"}
    
    mock_celery_task.assert_called_once()
    # Check that the task was sent to the correct queue
    assert mock_celery_task.call_args.kwargs['queue'] == 'vision_queue'

def test_catalog_intake_no_api_key(client):
    """Test the catalog intake endpoint without an API key."""
    dummy_content = b"this is a dummy image"
    files = {'file': ('test_image.jpg', dummy_content, 'image/jpeg')}
    response = client.post("/api/ai/catalog-intake", files=files)
    assert response.status_code == 401
    assert "Invalid or missing API Key" in response.json()['detail']

def test_get_task_status_pending(client, mock_async_result, auth_headers):
    """Test checking the status of a pending task."""
    mock_result_instance = MagicMock()
    mock_result_instance.ready.return_value = False
    mock_async_result.return_value = mock_result_instance

    task_id = "pending-task-id"
    response = client.get(f"/api/ai/status/{task_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "task_id": task_id,
        "status": "PENDING",
        "result": None,
        "error": None
    }
    mock_async_result.assert_called_once_with(task_id, app=celery_app)

def test_get_task_status_success(client, mock_async_result, auth_headers):
    """Test checking the status of a successful task."""
    mock_result_instance = MagicMock()
    mock_result_instance.ready.return_value = True
    mock_result_instance.successful.return_value = True
    # The .get() method returns the actual result
    mock_result_instance.get.return_value = {"product_name": "Test Product", "category_standard": "Test", "description_long": "A test desc", "features_list": []}
    mock_async_result.return_value = mock_result_instance

    task_id = "success-task-id"
    response = client.get(f"/api/ai/status/{task_id}", headers=auth_headers)

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "SUCCESS"
    assert json_response["result"]["product_name"] == "Test Product"
    mock_async_result.assert_called_once_with(task_id, app=celery_app)

def test_get_task_status_failure(client, mock_async_result, auth_headers):
    """Test checking the status of a failed task."""
    mock_result_instance = MagicMock()
    mock_result_instance.ready.return_value = True
    mock_result_instance.successful.return_value = False
    mock_result_instance.result = "Something went wrong" # The exception object/string
    mock_async_result.return_value = mock_result_instance

    task_id = "failure-task-id"
    response = client.get(f"/api/ai/status/{task_id}", headers=auth_headers)

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "FAILURE"
    assert json_response["result"] is None
    assert "Something went wrong" in json_response["error"]
    mock_async_result.assert_called_once_with(task_id, app=celery_app)
