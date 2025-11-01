import os
import ollama # Import the official ollama library

from ..domain.ports import ITextGenerator

class OllamaClient(ITextGenerator):
    def __init__(self):
        self.api_url = os.environ.get("OLLAMA_API_URL", "http://ollama:11434")
        self.client = ollama.Client(host=self.api_url) # Initialize the official client

    def generate_text(self, prompt: str, model: str = "gemma:2b") -> str:
        """Generates text using the Ollama API with a specified model."""
        try:
            response = self.client.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=False
            )
            return response['message']['content']
        except ollama.ResponseError as e:
            print(f"Error calling Ollama API: {e}")
            raise RuntimeError(f"Failed to generate text with Ollama model {model}: {e}")
        except Exception as e:
            print(f"Error during Ollama text generation: {e}")
            raise RuntimeError(f"Failed to generate text with Ollama model {model}: {e}")