"""Device abstractions surfaced by the ImageBBS package."""
from __future__ import annotations

from typing import Any

from . import context as _context

__all__ = list(_context.__all__)
for _name in __all__:
    globals()[_name] = getattr(_context, _name)


def __getattr__(name: str) -> Any:
    return getattr(_context, name)


def __dir__() -> list[str]:
    return sorted(__all__)
