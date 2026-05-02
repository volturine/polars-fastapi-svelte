import datetime as dt
from enum import StrEnum

from sqlalchemy import JSON, Column, DateTime, Enum as SAEnum, String
from sqlmodel import Field, SQLModel


def _enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class ComputeRequestKind(StrEnum):
    PREVIEW = 'preview'
    SCHEMA = 'schema'
    ROW_COUNT = 'row_count'
    DOWNLOAD = 'download'
    EXPORT = 'export'
    REFRESH_DATASOURCE = 'refresh_datasource'
    SPAWN_ENGINE = 'spawn_engine'
    KEEPALIVE_ENGINE = 'keepalive_engine'
    CONFIGURE_ENGINE = 'configure_engine'
    SHUTDOWN_ENGINE = 'shutdown_engine'


class ComputeRequestStatus(StrEnum):
    QUEUED = 'queued'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class ComputeRequest(SQLModel, table=True):  # type: ignore[call-arg, assignment]
    __tablename__ = 'compute_requests'  # type: ignore[assignment]

    id: str = Field(sa_column=Column(String, primary_key=True))
    namespace: str = Field(sa_column=Column(String, nullable=False, index=True))
    kind: ComputeRequestKind = Field(
        sa_column=Column(
            SAEnum(ComputeRequestKind, native_enum=False, values_callable=_enum_values),
            nullable=False,
            index=True,
        )
    )
    status: ComputeRequestStatus = Field(
        sa_column=Column(
            SAEnum(ComputeRequestStatus, native_enum=False, values_callable=_enum_values),
            nullable=False,
            index=True,
        )
    )
    request_json: dict[str, object] = Field(sa_column=Column(JSON, nullable=False))
    response_json: dict[str, object] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    error_message: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    artifact_path: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    artifact_name: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    artifact_content_type: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    lease_owner: str | None = Field(default=None, sa_column=Column(String, nullable=True, index=True))
    lease_expires_at: dt.datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    created_at: dt.datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: dt.datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    completed_at: dt.datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
