import os
import requests
import json
from typing import Optional, List

class OllamaClient:
    def __init__(self):
        self.api_url = "http://ollama:11434"
        self.knowledge_base_path = "/app/knowledge_base/llms-full.txt"
        self.context_window = 4096 # Max characters for the context

    def _search_knowledge_base(self, keywords: List[str]) -> str:
        """Performs a simple keyword search on the knowledge base file."""
        if not os.path.exists(self.knowledge_base_path):
            return ""

        relevant_lines = []
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if any(keyword.lower() in line.lower() for keyword in keywords):
                        relevant_lines.append(line)
        except Exception as e:
            print(f"Error reading knowledge base: {e}")
            return ""

        context = "".join(relevant_lines)
        return context[:self.context_window] # Truncate to fit context window

    def generate(self, prompt: str, model: str = "gemma3", keywords: Optional[List[str]] = None) -> dict:
        """Generates text using the Ollama API, with optional RAG context."""
        
        final_prompt = prompt
        
        if keywords:
            print(f"Searching knowledge base with keywords: {keywords}")
            context = self._search_knowledge_base(keywords)
            if context:
                final_prompt = (
                    f"---\nContext from PixiJS Documentation ---\n"
                    f"{context}\n"
                    f"--- End of Context ---\n\n"
                    f"Based on the context above, please answer the following user request:\n"
                    f"{prompt}"
                )

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": final_prompt}
            ],
            "stream": False # We want the full response at once
        }

        try:
            response = requests.post(
                f"{self.api_url}/api/chat", # Changed to /api/chat
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status() # Raise an exception for bad status codes
            
            # The response from Ollama's /api/chat is a stream of JSON objects, one per line.
            # We take the last one which contains the full response.
            lines = response.text.strip().split('\n')
            last_line = json.loads(lines[-1])
            
            ollama_response_content = last_line.get("message", {}).get("content", "")

            # Extract JSON from markdown code block if present
            import re
            match = re.search(r'```json\n([\s\S]*?)\n```', ollama_response_content)
            if match:
                json_string = match.group(1)
            else:
                json_string = ollama_response_content

            return {"status": "SUCCESS", "response": json_string}
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama API: {e}")
            return {"status": "FAILURE", "error": str(e)}
        except json.JSONDecodeError as e:
            print(f"Error decoding Ollama response: {e}")
            return {"status": "FAILURE", "error": f"Failed to decode response: {response.text}"}
