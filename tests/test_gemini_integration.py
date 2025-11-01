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
    with patch.dict(os.environ, {
        "INTERNAL_SERVICE_SECRET": "test-secret-key",
        "GEMINI_API_KEY": "fake-gemini-api-key"
    }):
        yield

# Now import the app
from api.main import app
from api.infrastructure.gemini_client import GeminiClient
from api.infrastructure.gemini_image_client import GeminiImageClient

@pytest.fixture
def client():
    """A test client for the FastAPI app."""    
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_headers():
    return {"X-API-KEY": "test-secret-key"}

@patch('api.infrastructure.gemini_client.genai.Client')
def test_gemini_text_generation_success(mock_genai_client):
    mock_client_instance = mock_genai_client.return_value
    mock_models_instance = MagicMock()
    mock_client_instance.models = mock_models_instance
    
    mock_response = MagicMock()
    mock_response.text = "Generated text response"
    mock_models_instance.generate_content.return_value = mock_response

    gemini_client = GeminiClient()
    prompt = "Test prompt"
    response = gemini_client.generate_text(prompt)

    mock_models_instance.generate_content.assert_called_once_with(model='gemini-pro', contents=prompt)
    assert response == "Generated text response"

@patch('api.infrastructure.gemini_image_client.genai.Client')
@patch('api.infrastructure.gemini_image_client.Image')
@patch('api.infrastructure.gemini_image_client.uuid')
def test_gemini_image_generation_success(mock_uuid, mock_image, mock_genai_client):
    mock_client_instance = mock_genai_client.return_value
    mock_models_instance = MagicMock()
    mock_client_instance.models = mock_models_instance

    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data.data = b"fake_image_bytes"
    mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
    mock_models_instance.generate_content.return_value = mock_response

    mock_uuid.uuid4.return_value.hex = "testhex"
    mock_image_open = mock_image.open.return_value
    
    gemini_image_client = GeminiImageClient()
    prompt = "Test image prompt"
    response = gemini_image_client.generate_image(prompt)

    mock_models_instance.generate_content.assert_called_once_with(model='gemini-pro-vision', contents=[f"Generate an image of: {prompt}"])
    mock_image.open.assert_called_once() # Check if Image.open was called
    mock_image_open.save.assert_called_once() # Check if save was called
    assert "gemini_image_testhex.png" in response

@patch('api.infrastructure.gemini_client.GeminiClient.generate_text')
def test_generate_text_endpoint_success(mock_generate_text, client, auth_headers):
    mock_generate_text.return_value = "API Generated Text"
    response = client.post(
        "/api/ai/generate-text",
        headers=auth_headers,
        json={"prompt": "Hello", "model": "gemini"}
    )
    assert response.status_code == 200
    assert response.json()["result"] == "API Generated Text"
    mock_generate_text.assert_called_once_with("Hello", "gemini")

@patch('api.infrastructure.gemini_image_client.GeminiImageClient.generate_image')
def test_generate_image_endpoint_success(mock_generate_image, client, auth_headers):
    mock_generate_image.return_value = "/generated_images/test_image.png"
    response = client.post(
        "/api/ai/generate-image",
        headers=auth_headers,
        json={"prompt": "A beautiful landscape"}
    )
    assert response.status_code == 200
    assert response.json()["image_path"] == "/generated_images/test_image.png"
    mock_generate_image.assert_called_once_with("A beautiful landscape")