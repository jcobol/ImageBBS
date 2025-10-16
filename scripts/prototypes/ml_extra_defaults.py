"""Structured view of the recovered ``ml.extra`` overlay for host tooling.

This module wraps :mod:`scripts.prototypes.ml_extra_extract` so callers can
consume the pointer-directory records (macro slots, relocation addresses, and
raw PETSCII payloads) without reimplementing the extraction logic.  The helper
mirrors :mod:`scripts.prototypes.setup_defaults`: it resolves the archived
binary from ``v1.2/from-floppy/ml.extra`` by default and exposes dataclasses for
each recovered table, including the lightbar defaults and editor palette stored
near the overlay's tail section.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

from . import ml_extra_extract

_LIGHTBAR_TABLE_ADDR = 0xD3F6
_LIGHTBAR_TABLE_LENGTH = 6  # four flag bytes + underline char/colour
_PALETTE_ADDR = 0xC66A
_PALETTE_LENGTH = 4


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
class LightbarDefaults:
    """Initial flag bitmaps and underline settings exported by the overlay."""

    page1_left: int
    page1_right: int
    page2_left: int
    page2_right: int
    underline_char: int
    underline_color: int

    @property
    def bitmaps(self) -> Tuple[int, int, int, int]:
        """Return the lightbar bitmaps as a tuple in overlay order."""

        return (self.page1_left, self.page1_right, self.page2_left, self.page2_right)

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the defaults."""

        return {
            "page1_left": f"${self.page1_left:02x}",
            "page1_right": f"${self.page1_right:02x}",
            "page2_left": f"${self.page2_left:02x}",
            "page2_right": f"${self.page2_right:02x}",
            "underline_char": f"${self.underline_char:02x}",
            "underline_color": f"${self.underline_color:02x}",
        }


@dataclass(frozen=True)
class EditorPalette:
    """VIC-II colour IDs used by the recovered ml.extra overlay."""

    colours: Tuple[int, int, int, int]

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the palette."""

        return {
            "colours": [f"${value:02x}" for value in self.colours],
        }


@dataclass(frozen=True)
class MLExtraDefaults:
    """Aggregates recovered tables from the ``ml.extra`` overlay."""

    load_address: int
    lightbar: LightbarDefaults
    palette: EditorPalette
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

        lightbar_raw = _slice_memory(
            memory,
            load_address,
            _LIGHTBAR_TABLE_ADDR,
            _LIGHTBAR_TABLE_LENGTH,
        )
        lightbar = LightbarDefaults(
            page1_left=lightbar_raw[0],
            page1_right=lightbar_raw[1],
            page2_left=lightbar_raw[2],
            page2_right=lightbar_raw[3],
            underline_char=lightbar_raw[4],
            underline_color=lightbar_raw[5],
        )

        palette = EditorPalette(
            colours=tuple(
                _slice_memory(memory, load_address, _PALETTE_ADDR, _PALETTE_LENGTH)
            ),
        )

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
        return cls(load_address=load_address, lightbar=lightbar, palette=palette, macros=macros)


def _slice_memory(
    memory: Sequence[int], load_address: int, runtime_addr: int, length: int
) -> Tuple[int, ...]:
    """Return ``length`` bytes from ``memory`` starting at ``runtime_addr``."""

    index = ml_extra_extract.runtime_to_index(runtime_addr, load_addr=load_address)
    data = memory[index : index + length]
    if len(data) != length:
        raise ValueError(
            f"requested {length} bytes at ${runtime_addr:04x}, got {len(data)}"
        )
    return tuple(data)


_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_OVERLAY_PATH = _REPO_ROOT / "v1.2/from-floppy/ml.extra"


def default_overlay_path() -> Path:
    """Return the archived overlay path used by :class:`MLExtraDefaults`."""

    return _DEFAULT_OVERLAY_PATH


__all__ = [
    "EditorPalette",
    "LightbarDefaults",
    "MacroDirectoryEntry",
    "MLExtraDefaults",
    "default_overlay_path",
]
