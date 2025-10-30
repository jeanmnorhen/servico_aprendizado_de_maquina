import os
import requests
import json
import base64
import time
from typing import List

class LlavaClient:
    def __init__(self):
        self.api_url = "http://ollama:11434"
        self.model_name = "llava:7b"

    def _ensure_model_downloaded(self):
        print(f"Ensuring Ollama model {self.model_name} is downloaded...")
        try:
            # Check if model is already available
            response = requests.get(f"{self.api_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            if any(m.get("name") == self.model_name for m in models):
                print(f"Ollama model {self.model_name} is already downloaded.")
                return

            print(f"Ollama model {self.model_name} not found. Pulling...")
            # Pull the model
            pull_payload = {"name": self.model_name}
            pull_response = requests.post(f"{self.api_url}/api/pull", json=pull_payload, stream=True)
            pull_response.raise_for_status()

            for chunk in pull_response.iter_content(chunk_size=8192):
                if chunk:
                    try:
                        # Ollama streams JSON objects, one per line
                        for line in chunk.decode('utf-8').splitlines():
                            if line.strip():
                                data = json.loads(line)
                                if "status" in data:
                                    print(f"Pulling {self.model_name}: {data['status']}")
                                if "error" in data:
                                    raise Exception(f"Error pulling model: {data['error']}")
                    except json.JSONDecodeError:
                        # Sometimes a chunk might not be a complete JSON line
                        pass
            print(f"Ollama model {self.model_name} pulled successfully.")
            # Give Ollama a moment to load the model after pulling
            time.sleep(5)

        except requests.exceptions.RequestException as e:
            print(f"Error ensuring Ollama model {self.model_name} is downloaded: {e}")
            raise RuntimeError(f"Failed to ensure Ollama model {self.model_name} is downloaded: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during model download: {e}")
            raise RuntimeError(f"An unexpected error occurred during model download: {e}")

    def analyze_image(self, image_path: str, prompt: str, model: str = "llava") -> dict:
        """Analyzes an image using the Ollama LLaVA model."""
        self._ensure_model_downloaded() # Ensure model is downloaded before analysis

        if not os.path.exists(image_path):
            return {"status": "FAILURE", "error": f"Image file not found: {image_path}"}

        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            return {"status": "FAILURE", "error": f"Failed to read or encode image: {e}"}

        payload = {
            "model": self.model_name, # Use the ensured model name
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_data]
                }
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
            
            llava_response_content = last_line.get("message", {}).get("content", "")

            return {"status": "SUCCESS", "response": llava_response_content}
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama LLaVA API: {e}")
            return {"status": "FAILURE", "error": str(e)}
        except json.JSONDecodeError as e:
            print(f"Error decoding LLaVA response: {e}")
            return {"status": "FAILURE", "error": f"Failed to decode response: {response.text}"}
