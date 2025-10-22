"""Wrapper for the prototype module."""
from __future__ import annotations

from ._compat import mirror_module

_TARGET = mirror_module(globals(), "scripts.prototypes.ml_extra_refresh_pipeline")

if __name__ == "__main__":  # pragma: no cover - exercised via python -m
    raise SystemExit(_TARGET.main())
