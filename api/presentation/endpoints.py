# D:\Oficina\servico-ia-unificado\api\presentation\endpoints.py

import os
import traceback
from pathlib import Path # Import Path

from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Security, status, Form

from fastapi.security import APIKeyHeader



from ..application.use_cases import (



    ProcessAnimationScriptUseCase,



    ProcessCatalogIntakeUseCase,



    GetTaskStatusUseCase,



    GenerateProductDescriptionUseCase,



    TestTextWorkerUseCase,



    AnalyzeSpriteUseCase,



    GenerateImageUseCase # Import GenerateImageUseCase



)



from ..domain.models import (



    TaskTicket,



    TaskStatus,



    AnimationProcessRequest,



    GenerateProductDescriptionRequest



)



from ..domain.ports import ICeleryClient, ILlavaClient, ISpriteCatalogService, IImagenClient # Import IImagenClient



from ..infrastructure.celery_client import CeleryClient



from ..infrastructure.file_storage import LocalFileStorage



from ..infrastructure.llava_client import LlavaClient



from ..infrastructure.supabase.supabase_sprite_catalog_service import SupabaseSpriteCatalogService



from ..infrastructure.gemini_imagen_client import GeminiImagenClient # Import GeminiImagenClient



from ..schemas import SpriteAnalysisResult, GenerateImageRequest # Import GenerateImageRequest







from config.celery_config import celery_app # Import the global celery_app







router = APIRouter()







# --- Security ---



API_KEY_NAME = "X-API-KEY"



api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)







async def get_api_key(api_key: str = Security(api_key_header)):



    expected_api_key = os.environ.get("INTERNAL_SERVICE_SECRET")



    if not expected_api_key or api_key != expected_api_key:



        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key")



    return api_key







from ..config import UPLOAD_DIR # Import UPLOAD_DIR from config.py







# --- Dependency Injection (Manual) ---



def get_celery_client() -> CeleryClient:



    return CeleryClient()







def get_file_storage() -> LocalFileStorage:



    return LocalFileStorage()







def get_llava_client() -> LlavaClient:



    return LlavaClient()







def get_sprite_catalog_service() -> SupabaseSpriteCatalogService:



    return SupabaseSpriteCatalogService(UPLOAD_DIR)







def get_imagen_client() -> GeminiImagenClient:



    return GeminiImagenClient()







# --- API Endpoints ---







@router.get("/api/ai/send-simple-task", tags=["Test"])



def send_simple_task_endpoint(celery_client: ICeleryClient = Depends(get_celery_client)):



    """



    Endpoint to send a very simple task to the worker.



    """



    try:



        task = celery_client.send_task(



            'workers.text_worker.simple_test_task',



            queue='text_queue' # Add queue argument back



        )



        return {"status": "SUCCESS", "message": f"Simple task sent with ID: {task.id}. Check worker logs."}



    except Exception as e:



        return {"status": "FAILURE", "error": f"Failed to send simple task: {str(e)}"}







@router.get("/api/ai/celery-ping", tags=["Test"])



def celery_ping_endpoint():



    """



    Endpoint to test Celery broker connectivity.



    """



    try:



        with celery_app.connection() as connection:



            connection.info()



        return {"status": "SUCCESS", "message": "Celery broker connected successfully."}



    except Exception as e:



        return {"status": "FAILURE", "error": f"Failed to connect to Celery broker: {str(e)}"}







@router.get("/api/test-text-worker", tags=["Test"])



def test_text_worker_endpoint(



    celery_client: ICeleryClient = Depends(get_celery_client)



):



    """



    Endpoint to test the text worker with a simple, blocking task.



    """



    use_case = TestTextWorkerUseCase(celery_client)



    return use_case.execute()







@router.get("/api/health")



def health_check():



    return {"status": "ok"}







@router.post("/api/ai/animation-script", response_model=TaskTicket, status_code=status.HTTP_202_ACCEPTED)



async def process_animation_script_endpoint(



    request_data: AnimationProcessRequest,



    api_key: str = Depends(get_api_key),



    celery_client: ICeleryClient = Depends(get_celery_client)



):



    use_case = ProcessAnimationScriptUseCase(celery_client)



    return use_case.execute(request_data)







@router.post("/api/ai/catalog-intake", response_model=TaskTicket, status_code=status.HTTP_202_ACCEPTED)



async def process_catalog_intake_endpoint(



    file: UploadFile = File(...),



    project_id: Optional[str] = Form(None),



    api_key: str = Depends(get_api_key),



    celery_client: ICeleryClient = Depends(get_celery_client),



    file_storage: LocalFileStorage = Depends(get_file_storage)



):



    use_case = ProcessCatalogIntakeUseCase(celery_client, file_storage)



    try:



        return use_case.execute(file.file, file.filename, project_id)



    except Exception as e:



        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process file: {str(e)}")







