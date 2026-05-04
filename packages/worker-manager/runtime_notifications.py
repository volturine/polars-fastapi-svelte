from __future__ import annotations

from contracts.build_jobs.live import hub as build_job_hub
from contracts.compute_requests.live import request_hub


async def handle_runtime_payload(payload: dict[str, object]) -> None:
    kind = payload.get('kind')
    if kind == 'job':
        build_job_hub.publish()
        return
    if kind == 'compute_request':
        request_hub.publish()
