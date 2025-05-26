# communication_manager.py

import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from utils import get_logger

class CommunicationManager:
    _instance = None

    def __init__(self):
        self.clients = set()
        self.services = {}
        self.logger = get_logger("CommunicationManager")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_service(self, message_type: str, service):
        """Register a handler service for a specific message type."""
        self.services[message_type] = service
        self.logger.info(f"Registered service for type '{message_type}': {service.__class__.__name__}")

    async def register_client(self, websocket: WebSocket):
        await websocket.accept()
        self.clients.add(websocket)
        self.logger.info(f"Client connected: {websocket.client}")
        self.logger.info(f"[Client registered] Total: {len(self.clients)}")

    async def unregister_client(self, websocket: WebSocket):
        self.clients.discard(websocket)
        self.logger.info(f"Client disconnected: {websocket.client}")
        self.logger.info(f"[Client Unregistered] Total: {len(self.clients)}")

    async def send_to_all(self, data: dict):
        self.logger.info(f"Clients : [{self.clients}]")
        for client in list(self.clients):
            try:
                self.logger.info(f"[Sending] : {data}")
                await client.send_json(data)
            except Exception as e:
                self.logger.error(f"Failed to send to {client.client}: {e}")
                await self.unregister_client(client)

    # async def send(self, data: dict):
    #     if self.connection is None:
    #         return False
    #     async with self._lock:
    #         try:
    #             await self.connection.send(json.dumps(data))
    #             return True
    #         except Exception as e:
    #             self.logger.error(f"[Send Failed]: {e}")
    #             return False
    async def handle_connection(self, websocket: WebSocket):
        await self.register_client(websocket)
        try:
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)
                await self.route_message(data)
        except WebSocketDisconnect:
            await self.unregister_client(websocket)
        except Exception as e:
            self.logger.error(f"Error in WebSocket handler: {e}")

    async def route_message(self, data: dict):
        msg_type = data.get("type")
        service = self.services.get(msg_type)
        if service:
            await service.handle(data)
        else:
            self.logger.warning(f"No handler registered for message type: {msg_type}")
