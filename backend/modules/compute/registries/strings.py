from collections.abc import Callable

import polars as pl

STRING_METHODS: dict[str, Callable[[pl.Expr], pl.Expr]] = {
    'uppercase': lambda col: col.str.to_uppercase(),
    'lowercase': lambda col: col.str.to_lowercase(),
    'title': lambda col: col.str.to_titlecase(),
    'strip': lambda col: col.str.strip_chars(),
    'lstrip': lambda col: col.str.strip_chars_start(),
    'rstrip': lambda col: col.str.strip_chars_end(),
    'length': lambda col: col.str.len_chars(),
}


def get_string_method(name: str) -> Callable[[pl.Expr], pl.Expr] | None:
    return STRING_METHODS.get(name)
