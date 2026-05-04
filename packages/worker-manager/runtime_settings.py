from __future__ import annotations

from threading import Lock

from contracts.settings_models import AppSettings
from core.database import run_settings_db
from core.secrets import decrypt_secret

_RESOLVED_LOCK = Lock()
_RESOLVED_CACHE: dict[int, dict[str, object]] = {}


def _active_settings_engine_id() -> int:
    from core.database import get_settings_engine

    return id(get_settings_engine())


def invalidate_runtime_settings_cache() -> None:
    with _RESOLVED_LOCK:
        _RESOLVED_CACHE.clear()


def _load_resolved_snapshot(session) -> dict[str, object]:
    row = session.get(AppSettings, 1)
    if row is None:
        return {
            'exists': False,
            'smtp_host': '',
            'smtp_port': 587,
            'smtp_user': '',
            'smtp_password': '',
            'telegram_bot_enabled': False,
            'telegram_bot_token': '',
        }
    return {
        'exists': True,
        'smtp_host': row.smtp_host,
        'smtp_port': row.smtp_port,
        'smtp_user': row.smtp_user,
        'smtp_password': decrypt_secret(str(row.smtp_password or '')) if row.smtp_password else '',
        'telegram_bot_enabled': row.telegram_bot_enabled,
        'telegram_bot_token': decrypt_secret(str(row.telegram_bot_token or '')) if row.telegram_bot_token else '',
    }


def _get_resolved_snapshot() -> dict[str, object]:
    key = _active_settings_engine_id()
    with _RESOLVED_LOCK:
        cached = _RESOLVED_CACHE.get(key)
    if cached is not None:
        return cached
    snapshot = run_settings_db(_load_resolved_snapshot)
    with _RESOLVED_LOCK:
        _RESOLVED_CACHE[key] = snapshot
    return snapshot


def get_resolved_smtp() -> dict[str, object]:
    resolved = _get_resolved_snapshot()
    port = resolved['smtp_port']
    if bool(resolved['exists']) and bool(resolved['smtp_host']):
        return {
            'host': str(resolved['smtp_host']),
            'port': port if isinstance(port, int) else 587,
            'user': str(resolved['smtp_user']),
            'password': str(resolved['smtp_password']),
        }
    return {'host': '', 'port': 587, 'user': '', 'password': ''}


def get_resolved_telegram_settings() -> dict[str, object]:
    resolved = _get_resolved_snapshot()
    if not bool(resolved['exists']):
        return {'enabled': False, 'token': ''}
    token = str(resolved['telegram_bot_token'])
    enabled = bool(resolved['telegram_bot_enabled'] and token)
    return {'enabled': enabled, 'token': token}


def get_resolved_telegram_token() -> str:
    return str(get_resolved_telegram_settings()['token'])
