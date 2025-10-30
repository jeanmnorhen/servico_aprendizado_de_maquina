import os
import uuid
from pathlib import Path
from typing import Optional
import google.generativeai as genai
import google.generativeai.types as genai_types
from PIL import Image # Import Pillow for image handling

from ...domain.ports import IImagenClient

class GeminiImagenClient(IImagenClient):
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY") # Assuming GEMINI_API_KEY is set in .env
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest') # Or another suitable image generation model

    def generate_image(self, prompt: str, aspect_ratio: Optional[str] = "1:1", person_generation: Optional[str] = "allow_adult") -> str:
        print(f"Generating image for prompt: {prompt} with aspect_ratio={aspect_ratio}, person_generation={person_generation}")
        
        # Define the directory for generated sprites within the public folder
        generated_sprites_dir = Path("/app/Projeto_O_Cocriador/public/generated_sprites")
        generated_sprites_dir.mkdir(parents=True, exist_ok=True)

        # Generate a unique filename
        image_filename = f"generated_image_{uuid.uuid4().hex}.png"
        image_path = generated_sprites_dir / image_filename

        # Prepare generation config (adjust as per actual Gemini API capabilities for image generation)
        # Note: Parameters like aspect_ratio and person_generation are often handled via prompt engineering
        # or specific API call parameters if the model directly supports them.
        # For Gemini 1.5 Flash Image, we often build them into the text prompt.
        
        # Build a more specific prompt for image generation, including persona generation preferences
        generation_prompt = f"Generate a sprite image for animation: {prompt}. Aspect ratio: {aspect_ratio}. Person generation settings: {person_generation}. The image should be suitable for use as a sprite and have a transparent background if possible."


        try:
            # Use a dummy image generation for now until Gemini API specific image generation is fully integrated
            # For Gemini 1.5 Flash, image generation is usually returned as part of the content
            # or obtained via a specific image generation safety handler.
            # This exact method call may vary depending on the specific model endpoint.
            response = self.model.generate_content(
                [genai_types.Part.create(text=generation_prompt)], # Pass text as a part
                generation_config={
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "top_k": 60,
                },
                safety_settings={}
            )
            
            # Assuming the response contains an image in some format (e.g., base64 or a direct binary)
            # This part is highly dependent on the actual Gemini API response for image generation
            # For demonstration, we'll save a dummy image and log potential content.
            
            # Inspect the response to see if it contains image data
            # For a generative model, it might return text that describes an image or a URL to an image.
            # If it were returning a PIL Image or similar:
            # generated_image_pil = response.candidates[0].content.parts[0].image
            # if generated_image_pil:
            #     generated_image_pil.save(image_path)

            # For now, let's assume the model returns a direct image in one of its parts
            # or a textual description that needs further processing. Given the current setup,
            # a direct image part in text-only models is less likely. We'll use a dummy approach
            # and log the actual text response from the model.
            # The generated image will be a dummy red square.

            # Log the full response for debugging
            print(f"Gemini API raw response: {response.text}")
            
            # Placeholder: create a dummy image
            img = Image.new('RGB', (512, 512), color = 'red') 
            img.save(image_path)
            print(f"Dummy image saved to {image_path}")

            # Return the relative path that the frontend expects
            return f"/generated_sprites/{image_filename}"

        except Exception as e:
            print(f"Error generating image with Gemini API: {e}")
            raise RuntimeError(f"Failed to generate image with Gemini API: {e}")