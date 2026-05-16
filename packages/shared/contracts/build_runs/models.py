import datetime as dt

from sqlalchemy import JSON, Column, DateTime, Enum as SAEnum, Float, Integer, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from contracts.compute import schemas as compute_schemas
from contracts.enums import DataForgeStrEnum


class BuildRunStatus(DataForgeStrEnum):
    QUEUED = 'queued'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    ORPHANED = 'orphaned'

    @property
    def is_terminal(self) -> bool:
        return self in {BuildRunStatus.COMPLETED, BuildRunStatus.FAILED, BuildRunStatus.CANCELLED, BuildRunStatus.ORPHANED}

    def to_active_build_status(self) -> tuple[compute_schemas.ActiveBuildStatus, str | None]:
        if self == BuildRunStatus.QUEUED:
            return compute_schemas.ActiveBuildStatus.QUEUED, None
        if self == BuildRunStatus.RUNNING:
            return compute_schemas.ActiveBuildStatus.RUNNING, None
        if self == BuildRunStatus.COMPLETED:
            return compute_schemas.ActiveBuildStatus.COMPLETED, None
        if self == BuildRunStatus.CANCELLED:
            return compute_schemas.ActiveBuildStatus.CANCELLED, None
        if self == BuildRunStatus.FAILED:
            return compute_schemas.ActiveBuildStatus.FAILED, None
        return compute_schemas.ActiveBuildStatus.FAILED, 'Build orphaned during startup recovery'


class BuildRun(SQLModel, table=True):  # type: ignore[call-arg, assignment]
    __tablename__ = 'build_runs'  # type: ignore[assignment]

    id: str = Field(sa_column=Column(String, primary_key=True))
    namespace: str = Field(sa_column=Column(String, nullable=False, index=True))
    schedule_id: str | None = Field(default=None, sa_column=Column(String, nullable=True, index=True))
    analysis_id: str = Field(sa_column=Column(String, nullable=False, index=True))
    analysis_name: str = Field(sa_column=Column(String, nullable=False))
    status: BuildRunStatus = Field(
        sa_column=Column(SAEnum(BuildRunStatus, native_enum=False, values_callable=lambda enum_cls: enum_cls.values()), nullable=False, index=True)
    )
    request_json: dict[str, object] = Field(sa_column=Column(JSON, nullable=False))
    starter_json: dict[str, object] = Field(sa_column=Column(JSON, nullable=False))
    resource_config_json: dict[str, object] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    result_json: dict[str, object] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    current_engine_run_id: str | None = Field(default=None, sa_column=Column(String, nullable=True, index=True))
    current_kind: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    current_datasource_id: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    current_tab_id: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    current_tab_name: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    current_output_id: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    current_output_name: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    progress: float = Field(default=0.0, sa_column=Column(Float, nullable=False))
    elapsed_ms: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    estimated_remaining_ms: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    current_step: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    current_step_index: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    total_steps: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    total_tabs: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    duration_ms: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    error_message: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    cancelled_at: dt.datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    cancelled_by: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    created_at: dt.datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    started_at: dt.datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    completed_at: dt.datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    updated_at: dt.datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    version: int = Field(default=1, sa_column=Column(Integer, nullable=False))


class BuildEvent(SQLModel, table=True):  # type: ignore[call-arg, assignment]
    __tablename__ = 'build_events'  # type: ignore[assignment]
    __table_args__ = (UniqueConstraint('build_id', 'sequence', name='uq_build_events_build_sequence'),)

    id: str = Field(sa_column=Column(String, primary_key=True))
    build_id: str = Field(sa_column=Column(String, nullable=False, index=True))
    namespace: str = Field(sa_column=Column(String, nullable=False, index=True))
    sequence: int = Field(sa_column=Column(Integer, nullable=False))
    type: compute_schemas.BuildEventType = Field(
        sa_column=Column(SAEnum(compute_schemas.BuildEventType, native_enum=False, values_callable=lambda enum_cls: enum_cls.values()), nullable=False)
    )
    payload_json: dict[str, object] = Field(sa_column=Column(JSON, nullable=False))
    engine_run_id: str | None = Field(default=None, sa_column=Column(String, nullable=True, index=True))
    emitted_at: dt.datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    created_at: dt.datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
