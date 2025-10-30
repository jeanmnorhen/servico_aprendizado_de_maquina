# D:\Oficina\servico-ia-unificado\api\main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .presentation.endpoints import router
from .config import UPLOAD_DIR # Import UPLOAD_DIR from config.py

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Serviço de IA Unificado (Clean Arch)",
    description="API para processamento de IA de texto e multimodal.",
    version="2.0.0"
)

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Parameterize this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router from the presentation layer
app.include_router(router)