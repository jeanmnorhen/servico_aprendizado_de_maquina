# D:\Oficina\servico-ia-unificado\api\infrastructure\file_storage.py

import uuid
import shutil
from pathlib import Path
from typing import Any

from ..domain.ports import IFileStorage

UPLOAD_DIR = Path("/app/uploads") # This will be a Docker volume

class LocalFileStorage(IFileStorage):
    def save_file(self, file_content: Any, original_filename: str) -> str:
        # Ensure the upload directory exists
        UPLOAD_DIR.mkdir(exist_ok=True)

        file_extension = Path(original_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file_content, buffer)
        
        return str(file_path)
