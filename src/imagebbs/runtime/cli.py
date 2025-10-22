"""Wrapper for the prototype runtime module."""
from __future__ import annotations

from .._compat import mirror_module

_TARGET = mirror_module(globals(), "scripts.prototypes.runtime.cli")
