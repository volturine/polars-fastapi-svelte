import logging
import uuid
from collections import deque
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import croniter  # type: ignore[import-untyped]
from sqlalchemy import and_, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlmodel import Session, col

from core.config import settings
from core.exceptions import AnalysisNotFoundError, DataSourceNotFoundError, ScheduleNotFoundError, ScheduleValidationError
from core.namespace import get_namespace
from modules.analysis.models import Analysis
from modules.analysis.pipeline_types import PipelineTab
from modules.build_jobs import service as build_job_service
from modules.build_jobs.live import hub as build_job_hub
from modules.build_runs import service as build_run_service
from modules.build_runs.models import BuildRunStatus
from modules.compute import schemas as compute_schemas, service as compute_service
from modules.compute.manager import ProcessManager
from modules.datasource.models import DataSource
from modules.datasource.service import is_reingestable_raw_datasource
from modules.engine_runs.models import EngineRun
from modules.runtime import ipc as runtime_ipc
from modules.scheduler.models import Schedule
from modules.scheduler.schemas import ScheduleCreate, ScheduleResponse, ScheduleUpdate

logger = logging.getLogger(__name__)

_SCHEDULE_TERMINAL_STATUSES = frozenset(
    {
        BuildRunStatus.COMPLETED,
        BuildRunStatus.FAILED,
        BuildRunStatus.CANCELLED,
        BuildRunStatus.ORPHANED,
    }
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _naive_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=None) if value.tzinfo is not None else value


def _lease_seconds() -> int:
    return max(settings.scheduler_check_interval * 2, 30)


def _schedule_starter(schedule_id: str) -> compute_schemas.BuildStarter:
    return compute_schemas.BuildStarter(triggered_by=f'schedule:{schedule_id}')


def _mark_schedule_failure(
    session: Session,
    *,
    schedule: Schedule,
    error: str,
    now: datetime | None = None,
) -> Schedule:
    stamp = now or _utcnow()
    schedule.last_failure_at = stamp
    schedule.lease_owner = None
    schedule.lease_expires_at = None
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


def mark_schedule_enqueue_failed(session: Session, schedule_id: str, *, error: str) -> Schedule | None:
    schedule = session.get(Schedule, schedule_id)
    if schedule is None:
        return None
    return _mark_schedule_failure(session, schedule=schedule, error=error)


def _build_analysis_request(
    session: Session, schedule: Schedule, analysis_id: str
) -> tuple[compute_schemas.BuildRequest, str, str, str | None, str | None]:
    analysis = session.get(Analysis, analysis_id)
    if not analysis:
        raise ValueError(f'Analysis {analysis_id} not found for datasource {schedule.datasource_id}')

    pipeline = analysis.pipeline
    target_tab = next(
        (tab for tab in pipeline.tabs if tab.output.result_id == schedule.datasource_id),
        None,
    )
    if target_tab is None:
        raise ValueError(f'No tab found in analysis {analysis_id} that produces datasource {schedule.datasource_id}')

    pipeline_payload = compute_service.build_analysis_pipeline_payload(session, analysis, datasource_id=schedule.datasource_id)
    request = compute_schemas.BuildRequest.model_validate(
        {
            'analysis_pipeline': pipeline_payload,
            'tab_id': target_tab.id,
        }
    )
    return request, str(analysis.id), analysis.name, target_tab.id, target_tab.name


def _build_refresh_request(schedule: Schedule) -> compute_schemas.BuildRequest:
    pipeline = {
        'analysis_id': schedule.id,
        'tabs': [
            {
                'id': schedule.id,
                'name': 'Scheduled refresh',
                'datasource': {
                    'id': schedule.datasource_id,
                    'analysis_tab_id': None,
                    'source_type': 'schedule',
                    'config': {'branch': 'master'},
                },
                'output': {
                    'result_id': schedule.datasource_id,
                    'datasource_type': 'iceberg',
                    'format': 'parquet',
                    'filename': f'schedule_{schedule.id}',
                },
                'steps': [],
            }
        ],
    }
    return compute_schemas.BuildRequest.model_validate({'analysis_pipeline': pipeline, 'tab_id': schedule.id})


