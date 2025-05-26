# rover_server.py

import uvicorn
from fastapi import FastAPI, WebSocket
import asyncio

from utils import get_logger
from communication_manager import CommunicationManager
from services.image_service import ImageService
from services.joystick_control_service import JoystickControlService




app = FastAPI()
logger = get_logger("FastServer", console=True)

# --- Initialize Communication Manager ---
comm = CommunicationManager.get_instance()
comm.register_service("camera_frame", ImageService())

manual = JoystickControlService()
comm.register_service("manual_control", manual)
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(manual.start())  # Safe now

# --- WebSocket Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await comm.handle_connection(websocket)

# --- Health Check ---
@app.get("/health")
async def health():
    return {"status": "ok"}

# --- Run the App ---
if __name__ == "__main__":
    logger.info("Starting Rover Server...")
    uvicorn.run("rover_server:app", host="0.0.0.0", port=8000, reload=True)
