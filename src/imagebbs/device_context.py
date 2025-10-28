"""Compatibility shim exposing the device context stack."""
from __future__ import annotations

from .device import context as _context

__all__ = list(_context.__all__)
for _name in __all__:
    globals()[_name] = getattr(_context, _name)


def __getattr__(name: str):
    return getattr(_context, name)


def __dir__() -> list[str]:
    return sorted(__all__)
