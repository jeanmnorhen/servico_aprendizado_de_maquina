import os
import uuid
from pathlib import Path
from io import BytesIO
from PIL import Image

import google.genai as genai
from google.api_core.exceptions import ResourceExhausted # Import ResourceExhausted
from fastapi import HTTPException, status # Import HTTPException and status

from ..domain.ports import IImageGenerator

class GeminiImageClient(IImageGenerator):
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        
        self.client = genai.Client(api_key=api_key)

    def generate_image(self, prompt: str) -> str:
        """Generates an image using the Gemini API."""
        print(f"Generating image with Gemini for prompt: {prompt}")

        try:
            # Prepend the prompt with instructions for the model to generate an image
            generation_prompt = f"Generate an image of: {prompt}"

            response = self.client.models.generate_content(
                model='gemini-pro-vision', # Or appropriate model for image generation
                contents=[generation_prompt] # Pass prompt as a list
            )

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

            # Define and create the directory for generated images
            output_dir = Path("generated_images")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate a unique filename and save the image
            image_filename = f"gemini_image_{uuid.uuid4().hex}.png"
            image_path = output_dir / image_filename
            image.save(image_path)
            
            print(f"Image saved to {image_path}")

            # Return the web-accessible path
            return f"/{output_dir.name}/{image_filename}"

        except ResourceExhausted as e: # Catch specific quota error
            print(f"Quota exceeded for Gemini API: {e}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Quota exceeded for Gemini API: {e}"
            )
        except Exception as e:
            print(f"Error generating image with Gemini: {e}")
            raise RuntimeError(f"Failed to generate image with Gemini: {e}")
