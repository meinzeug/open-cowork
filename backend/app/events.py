import asyncio
import logging
from typing import Any, Dict, List

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from app.models.messages import SessionState

logger = logging.getLogger(__name__)


class SessionEventHub:
    def __init__(self) -> None:
        self._connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(session_id, []).append(websocket)
        logger.info("WebSocket connected for session %s", session_id)

    async def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self._connections.get(session_id, [])
            if websocket in connections:
                connections.remove(websocket)
            if not connections and session_id in self._connections:
                del self._connections[session_id]
        logger.info("WebSocket disconnected for session %s", session_id)

    async def publish(self, session: SessionState, event_type: str, extra: Dict[str, Any] | None = None) -> None:
        payload: Dict[str, Any] = {
            "type": event_type,
            "session_id": session.session_id,
            "session": session.model_dump(),
        }
        if extra:
            payload["extra"] = extra

        async with self._lock:
            connections = list(self._connections.get(session.session_id, []))

        if not connections:
            return

        disconnected: List[WebSocket] = []
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except (RuntimeError, WebSocketDisconnect):
                disconnected.append(websocket)
            except Exception as exc:
                logger.warning("Failed to send WebSocket event for session %s: %s", session.session_id, exc)
                disconnected.append(websocket)

        if disconnected:
            async with self._lock:
                active = self._connections.get(session.session_id, [])
                self._connections[session.session_id] = [
                    ws for ws in active if ws not in disconnected
                ]
                if not self._connections[session.session_id]:
                    del self._connections[session.session_id]


session_event_hub = SessionEventHub()
