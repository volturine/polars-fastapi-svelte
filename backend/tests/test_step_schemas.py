import pytest

from modules.analysis.step_schemas import SelectConfig, get_step_catalog, validate_step


def test_select_config_includes_cast_map_schema() -> None:
    schema = SelectConfig.model_json_schema()
    props = schema.get('properties', {})
    cast_map = props.get('cast_map', {})
    additional = cast_map.get('additionalProperties', {})
    assert cast_map.get('type') == 'object'
    assert additional.get('enum') == ['Int64', 'Float64', 'Boolean', 'String', 'Utf8', 'Date', 'Datetime']


def test_step_catalog_excludes_removed_counts_steps() -> None:
    types = {item['type'] for item in get_step_catalog()}
    assert 'value_counts' not in types
    assert 'null_count' not in types


def test_validate_step_rejects_removed_counts_steps() -> None:
    with pytest.raises(ValueError, match='Unknown step type'):
        validate_step('value_counts', {'column': 'x'})
    with pytest.raises(ValueError, match='Unknown step type'):
        validate_step('null_count', {})
