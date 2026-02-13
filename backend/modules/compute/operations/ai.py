from typing import Literal

import polars as pl
from pydantic import ConfigDict

from modules.ai import get_ai_client
from modules.compute.core.base import OperationHandler, OperationParams


class AIParams(OperationParams):
    model_config = ConfigDict(extra='forbid')

    provider: Literal['ollama', 'openai'] = 'ollama'
    model: str = 'llama2'
    input_column: str
    output_column: str
    prompt_template: str = 'Classify this text: {{text}}'
    batch_size: int = 10
    endpoint_url: str | None = None
    api_key: str | None = None
    request_options: dict | None = None


class AIHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'ai'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = AIParams.model_validate(params)
        if validated.batch_size < 1:
            raise ValueError('batch_size must be at least 1')
        df = lf.collect()
        if validated.input_column not in df.columns:
            raise ValueError(f'Input column not found: {validated.input_column}')

        texts = df[validated.input_column].to_list()
        client = get_ai_client(
            validated.provider,
            endpoint_url=validated.endpoint_url,
            api_key=validated.api_key,
        )
        results: list[str] = []
        for offset in range(0, len(texts), validated.batch_size):
            batch = texts[offset : offset + validated.batch_size]
            prompts = [validated.prompt_template.replace('{{text}}', str(text)) for text in batch]
            outputs = client.generate_batch(
                prompts,
                model=validated.model,
                options=validated.request_options,
            )
            results.extend(outputs)

        if len(results) != len(texts):
            raise ValueError('AI output length mismatch')
        return df.with_columns(pl.Series(name=validated.output_column, values=results)).lazy()
