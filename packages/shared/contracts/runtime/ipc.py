from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import logging
import socket
import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Literal

import psycopg
from psycopg import Notify

from core.config import settings

logger = logging.getLogger(__name__)

_CHANNEL = 'runtime_events'
ListenerKind = Literal['api', 'job']


def _psycopg_conninfo() -> str:
    return settings.database_url.replace('postgresql+psycopg://', 'postgresql://', 1)


def _socket_path(listener: ListenerKind) -> Path:
    digest = hashlib.sha1(f'{settings.data_dir}:{listener}'.encode()).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / f'df-runtime-{digest}.sock'


async def start_api_server(listener: ListenerKind = 'api') -> socket.socket | psycopg.Connection | None:
    if settings.is_postgres:
        connection = psycopg.connect(_psycopg_conninfo(), autocommit=True)
        connection.execute(f'LISTEN {_CHANNEL}')
        return connection
    path = _socket_path(listener)
    path.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(FileNotFoundError):
        path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(path))
    server.listen()
    server.setblocking(False)
    return server


async def serve_api_notifications(
    server: socket.socket | psycopg.Connection,
    stop_event,
    handler: Callable[[dict[str, object]], Awaitable[None]],
) -> None:
    if isinstance(server, psycopg.Connection):
        await _serve_postgres_notifications(server, stop_event, handler)
        return
    await _serve_unix_notifications(server, stop_event, handler)


async def _serve_unix_notifications(server: socket.socket, stop_event, handler: Callable[[dict[str, object]], Awaitable[None]]) -> None:
    loop = asyncio.get_running_loop()
    while not stop_event.is_set():
        accept_task = asyncio.create_task(loop.sock_accept(server))
        stop_task = asyncio.create_task(stop_event.wait())
        done, pending = await asyncio.wait({accept_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        if stop_task in done:
            return
        conn, _ = await accept_task
        try:
            data = await loop.sock_recv(conn, 4096)
            if not data:
                continue
            payload = json.loads(data.decode('utf-8').strip())
            if isinstance(payload, dict):
                await handler(payload)
        except Exception as exc:
            logger.debug('Ignoring malformed runtime IPC payload: %s', exc)
        finally:
            conn.close()


async def _serve_postgres_notifications(
    connection: psycopg.Connection,
    stop_event,
    handler: Callable[[dict[str, object]], Awaitable[None]],
) -> None:
    while not stop_event.is_set():
        notifications = await asyncio.to_thread(lambda: list(connection.notifies(timeout=0.5, stop_after=100)))
        if not notifications:
            continue
        for notify in notifications:
            try:
                payload = json.loads(_notify_payload(notify))
            except json.JSONDecodeError as exc:
                logger.debug('Ignoring malformed Postgres runtime notification: %s', exc)
                continue
            if isinstance(payload, dict):
                await handler(payload)


def _notify_payload(notify: Notify) -> str:
    return notify.payload


async def stop_api_server(server: socket.socket | psycopg.Connection | None, *, listener: ListenerKind = 'api') -> None:
    if server is None:
        return
    if isinstance(server, psycopg.Connection):
        server.close()
        return
    server.close()
    path = _socket_path(listener)
    with contextlib.suppress(FileNotFoundError):
        path.unlink()


async def handle_api_payload(payload: dict[str, object]) -> None:
    kind = payload.get('kind')
    if kind == 'build':
        from contracts.build_runs.live import BuildNotification, hub as build_hub

        namespace = payload.get('namespace')
        build_id = payload.get('build_id')
        latest_sequence = payload.get('latest_sequence')
        if isinstance(namespace, str) and isinstance(build_id, str) and isinstance(latest_sequence, int):
            await build_hub.publish(
                BuildNotification(
                    namespace=namespace,
                    build_id=build_id,
                    latest_sequence=latest_sequence,
                )
            )
        return
    if kind == 'engine':
        from modules.compute.engine_live import registry as engine_registry

        namespace = payload.get('namespace')
        if isinstance(namespace, str):
            await engine_registry.publish_snapshot(namespace, [])
        return
    if kind == 'job':
        from contracts.build_jobs.live import hub as build_job_hub

        build_job_hub.publish()


def notify_api_build(namespace: str, build_id: str, latest_sequence: int) -> None:
    _send_api_message(
        {
            'kind': 'build',
            'namespace': namespace,
            'build_id': build_id,
            'latest_sequence': latest_sequence,
        },
        listener='api',
    )


def notify_api_engine(namespace: str) -> None:
    _send_api_message(
        {
            'kind': 'engine',
            'namespace': namespace,
        },
        listener='api',
    )


def notify_build_job() -> None:
    _send_api_message({'kind': 'job'}, listener='job')


def _send_api_message(payload: dict[str, object], *, listener: ListenerKind) -> None:
    if settings.is_postgres:
        _send_postgres_message(payload)
        return
    _send_unix_message(payload, listener=listener)


def _send_postgres_message(payload: dict[str, object]) -> None:
    data = json.dumps(payload)
    with contextlib.suppress(Exception), psycopg.connect(_psycopg_conninfo(), autocommit=True) as connection:
        connection.execute('SELECT pg_notify(%s, %s)', (_CHANNEL, data))


def _send_unix_message(payload: dict[str, object], *, listener: ListenerKind) -> None:
    path = _socket_path(listener)
    if not path.exists():
        return
    data = json.dumps(payload).encode('utf-8') + b'\n'
    with contextlib.suppress(OSError), socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(0.2)
        client.connect(str(path))
        client.sendall(data)
