import os
import sys
import shutil
import requests
import cv2
import numpy as np
import base64
from config.celery_config import celery_app
from api.schemas import ProductData
from api.infrastructure.llava_client import LlavaClient # Import LlavaClient
from api.config import UPLOAD_DIR # Import UPLOAD_DIR

@celery_app.task(name='workers.vision_worker.process_product_image')
def process_product_image(image_path: str, project_id: str):
    """
    Celery task to process a product image and generate structured data.
    """
    # This task should ideally be refactored to use AnalyzeSpriteUseCase directly
    # or have a more generic image processing flow.
    # For now, it will use LlavaClient directly.

    llava_client = LlavaClient() # Instantiate LlavaClient

    try:
        print(f"Processing image at path: {image_path}")
        
        # --- GEMINI DEBUGGING ---
        import os
        upload_dir = "/app/uploads"
        try:
            print(f"Listing contents of {upload_dir}: {os.listdir(upload_dir)}")
        except Exception as e:
            print(f"Could not list contents of {upload_dir}: {e}")
        print(f"Checking for file existence at {image_path}: {os.path.exists(image_path)}")
        # --- END GEMINI DEBUGGING ---

        # 1. Pre-process the image using OpenCV (if necessary, or pass directly to LlavaClient)
        # For now, we'll assume LlavaClient handles the image data directly.
        
        # 2. Run inference using LlavaClient
        prompt = (
            "You are an expert product cataloger. Analyze the following image of a product "
            "and generate the structured data based on the Pydantic schema. "
            "Provide a concise, SEO-friendly product name, a standard high-level category, "
            "a detailed description of at least 50 words, and a list of 3-5 key features."
        )
        
        response = llava_client.analyze_image(image_path=image_path, prompt=prompt)
        
        if response["status"] == "SUCCESS":
            # This part needs to be adapted to ProductData schema if this task is still for products
            # For now, returning raw response
            print("Inference successful. Cleaning up image file.")
            os.remove(image_path) # Clean up the uploaded file
            return response["response"]
        else:
            raise RuntimeError(f"LLaVA API call failed: {response['error']}")

    except Exception as e:
        print(f"An error occurred in the Celery task: {e}")
        # Clean up the file even if an error occurs
        if os.path.exists(image_path):
            os.remove(image_path)
        raise e # Re-raise the exception so Celery marks the task as FAILED