"""Ampersand runtime utilities exposed via the ImageBBS package."""
from __future__ import annotations

from typing import Any

from . import dispatcher as _dispatcher
from . import registry as _registry

__all__ = sorted(set(_dispatcher.__all__) | set(_registry.__all__))
for _name in __all__:
    if hasattr(_dispatcher, _name):
        globals()[_name] = getattr(_dispatcher, _name)
    else:
        globals()[_name] = getattr(_registry, _name)


def __getattr__(name: str) -> Any:
    if hasattr(_dispatcher, name):
        return getattr(_dispatcher, name)
    return getattr(_registry, name)


def __dir__() -> list[str]:
    return sorted(__all__)
