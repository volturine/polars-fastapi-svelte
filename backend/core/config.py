from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Polars-FastAPI-Svelte Analysis Platform'
    app_version: str = '1.0.0'

    database_url: str = 'sqlite+aiosqlite:///./database/app.db'

    upload_dir: Path = Path('./data/uploads')
    results_dir: Path = Path('./data/results')

    max_upload_size: int = 10 * 1024 * 1024 * 1024
    compute_timeout: int = 300


settings = Settings()

settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.results_dir.mkdir(parents=True, exist_ok=True)
