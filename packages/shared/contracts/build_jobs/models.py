import datetime as dt
from enum import StrEnum

from sqlalchemy import Column, DateTime, Enum as SAEnum, Integer, String
from sqlmodel import Field, SQLModel


def _enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class BuildJobStatus(StrEnum):
    QUEUED = 'queued'
    LEASED = 'leased'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class BuildJob(SQLModel, table=True):  # type: ignore[call-arg, assignment]
    __tablename__ = 'build_jobs'  # type: ignore[assignment]

    id: str = Field(sa_column=Column(String, primary_key=True))
    build_id: str = Field(sa_column=Column(String, nullable=False, index=True, unique=True))
    namespace: str = Field(sa_column=Column(String, nullable=False, index=True))
    status: BuildJobStatus = Field(
        sa_column=Column(
            SAEnum(BuildJobStatus, native_enum=False, values_callable=_enum_values),
            nullable=False,
            index=True,
        ),
    )
    priority: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    lease_owner: str | None = Field(default=None, sa_column=Column(String, nullable=True, index=True))
    lease_expires_at: dt.datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    attempts: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    max_attempts: int = Field(default=1, sa_column=Column(Integer, nullable=False))
    last_error: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    available_at: dt.datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    created_at: dt.datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: dt.datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
