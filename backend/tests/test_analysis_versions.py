from datetime import UTC, datetime

from modules.analysis.models import Analysis
from modules.analysis_versions.models import AnalysisVersion


def test_list_versions_returns_versions(test_db_session, client):
    analysis_id = 'analysis-version-1'
    analysis = Analysis(
        id=analysis_id,
        name='Versioned Analysis',
        description=None,
        pipeline_definition={'steps': [], 'datasource_ids': [], 'tabs': []},
        status='draft',
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    version = AnalysisVersion(
        id='version-1',
        analysis_id=analysis_id,
        version=1,
        name='Versioned Analysis',
        description=None,
        pipeline_definition={'steps': [], 'datasource_ids': [], 'tabs': []},
        created_at=datetime.now(UTC),
    )
    test_db_session.add(analysis)
    test_db_session.add(version)
    test_db_session.commit()

    response = client.get(f'/api/v1/analysis/{analysis_id}/versions')

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['version'] == 1


def test_restore_version_updates_analysis(test_db_session, client):
    analysis_id = 'analysis-version-2'
    analysis = Analysis(
        id=analysis_id,
        name='Original',
        description=None,
        pipeline_definition={'steps': [], 'datasource_ids': [], 'tabs': []},
        status='draft',
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    version = AnalysisVersion(
        id='version-2',
        analysis_id=analysis_id,
        version=2,
        name='Restored',
        description='restored',
        pipeline_definition={'steps': [{'id': 'step-1', 'type': 'select', 'config': {}}], 'datasource_ids': [], 'tabs': []},
        created_at=datetime.now(UTC),
    )
    test_db_session.add(analysis)
    test_db_session.add(version)
    test_db_session.commit()

    response = client.post(f'/api/v1/analysis/{analysis_id}/versions/2/restore')

    assert response.status_code == 200
    payload = response.json()
    assert payload['name'] == 'Restored'
