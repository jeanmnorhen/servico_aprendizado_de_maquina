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



# --- Persistence --- #

class ChatHistory(BaseModel):
    session_id: str
    human_message: str
    ai_message: str

