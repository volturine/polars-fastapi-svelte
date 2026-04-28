import logging
from threading import Lock

from sqlmodel import Session

from contracts.settings_models import AppSettings
from contracts.settings_schemas import SettingsResponse, SettingsUpdate
from core.secrets import (
    decrypt_secret,
    encrypt_secret,
    is_masked_secret,
    mask_secret,
    should_migrate_secret,
)

logger = logging.getLogger(__name__)

_RESOLVED_LOCK = Lock()
_RESOLVED_CACHE: dict[int, dict[str, object]] = {}


def invalidate_resolved_settings_cache() -> None:
    with _RESOLVED_LOCK:
        _RESOLVED_CACHE.clear()


def _warn_bootstrap_secret_missing(name: str) -> None:
    logging.warning('Skipping %s bootstrap because SETTINGS_ENCRYPTION_KEY is not set', name)


def _read_secret(row: AppSettings, field: str) -> str:
    stored = str(getattr(row, field, '') or '')
    if not stored:
        return ''
    value = decrypt_secret(stored)
    if should_migrate_secret(stored):
        setattr(row, field, encrypt_secret(value))
    return value


def _write_secret(row: AppSettings, field: str, value: str) -> None:
    setattr(row, field, encrypt_secret(value))


def _resolve_updated_secret(row: AppSettings, field: str, value: str | None) -> str:
    if value is None:
        return _read_secret(row, field)
    if is_masked_secret(value):
        return _read_secret(row, field)
    return value


def _masked_settings_response(row: AppSettings) -> SettingsResponse:
    smtp_password = _read_secret(row, 'smtp_password')
    telegram_bot_token = _read_secret(row, 'telegram_bot_token')
    openrouter_api_key = _read_secret(row, 'openrouter_api_key')
    openai_api_key = _read_secret(row, 'openai_api_key')
    huggingface_api_token = _read_secret(row, 'huggingface_api_token')
    return SettingsResponse(
        smtp_host=row.smtp_host,
        smtp_port=row.smtp_port,
        smtp_user=row.smtp_user,
        smtp_password=mask_secret(smtp_password),
        telegram_bot_token=mask_secret(telegram_bot_token),
        telegram_bot_enabled=row.telegram_bot_enabled,
        openrouter_api_key=mask_secret(openrouter_api_key),
        openrouter_default_model=row.openrouter_default_model,
        openai_api_key=mask_secret(openai_api_key),
        openai_endpoint_url=row.openai_endpoint_url,
        openai_default_model=row.openai_default_model,
        openai_organization_id=row.openai_organization_id,
        ollama_endpoint_url=row.ollama_endpoint_url,
        ollama_default_model=row.ollama_default_model,
        huggingface_api_token=mask_secret(huggingface_api_token),
        huggingface_default_model=row.huggingface_default_model,
        public_idb_debug=row.public_idb_debug,
    )


def get_settings(session: Session) -> SettingsResponse:
    row = session.get(AppSettings, 1)
    if not row:
        row = AppSettings(id=1)
        session.add(row)
        session.commit()
        session.refresh(row)
    return _masked_settings_response(row)


def resolve_settings(session: Session) -> dict[str, object]:
    row = session.get(AppSettings, 1)
    if not row:
        row = AppSettings(id=1)
        session.add(row)
        session.commit()
        session.refresh(row)
    key = id(session.get_bind())
    with _RESOLVED_LOCK:
        cached = _RESOLVED_CACHE.get(key)
        if cached is not None:
            return cached
    resolved = {
        'smtp_host': row.smtp_host,
        'smtp_port': row.smtp_port,
        'smtp_user': row.smtp_user,
        'smtp_password': _read_secret(row, 'smtp_password'),
        'telegram_bot_token': _read_secret(row, 'telegram_bot_token'),
        'telegram_bot_enabled': row.telegram_bot_enabled,
        'openrouter_api_key': _read_secret(row, 'openrouter_api_key'),
        'openrouter_default_model': row.openrouter_default_model,
        'openai_api_key': _read_secret(row, 'openai_api_key'),
        'openai_endpoint_url': row.openai_endpoint_url,
        'openai_default_model': row.openai_default_model,
        'openai_organization_id': row.openai_organization_id,
        'ollama_endpoint_url': row.ollama_endpoint_url,
        'ollama_default_model': row.ollama_default_model,
        'huggingface_api_token': _read_secret(row, 'huggingface_api_token'),
        'huggingface_default_model': row.huggingface_default_model,
        'public_idb_debug': row.public_idb_debug,
    }
    with _RESOLVED_LOCK:
        _RESOLVED_CACHE[key] = resolved
    return resolved


def seed_settings_from_env(session: Session) -> None:
    from core.config import settings

    row = session.get(AppSettings, 1)
    if not row:
        row = AppSettings(id=1)
        session.add(row)
    if settings.smtp_host:
        row.smtp_host = settings.smtp_host
    if settings.smtp_port:
        row.smtp_port = settings.smtp_port
    if settings.smtp_user:
        row.smtp_user = settings.smtp_user
    if settings.smtp_password:
        _write_secret(row, 'smtp_password', settings.smtp_password)
    if settings.telegram_bot_token:
        _write_secret(row, 'telegram_bot_token', settings.telegram_bot_token)
    if settings.openrouter_api_key:
        _write_secret(row, 'openrouter_api_key', settings.openrouter_api_key)
    if settings.openai_api_key:
        _write_secret(row, 'openai_api_key', settings.openai_api_key)
    if settings.huggingface_api_token:
        _write_secret(row, 'huggingface_api_token', settings.huggingface_api_token)
    session.add(row)
    session.commit()
    invalidate_resolved_settings_cache()


def update_settings(session: Session, payload: SettingsUpdate) -> SettingsResponse:
    row = session.get(AppSettings, 1)
    if not row:
        row = AppSettings(id=1)
        session.add(row)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key.endswith('password') or key.endswith('token') or key.endswith('api_key'):
            if value is not None:
                _write_secret(row, key, _resolve_updated_secret(row, key, value))
            continue
        setattr(row, key, value)
    session.add(row)
    session.commit()
    session.refresh(row)
    invalidate_resolved_settings_cache()
    return _masked_settings_response(row)
