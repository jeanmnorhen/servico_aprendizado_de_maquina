from typing import Optional
from celery import Celery # Keep this for type hinting if needed
from celery.result import AsyncResult # Add this import
import os
from config.celery_config import celery_app # Import the global instance

from ..domain.ports import ICeleryClient
from ..domain.models import TaskTicket, TaskStatus

class CeleryClient(ICeleryClient):
    def __init__(self):
        self.celery_app = celery_app # Use the global instance

    def send_task(self, name: str, args: Optional[list] = None, kwargs: Optional[dict] = None, queue: Optional[str] = None) -> AsyncResult:
        task_result = self.celery_app.send_task(name, args=args, kwargs=kwargs, queue=queue)
        return task_result

    def get_task_status(self, task_id: str) -> TaskStatus:
        task_result = AsyncResult(task_id, app=self.celery_app)

        if task_result.ready():
            if task_result.successful():
                return TaskStatus(
                    task_id=task_id,
                    status="SUCCESS",
                    result=task_result.get(),
                    error=None
                )
            else:
                error_info = str(task_result.result)
                return TaskStatus(
                    task_id=task_id,
                    status="FAILURE",
                    result=None,
                    error=error_info
                )
        else:
            return TaskStatus(
                task_id=task_id,
                status="PENDING",
                result=None,
                error=None
            )