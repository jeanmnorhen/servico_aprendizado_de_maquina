import os
import uuid
from pathlib import Path
from io import BytesIO
from PIL import Image

import google.generativeai as genai

from ..domain.ports import IImageGenerator

class GeminiImageClient(IImageGenerator):
    def __init__(self):
        # This client uses the same API Key as the text generation client
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel('gemini-1.5-flash') # Using the standard flash model

        # Define and create the directory for generated images
        self.output_dir = Path("generated_images")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_image(self, prompt: str) -> str:
        """Generates an image using the Gemini API."""
        print(f"Generating image with Gemini for prompt: {prompt}")

        try:
            # Prepend the prompt with instructions for the model to generate an image
            generation_prompt = f"Generate an image of: {prompt}"

            response = self.model.generate_content(generation_prompt)

            # Find the part of the response that contains image data
            image_part = None
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_part = part
                    break
            
            if image_part is None:
                # If no image is returned, the model might have just responded with text.
                # We can either raise an error or return the text.
                text_response = response.text
                raise RuntimeError(f"Model did not return an image. It responded with: '{text_response}'")

            # Process the image data
            image_bytes = image_part.inline_data.data
            image = Image.open(BytesIO(image_bytes))

            # Generate a unique filename and save the image
            image_filename = f"gemini_image_{uuid.uuid4().hex}.png"
            image_path = self.output_dir / image_filename
            image.save(image_path)
            
            print(f"Image saved to {image_path}")

            # Return the web-accessible path
            return f"/{self.output_dir.name}/{image_filename}"

        except Exception as e:
            print(f"Error generating image with Gemini: {e}")
            raise RuntimeError(f"Failed to generate image with Gemini: {e}")
