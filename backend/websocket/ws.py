import json
from typing import Optional, Set

import structlog
from fastapi import WebSocket, WebSocketDisconnect
from jose import JWTError

logger = structlog.get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)
        logger.info("ws_connected", active=len(self.active))

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)
        logger.info("ws_disconnected", active=len(self.active))

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


async def _validate_token(token: str) -> Optional[str]:
    """Validate a JWT and return the user_id if valid."""
    from ..auth.auth import decode_token
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except JWTError:
        return None


async def news_ws(ws: WebSocket):
    """WebSocket endpoint requiring initial auth message."""
    await ws.accept()

    user_id = None

    try:
        # ── Require auth within first message ──
        data = await ws.receive_text()
        msg = json.loads(data)

        if msg.get("type") == "auth" and msg.get("token"):
            user_id = await _validate_token(msg["token"])
            if user_id:
                await ws.send_json({"type": "auth_ok"})
                logger.info("ws_authenticated")
            else:
                await ws.send_json({"type": "auth_error", "message": "Invalid token"})
                await ws.close(code=4001)
                return
        else:
            await ws.send_json({"type": "auth_error", "message": "Authentication required"})
            await ws.close(code=4001)
            return

        manager.active.add(ws)
        logger.info("ws_connected", active=len(manager.active))

        # ── Normal message loop ──
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
        manager.active.discard(ws)
        logger.info("ws_disconnected", active=len(manager.active))
    except Exception as e:
        logger.error("ws_error", error=str(e))
        manager.active.discard(ws)
