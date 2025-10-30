import os
from pathlib import Path
import google.generativeai as genai
from PIL import Image

from ..domain.ports import ITextGenerator, IGeminiClient # Implement both for now

class GeminiClient(ITextGenerator, IGeminiClient):
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        genai.configure(api_key=api_key)
        
        # Model for text generation
        self.text_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        # Model for vision (image analysis)
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')

    def generate_text(self, prompt: str, model: str = 'gemini-1.5-flash-latest') -> str:
        # The 'model' parameter is for interface compatibility, but this client uses its configured model.
        try:
            response = self.text_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating text with Gemini API: {e}")
            raise RuntimeError(f"Failed to generate text with Gemini API: {e}")

    def analyze_image(self, image_path: str, prompt: str) -> str:
        try:
            img = Image.open(image_path)
            response = self.vision_model.generate_content([prompt, img])
            return response.text
        except FileNotFoundError:
            print(f"Error: Image file not found at {image_path}")
            raise
        except Exception as e:
            print(f"Error analyzing image with Gemini API: {e}")
            raise RuntimeError(f"Failed to analyze image with Gemini API: {e}")
