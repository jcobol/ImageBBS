"""Structured view of the recovered ``ml.extra`` overlay for host tooling.

This module wraps :mod:`scripts.prototypes.ml_extra_extract` so callers can
consume the pointer-directory records (macro slots, relocation addresses, and
raw PETSCII payloads) without reimplementing the extraction logic.  The helper
mirrors :mod:`scripts.prototypes.setup_defaults`: it resolves the archived
binary from ``v1.2/from-floppy/ml.extra`` by default, exposes dataclasses for
each recovered table, and leaves room for future lightbar/palette metadata once
those segments are decoded.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from . import ml_extra_extract


@dataclass(frozen=True)
class MacroDirectoryEntry:
    """Single pointer-directory record recovered from ``ml.extra``."""

    slot: int
    address: int
    payload: Tuple[int, ...]
    decoded_text: str

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the entry."""

        return {
            "slot": self.slot,
            "address": f"${self.address:04x}",
            "bytes": [f"${value:02x}" for value in self.payload],
            "text": self.decoded_text,
        }


@dataclass(frozen=True)
class MLExtraDefaults:
    """Aggregates recovered tables from the ``ml.extra`` overlay."""

    load_address: int
    macros: Tuple[MacroDirectoryEntry, ...]

    @property
    def macro_slots(self) -> Tuple[int, ...]:
        """Return the slot identifiers in pointer-directory order."""

        return tuple(entry.slot for entry in self.macros)

    @property
    def macros_by_slot(self) -> Dict[int, MacroDirectoryEntry]:
        """Expose a mapping from slot identifier to macro payload."""

        return {entry.slot: entry for entry in self.macros}

    @classmethod
    def from_overlay(cls, overlay_path: Optional[Path] = None) -> "MLExtraDefaults":
        """Load the archived ``ml.extra`` overlay and decode its tables."""

        path = overlay_path or default_overlay_path()
        load_address, memory = ml_extra_extract.load_prg(path)
        macros = tuple(
            MacroDirectoryEntry(
                slot=entry.slot,
                address=entry.address,
                payload=tuple(entry.data),
                decoded_text=entry.text,
            )
            for entry in ml_extra_extract.iter_pointer_directory(
                memory, load_addr=load_address
            )
        )
        return cls(load_address=load_address, macros=macros)


_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_OVERLAY_PATH = _REPO_ROOT / "v1.2/from-floppy/ml.extra"


def default_overlay_path() -> Path:
    """Return the archived overlay path used by :class:`MLExtraDefaults`."""

    return _DEFAULT_OVERLAY_PATH


__all__ = [
    "MacroDirectoryEntry",
    "MLExtraDefaults",
    "default_overlay_path",
]
