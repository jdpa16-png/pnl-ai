"""
WebSocket session manager.
Tracks one WebSocket connection per classification session and provides
the async bridge used by the classifier thread to push questions and
receive answers from the browser.
"""
from __future__ import annotations

import asyncio

from fastapi import WebSocket


class WsManager:
    def __init__(self) -> None:
        self._sockets: dict[str, WebSocket] = {}
        self._answer_queues: dict[str, asyncio.Queue[str]] = {}

    async def connect(self, session_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._sockets[session_id] = ws
        self._answer_queues[session_id] = asyncio.Queue()

    def disconnect(self, session_id: str) -> None:
        self._sockets.pop(session_id, None)
        self._answer_queues.pop(session_id, None)

    async def send(self, session_id: str, data: dict) -> None:
        ws = self._sockets.get(session_id)
        if ws:
            await ws.send_json(data)

    async def wait_for_answer(self, session_id: str, timeout: float = 300.0) -> str:
        """Blocks (async) until the frontend sends a category answer."""
        q = self._answer_queues.get(session_id)
        if not q:
            raise RuntimeError(f"No answer queue for session '{session_id}'")
        return await asyncio.wait_for(q.get(), timeout=timeout)

    async def put_answer(self, session_id: str, answer: str) -> None:
        q = self._answer_queues.get(session_id)
        if q:
            await q.put(answer)

    def is_connected(self, session_id: str) -> bool:
        return session_id in self._sockets


manager = WsManager()
