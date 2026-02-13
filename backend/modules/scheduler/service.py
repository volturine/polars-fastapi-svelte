import uuid
from datetime import UTC, datetime

import croniter  # type: ignore[import-untyped]
from sqlalchemy import select
from sqlmodel import Session

from modules.analysis.models import Analysis, AnalysisDataSource
from modules.datasource.models import DataSource
from modules.scheduler.models import Schedule
from modules.scheduler.schemas import ScheduleCreate, ScheduleResponse, ScheduleUpdate


def list_schedules(session: Session, analysis_id: str) -> list[ScheduleResponse]:
    result = session.execute(select(Schedule).where(Schedule.analysis_id == analysis_id))  # type: ignore[arg-type]
    schedules = result.scalars().all()
    return [ScheduleResponse.model_validate(schedule) for schedule in schedules]


def create_schedule(session: Session, payload: ScheduleCreate) -> ScheduleResponse:
    next_run = _compute_next_run(payload.cron_expression)
    record = Schedule(
        id=str(uuid.uuid4()),
        analysis_id=payload.analysis_id,
        cron_expression=payload.cron_expression,
        enabled=payload.enabled,
        last_run=None,
        next_run=next_run,
        created_at=datetime.now(UTC),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return ScheduleResponse.model_validate(record)


def update_schedule(session: Session, schedule_id: str, payload: ScheduleUpdate) -> ScheduleResponse:
    schedule = session.get(Schedule, schedule_id)
    if not schedule:
        raise ValueError('Schedule not found')
    update_data = payload.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)
    if payload.cron_expression:
        schedule.next_run = _compute_next_run(payload.cron_expression)
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return ScheduleResponse.model_validate(schedule)


def delete_schedule(session: Session, schedule_id: str) -> None:
    schedule = session.get(Schedule, schedule_id)
    if not schedule:
        raise ValueError('Schedule not found')
    session.delete(schedule)
    session.commit()


def get_build_order(session: Session, analysis_id: str) -> list[str]:
    graph: dict[str, set[str]] = {}
    in_degree: dict[str, int] = {}

    analyses = session.execute(select(Analysis)).scalars().all()
    for analysis in analyses:
        if analysis.id not in graph:
            graph[analysis.id] = set()
            in_degree[analysis.id] = 0

    deps = session.execute(select(AnalysisDataSource)).scalars().all()
    for dep in deps:
        datasource = session.get(DataSource, dep.datasource_id)
        if not datasource or not datasource.created_by_analysis_id:
            continue
        upstream = datasource.created_by_analysis_id
        graph.setdefault(upstream, set()).add(dep.analysis_id)
        in_degree[dep.analysis_id] = in_degree.get(dep.analysis_id, 0) + 1

    queue = [aid for aid, degree in in_degree.items() if degree == 0]
    ordered: list[str] = []
    while queue:
        node = queue.pop(0)
        ordered.append(node)
        for neighbor in graph.get(node, set()):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    if analysis_id in ordered:
        return ordered
    return ordered


def should_run(cron_expr: str, last_run: datetime | None) -> bool:
    if not cron_expr:
        return False
    if last_run is None:
        return True
    cron = croniter.croniter(cron_expr, last_run)
    next_run = cron.get_next(datetime)
    return next_run <= datetime.now(UTC)


def _compute_next_run(cron_expr: str) -> datetime | None:
    if not cron_expr:
        return None
    cron = croniter.croniter(cron_expr, datetime.now(UTC))
    return cron.get_next(datetime)
