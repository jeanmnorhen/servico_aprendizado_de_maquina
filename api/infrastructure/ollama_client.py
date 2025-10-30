import requests
import json

from ..domain.ports import ITextGenerator

class OllamaClient(ITextGenerator):
    def __init__(self):
        self.api_url = "http://ollama:11434"

    def generate_text(self, prompt: str, model: str) -> str:
        """Generates text using the Ollama API with a specified model."""
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.api_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            lines = response.text.strip().split('\n')
            last_line = json.loads(lines[-1])
            
            return last_line.get("message", {}).get("content", "")
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama API: {e}")
            raise RuntimeError(f"Failed to generate text with Ollama model {model}: {e}")
        except json.JSONDecodeError as e:
            print(f"Error decoding Ollama response: {e}")
            raise RuntimeError(f"Failed to decode Ollama response: {response.text}")