@router.post("/api/ai/generate-product-description", response_model=TaskTicket, status_code=status.HTTP_202_ACCEPTED)



async def generate_product_description_endpoint(



    request_data: GenerateProductDescriptionRequest,



    api_key: str = Depends(get_api_key),



    celery_client: ICeleryClient = Depends(get_celery_client)



):



    use_case = GenerateProductDescriptionUseCase(celery_client)



    return use_case.execute(request_data)







@router.post("/api/ai/analyze-sprite", response_model=SpriteAnalysisResult, status_code=status.HTTP_200_OK)



async def analyze_sprite_endpoint(



    file: UploadFile = File(...),



    api_key: str = Depends(get_api_key),



    file_storage: LocalFileStorage = Depends(get_file_storage),



    llava_client: ILlavaClient = Depends(get_llava_client),



    sprite_catalog_service: ISpriteCatalogService = Depends(get_sprite_catalog_service)



):



    """Analyzes an uploaded sprite image using LLaVA and returns structured metadata."""



    try:



        # Save the uploaded file temporarily



        temp_file_path = file_storage.save_file(file.file, file.filename)



        



        # Use the AnalyzeSpriteUseCase to process the image



        use_case = AnalyzeSpriteUseCase(llava_client, sprite_catalog_service)



        analysis_result = use_case.execute(temp_file_path)



        



        # Optionally, delete the temporary file after analysis



        os.remove(temp_file_path)







        return analysis_result



    except Exception as e:



        print(f"Error in analyze_sprite_endpoint: {e}")



        traceback.print_exc()



        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to analyze sprite: {str(e)}")







@router.post("/api/ai/generate-image", response_model=dict, status_code=status.HTTP_202_ACCEPTED)



async def generate_image_endpoint(



    request_data: GenerateImageRequest,



    api_key: str = Depends(get_api_key),



    imagen_client: IImagenClient = Depends(get_imagen_client),



    celery_client: ICeleryClient = Depends(get_celery_client),



    sprite_catalog_service: ISpriteCatalogService = Depends(get_sprite_catalog_service)



):



    """Generates an image from a text prompt using Imagen and triggers LLaVA analysis."""



    try:



        use_case = GenerateImageUseCase(imagen_client, celery_client, sprite_catalog_service)



        result = use_case.execute(request_data.prompt, request_data.aspect_ratio, request_data.person_generation)



        return result



    except Exception as e:



        print(f"Error in generate_image_endpoint: {e}")



        traceback.print_exc()



        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate image: {str(e)}")







@router.get("/api/ai/sprites-catalog", response_model=List[SpriteAnalysisResult], status_code=status.HTTP_200_OK)



async def get_sprites_catalog_endpoint(



    api_key: str = Depends(get_api_key),



    sprite_catalog_service: ISpriteCatalogService = Depends(get_sprite_catalog_service)



):



    """Retrieves all analyzed sprite metadata from the catalog."""



    try:



        catalog = sprite_catalog_service.get_all_sprites_metadata()



        return catalog



    except Exception as e:



        print(f"Error in get_sprites_catalog_endpoint: {e}")



        traceback.print_exc()



        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve sprite catalog: {str(e)}")







@router.delete("/api/ai/sprites/{image_path:path}", status_code=status.HTTP_204_NO_CONTENT)



async def delete_sprite_endpoint(



    image_path: str,



    api_key: str = Depends(get_api_key),



    sprite_catalog_service: ISpriteCatalogService = Depends(get_sprite_catalog_service)



):



    """Deactivates a sprite and moves its physical file to an archive directory."""



    try:



        # Deactivate sprite in Supabase



        sprite_catalog_service.deactivate_sprite(image_path)







        # Move physical file to archive



        public_sprites_dir = Path("/app/Projeto_O_Cocriador/public/sprites")



        archive_dir = Path("/app/Projeto_O_Cocriador/public/sprites_archive")



        archive_dir.mkdir(parents=True, exist_ok=True)







        # Construct full paths



        source_path = public_sprites_dir / image_path.lstrip('/')



        destination_path = archive_dir / image_path.lstrip('/')







        if source_path.exists():



            # Ensure destination directory exists



            destination_path.parent.mkdir(parents=True, exist_ok=True)



            os.rename(source_path, destination_path)



            print(f"Moved {source_path} to {destination_path}")



        else:



            print(f"Warning: Physical file not found at {source_path}")







        return {"message": "Sprite deactivated and archived successfully"}



    except Exception as e:



        print(f"Error in delete_sprite_endpoint: {e}")



        traceback.print_exc()



        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete sprite: {str(e)}")







@router.get("/api/ai/status/{task_id}", response_model=TaskStatus)



async def get_task_status(



    task_id: str,



    api_key: str = Depends(get_api_key),



    celery_client: ICeleryClient = Depends(get_celery_client)



):



    use_case = GetTaskStatusUseCase(celery_client)



    return use_case.execute(task_id)
