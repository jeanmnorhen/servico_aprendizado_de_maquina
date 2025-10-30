# D:\Oficina\servico-ia-unificado\api\domain\models.py

from typing import Optional, List
from pydantic import BaseModel

# --- Task Management --- #

class TaskTicket(BaseModel):
    task_id: str
    status: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None

# --- Text Processing --- #

class AnimationProcessRequest(BaseModel):
    script: str
    project_id: Optional[str] = None

class GenerateProductDescriptionRequest(BaseModel):
    product_name_input: str
    category_hint: Optional[str] = None

class Keyframe(BaseModel):
    character_name: str
    x: int
    y: int
    rotation: float = 0.0

class KeyframeList(BaseModel):
    keyframes: List[Keyframe]

# --- Vision Processing --- #

class ProductData(BaseModel):
    product_name: str
    category: str
    description: str
    features: List[str]
