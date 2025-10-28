"""Compat shim that re-exports the ampersand dispatcher primitives."""
from __future__ import annotations

from .ampersand.dispatcher import (
    AmpersandDispatchContext,
    AmpersandDispatcher,
    AmpersandInvocation,
)

__all__ = ["AmpersandDispatchContext", "AmpersandDispatcher", "AmpersandInvocation"]

