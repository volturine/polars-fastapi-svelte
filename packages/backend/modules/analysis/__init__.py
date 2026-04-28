"""Analysis module."""

from typing import Any

_router: Any = None
__all__ = ['router']


def __getattr__(name: str) -> Any:
    if name == 'router':
        global _router
        if _router is None:
            from modules.analysis.routes import router as loaded_router

            _router = loaded_router
        return _router
    raise AttributeError(name)
