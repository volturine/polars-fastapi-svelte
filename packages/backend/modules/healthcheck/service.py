from sqlmodel import Session

from core import healthcheck_service as shared_healthcheck_service
from modules.healthcheck.schemas import HealthCheckCreate, HealthCheckResponse, HealthCheckResultResponse, HealthCheckUpdate

HealthcheckDetails = shared_healthcheck_service.HealthcheckDetails
HealthcheckEvaluator = shared_healthcheck_service.HealthcheckEvaluator
run_healthchecks = shared_healthcheck_service.run_healthchecks


def list_healthchecks(session: Session, datasource_id: str) -> list[HealthCheckResponse]:
    return [HealthCheckResponse.model_validate(item) for item in shared_healthcheck_service.list_healthchecks(session, datasource_id)]


def list_all_healthchecks(session: Session) -> list[HealthCheckResponse]:
    return [HealthCheckResponse.model_validate(item) for item in shared_healthcheck_service.list_all_healthchecks(session)]


def create_healthcheck(session: Session, payload: HealthCheckCreate) -> HealthCheckResponse:
    created = shared_healthcheck_service.create_healthcheck(
        session,
        shared_healthcheck_service.HealthCheckCreate.model_validate(payload.model_dump()),
    )
    return HealthCheckResponse.model_validate(created)


def update_healthcheck(session: Session, healthcheck_id: str, payload: HealthCheckUpdate) -> HealthCheckResponse:
    updated = shared_healthcheck_service.update_healthcheck(
        session,
        healthcheck_id,
        shared_healthcheck_service.HealthCheckUpdate.model_validate(payload.model_dump(exclude_none=True)),
    )
    return HealthCheckResponse.model_validate(updated)


def delete_healthcheck(session: Session, healthcheck_id: str) -> None:
    shared_healthcheck_service.delete_healthcheck(session, healthcheck_id)


def list_results(session: Session, datasource_id: str, limit: int = 10) -> list[HealthCheckResultResponse]:
    return [
        HealthCheckResultResponse.model_validate(item) for item in shared_healthcheck_service.list_results(session, datasource_id, limit)
    ]


def list_all_results(session: Session, limit: int = 10) -> list[HealthCheckResultResponse]:
    return [HealthCheckResultResponse.model_validate(item) for item in shared_healthcheck_service.list_all_results(session, limit)]


def list_results_for_check(session: Session, healthcheck_id: str, limit: int = 10) -> list[HealthCheckResultResponse]:
    return [
        HealthCheckResultResponse.model_validate(item)
        for item in shared_healthcheck_service.list_results_for_check(session, healthcheck_id, limit)
    ]
