import os
from pathlib import Path
import google.genai as genai
from PIL import Image
from google.api_core.exceptions import ResourceExhausted # Import ResourceExhausted
from fastapi import HTTPException, status # Import HTTPException and status

from ..domain.ports import ITextGenerator, IGeminiClient # Implement both for now

class GeminiClient(ITextGenerator, IGeminiClient):
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        
        self.client = genai.Client(api_key=api_key)
        
    def generate_text(self, prompt: str, model: str = 'gemini-pro') -> str:
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt
            )
            return response.text
        except ResourceExhausted as e: # Catch specific quota error
            print(f"Quota exceeded for Gemini API: {e}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Quota exceeded for Gemini API: {e}"
            )
        except Exception as e:
            print(f"Error generating text with Gemini API: {e}")
            raise RuntimeError(f"Failed to generate text with Gemini API: {e}")

    def analyze_image(self, image_path: str, prompt: str) -> str:
        try:
            img = Image.open(image_path)
            response = self.client.models.generate_content(
                model='gemini-pro-vision',
                contents=[prompt, img]
            )
            return response.text
        except FileNotFoundError:
            print(f"Error: Image file not found at {image_path}")
            raise
        except ResourceExhausted as e: # Catch specific quota error
            print(f"Quota exceeded for Gemini API: {e}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Quota exceeded for Gemini API: {e}"
            )
        except Exception as e:
            print(f"Error analyzing image with Gemini API: {e}")
            raise RuntimeError(f"Failed to analyze image with Gemini API: {e}")
