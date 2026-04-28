"""Analysis versions module."""

from typing import Any

__all__ = ['router']


def __getattr__(name: str) -> Any:
    if name == 'router':
        from modules.analysis_versions.routes import router

        return router
    raise AttributeError(name)
