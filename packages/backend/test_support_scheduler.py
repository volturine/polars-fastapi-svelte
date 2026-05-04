from __future__ import annotations

from collections import deque
from typing import Any, TypedDict, cast

from scheduler_service import build_analysis_pipeline_payload
from sqlmodel import Session

from contracts.analysis.models import Analysis
from core.exceptions import AnalysisNotFoundError, ScheduleValidationError


class RunAnalysisBuildTabResult(TypedDict, total=False):
    tab_id: str
    tab_name: str
    status: str
    error: str


class RunAnalysisBuildResult(TypedDict):
    analysis_id: str
    tabs_built: int
    results: list[RunAnalysisBuildTabResult]


def _resolve_upstream_tabs(tabs: list[Any], target_tab_id: str) -> set[str]:
    output_to_tab: dict[str, str] = {}
    tab_input: dict[str, str] = {}

    for tab in tabs:
        tab_id = getattr(tab, 'id', None)
        output = getattr(tab, 'output', None)
        datasource = getattr(tab, 'datasource', None)
        output_id = getattr(output, 'result_id', None)
        input_id = getattr(datasource, 'id', None)
        if tab_id and output_id:
            output_to_tab[str(output_id)] = str(tab_id)
        if tab_id and input_id:
            tab_input[str(tab_id)] = str(input_id)

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
    manager: Any | None = None,
    datasource_id: str | None = None,
    triggered_by: str = 'schedule',
    tab_id: str | None = None,
) -> RunAnalysisBuildResult:
    analysis = session.get(Analysis, analysis_id)
    if not analysis:
        raise AnalysisNotFoundError(analysis_id)

    import compute_service

    pipeline_payload = build_analysis_pipeline_payload(session, analysis, datasource_id=datasource_id)

    pipeline = analysis.pipeline
    if not pipeline.tabs:
        return {'analysis_id': analysis_id, 'tabs_built': 0, 'results': []}

    required_tabs = _resolve_upstream_tabs(pipeline.tabs, tab_id) if tab_id else None

    results: list[RunAnalysisBuildTabResult] = []
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

        target_step_id = steps[-1].id if steps else 'source'

        try:
            if has_output:
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
                    manager=cast(Any, manager),
                    target_step_id=target_step_id,
                    analysis_pipeline=pipeline_payload,
                    filename=filename,
                    iceberg_options=iceberg_options,
                    analysis_id=analysis_id,
                    request_json={'analysis_pipeline': pipeline_payload, 'tab_id': current_tab_id},
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
        except Exception as exc:
            results.append({'tab_id': current_tab_id, 'tab_name': tab_name, 'status': 'failed', 'error': str(exc)})

    return {'analysis_id': analysis_id, 'tabs_built': tabs_built, 'results': results}
