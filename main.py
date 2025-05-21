from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import asyncio

from joystick_reader import monitor_joystick  # Assuming this function exists in joystick.py

app = FastAPI()
clients = set()  # Assuming only one client for now

# --- Client Manager Functions ---

async def register_client(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    print(f"Client connected: {websocket}")

async def unregister_client(websocket: WebSocket):
    clients.remove(websocket)
    print(f"Client disconnected: {websocket}")

async def send_to_clients(data: str, dtype: str='text'):
    print(f"[Server] Sending: {data}")
    for client in clients.copy():
        try:
            if dtype=='json':
                await client.send_json(data)
            else:
                await client.send_text(str(data))
        except Exception as e:
            print(f"Error sending to {client}: {e}")
            await unregister_client(client)

# --- WebSocket Endpoint ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await register_client(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"[Server] Received from client: {data}")
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        await unregister_client(websocket)

# --- Startup Event ---

@app.on_event("startup")
async def startup_event():
    print("[Server] Starting joystick monitor...")
    asyncio.create_task(monitor_joystick(send_to_clients))

# --- Run the Server ---

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
