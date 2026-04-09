from __future__ import annotations

import asyncio
from dataclasses import dataclass
from threading import Lock
from typing import Any

from fastapi import WebSocket

from modules.engine_runs import schemas


@dataclass(slots=True)
class EngineRunListWatcher:
    websocket: WebSocket
    loop: asyncio.AbstractEventLoop
    params: schemas.EngineRunListParams
    run_ids: tuple[str, ...] = ()


class EngineRunWatcherRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._watchers: dict[str, dict[WebSocket, EngineRunListWatcher]] = {}

    def add(
        self,
        namespace: str,
        websocket: WebSocket,
        *,
        loop: asyncio.AbstractEventLoop,
        params: schemas.EngineRunListParams,
    ) -> None:
        with self._lock:
            self._watchers.setdefault(namespace, {})[websocket] = EngineRunListWatcher(
                websocket=websocket,
                loop=loop,
                params=params,
            )

    def discard(self, namespace: str, websocket: WebSocket) -> None:
        with self._lock:
            watchers = self._watchers.get(namespace)
            if watchers is None:
                return
            watchers.pop(websocket, None)
            if watchers:
                return
            self._watchers.pop(namespace, None)

    def watchers(self, namespace: str) -> list[EngineRunListWatcher]:
        with self._lock:
            return list(self._watchers.get(namespace, {}).values())

    def set_run_ids(self, namespace: str, websocket: WebSocket, run_ids: tuple[str, ...]) -> None:
        with self._lock:
            watchers = self._watchers.get(namespace)
            if watchers is None:
                return
            watcher = watchers.get(websocket)
            if watcher is None:
                return
            watcher.run_ids = run_ids

    def clear(self) -> None:
        with self._lock:
            self._watchers.clear()

    def broadcast(self, namespace: str, payloads: list[tuple[EngineRunListWatcher, dict[str, Any]]]) -> None:
        for watcher, payload in payloads:
            try:
                watcher.loop.call_soon_threadsafe(self._schedule_send, namespace, watcher.websocket, payload)
            except RuntimeError:
                self.discard(namespace, watcher.websocket)

    def _schedule_send(self, namespace: str, websocket: WebSocket, payload: dict[str, Any]) -> None:
        asyncio.create_task(self._send(namespace, websocket, payload))

    async def _send(self, namespace: str, websocket: WebSocket, payload: dict[str, Any]) -> None:
        try:
            await websocket.send_json(payload)
        except Exception:
            self.discard(namespace, websocket)


registry = EngineRunWatcherRegistry()
