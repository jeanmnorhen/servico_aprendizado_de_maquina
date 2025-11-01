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

from workers.text_worker import generate_product_description

@pytest.fixture
def sample_product_data() -> dict:
    """Provides a sample product data for the text worker task."""
    return {
        "product_name_input": "carro de corrida vermelho",
        "category_hint": "brinquedo"
    }

@pytest.fixture
def valid_ollama_response() -> str:
    """Provides a valid JSON string that conforms to the expected output."""
    return json.dumps({
        "nome": "Carro de Corrida Vermelho",
        "descrição": "Um carro de corrida vermelho de alta velocidade.",
        "categoria": "Brinquedos"
    })

@pytest.fixture
def invalid_ollama_response_json() -> str:
    """Provides an invalid JSON string."""
    return "this is not json"

@patch('workers.text_worker.OllamaClient')
def test_generate_product_description_success(mock_ollama_client, sample_product_data, valid_ollama_response):
    """Tests the successful generation of a product description."""
    mock_instance = mock_ollama_client.return_value
    mock_instance.generate.return_value = {"status": "SUCCESS", "response": valid_ollama_response}

    result = generate_product_description(sample_product_data["product_name_input"], sample_product_data["category_hint"])

    mock_instance.generate.assert_called_once()
    assert isinstance(result, dict)
    assert result['nome'] == "Carro de Corrida Vermelho"
    assert result['descrição'] == "Um carro de corrida vermelho de alta velocidade."
    assert result['categoria'] == "Brinquedos"

@patch('workers.text_worker.OllamaClient')
def test_generate_product_description_json_decode_error(mock_ollama_client, sample_product_data, invalid_ollama_response_json):
    """Tests that a JSON decoding error is handled correctly."""
    mock_instance = mock_ollama_client.return_value
    mock_instance.generate.return_value = {"status": "SUCCESS", "response": invalid_ollama_response_json}

    with pytest.raises(ValueError) as excinfo:
        generate_product_description(sample_product_data["product_name_input"], sample_product_data["category_hint"])
    
    assert "Ollama response was not valid JSON" in str(excinfo.value)

@patch('workers.text_worker.OllamaClient')
def test_generate_product_description_ollama_failure(mock_ollama_client, sample_product_data):
    """Tests handling of a failure response from the Ollama client."""
    mock_instance = mock_ollama_client.return_value
    mock_instance.generate.return_value = {"status": "FAILURE", "error": "Ollama is down"}

    with pytest.raises(RuntimeError) as excinfo:
        generate_product_description(sample_product_data["product_name_input"], sample_product_data["category_hint"])
    
    assert "Ollama API call failed" in str(excinfo.value)