from collections.abc import Callable

import polars as pl


def _csv_opts(options: dict | None) -> dict:
    if not options:
        return {}
    return {
        'separator': options.get('delimiter', ','),
        'quote_char': options.get('quote_char', '"'),
        'has_header': options.get('has_header', True),
        'skip_rows': options.get('skip_rows', 0),
        'encoding': options.get('encoding', 'utf8'),
    }


FILE_LOADERS: dict[str, Callable[[str, dict | None], pl.LazyFrame]] = {
    'csv': lambda path, options: pl.scan_csv(path, **_csv_opts(options)),
    'parquet': lambda path, _options: pl.scan_parquet(path),
    'json': lambda path, _options: pl.read_json(path).lazy(),
    'ndjson': lambda path, _options: pl.scan_ndjson(path),
    'excel': lambda path, _options: pl.read_excel(path).lazy(),
}


def _load_file(config: dict) -> pl.LazyFrame:
    file_path = config['file_path']
    file_type = config['file_type']
    csv_options = config.get('csv_options')
    options = csv_options or config.get('options')
    loader = FILE_LOADERS.get(file_type)
    if not loader:
        raise ValueError(f'Unsupported file type: {file_type}')
    return loader(file_path, options)


def _load_database(config: dict) -> pl.LazyFrame:
    connection_string = config['connection_string']
    query = config['query']
    return pl.read_database(query, connection_string).lazy()


def _load_duckdb(config: dict) -> pl.LazyFrame:
    import duckdb

    db_path = config.get('db_path')
    query = config['query']
    read_only = config.get('read_only', True)
    conn = duckdb.connect(database=db_path, read_only=read_only) if db_path else duckdb.connect(database=':memory:')
    return conn.execute(query).fetch_df().lazy()


DATASOURCE_LOADERS: dict[str, Callable[[dict], pl.LazyFrame]] = {
    'file': _load_file,
    'database': _load_database,
    'duckdb': _load_duckdb,
}


def load_datasource(config: dict) -> pl.LazyFrame:
    source_type = config.get('source_type', 'file')
    loader = DATASOURCE_LOADERS.get(source_type)
    if not loader:
        raise ValueError(f'Unsupported source type: {source_type}')
    return loader(config)