def _enqueue_schedule_refresh_build(
    session: Session,
    *,
    schedule: Schedule,
    target_kind: str,
    namespace: str,
    now: datetime,
) -> build_run_service.BuildRun:
    build_id = str(uuid.uuid4())
    analysis_name = f'Schedule refresh {schedule.datasource_id}'
    run = build_run_service.create_build_run(
        session,
        build_id=build_id,
        namespace=namespace,
        schedule_id=schedule.id,
        analysis_id=schedule.id,
        analysis_name=analysis_name,
        request_json=_build_refresh_request(schedule).model_dump(mode='json'),
        starter_json=_schedule_starter(schedule.id).model_dump(mode='json'),
        status=BuildRunStatus.QUEUED,
        current_kind=target_kind,
        current_datasource_id=schedule.datasource_id,
        current_tab_id=schedule.id,
        current_tab_name='Scheduled refresh',
        current_output_id=schedule.datasource_id,
        current_output_name=analysis_name,
        total_tabs=1,
        created_at=now,
        started_at=now,
    )
    build_job_service.create_job(session, build_id=build_id, namespace=namespace)
    return run


def _enqueue_schedule_analysis_build(
    session: Session,
    *,
    schedule: Schedule,
    namespace: str,
    analysis_id: str,
    analysis_name: str,
    tab_id: str | None,
    tab_name: str | None,
    request: compute_schemas.BuildRequest,
    now: datetime,
) -> build_run_service.BuildRun:
    build_id = str(uuid.uuid4())
    run = build_run_service.create_build_run(
        session,
        build_id=build_id,
        namespace=namespace,
        schedule_id=schedule.id,
        analysis_id=analysis_id,
        analysis_name=analysis_name,
        request_json=request.model_dump(mode='json'),
        starter_json=_schedule_starter(schedule.id).model_dump(mode='json'),
        status=BuildRunStatus.QUEUED,
        current_kind='datasource_update',
        current_datasource_id=schedule.datasource_id,
        current_tab_id=tab_id,
        current_tab_name=tab_name,
        current_output_id=schedule.datasource_id,
        current_output_name=tab_name,
        total_tabs=len(request.analysis_pipeline.tabs),
        created_at=now,
        started_at=now,
    )
    build_job_service.create_job(session, build_id=build_id, namespace=namespace)
    return run


def is_schedule_target_eligible(datasource: DataSource) -> bool:
    """Schedules can target any existing datasource."""
    return datasource is not None


def _resolve_schedule_target(session: Session, datasource_id: str) -> tuple[str, str | None, str | None]:
    """Resolve schedule execution path and optional analysis provenance.

    Returns: (target_kind, analysis_id, tab_id)
    target_kind: analysis | raw | datasource
    """
    datasource = session.get(DataSource, datasource_id)
    if not datasource:
        raise DataSourceNotFoundError(datasource_id)

    analysis_id = datasource.created_by_analysis_id
    if datasource.created_by == 'analysis' and analysis_id:
        tab_id = datasource.config.get('analysis_tab_id') if isinstance(datasource.config, dict) else None
        return 'analysis', analysis_id, tab_id

    if is_reingestable_raw_datasource(datasource):
        return 'raw', None, None

    return 'datasource', None, None


def _build_schedule_response(
    schedule: Schedule,
    datasource: DataSource | None,
    analysis: Analysis | None,
) -> ScheduleResponse:
    """Build a schedule response from preloaded related models."""
    data = {
        'id': schedule.id,
        'datasource_id': schedule.datasource_id,
        'cron_expression': schedule.cron_expression,
        'enabled': schedule.enabled,
        'depends_on': schedule.depends_on,
        'trigger_on_datasource_id': schedule.trigger_on_datasource_id,
        'last_run': schedule.last_run,
        'next_run': schedule.next_run,
        'created_at': schedule.created_at,
    }

    if datasource:
        data['analysis_id'] = datasource.created_by_analysis_id

        tab_id = datasource.config.get('analysis_tab_id') if isinstance(datasource.config, dict) else None
        data['tab_id'] = tab_id

        if analysis:
            data['analysis_name'] = analysis.name

            if tab_id:
                for ptab in analysis.pipeline.tabs:
                    if ptab.id == tab_id:
                        data['tab_name'] = ptab.name or 'unnamed'
                        break

    return ScheduleResponse.model_validate(data)


