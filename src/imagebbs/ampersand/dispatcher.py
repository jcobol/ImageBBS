"""Wrapper for the prototype ampersand dispatcher."""
from __future__ import annotations

from .._compat import mirror_module

_TARGET = mirror_module(globals(), "scripts.prototypes.ampersand_dispatcher")
