from collections.abc import Sequence

import requests  # type: ignore[import-untyped]

from core.config import settings


class AIClient:
    def generate(self, prompt: str, *, model: str, options: dict | None = None) -> str:
        raise NotImplementedError

    def generate_batch(self, prompts: Sequence[str], *, model: str, options: dict | None = None) -> list[str]:
        return [self.generate(prompt, model=model, options=options) for prompt in prompts]


class OllamaClient(AIClient):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip('/')

    def generate(self, prompt: str, *, model: str, options: dict | None = None) -> str:
        payload: dict[str, object] = {'model': model, 'prompt': prompt}
        if options:
            payload['options'] = options
        response = requests.post(f'{self.base_url}/api/generate', json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return str(data.get('response', ''))


class OpenAIClient(AIClient):
    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = (base_url or 'https://api.openai.com').rstrip('/')

    def generate(self, prompt: str, *, model: str, options: dict | None = None) -> str:
        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
        }
        if options:
            payload.update(options)
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        response = requests.post(
            f'{self.base_url}/v1/chat/completions',
            json=payload,
            headers=headers,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get('choices', [])
        if not choices:
            return ''
        message = choices[0].get('message', {})
        return str(message.get('content', ''))


def get_ai_client(
    provider: str,
    *,
    endpoint_url: str | None = None,
    api_key: str | None = None,
) -> AIClient:
    if provider == 'ollama':
        return OllamaClient(endpoint_url or settings.ollama_base_url)
    if provider == 'openai':
        key = api_key or settings.openai_api_key
        if not key:
            raise ValueError('OPENAI_API_KEY not configured')
        return OpenAIClient(key, base_url=endpoint_url)
    raise ValueError(f'Unknown AI provider: {provider}')
