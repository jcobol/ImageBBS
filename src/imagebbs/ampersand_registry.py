"""Compat shim that re-exports the ampersand registry primitives."""
from __future__ import annotations

from .ampersand.registry import AmpersandHandler, AmpersandRegistry, AmpersandResult

__all__ = ["AmpersandHandler", "AmpersandRegistry", "AmpersandResult"]

