"""Public ImageBBS API that mirrors the prototype re-exports."""
from __future__ import annotations

from importlib import import_module
from typing import Any

_prototypes = import_module("scripts.prototypes")
__all__ = list(getattr(_prototypes, "__all__", ()))
for _name in __all__:
    globals()[_name] = getattr(_prototypes, _name)

def __getattr__(name: str) -> Any:
    return getattr(_prototypes, name)


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(dir(_prototypes)))
