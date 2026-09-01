import asyncio
import json
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from ..config import settings

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.user_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        for user_id, conns in list(self.user_connections.items()):
            conns.discard(websocket)
            if not conns:
                del self.user_connections[user_id]

    def authenticate_user(self, user_id: str, websocket: WebSocket):
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        payload = json.dumps(message)
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)


manager = ConnectionManager()


@router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Welcome message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Connected to Samachar Real-Time Fact & News Wire",
            "timestamp": asyncio.get_event_loop().time()
        }))

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "auth":
                    token = msg.get("token")
                    if token:
                        try:
                            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                            user_id = payload.get("sub")
                            if user_id:
                                manager.authenticate_user(user_id, websocket)
                                await websocket.send_text(json.dumps({
                                    "type": "auth_success",
                                    "user_id": user_id
                                }))
                        except JWTError:
                            await websocket.send_text(json.dumps({
                                "type": "auth_error",
                                "message": "Invalid auth token"
                            }))
                elif msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