def _enrich_schedule_response(session: Session, schedule: Schedule) -> ScheduleResponse:
    """Enrich schedule with resolved analysis/tab info from datasource provenance."""
    datasource = session.get(DataSource, schedule.datasource_id)
    analysis = None
    if datasource and datasource.created_by_analysis_id:
        analysis = session.get(Analysis, datasource.created_by_analysis_id)
    return _build_schedule_response(schedule, datasource, analysis)


def _enrich_schedule_response_batch(
    schedules: Sequence[Schedule],
    ds_map: dict[str, DataSource],
    analysis_map: dict[str, Analysis],
) -> list[ScheduleResponse]:
    """Enrich schedules using preloaded datasource and analysis maps."""
    responses: list[ScheduleResponse] = []
    for schedule in schedules:
        datasource = ds_map.get(schedule.datasource_id)
        analysis = None
        if datasource and datasource.created_by_analysis_id:
            analysis = analysis_map.get(datasource.created_by_analysis_id)
        responses.append(_build_schedule_response(schedule, datasource, analysis))
    return responses


def list_schedules(
    session: Session,
    datasource_id: str | None = None,
) -> list[ScheduleResponse]:
    """List schedules with optional filtering by target datasource."""
    query = select(Schedule)
    if datasource_id:
        query = query.where(col(Schedule.datasource_id) == datasource_id)
    result = session.execute(query)
    schedules = result.scalars().all()
    datasource_ids = {schedule.datasource_id for schedule in schedules}

    ds_map: dict[str, DataSource] = {}
    if datasource_ids:
        datasources = session.execute(select(DataSource).where(col(DataSource.id).in_(list(datasource_ids)))).scalars().all()
        ds_map = {str(datasource.id): datasource for datasource in datasources}

    analysis_ids = {datasource.created_by_analysis_id for datasource in ds_map.values() if datasource.created_by_analysis_id}

    analysis_map: dict[str, Analysis] = {}
    if analysis_ids:
        analyses = session.execute(select(Analysis).where(col(Analysis.id).in_(list(analysis_ids)))).scalars().all()
        analysis_map = {str(analysis.id): analysis for analysis in analyses}

    return _enrich_schedule_response_batch(schedules, ds_map, analysis_map)


