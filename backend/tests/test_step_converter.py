from modules.compute.step_converter import convert_groupby_config, convert_rename_config


def test_convert_groupby_config_prefers_group_by() -> None:
    result = convert_groupby_config(
        {
            'group_by': ['team'],
            'groupBy': ['legacy_team'],
            'aggregations': [{'column': 'score', 'function': 'sum', 'alias': 'total'}],
        }
    )
    assert result['group_by'] == ['team']
    assert result['aggregations'] == [{'column': 'score', 'function': 'sum', 'alias': 'total'}]


def test_convert_groupby_config_falls_back_to_legacy_groupby() -> None:
    result = convert_groupby_config(
        {
            'groupBy': ['team'],
            'aggregations': [{'column': 'score', 'function': 'sum'}],
        }
    )
    assert result['group_by'] == ['team']
    assert result['aggregations'] == [{'column': 'score', 'function': 'sum', 'alias': None}]


def test_convert_rename_config_accepts_column_mapping_and_mapping() -> None:
    by_column_mapping = convert_rename_config({'column_mapping': {'old': 'new'}})
    by_mapping = convert_rename_config({'mapping': {'old': 'new'}})

    assert by_column_mapping == {'mapping': {'old': 'new'}}
    assert by_mapping == {'mapping': {'old': 'new'}}
