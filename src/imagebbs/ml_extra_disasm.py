"""Wrapper for the prototype module."""
from __future__ import annotations

from typing import Any

from ._compat import mirror_module

_TARGET = mirror_module(globals(), "scripts.prototypes.ml_extra_disasm")
__doc__ = _TARGET.__doc__


def __getattr__(name: str) -> Any:
    return getattr(_TARGET, name)