def create_schedule(session: Session, payload: ScheduleCreate) -> ScheduleResponse:
    """Create a new schedule targeting a specific datasource.

    analysis_id and tab_id are resolved from datasource provenance at execution time.
    """
    # Validate datasource exists
    datasource = session.get(DataSource, payload.datasource_id)
    if not datasource:
        raise DataSourceNotFoundError(payload.datasource_id)
    if datasource.created_by == 'analysis' and not datasource.created_by_analysis_id:
        raise ScheduleValidationError('Datasource has no analysis provenance', details={'datasource_id': payload.datasource_id})

    # Validate dependency if provided
    if payload.depends_on:
        dep_schedule = session.get(Schedule, payload.depends_on)
        if not dep_schedule:
            raise ScheduleValidationError('Dependency schedule not found', details={'depends_on': payload.depends_on})

    # Validate trigger datasource if provided
    if payload.trigger_on_datasource_id:
        trigger_ds = session.get(DataSource, payload.trigger_on_datasource_id)
        if not trigger_ds:
            raise DataSourceNotFoundError(payload.trigger_on_datasource_id)

    next_run = _compute_next_run(payload.cron_expression)
    record = Schedule(
        id=str(uuid.uuid4()),
        datasource_id=payload.datasource_id,
        cron_expression=payload.cron_expression,
        enabled=payload.enabled,
        depends_on=payload.depends_on,
        trigger_on_datasource_id=payload.trigger_on_datasource_id,
        last_run=None,
        next_run=next_run,
        created_at=datetime.now(UTC),
        # Backward compatibility: store analysis_id for existing code
        analysis_id=datasource.created_by_analysis_id,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return _enrich_schedule_response(session, record)


def update_schedule(session: Session, schedule_id: str, payload: ScheduleUpdate) -> ScheduleResponse:
    schedule = session.get(Schedule, schedule_id)
    if not schedule:
        raise ScheduleNotFoundError(schedule_id)

    # Validate new datasource if provided
    if payload.datasource_id:
        datasource = session.get(DataSource, payload.datasource_id)
        if not datasource:
            raise DataSourceNotFoundError(payload.datasource_id)
        # Update backward-compat analysis_id
        schedule.analysis_id = datasource.created_by_analysis_id

    # Validate dependency if provided
    if payload.depends_on:
        dep_schedule = session.get(Schedule, payload.depends_on)
        if not dep_schedule:
            raise ScheduleValidationError('Dependency schedule not found', details={'depends_on': payload.depends_on})

    # Validate trigger datasource if provided
    if payload.trigger_on_datasource_id:
        trigger_ds = session.get(DataSource, payload.trigger_on_datasource_id)
        if not trigger_ds:
            raise DataSourceNotFoundError(payload.trigger_on_datasource_id)

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key != 'analysis_id':  # Don't allow direct analysis_id updates
            setattr(schedule, key, value)

    if payload.cron_expression:
        schedule.next_run = _compute_next_run(payload.cron_expression)

    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return _enrich_schedule_response(session, schedule)


def delete_schedule(session: Session, schedule_id: str) -> None:
    schedule = session.get(Schedule, schedule_id)
    if not schedule:
        raise ScheduleNotFoundError(schedule_id)
    session.delete(schedule)
    session.commit()


def get_build_order(session: Session, analysis_id: str) -> list[str]:
    """Compute topological build order for analyses based on datasource dependencies.

    Returns list of analysis IDs in dependency order (upstream first).
    """
    from modules.analysis.models import Analysis, AnalysisDataSource

    graph: dict[str, set[str]] = {}
    in_degree: dict[str, int] = {}

    analyses = session.execute(select(Analysis)).scalars().all()
    for analysis in analyses:
        if analysis.id not in graph:
            graph[analysis.id] = set()
            in_degree[analysis.id] = 0

    deps = (
        session.execute(
            select(AnalysisDataSource).where(AnalysisDataSource.analysis_id.in_(list(graph.keys()))),  # type: ignore[arg-type, attr-defined]
        )
        .scalars()
        .all()
    )
    dep_ds_ids = [dep.datasource_id for dep in deps]
    datasources_by_id: dict[str, DataSource] = {}
    if dep_ds_ids:
        ds_rows = session.execute(select(DataSource).where(col(DataSource.id).in_(dep_ds_ids))).scalars().all()
        datasources_by_id = {str(ds.id): ds for ds in ds_rows}
    for dep in deps:
        datasource = datasources_by_id.get(dep.datasource_id)
        if not datasource or not datasource.created_by_analysis_id:
            continue
        upstream = datasource.created_by_analysis_id
        if upstream not in graph or dep.analysis_id not in graph:
            continue
        edges = graph.setdefault(upstream, set())
        is_new = dep.analysis_id not in edges
        edges.add(dep.analysis_id)
        if is_new:
            in_degree[dep.analysis_id] = in_degree.get(dep.analysis_id, 0) + 1

    queue = deque(aid for aid, degree in in_degree.items() if degree == 0)
    ordered: list[str] = []
    while queue:
        node = queue.popleft()
        ordered.append(node)
        for neighbor in graph.get(node, set()):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    return ordered


def should_run(cron_expr: str, last_run: datetime | None) -> bool:
    if not cron_expr:
        return False
    if last_run is None:
        return True
    naive_last = last_run.replace(tzinfo=None) if last_run.tzinfo else last_run
    cron = croniter.croniter(cron_expr, naive_last)
    next_run = cron.get_next(datetime)
    now = datetime.now(UTC).replace(tzinfo=None)
    return next_run <= now


def _is_triggered_by_datasource(
    session: Session,
    datasource_id: str,
    last_run: datetime | None,
) -> bool:
    datasource = session.get(DataSource, datasource_id)
    if not datasource:
        return False
    result = session.execute(
        select(EngineRun)
        .where(EngineRun.datasource_id == datasource_id)  # type: ignore[arg-type]
        .where(EngineRun.status == 'success')  # type: ignore[arg-type]
        .where(EngineRun.kind.in_(['datasource_update', 'datasource_create']))  # type: ignore[arg-type, attr-defined]
        .order_by(EngineRun.created_at.desc())  # type: ignore[arg-type, attr-defined]
        .limit(1),
    )
    latest = result.scalar_one_or_none()
    if not latest:
        return False
    if last_run is None:
        return True
    last_dt = last_run.replace(tzinfo=None) if last_run.tzinfo else last_run
    created = latest.created_at.replace(tzinfo=None) if latest.created_at.tzinfo else latest.created_at
    return created > last_dt


def _is_triggered_by_schedule(
    session: Session,
    dependency_id: str,
    last_triggered_at: datetime | None,
) -> bool:
    dependency = session.get(Schedule, dependency_id)
    if dependency is None or dependency.last_success_at is None:
        return False
    completed = dependency.last_success_at.replace(tzinfo=None) if dependency.last_success_at.tzinfo else dependency.last_success_at
    if last_triggered_at is None:
        return True
    previous = last_triggered_at.replace(tzinfo=None) if last_triggered_at.tzinfo else last_triggered_at
    return completed > previous


def get_due_schedules(session: Session) -> list[Schedule]:
    """Return all enabled schedules that are due to run."""
    result = session.execute(
        select(Schedule).where(col(Schedule.enabled) == True),  # type: ignore[arg-type]  # noqa: E712
    )
    schedules = result.scalars().all()
    ds_ids = [sched.datasource_id for sched in schedules]
    valid_ds_ids: set[str] = set()
    if ds_ids:
        id_rows = session.execute(select(col(DataSource.id)).where(col(DataSource.id).in_(ds_ids))).all()
        valid_ds_ids = {str(row[0]) for row in id_rows}
    due: list[Schedule] = []
    for sched in schedules:
        if sched.datasource_id not in valid_ds_ids:
            continue
        reference = sched.last_triggered_at or sched.last_run
        if sched.depends_on and _is_triggered_by_schedule(session, sched.depends_on, sched.last_triggered_at):
            due.append(sched)
            continue
        if sched.trigger_on_datasource_id and _is_triggered_by_datasource(
            session,
            sched.trigger_on_datasource_id,
            reference,
        ):
            due.append(sched)
            continue
        if sched.depends_on or sched.trigger_on_datasource_id:
            continue
        if should_run(sched.cron_expression, reference):
            due.append(sched)
    return due


def claim_due_schedules(
    session: Session,
    *,
    worker_id: str,
    limit: int = 100,
    now: datetime | None = None,
    lease_seconds: int | None = None,
) -> list[Schedule]:
    stamp = now or _utcnow()
    naive_stamp = _naive_utc(stamp)
    ttl = lease_seconds or _lease_seconds()
    lease_until = stamp + timedelta(seconds=ttl)
    table = Schedule.metadata.tables[Schedule.__tablename__]
    base = (
        select(Schedule)
        .where(col(Schedule.enabled) == True)  # type: ignore[arg-type]  # noqa: E712
        .where(
            or_(
                table.c.lease_owner.is_(None),
                and_(table.c.lease_expires_at.is_not(None), table.c.lease_expires_at <= naive_stamp),
            )
        )
    )
    dialect = session.get_bind().dialect.name
    stmt = base.with_for_update(skip_locked=True) if dialect == 'postgresql' else base
    schedules = list(session.execute(stmt).scalars().all())
    due_ids = {schedule.id for schedule in get_due_schedules(session)}
    due = [schedule for schedule in schedules if schedule.id in due_ids]
    claimed: list[Schedule] = []
    for schedule in due[:limit]:
        if build_run_service.has_inflight_build_for_schedule(session, schedule.id):
            continue
        claim = update(Schedule).where(Schedule.id == schedule.id)
        claim = (
            claim.where(table.c.lease_owner.is_(None))
            if schedule.lease_owner is None
            else claim.where(Schedule.lease_owner == schedule.lease_owner)  # type: ignore[arg-type]
        )
        if schedule.lease_expires_at is None:
            claim = claim.where(table.c.lease_expires_at.is_(None))
        else:
            claim = claim.where(Schedule.lease_expires_at == schedule.lease_expires_at)  # type: ignore[arg-type]
        result = cast(
            CursorResult[Any],
            session.execute(
                claim.values(
                    lease_owner=worker_id,
                    lease_expires_at=_naive_utc(lease_until),
                    last_claimed_at=naive_stamp,
                )
            ),
        )
        if result.rowcount != 1:
            continue
        claimed.append(schedule)
    if not claimed:
        session.rollback()
        return []
    session.commit()
    claimed_ids = [schedule.id for schedule in claimed]
    refreshed = session.execute(select(Schedule).where(col(Schedule.id).in_(claimed_ids))).scalars().all()
    return list(refreshed)


def mark_schedule_run(session: Session, schedule_id: str) -> None:
    """Update last_run to now and recompute next_run after a successful build."""
    schedule = session.get(Schedule, schedule_id)
    if not schedule:
        return
    now = _utcnow().replace(tzinfo=None)
    schedule.last_run = now
    schedule.last_success_at = now
    schedule.next_run = _compute_next_run(schedule.cron_expression)
    schedule.lease_owner = None
    schedule.lease_expires_at = None
    session.add(schedule)
    session.commit()


def enqueue_schedule_run(session: Session, schedule_id: str, *, worker_id: str) -> str:
    schedule = session.get(Schedule, schedule_id)
    if not schedule:
        raise ValueError(f'Schedule {schedule_id} not found')
    if build_run_service.has_inflight_build_for_schedule(session, schedule_id):
        raise ValueError(f'Schedule {schedule_id} already has an in-flight build')

    stamp = _utcnow()
    naive_stamp = _naive_utc(stamp)
    if schedule.lease_owner != worker_id:
        raise ValueError(f'Schedule {schedule_id} is not leased by {worker_id}')
    if schedule.lease_expires_at is not None and _naive_utc(schedule.lease_expires_at) <= naive_stamp:
        raise ValueError(f'Schedule {schedule_id} lease has expired')

    target_kind, analysis_id, _ = _resolve_schedule_target(session, schedule.datasource_id)
    namespace = get_namespace()
    schedule.last_triggered_at = naive_stamp
    schedule.last_failure_at = None

    if target_kind == 'raw':
        run = _enqueue_schedule_refresh_build(
            session,
            schedule=schedule,
            target_kind='raw',
            namespace=namespace,
            now=stamp,
        )
        build_job_hub.publish()
        runtime_ipc.notify_build_job()
        return run.id

    if target_kind == 'datasource':
        run = _enqueue_schedule_refresh_build(
            session,
            schedule=schedule,
            target_kind='datasource_update',
            namespace=namespace,
            now=stamp,
        )
        build_job_hub.publish()
        runtime_ipc.notify_build_job()
        return run.id

    if analysis_id is None:
        raise ValueError(f'Analysis provenance missing for schedule {schedule_id}')
    request, resolved_analysis_id, analysis_name, tab_id, tab_name = _build_analysis_request(session, schedule, analysis_id)
    run = _enqueue_schedule_analysis_build(
        session,
        schedule=schedule,
        namespace=namespace,
        analysis_id=resolved_analysis_id,
        analysis_name=analysis_name,
        tab_id=tab_id,
        tab_name=tab_name,
        request=request,
        now=stamp,
    )
    build_job_hub.publish()
    runtime_ipc.notify_build_job()
    return run.id


def reconcile_schedule_run(session: Session, *, build_id: str) -> Schedule | None:
    run = build_run_service.get_build_run(session, build_id)
    if run is None or run.schedule_id is None or run.status not in _SCHEDULE_TERMINAL_STATUSES:
        return None
    schedule = session.get(Schedule, run.schedule_id)
    if schedule is None:
        return None

    completed = run.completed_at or run.updated_at
    stamp = completed.replace(tzinfo=None) if completed.tzinfo is not None else completed
    schedule.lease_owner = None
    schedule.lease_expires_at = None
    if run.status == BuildRunStatus.COMPLETED:
        schedule.last_run = stamp
        schedule.last_success_at = stamp
        schedule.last_successful_build_id = run.id
        schedule.next_run = _compute_next_run(schedule.cron_expression)
    else:
        schedule.last_failure_at = stamp
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


def _resolve_upstream_tabs(tabs: list[PipelineTab], target_tab_id: str) -> set[str]:
    """Find all tab IDs that the target tab depends on via lazyframe inputs (including itself)."""
    output_to_tab: dict[str, str] = {}
    tab_input: dict[str, str] = {}

    for tab in tabs:
        if tab.id and tab.output.result_id:
            output_to_tab[tab.output.result_id] = tab.id
        if tab.id and tab.datasource.id:
            tab_input[tab.id] = tab.datasource.id

    required: set[str] = set()
    queue: deque[str] = deque([target_tab_id])
    while queue:
        current = queue.popleft()
        if current in required:
            continue
        required.add(current)
        input_ds = tab_input.get(current)
        if input_ds and input_ds in output_to_tab:
            upstream = output_to_tab[input_ds]
            if upstream not in required:
                queue.append(upstream)

    return required


def run_analysis_build(
    session: Session,
    analysis_id: str,
    manager: ProcessManager | None = None,
    datasource_id: str | None = None,
    triggered_by: str = 'schedule',
    tab_id: str | None = None,
) -> dict:
    """Execute a full build for an analysis — run all tabs.

    Tabs with output config export data via export_data().
    Tabs without output config are skipped.
    Engine runs are tagged with ``triggered_by`` (default 'schedule').
    If ``tab_id`` is provided, that tab and its upstream lazyframe
    dependencies are built.

    Returns a dict with build results per tab.
    """
    from modules.compute import service as compute_service

    analysis = session.get(Analysis, analysis_id)
    if not analysis:
        raise AnalysisNotFoundError(analysis_id)

    pipeline_payload = compute_service.build_analysis_pipeline_payload(session, analysis, datasource_id=datasource_id)

    pipeline = analysis.pipeline
    if not pipeline.tabs:
        logger.warning(f'Scheduler: analysis {analysis_id} has no tabs, skipping build')
        return {'analysis_id': analysis_id, 'tabs_built': 0, 'results': []}

    required_tabs = _resolve_upstream_tabs(pipeline.tabs, tab_id) if tab_id else None

    results: list[dict] = []
    tabs_built = 0

    for tab in pipeline.tabs:
        current_tab_id = tab.id or 'unknown'
        tab_name = tab.name or 'unnamed'
        tab_datasource_id = tab.datasource.id
        tab_output_id = tab.output.result_id
        has_output = bool(tab.output.filename)
        steps = tab.steps

        if not tab_datasource_id:
            continue

        if required_tabs and current_tab_id not in required_tabs:
            continue

        if datasource_id and tab_output_id != datasource_id:
            continue

        # Determine the target step (last step, or 'source' if no steps)
        target_step_id = steps[-1].id if steps else 'source'

        try:
            if has_output:
                # Tab has export config — run full export (Iceberg-only)
                filename = tab.output.filename or f'{tab_name}_out'

                iceberg_cfg = tab.output.to_dict().get('iceberg')
                iceberg_options = (
                    {
                        'table_name': iceberg_cfg.get('table_name', 'exported_data'),
                        'namespace': iceberg_cfg.get('namespace', 'outputs'),
                        'branch': iceberg_cfg.get('branch', 'master'),
                    }
                    if isinstance(iceberg_cfg, dict)
                    else None
                )

                compute_service.export_data(
                    session=session,
                    manager=manager,  # type: ignore[arg-type]
                    target_step_id=target_step_id,
                    analysis_pipeline=pipeline_payload,
                    filename=filename,
                    iceberg_options=iceberg_options,
                    analysis_id=analysis_id,
                    triggered_by=triggered_by,
                    result_id=tab.output.result_id,
                    tab_id=current_tab_id,
                )
            else:
                if required_tabs and current_tab_id != tab_id:
                    tabs_built += 1
                    results.append({'tab_id': current_tab_id, 'tab_name': tab_name, 'status': 'success'})
                    continue
                raise ScheduleValidationError(f'Tab {current_tab_id} missing output configuration')

            tabs_built += 1
            results.append({'tab_id': current_tab_id, 'tab_name': tab_name, 'status': 'success'})
            logger.info(f'Scheduler: built tab {tab_name} ({current_tab_id}) for analysis {analysis_id}')
        except Exception as e:
            results.append({'tab_id': current_tab_id, 'tab_name': tab_name, 'status': 'failed', 'error': str(e)})
            logger.error(f'Scheduler: failed to build tab {tab_name} ({current_tab_id}) for analysis {analysis_id}: {e}')

    return {'analysis_id': analysis_id, 'tabs_built': tabs_built, 'results': results}


def _compute_next_run(cron_expr: str) -> datetime | None:
    if not cron_expr:
        return None
    cron = croniter.croniter(cron_expr, datetime.now(UTC))
    return cron.get_next(datetime)
