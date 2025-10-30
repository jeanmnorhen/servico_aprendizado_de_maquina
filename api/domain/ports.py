# D:\Oficina\servico-ia-unificado\api\domain\ports.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from .models import TaskTicket, TaskStatus
from ..schemas import SpriteAnalysisResult # Import SpriteAnalysisResult

from celery.result import AsyncResult

class ICeleryClient:
    def send_task(self, name: str, args: Optional[list] = None, kwargs: Optional[dict] = None, queue: Optional[str] = None) -> AsyncResult:
        pass

    @abstractmethod
    def get_task_status(self, task_id: str) -> TaskStatus:
        pass

class IFileStorage(ABC):
    @abstractmethod
    def save_file(self, file_content: Any, filename: str) -> str:
        """Saves a file and returns its path."""
        pass

class ILlavaClient(ABC):
    @abstractmethod
    def analyze_image(self, image_path: str, prompt: str, model: str) -> dict:
        """Analyzes an image using a vision model and returns a text description."""
        pass

from abc import ABC, abstractmethod
from typing import List, Optional

from ..schemas import TaskStatus, SpriteAnalysisResult

class ICeleryClient(ABC):
    @abstractmethod
    def send_task(self, task_name: str, args: list = None, kwargs: dict = None, queue: str = None) -> Any:
        pass

    @abstractmethod
    def get_task_status(self, task_id: str) -> TaskStatus:
        pass

class IFileStorage(ABC):
    @abstractmethod
    def save_file(self, file_content: Any, filename: str) -> str:
        pass

class ILlavaClient(ABC):
    @abstractmethod
    def analyze_image(self, image_path: str, prompt: str, model: str = "llava") -> dict:
        pass

class ISpriteCatalogService(ABC):
    @abstractmethod
    def add_sprite_metadata(self, sprite_metadata: SpriteAnalysisResult, image_path: str) -> None:
        pass

    @abstractmethod
    def get_all_sprites_metadata(self) -> List[SpriteAnalysisResult]:
        pass

    @abstractmethod
    def deactivate_sprite(self, image_path: str) -> None:
        pass

class IImagenClient(ABC):
    @abstractmethod
    def generate_image(self, prompt: str, aspect_ratio: Optional[str] = "1:1", person_generation: Optional[str] = "allow_adult") -> str:
        pass
