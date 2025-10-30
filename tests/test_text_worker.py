import pytest
import json
from unittest.mock import patch, MagicMock
import os
import sys

from pydantic import ValidationError

# Add the service's root directory to the path to allow for relative imports
service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from workers.text_worker import process_animation_script
from api.schemas import AnimationSceneDescription, AnimationProcessRequest

@pytest.fixture
def sample_request_data() -> dict:
    """Provides a sample request dictionary for the animation task."""
    return {
        "script": "Um personagem anda para a direita e depois para a esquerda.",
        "project_id": "proj-123",
        "current_animation_state": None
    }

@pytest.fixture
def valid_ai_response() -> str:
    """Provides a valid JSON string that conforms to the AnimationSceneDescription schema."""
    return json.dumps({
        "scene_id": "scene-001",
        "background_type": "Graphics",
        "background_data": [{"shape": "rect", "params": [0, 0, 800, 600], "fill": "0x1099bb"}],
        "assets": [
            {
                "asset_id": "heroi",
                "type": "CharacterModular",
                "parts": [
                    { "part_id": "tronco", "shape": "rect", "params": [0, 0, 50, 100], "fill": "0x0000FF" },
                    { "part_id": "cabeça", "shape": "circle", "params": [25, -25, 25], "fill": "0xFF0000" }
                ],
                "position": { "x": 0.2, "y": 0.8 },
                "z_index": 10
            }
        ],
        "animation_steps": [
            {
                "target_id": "heroi",
                "action": "to",
                "duration": 2.0,
                "params": { "x": 0.8 }
            }
        ]
    })

@pytest.fixture
def invalid_ai_response_schema() -> str:
    """Provides an invalid JSON string with missing fields."""
    return json.dumps({
        "scene_id": "scene-002",
        # Missing background_type, assets, etc.
        "animation_steps": []
    })

@patch('workers.text_worker.OllamaClient')
def test_process_animation_script_success(mock_ollama_client, sample_request_data, valid_ai_response):
    """Tests the successful processing of an animation script."""
    # Configure the mock
    mock_instance = mock_ollama_client.return_value
    mock_instance.generate.return_value = {"status": "SUCCESS", "response": valid_ai_response}

    # Execute the task
    result = process_animation_script(sample_request_data)

    # Assertions
    mock_instance.generate.assert_called_once()
    assert isinstance(result, dict)
    assert result['scene_id'] == "scene-001"
    assert len(result['assets']) == 1
    assert result['assets'][0]['asset_id'] == "heroi"

@patch('workers.text_worker.OllamaClient')
def test_process_animation_script_validation_error(mock_ollama_client, sample_request_data, invalid_ai_response_schema):
    """Tests that a Pydantic ValidationError is handled correctly."""
    mock_instance = mock_ollama_client.return_value
    mock_instance.generate.return_value = {"status": "SUCCESS", "response": invalid_ai_response_schema}

    with pytest.raises(ValueError) as excinfo:
        process_animation_script(sample_request_data)
    
    assert "did not match the AnimationSceneDescription schema" in str(excinfo.value)

@patch('workers.text_worker.OllamaClient')
def test_process_animation_script_json_decode_error(mock_ollama_client, sample_request_data):
    """Tests that a JSON decoding error is handled correctly."""
    mock_instance = mock_ollama_client.return_value
    mock_instance.generate.return_value = {"status": "SUCCESS", "response": "this is not json"}

    with pytest.raises(ValueError) as excinfo:
        process_animation_script(sample_request_data)
    
    assert "was not valid JSON" in str(excinfo.value)

@patch('workers.text_worker.OllamaClient')
def test_process_animation_script_ollama_failure(mock_ollama_client, sample_request_data):
    """Tests handling of a failure response from the Ollama client."""
    mock_instance = mock_ollama_client.return_value
    mock_instance.generate.return_value = {"status": "FAILURE", "error": "Ollama is down"}

    with pytest.raises(RuntimeError) as excinfo:
        process_animation_script(sample_request_data)
    
    assert "Ollama API call failed" in str(excinfo.value)
