import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlmodel import Session

from contracts.compute_requests.models import ComputeRequest, ComputeRequestKind, ComputeRequestStatus


def _utcnow() -> datetime:
    return datetime.now(UTC)


def create_request(
    session: Session,
    *,
    namespace: str,
    kind: ComputeRequestKind | str,
    request_json: dict[str, object],
) -> ComputeRequest:
    now = _utcnow()
    request = ComputeRequest(
        id=str(uuid.uuid4()),
        namespace=namespace,
        kind=kind if isinstance(kind, ComputeRequestKind) else ComputeRequestKind(kind),
        status=ComputeRequestStatus.QUEUED,
        request_json=request_json,
        created_at=now,
        updated_at=now,
    )
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


def get_request(session: Session, request_id: str) -> ComputeRequest | None:
    return session.get(ComputeRequest, request_id)


def claim_next_request(session: Session, *, worker_id: str, lease_seconds: int = 30) -> ComputeRequest | None:
    now = _utcnow()
    lease_until = now + timedelta(seconds=lease_seconds)
    table = ComputeRequest.metadata.tables[ComputeRequest.__tablename__]
    base = (
        select(ComputeRequest)
        .where(
            or_(
                table.c.status == ComputeRequestStatus.QUEUED,
                and_(
                    table.c.status == ComputeRequestStatus.RUNNING,
                    table.c.lease_expires_at.is_not(None),
                    table.c.lease_expires_at <= now,
                ),
            )
        )
        .order_by(table.c.created_at)
        .limit(1)
    )
    dialect = session.get_bind().dialect.name
    stmt = base.with_for_update(skip_locked=True) if dialect == 'postgresql' else base
    row = session.execute(stmt).scalars().first()
    if row is None:
        return None
    previous_status = row.status
    previous_owner = row.lease_owner
    previous_expires = row.lease_expires_at
    claim = update(ComputeRequest).where(ComputeRequest.id == row.id).where(ComputeRequest.status == previous_status)  # type: ignore[arg-type]
    claim = (
        claim.where(table.c.lease_owner.is_(None)) if previous_owner is None else claim.where(ComputeRequest.lease_owner == previous_owner)
    )  # type: ignore[arg-type]
    if previous_expires is None:
        claim = claim.where(table.c.lease_expires_at.is_(None))
    else:
        claim = claim.where(ComputeRequest.lease_expires_at == previous_expires)  # type: ignore[arg-type]
    result = session.execute(
        claim.values(
            status=ComputeRequestStatus.RUNNING,
            lease_owner=worker_id,
            lease_expires_at=lease_until,
            updated_at=now,
        )
    )
    if not isinstance(result, CursorResult) or result.rowcount != 1:
        session.rollback()
        return None
    session.commit()
    claimed = session.get(ComputeRequest, row.id)
    return claimed


def renew_request_lease(session: Session, request_id: str, *, worker_id: str, lease_seconds: int = 30) -> ComputeRequest | None:
    request = session.get(ComputeRequest, request_id)
    if request is None:
        return None
    if request.lease_owner != worker_id or request.status != ComputeRequestStatus.RUNNING:
        return None
    request.lease_expires_at = _utcnow() + timedelta(seconds=lease_seconds)
    request.updated_at = _utcnow()
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


def mark_request_completed(
    session: Session,
    request_id: str,
    *,
    response_json: dict[str, object] | None = None,
    artifact_path: str | None = None,
    artifact_name: str | None = None,
    artifact_content_type: str | None = None,
) -> ComputeRequest:
    request = session.get(ComputeRequest, request_id)
    if request is None:
        raise ValueError(f'Compute request {request_id} not found')
    request.status = ComputeRequestStatus.COMPLETED
    request.response_json = response_json
    request.error_message = None
    request.artifact_path = artifact_path
    request.artifact_name = artifact_name
    request.artifact_content_type = artifact_content_type
    request.completed_at = _utcnow()
    request.updated_at = request.completed_at
    request.lease_owner = None
    request.lease_expires_at = None
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


def mark_request_failed(
    session: Session,
    request_id: str,
    *,
    error_message: str,
    response_json: dict[str, object] | None = None,
) -> ComputeRequest:
    request = session.get(ComputeRequest, request_id)
    if request is None:
        raise ValueError(f'Compute request {request_id} not found')
    request.status = ComputeRequestStatus.FAILED
    request.error_message = error_message
    request.response_json = response_json
    request.completed_at = _utcnow()
    request.updated_at = request.completed_at
    request.lease_owner = None
    request.lease_expires_at = None
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


def queued_request_count(session: Session) -> int:
    stmt = select(ComputeRequest).where(ComputeRequest.status == ComputeRequestStatus.QUEUED)  # type: ignore[arg-type]
    return len(session.execute(stmt).scalars().all())


def cleanup_completed_requests(session: Session, *, older_than_seconds: int) -> int:
    cutoff = _utcnow() - timedelta(seconds=older_than_seconds)
    table = ComputeRequest.metadata.tables[ComputeRequest.__tablename__]
    stmt = select(ComputeRequest).where(table.c.completed_at.is_not(None)).where(table.c.completed_at < cutoff)
    rows = list(session.execute(stmt).scalars().all())
    for row in rows:
        session.delete(row)
    session.commit()
    return len(rows)
