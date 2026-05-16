from contracts.datasource.models import DataSource, DataSourceCreatedBy, DataSourceTargetKind
from contracts.datasource.source_types import DataSourceType
from contracts.healthcheck_models import HealthCheckType


def test_datasource_target_kind_is_model_owned() -> None:
    analysis_output = DataSource(
        id='ds-analysis',
        name='Analysis Output',
        source_type=DataSourceType.ICEBERG.value,
        config={'analysis_tab_id': 'tab-1'},
        created_by=DataSourceCreatedBy.ANALYSIS.value,
        created_by_analysis_id='analysis-1',
        created_at='2024-01-01T00:00:00Z',
    )
    raw_import = DataSource(
        id='ds-raw',
        name='Raw Import',
        source_type=DataSourceType.ICEBERG.value,
        config={'source': {'source_type': DataSourceType.FILE.value}},
        created_by=DataSourceCreatedBy.IMPORT.value,
        created_at='2024-01-01T00:00:00Z',
    )
    derived = DataSource(
        id='ds-derived',
        name='Derived',
        source_type=DataSourceType.ICEBERG.value,
        config={},
        created_by=DataSourceCreatedBy.IMPORT.value,
        created_at='2024-01-01T00:00:00Z',
    )

    assert analysis_output.target_kind() == DataSourceTargetKind.ANALYSIS
    assert raw_import.target_kind() == DataSourceTargetKind.RAW
    assert derived.target_kind() == DataSourceTargetKind.DATASOURCE


def test_healthcheck_type_owns_uniqueness_rule() -> None:
    assert HealthCheckType.ROW_COUNT.requires_unique_per_datasource is True
    assert HealthCheckType.COLUMN_NULL.requires_unique_per_datasource is False
