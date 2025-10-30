from ..domain.ports import ITextGenerator
from .gemini_client import GeminiClient
from .ollama_client import OllamaClient

class ModelFactory:
    def __init__(self):
        # Cache instances to avoid re-creating them on every request
        self._clients = {
            "gemini": GeminiClient(),
            "ollama": OllamaClient()
        }

    def get_text_generator(self, model_name: str) -> ITextGenerator:
        """Gets the appropriate text generator client based on the model name."""
        # Simple logic: if the model is 'gemini', use GeminiClient.
        # Otherwise, assume it's an Ollama model.
        if model_name.lower() == 'gemini':
            return self._clients["gemini"]
        else:
            # For any other model name (e.g., 'codellama', 'gemma'), use the Ollama client.
            # The Ollama client itself will handle which specific model to call.
            return self._clients["ollama"]
