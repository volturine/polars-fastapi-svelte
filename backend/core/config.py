import os
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Root data directory (relative to project root, not backend/)
DATA_DIR = Path(__file__).parent.parent.parent / 'data'


def _resolve_dir(value: Path | str) -> Path:
    """Ensure a directory path exists and return it."""
    path_value = Path(value)
    path_value.mkdir(parents=True, exist_ok=True)
    return path_value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    app_name: str = 'Polars-FastAPI-Svelte Analysis Platform'
    app_version: str = '1.0.0'

    # Debug mode - enables SQL echo, verbose logging
    debug: bool = False

    # CORS origins - comma-separated list of allowed origins
    cors_origins: str = (
        'http://localhost:3000,http://127.0.0.1:3000,http://0.0.0.0:3000,http://192.168.1.140:3000,http://100.68.183.19:3000'
    )

    database_url: str = 'sqlite+aiosqlite:///./database/app.db'

    # All data directories under root data/ folder
    upload_dir: Path = Field(default=DATA_DIR / 'uploads', alias='UPLOAD_DIR')
    results_dir: Path = Field(default=DATA_DIR / 'results', alias='RESULTS_DIR')
    exports_dir: Path = Field(default=DATA_DIR / 'exports', alias='EXPORTS_DIR')

    max_upload_size: int = Field(default=10 * 1024 * 1024 * 1024, alias='MAX_UPLOAD_SIZE')

    # Engine idle timeout in seconds (default 5 minutes)
    # Engines without keepalive pings will be terminated after this duration
    engine_idle_timeout: int = Field(default=300, alias='ENGINE_IDLE_TIMEOUT')

    # Job execution timeout in seconds (default 5 minutes)
    # Jobs that take longer than this will timeout
    job_timeout: int = Field(default=300, alias='JOB_TIMEOUT')

    # Job TTL in seconds (default 30 minutes)
    # Completed jobs will be cleaned up after this duration
    job_ttl: int = Field(default=1800, alias='JOB_TTL')

    # Maximum number of jobs to keep in memory
    max_jobs_in_memory: int = Field(default=1000, alias='MAX_JOBS_IN_MEMORY')

    # Engine cleanup interval in seconds (default 30 seconds)
    engine_cleanup_interval: int = Field(default=30, alias='ENGINE_CLEANUP_INTERVAL')

    # Process shutdown timeout in seconds (default 5 seconds)
    process_shutdown_timeout: int = Field(default=5, alias='PROCESS_SHUTDOWN_TIMEOUT')

    # Process terminate timeout in seconds (default 2 seconds)
    process_terminate_timeout: int = Field(default=2, alias='PROCESS_TERMINATE_TIMEOUT')

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]

    @field_validator('upload_dir', 'results_dir', 'exports_dir', mode='before')
    @classmethod
    def _ensure_dirs(cls, value: Path) -> Path:
        return _resolve_dir(value)

    @field_validator('engine_idle_timeout', 'job_timeout', 'job_ttl', 'engine_cleanup_interval')
    @classmethod
    def _validate_positive_timeout(cls, value: int, info) -> int:
        """Ensure timeout values are positive."""
        if value <= 0:
            raise ValueError(f'{info.field_name} must be positive, got {value}')
        return value

    @field_validator('max_jobs_in_memory')
    @classmethod
    def _validate_max_jobs(cls, value: int) -> int:
        """Ensure max jobs is reasonable."""
        if value < 10:
            raise ValueError(f'max_jobs_in_memory must be at least 10, got {value}')
        if value > 100000:
            raise ValueError(f'max_jobs_in_memory must be at most 100000, got {value}')
        return value

    @field_validator('max_upload_size')
    @classmethod
    def _validate_upload_size(cls, value: int) -> int:
        """Ensure upload size is reasonable."""
        if value < 1024:  # At least 1KB
            raise ValueError(f'max_upload_size must be at least 1024 bytes, got {value}')
        return value

    @model_validator(mode='after')
    def _validate_directories_writable(self):
        """Ensure all directories are writable."""
        for dir_name in ['upload_dir', 'results_dir', 'exports_dir']:
            dir_path = getattr(self, dir_name)
            if not os.access(dir_path, os.W_OK):
                raise ValueError(f'{dir_name} is not writable: {dir_path}')
        return self


settings = Settings()
