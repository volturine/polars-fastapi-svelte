from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from core.database import get_db
from modules.analysis import schemas, service
from modules.compute import service as compute_service
from modules.locks import service as lock_service

router = APIRouter(prefix='/analysis', tags=['analysis'])


@router.post('', response_model=schemas.AnalysisResponseSchema)
def create_analysis(
    data: schemas.AnalysisCreateSchema,
    session: Session = Depends(get_db),
):
    """Create a new analysis with pipeline definition."""
    try:
        return service.create_analysis(session, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to create analysis: {str(e)}')


@router.get('', response_model=list[schemas.AnalysisGalleryItemSchema])
def list_analyses(session: Session = Depends(get_db)):
    """List all analyses as gallery items."""
    try:
        return service.list_analyses(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to list analyses: {str(e)}')


@router.get('/{analysis_id}', response_model=schemas.AnalysisResponseSchema)
def get_analysis(
    analysis_id: str,
    session: Session = Depends(get_db),
):
    """Get a specific analysis by ID."""
    try:
        return service.get_analysis(session, analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to get analysis: {str(e)}')


@router.put('/{analysis_id}', response_model=schemas.AnalysisResponseSchema)
def update_analysis(
    analysis_id: str,
    data: schemas.AnalysisUpdateSchema,
    session: Session = Depends(get_db),
):
    """Update an existing analysis."""
    try:
        service.get_analysis(session, analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not data.client_id or not data.lock_token:
        raise HTTPException(status_code=409, detail='Editing lock required')

    try:
        lock_service.validate_lock(session, analysis_id, data.client_id, data.lock_token)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    try:
        return service.update_analysis(session, analysis_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to update analysis: {str(e)}')


@router.delete('/{analysis_id}')
def delete_analysis(
    analysis_id: str,
    session: Session = Depends(get_db),
):
    """Delete an analysis and its associations."""
    try:
        service.delete_analysis(session, analysis_id)
        return {'message': f'Analysis {analysis_id} deleted successfully'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to delete analysis: {str(e)}')


@router.post('/{analysis_id}/datasource/{datasource_id}')
def link_datasource(
    analysis_id: str,
    datasource_id: str,
    session: Session = Depends(get_db),
):
    """Link a datasource to an analysis."""
    try:
        service.link_datasource(session, analysis_id, datasource_id)
        return {'message': f'DataSource {datasource_id} linked to Analysis {analysis_id}'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to link datasource: {str(e)}')


@router.post('/{analysis_id}/execute')
async def execute_analysis(
    analysis_id: str,
    request: Request,
    analysis_tab_id: str | None = None,
    session: Session = Depends(get_db),
):
    """Execute an analysis and return schema + sample rows."""
    analysis_payload = None
    body = None
    try:
        body = await request.json()
    except Exception:
        body = None
    if isinstance(body, dict):
        analysis_payload = body.get('pipeline')

    if analysis_payload:
        if not isinstance(analysis_payload, dict):
            raise HTTPException(status_code=400, detail='pipeline payload must be a dict')
        tabs = analysis_payload.get('tabs', [])
        if not isinstance(tabs, list):
            raise HTTPException(status_code=400, detail='pipeline tabs must be a list')
        if analysis_tab_id:
            selected = next((tab for tab in tabs if tab.get('id') == analysis_tab_id), None)
        else:
            selected = next((tab for tab in tabs if tab.get('steps')), None)
        if not selected:
            selected = tabs[0] if tabs else None
        if not selected:
            raise HTTPException(status_code=400, detail='pipeline payload missing tabs')
        datasource_id = selected.get('datasource_id')
        pipeline_steps = selected.get('steps', [])
        if not datasource_id:
            raise HTTPException(status_code=400, detail='Analysis tab missing datasource_id')
        if not isinstance(pipeline_steps, list):
            raise HTTPException(status_code=400, detail='Analysis tab steps must be a list')
        config = selected.get('datasource_config') or {}
        if config and not isinstance(config, dict):
            raise HTTPException(status_code=400, detail='Analysis tab datasource_config must be a dict')
        next_config = {**config}
        payload_id = analysis_payload.get('analysis_id')
        payload_id = str(payload_id) if payload_id is not None else None
        if payload_id and payload_id == str(analysis_id):
            next_config['analysis_pipeline'] = analysis_payload
    else:
        try:
            analysis = service.get_analysis(session, analysis_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

        pipeline = analysis.pipeline_definition
        tabs = pipeline.get('tabs', []) if isinstance(pipeline, dict) else []
        if tabs:
            selected = None
            if analysis_tab_id:
                selected = next((tab for tab in tabs if tab.get('id') == analysis_tab_id), None)
            if not selected:
                selected = next((tab for tab in tabs if tab.get('steps')), tabs[0])
            datasource_id = selected.get('datasource_id')
            pipeline_steps = selected.get('steps', [])
            if not datasource_id:
                raise HTTPException(status_code=400, detail='Analysis tab missing datasource_id')
            next_config = selected.get('datasource_config') or {}
        else:
            pipeline_steps = pipeline.get('steps', []) if isinstance(pipeline, dict) else []
            datasource_ids = pipeline.get('datasource_ids', []) if isinstance(pipeline, dict) else []
            if not datasource_ids:
                raise HTTPException(status_code=400, detail='Analysis has no datasource')
            datasource_id = datasource_ids[0]
            next_config = {}

    preview = compute_service.preview_step(
        session=session,
        datasource_id=str(datasource_id),
        pipeline_steps=pipeline_steps,
        target_step_id=pipeline_steps[-1]['id'] if pipeline_steps else 'source',
        row_limit=50,
        page=1,
        analysis_id=analysis_id,
        datasource_config=next_config,
    )

    return {
        'schema': preview.column_types,
        'rows': preview.data,
        'row_count': preview.total_rows,
    }


@router.delete('/{analysis_id}/datasources/{datasource_id}', status_code=204)
def unlink_datasource(
    analysis_id: str,
    datasource_id: str,
    session: Session = Depends(get_db),
):
    """Unlink a datasource from an analysis."""
    try:
        service.unlink_datasource(session, analysis_id, datasource_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to unlink datasource: {str(e)}')
