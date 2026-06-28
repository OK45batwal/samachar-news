import json
import logging
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)
        logger.info("WebSocket connected (%d active)", len(self.active))

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)
        logger.info("WebSocket disconnected (%d active)", len(self.active))

    async def broadcast(self, message: dict):
        dead = set()
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self.active -= dead

    async def broadcast_news_alert(self, article: dict):
        await self.broadcast({
            "type": "news_alert",
            "data": article,
        })

    async def broadcast_stats_update(self, stats: dict):
        await self.broadcast({
            "type": "stats_update",
            "data": stats,
        })

manager = ConnectionManager()

async def news_ws(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type")

            if msg_type == "ping":
                await ws.send_json({"type": "pong"})
            elif msg_type == "subscribe":
                await ws.send_json({"type": "subscribed", "channel": msg.get("channel")})
            elif msg_type == "unsubscribe":
                await ws.send_json({"type": "unsubscribed", "channel": msg.get("channel")})
            else:
                await ws.send_json({"type": "error", "message": f"Unknown message type: {msg_type}"})
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        manager.disconnect(ws)
