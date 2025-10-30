import os
import sys
import shutil
import requests
import cv2
import numpy as np
import base64
from config.celery_config import celery_app
from api.schemas import ProductData, SpriteAnalysisResult
from api.infrastructure.supabase.supabase_sprite_catalog_service import SupabaseSpriteCatalogService
from api.infrastructure.llava_client import LlavaClient # Import LlavaClient
from api.config import UPLOAD_DIR # Import UPLOAD_DIR
from api.application.use_cases import AnalyzeSpriteUseCase # Import AnalyzeSpriteUseCase

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

@celery_app.task(name='workers.vision_worker.monitor_sprites_directory')
def monitor_sprites_directory():
    """
    Celery task to monitor the public/sprites directory for new images
    and trigger LLaVA analysis.
    """
    print("Monitoring public/sprites directory for new images...")
    SPRITES_PUBLIC_DIR = "/app/Projeto_O_Cocriador/public/sprites" # Path inside the worker container
    FASTAPI_URL = "http://unified_ai_api:8000" # Docker service name
    API_KEY = os.environ.get("INTERNAL_SERVICE_SECRET")

    if not API_KEY:
        print("INTERNAL_SERVICE_SECRET not set. Cannot analyze sprites.")
        return

    # Initialize Supabase client to check for existing sprites
    # Note: This is a simplified client for checking existence, not for full CRUD
    try:
        supabase_service = SupabaseSpriteCatalogService(UPLOAD_DIR) # UPLOAD_DIR is not used here, but required by constructor
        existing_sprites_metadata = supabase_service.get_all_sprites_metadata()
        existing_sprite_paths = {item.image_path for item in existing_sprites_metadata}
    except Exception as e:
        print(f"Error connecting to Supabase or retrieving existing sprites: {e}")
        return

    for root, _, files in os.walk(SPRITES_PUBLIC_DIR):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                full_path = os.path.join(root, file)
                # Calculate relative path for comparison with Supabase
                relative_path = os.path.relpath(full_path, SPRITES_PUBLIC_DIR)
                frontend_image_path = f"/sprites/{relative_path.replace(os.sep, '/')}"

                if frontend_image_path not in existing_sprite_paths:
                    print(f"New sprite detected: {full_path}. Triggering analysis...")
                    try:
                        with open(full_path, 'rb') as f:
                            files = {'file': (file, f, 'image/png')}
                            headers = {'X-API-Key': API_KEY}
                            response = requests.post(f"{FASTAPI_URL}/api/ai/analyze-sprite", files=files, headers=headers, timeout=60)
                            response.raise_for_status()
                            print(f"Successfully triggered analysis for {file}")
                    except requests.exceptions.RequestException as e:
                        print(f"Error triggering analysis for {file}: {e}")
                    except Exception as e:
                        print(f"An unexpected error occurred for {file}: {e}")
                else:
                    print(f"Sprite {file} already processed. Skipping.")

@celery_app.task(name='workers.vision_worker.analyze_generated_image')
def analyze_generated_image(image_path: str):
    """
    Celery task to analyze a newly generated image and add its metadata to the sprite catalog.
    """
    llava_client = LlavaClient()
    supabase_service = SupabaseSpriteCatalogService(UPLOAD_DIR)
    use_case = AnalyzeSpriteUseCase(llava_client, supabase_service)

    try:
        print(f"Analyzing generated image at path: {image_path}")
        analysis_result = use_case.execute(image_path)
        print(f"Successfully analyzed generated image: {analysis_result.name}")
        return analysis_result.model_dump()
    except Exception as e:
        print(f"Error analyzing generated image {image_path}: {e}")
        raise e