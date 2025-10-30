from typing import Optional, Any, List
import json
from pydantic import ValidationError

from ..domain.ports import ICeleryClient, IFileStorage, ILlavaClient
from ..domain.models import TaskTicket, TaskStatus, GenerateProductDescriptionRequest

class TestTextWorkerUseCase:
    def __init__(self, celery_client: ICeleryClient):
        self.celery_client = celery_client

    def execute(self) -> dict:
        try:
            task = self.celery_client.send_task(
                'workers.text_worker.generate_product_description',
                kwargs={
                    "product_name_input": "carro de corrida vermelho",
                    "category_hint": None
                }, # Provide both arguments
                queue='text_queue'
            )
            # This is a blocking call, suitable only for a test endpoint
            result = task.get(timeout=300) # 5 minute timeout
            return {"status": "SUCCESS", "result": result}
        except Exception as e:
            return {"status": "FAILURE", "error": str(e)}

class ProcessCatalogIntakeUseCase:
    def __init__(self, celery_client: ICeleryClient, file_storage: IFileStorage):
        self.celery_client = celery_client
        self.file_storage = file_storage

    def execute(self, file_content: Any, original_filename: str, project_id: Optional[str]) -> TaskTicket:
        file_path = self.file_storage.save_file(file_content, original_filename)
        task = self.celery_client.send_task(
            'workers.vision_worker.process_product_image',
            args=[str(file_path), project_id],
            queue='vision_queue'
        )
        return TaskTicket(task_id=task.id, status="PENDING")

class GenerateProductDescriptionUseCase:
    def __init__(self, celery_client: ICeleryClient):
        self.celery_client = celery_client

    def execute(self, request_data: GenerateProductDescriptionRequest) -> TaskTicket:
        task = self.celery_client.send_task(
            'workers.text_worker.generate_product_description',
            args=[request_data.product_name_input, request_data.category_hint],
            queue='text_queue'
        )
        return TaskTicket(task_id=task.id, status="PENDING")

class GetTaskStatusUseCase:
    def __init__(self, celery_client: ICeleryClient):
        self.celery_client = celery_client

    def execute(self, task_id: str) -> TaskStatus:
        return self.celery_client.get_task_status(task_id)
