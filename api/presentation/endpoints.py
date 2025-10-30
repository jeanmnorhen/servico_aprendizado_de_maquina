# D:\Oficina\servico-ia-unificado\api\presentation\endpoints.py

import os
import traceback
from pathlib import Path # Import Path

from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Security, status, Form, Body

from fastapi.security import APIKeyHeader



from ..application.use_cases import (
    GetTaskStatusUseCase,
    GenerateProductDescriptionUseCase,
    TestTextWorkerUseCase
)
from ..application.gemini_use_cases import GenerateTextUseCase # Import new use case

from ..domain.models import (
    TaskTicket,
    TaskStatus,
    GenerateProductDescriptionRequest
)

from ..infrastructure.model_factory import ModelFactory # Import the factory

from config.celery_config import celery_app # Import the global celery_app

from pydantic import BaseModel # Import BaseModel for request body


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

def get_chat_repository() -> IChatRepository: # Add dependency injector for Repository
    return PostgresChatRepository()

def get_model_factory() -> ModelFactory: # Add dependency injector for Factory
    return ModelFactory()

# --- Request Models ---
class GenerateTextRequest(BaseModel):
    prompt: str
    model: str # Add model field
    session_id: Optional[str] = None

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



@router.post("/api/ai/generate-product-description", response_model=TaskTicket, status_code=status.HTTP_202_ACCEPTED)

async def generate_product_description_endpoint(

    request_data: GenerateProductDescriptionRequest,

    api_key: str = Depends(get_api_key),

    celery_client: ICeleryClient = Depends(get_celery_client)

):

    use_case = GenerateProductDescriptionUseCase(celery_client)

    return use_case.execute(request_data)

@router.post("/api/ai/generate-text", tags=["AI"])
async def generate_text_endpoint(
    request: GenerateTextRequest,
    api_key: str = Depends(get_api_key),
    model_factory: ModelFactory = Depends(get_model_factory),
    chat_repo: IChatRepository = Depends(get_chat_repository)
):
    """
    Generates text using a specified model (e.g., 'gemini', 'codellama').
    """
    use_case = GenerateTextUseCase(model_factory, chat_repo)
    result = use_case.execute(request.prompt, request.model, request.session_id)
    if result["status"] == "FAILURE":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return result

@router.get("/api/ai/status/{task_id}", response_model=TaskStatus)

async def get_task_status(

    task_id: str,

    api_key: str = Depends(get_api_key),

    celery_client: ICeleryClient = Depends(get_celery_client)

):

    use_case = GetTaskStatusUseCase(celery_client)

    return use_case.execute(task_id)

from ..application.image_use_cases import GenerateImageUseCase
from ..domain.ports import IImageGenerator
from ..infrastructure.gemini_image_client import GeminiImageClient

def get_image_generator() -> IImageGenerator:
    return GeminiImageClient()

class GenerateImageRequest(BaseModel):
    prompt: str

@router.post("/api/ai/generate-image", tags=["AI"])
async def generate_image_endpoint(
    request: GenerateImageRequest,
    api_key: str = Depends(get_api_key),
    image_generator: IImageGenerator = Depends(get_image_generator)
):
    """
    Generates an image using the Vertex AI Imagen model.
    """
    use_case = GenerateImageUseCase(image_generator)
    result = use_case.execute(request.prompt)
    if result["status"] == "FAILURE":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return result

