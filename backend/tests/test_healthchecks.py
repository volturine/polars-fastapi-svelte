from datetime import UTC, datetime

from modules.datasource.models import DataSource


def test_healthcheck_crud(test_db_session, client):
    datasource_id = 'ds-health-1'
    datasource = DataSource(
        id=datasource_id,
        name='Health Source',
        source_type='file',
        config={'file_path': '/tmp/file.csv', 'file_type': 'csv', 'options': {}},
        created_at=datetime.now(UTC),
    )
    test_db_session.add(datasource)
    test_db_session.commit()

    create_payload = {
        'datasource_id': datasource_id,
        'name': 'Row Count Check',
        'check_type': 'row_count',
        'config': {'min_rows': 1},
        'enabled': True,
    }
    create_response = client.post('/api/v1/healthchecks', json=create_payload)
    assert create_response.status_code == 200
    created = create_response.json()
    assert created['name'] == 'Row Count Check'

    list_response = client.get(f'/api/v1/healthchecks?datasource_id={datasource_id}')
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert len(list_payload) == 1

    update_response = client.put(
        f'/api/v1/healthchecks/{created["id"]}',
        json={'name': 'Updated Check', 'enabled': False},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated['name'] == 'Updated Check'
    assert updated['enabled'] is False

    delete_response = client.delete(f'/api/v1/healthchecks/{created["id"]}')
    assert delete_response.status_code == 200
