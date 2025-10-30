# D:\Oficina\servico-ia-unificado\api\main.py

from fastapi import FastAPI
from .presentation import endpoints
import os
import uvicorn

from fastapi.staticfiles import StaticFiles

# --- Ngrok Tunnel (for local development) ---
# In a production environment, you would not use Ngrok.
# This allows exposing the local Docker container to a public URL for Vercel.
if os.environ.get("ENVIRONMENT") == "development":
    from pyngrok import ngrok
    
    NGROK_AUTHTOKEN = os.environ.get("NGROK_AUTHTOKEN")
    if not NGROK_AUTHTOKEN:
        print("NGROK_AUTHTOKEN is not set, skipping ngrok tunnel.")
    else:
        ngrok.set_auth_token(NGROK_AUTHTOKEN)
        # Open a tunnel to the port your FastAPI app is running on
        public_url = ngrok.connect(8000, "http")
        print(f" * Ngrok tunnel available at: {public_url}")
# --------------------------------------------

app = FastAPI(
    title="Serviço de Aprendizado de Máquina",
    description="Um serviço para orquestrar modelos de IA e workers.",
    version="0.1.0"
)

# Mount static files directory for generated images
app.mount("/generated_images", StaticFiles(directory="generated_images"), name="generated_images")

app.include_router(endpoints.router)

@app.on_event("startup")
async def startup_event():
    print("API is starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    print("API is shutting down...")
    # Disconnect Ngrok tunnel if it's running
    if os.environ.get("ENVIRONMENT") == "development" and os.environ.get("NGROK_AUTHTOKEN"):
        ngrok.disconnect_all()
        print("Ngrok tunnels disconnected.")