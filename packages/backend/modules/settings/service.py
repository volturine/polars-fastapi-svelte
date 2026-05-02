from sqlmodel import Session

from core import settings_service as shared_settings_service
from modules.settings.schemas import SettingsResponse, SettingsUpdate


def invalidate_resolved_settings_cache() -> None:
    shared_settings_service.invalidate_resolved_settings_cache()


def seed_settings_from_env(session: Session) -> None:
    shared_settings_service.seed_settings_from_env(session)


def get_settings(session: Session) -> SettingsResponse:
    return SettingsResponse.model_validate(shared_settings_service.get_settings(session))


def update_settings(session: Session, data: SettingsUpdate) -> SettingsResponse:
    updated = shared_settings_service.update_settings(
        session,
        shared_settings_service.SettingsUpdate.model_validate(data.model_dump(exclude_unset=True)),
    )
    return SettingsResponse.model_validate(updated)


def get_resolved_smtp() -> dict[str, object]:
    return shared_settings_service.get_resolved_smtp()


def get_resolved_telegram_token() -> str:
    return shared_settings_service.get_resolved_telegram_token()


def get_resolved_telegram_settings() -> dict[str, object]:
    return shared_settings_service.get_resolved_telegram_settings()


def get_resolved_openrouter_key() -> str:
    return shared_settings_service.get_resolved_openrouter_key()


def get_resolved_openai_settings() -> dict[str, str]:
    return shared_settings_service.get_resolved_openai_settings()


def get_resolved_ollama_settings() -> dict[str, str]:
    return shared_settings_service.get_resolved_ollama_settings()


def get_resolved_huggingface_settings() -> dict[str, str]:
    return shared_settings_service.get_resolved_huggingface_settings()


def get_resolved_default_model() -> str:
    return shared_settings_service.get_resolved_default_model()
