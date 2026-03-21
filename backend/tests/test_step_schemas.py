from modules.analysis.step_schemas import SelectConfig


def test_select_config_includes_cast_map_schema() -> None:
    schema = SelectConfig.model_json_schema()
    props = schema.get('properties', {})
    cast_map = props.get('cast_map', {})
    additional = cast_map.get('additionalProperties', {})
    assert cast_map.get('type') == 'object'
    assert additional.get('enum') == ['Int64', 'Float64', 'Boolean', 'String', 'Utf8', 'Date', 'Datetime']
