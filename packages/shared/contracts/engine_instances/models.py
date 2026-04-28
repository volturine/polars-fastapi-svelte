import datetime as dt
from enum import StrEnum

from sqlalchemy import JSON, Column, DateTime, Enum as SAEnum, Integer, String
from sqlmodel import Field, SQLModel


def _enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class EngineInstanceStatus(StrEnum):
    STARTING = 'starting'
    IDLE = 'idle'
    RUNNING = 'running'
    STOPPING = 'stopping'
    STOPPED = 'stopped'
    FAILED = 'failed'


class EngineInstance(SQLModel, table=True):  # type: ignore[call-arg, assignment]
    __tablename__ = 'engine_instances'  # type: ignore[assignment]

    id: str = Field(sa_column=Column(String, primary_key=True))
    worker_id: str = Field(sa_column=Column(String, nullable=False, index=True))
    namespace: str = Field(sa_column=Column(String, nullable=False, index=True))
    analysis_id: str = Field(sa_column=Column(String, nullable=False, index=True))
    process_id: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    status: EngineInstanceStatus = Field(
        sa_column=Column(
            SAEnum(EngineInstanceStatus, native_enum=False, values_callable=_enum_values),
            nullable=False,
            index=True,
        ),
    )
    current_job_id: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    current_build_id: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    current_engine_run_id: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    resource_config_json: dict[str, object] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    effective_resources_json: dict[str, object] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    last_activity_at: dt.datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    last_seen_at: dt.datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    updated_at: dt.datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
