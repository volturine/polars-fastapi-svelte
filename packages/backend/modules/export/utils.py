from __future__ import annotations

import re


def export_slug(value: str, *, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or fallback


def build_export_filename(analysis_name: str, tab_name: str | None, format_name: str) -> str:
    extension = "py" if format_name == "polars" else "sql"
    analysis_slug = export_slug(analysis_name, fallback="analysis")
    if tab_name:
        return f"{analysis_slug}_{export_slug(tab_name, fallback='item')}.{extension}"
    return f"{analysis_slug}_pipeline.{extension}"
