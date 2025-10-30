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

from ..domain.ports import ICeleryClient, ILlavaClient, IGeminiClient # Import new port
from ..infrastructure.celery_client import CeleryClient
from ..infrastructure.file_storage import LocalFileStorage
from ..infrastructure.llava_client import LlavaClient
from ..infrastructure.gemini_client import GeminiClient # Import new client

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

def get_gemini_client() -> IGeminiClient: # Add dependency injector for Gemini
    return GeminiClient()

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
    prompt: str = Body(..., embed=True),
    api_key: str = Depends(get_api_key),
    gemini_client: IGeminiClient = Depends(get_gemini_client)
):
    """
    Generates text using the Gemini Pro model.
    """
    use_case = GenerateTextUseCase(gemini_client)
    result = use_case.execute(prompt)
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
