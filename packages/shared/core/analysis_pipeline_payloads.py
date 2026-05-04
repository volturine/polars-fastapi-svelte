from typing import Any

from sqlmodel import Session

from contracts.analysis.models import Analysis
from contracts.datasource.models import DataSource


def build_analysis_pipeline_payload(session: Session, analysis: Analysis, datasource_id: str | None = None) -> dict[str, Any]:
    pipeline = analysis.pipeline_definition
    tabs = pipeline.get('tabs', []) if isinstance(pipeline, dict) else []
    if not isinstance(tabs, list) or not tabs:
        return {'analysis_id': str(analysis.id), 'tabs': []}

    output_map: dict[str, str] = {}
    for tab in tabs:
        if not isinstance(tab, dict):
            continue
        tab_id = tab.get('id')
        output = tab.get('output')
        if not isinstance(output, dict):
            raise ValueError('Analysis pipeline tab missing output configuration')
        output_id = output.get('result_id')
        if not output_id:
            raise ValueError('Analysis pipeline tab missing output.result_id')
        if tab_id:
            output_map[str(tab_id)] = str(output_id)

    output_to_tab = {output_id: tab_id for tab_id, output_id in output_map.items()}

    def enrich_step(step: dict[str, object]) -> dict[str, Any]:
        config = step.get('config')
        if not isinstance(config, dict):
            return step
        next_config = dict(config)
        right_source = next_config.get('right_source') or next_config.get('rightDataSource')
        if isinstance(right_source, str) and right_source and right_source not in output_to_tab:
            datasource_model = session.get(DataSource, right_source)
            if datasource_model is not None:
                next_config['right_source_datasource'] = {
                    'id': right_source,
                    'analysis_tab_id': None,
                    'source_type': datasource_model.source_type,
                    'config': dict(datasource_model.config),
                }
        raw_sources = next_config.get('sources')
        source_ids = [raw_sources] if isinstance(raw_sources, str) else raw_sources if isinstance(raw_sources, list) else []
        refs: list[dict[str, Any]] = []
        for source in source_ids:
            if not isinstance(source, str) or not source or source in output_to_tab:
                continue
            datasource_model = session.get(DataSource, source)
            if datasource_model is None:
                continue
            refs.append(
                {
                    'id': source,
                    'analysis_tab_id': None,
                    'source_type': datasource_model.source_type,
                    'config': dict(datasource_model.config),
                }
            )
        if refs:
            next_config['source_datasources'] = refs
        return {**step, 'config': next_config}

    next_tabs: list[dict[str, Any]] = []
    for tab in tabs:
        if not isinstance(tab, dict):
            continue
        datasource = tab.get('datasource')
        if not isinstance(datasource, dict):
            raise ValueError('Analysis pipeline tab datasource must be a dict')
        output = tab.get('output')
        if not isinstance(output, dict):
            raise ValueError('Analysis pipeline tab missing output configuration')
        output_id = output.get('result_id')
        if not output_id:
            raise ValueError('Analysis pipeline tab missing output.result_id')
        config = datasource.get('config')
        if not isinstance(config, dict):
            raise ValueError('Analysis pipeline tab datasource.config must be a dict')
        branch = config.get('branch')
        if not isinstance(branch, str) or not branch.strip():
            raise ValueError('Analysis pipeline tab datasource.config.branch is required')
        tab_datasource_id = datasource.get('id')
        if not tab_datasource_id:
            raise ValueError('Analysis pipeline tab missing datasource.id')
        analysis_tab_id = datasource.get('analysis_tab_id') if isinstance(datasource.get('analysis_tab_id'), str) else None
        source_type = 'analysis' if analysis_tab_id or str(tab_datasource_id) in output_to_tab else None
        merged_config = dict(config)
        if source_type is None:
            datasource_model = session.get(DataSource, str(tab_datasource_id))
            if datasource_model is not None:
                source_type = datasource_model.source_type
                merged_config = {'branch': branch, **datasource_model.config, **config}
        if datasource_id and str(datasource_id) != str(output_id) and str(datasource_id) != str(tab_datasource_id):
            next_tabs.append(
                {
                    **tab,
                    'datasource': {
                        **datasource,
                        'id': tab_datasource_id,
                        'analysis_tab_id': analysis_tab_id,
                        'source_type': source_type,
                        'config': merged_config,
                    },
                    'steps': [enrich_step(step) for step in tab.get('steps', []) if isinstance(step, dict)],
                }
            )
            continue
        next_tabs.append(
            {
                **tab,
                'datasource': {
                    **datasource,
                    'id': tab_datasource_id,
                    'analysis_tab_id': analysis_tab_id,
                    'source_type': source_type,
                    'config': merged_config,
                },
                'steps': [enrich_step(step) for step in tab.get('steps', []) if isinstance(step, dict)],
            }
        )

    return {
        'analysis_id': str(analysis.id),
        'tabs': next_tabs,
    }
