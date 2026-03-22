"""Helpers for MCP tool contract schema access and output formatting."""

from __future__ import annotations

from typing import Any


def tool_input_schema(tool: dict[str, Any]) -> dict[str, Any]:
    contract = tool.get('contract')
    if isinstance(contract, dict):
        schema = contract.get('input_schema')
        if isinstance(schema, dict):
            return schema
    schema = tool.get('input_schema')
    if isinstance(schema, dict):
        return schema
    return {'type': 'object'}


def tool_output_schema(tool: dict[str, Any]) -> dict[str, Any] | None:
    contract = tool.get('contract')
    if isinstance(contract, dict):
        schema = contract.get('output_schema')
        if isinstance(schema, dict):
            return schema
        if schema is None:
            return None
    schema = tool.get('output_schema')
    if isinstance(schema, dict):
        return schema
    return None


def top_level_output_fields(schema: Any) -> list[str]:
    if not isinstance(schema, dict):
        return []
    if schema.get('type') == 'object':
        props = schema.get('properties')
        if not isinstance(props, dict):
            return []
        return [key for key in props if isinstance(key, str)]
    if schema.get('type') == 'array':
        items = schema.get('items')
        if not isinstance(items, dict):
            return []
        props = items.get('properties')
        if not isinstance(props, dict):
            return []
        return [key for key in props if isinstance(key, str)]
    return []


def format_output_details(output: dict[str, Any] | None, field_limit: int = 8) -> str:
    if not isinstance(output, dict):
        return ''
    parts: list[str] = []
    status_code = output.get('status_code')
    if isinstance(status_code, str) and status_code:
        parts.append(f'status_code={status_code}')
    content_type = output.get('content_type')
    if isinstance(content_type, str) and content_type:
        parts.append(f'content_type={content_type}')
    response_model = output.get('response_model')
    if isinstance(response_model, str) and response_model:
        parts.append(f'response_model={response_model}')
    fields = top_level_output_fields(output.get('schema'))[:field_limit]
    if fields:
        parts.append(f'fields={", ".join(fields)}')
    if not parts:
        return ''
    return '  Expected output: ' + '; '.join(parts)


def output_hint(output: dict[str, Any] | None, field_limit: int = 5) -> str:
    if not isinstance(output, dict):
        return ''
    parts: list[str] = []
    status_code = output.get('status_code')
    if isinstance(status_code, str) and status_code:
        parts.append(f'status {status_code}')
    content_type = output.get('content_type')
    if isinstance(content_type, str) and content_type:
        parts.append(content_type)
    response_model = output.get('response_model')
    if isinstance(response_model, str) and response_model:
        parts.append(f'model {response_model}')
    fields = top_level_output_fields(output.get('schema'))[:field_limit]
    if fields:
        parts.append(f'fields: {", ".join(fields)}')
    if not parts:
        return ''
    return 'Expected output: ' + '; '.join(parts)
