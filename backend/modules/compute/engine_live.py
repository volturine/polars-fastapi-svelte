from __future__ import annotations

import asyncio
from collections.abc import Callable

from fastapi import WebSocket

from core.namespace import get_namespace
from modules.compute import schemas
from modules.compute.core.base import EngineStatusInfo
from modules.engine_instances import service as engine_instance_service


class EngineRegistry:
    def __init__(self) -> None:
        self._watchers: dict[str, set[WebSocket]] = {}
        self._waiters: dict[str, list[asyncio.Future[str]]] = {}
        self._lock = asyncio.Lock()
        self._version: dict[str, int] = {}

    async def add_watcher(self, namespace: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._watchers.setdefault(namespace, set()).add(websocket)

    async def remove_watcher(self, namespace: str, websocket: WebSocket) -> None:
        async with self._lock:
            watchers = self._watchers.get(namespace)
            if not watchers:
                return
            watchers.discard(websocket)
            if watchers:
                return
            self._watchers.pop(namespace, None)

    async def clear(self) -> None:
        async with self._lock:
            self._watchers.clear()
            waiters = self._waiters
            self._waiters = {}
            self._version = {}
        for items in waiters.values():
            for future in items:
                if future.done():
                    continue
                future.cancel()

    async def wait_for_namespace(self, namespace: str, last_seen: str | None = None) -> str:
        async with self._lock:
            current = self._version.get(namespace, 0)
            current_token = str(current)
            if last_seen is not None and current_token != last_seen:
                return current_token
        loop = asyncio.get_running_loop()
        future: asyncio.Future[str] = loop.create_future()
        async with self._lock:
            self._waiters.setdefault(namespace, []).append(future)
        try:
            return await future
        finally:
            await self._discard_waiter(namespace, future)

    async def publish_snapshot(self, namespace: str, statuses: list[EngineStatusInfo]) -> None:
        del statuses
        async with self._lock:
            version = self._version.get(namespace, 0) + 1
            self._version[namespace] = version
            waiters = self._waiters.pop(namespace, [])
        for future in waiters:
            if future.done():
                continue
            future.set_result(str(version))

    async def _discard_waiter(self, namespace: str, future: asyncio.Future[str]) -> None:
        async with self._lock:
            current = self._waiters.get(namespace)
            if current is None:
                return
            next_waiters = [item for item in current if item is not future and not item.done()]
            if next_waiters:
                self._waiters[namespace] = next_waiters
                return
            self._waiters.pop(namespace, None)

    async def current_version(self, namespace: str) -> str | None:
        async with self._lock:
            current = self._version.get(namespace, 0)
            if current <= 0:
                return None
            return str(current)


registry = EngineRegistry()


def create_snapshot_notifier(
    loop: asyncio.AbstractEventLoop,
    persist: Callable[[str, list[EngineStatusInfo]], None] | None = None,
) -> Callable[[list[EngineStatusInfo]], None]:
    def notify(statuses: list[EngineStatusInfo]) -> None:
        if loop.is_closed():
            return
        namespace = get_namespace()
        if persist is not None:
            persist(namespace, statuses)
        if not loop.is_running():
            return
        loop.call_soon_threadsafe(loop.create_task, registry.publish_snapshot(namespace, statuses))

    notify._persist = persist  # type: ignore[attr-defined]
    return notify


def persist_engine_snapshot(
    persist: Callable[[str, list[EngineStatusInfo]], None] | None,
    *,
    namespace: str,
    statuses: list[EngineStatusInfo],
) -> None:
    if persist is not None:
        persist(namespace, statuses)


def load_engine_snapshot(session, *, namespace: str, defaults: dict[str, object]) -> schemas.EngineListSnapshotMessage:
    rows = engine_instance_service.list_engine_projection(session, namespace=namespace)
    statuses = [
        schemas.EngineStatusSchema.model_validate(engine_instance_service.serialize_engine_instance(row, defaults=defaults)) for row in rows
    ]
    return schemas.EngineListSnapshotMessage(engines=statuses, total=len(statuses))
