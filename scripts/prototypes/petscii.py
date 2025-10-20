"""PETSCII translation helpers shared across runtime components."""
from __future__ import annotations

from typing import Final, Iterable


def _build_base_glyphs() -> tuple[str, ...]:
    table = [" "] * 0x80
    table[0x00] = "@"
    for offset in range(26):
        table[0x01 + offset] = chr(ord("A") + offset)
    table[0x1B] = "["
    table[0x1C] = "£"
    table[0x1D] = "]"
    table[0x1E] = "↑"
    table[0x1F] = "←"
    for code in range(0x20, 0x40):
        table[code] = chr(code)
    for code in range(0x40, 0x5B):
        table[code] = chr(code)
    table[0x5B] = "["
    table[0x5C] = "\\"
    table[0x5D] = "]"
    table[0x5E] = "^"
    table[0x5F] = "_"
    for code in range(0x60, 0x7B):
        table[code] = chr(code)
    table[0x7B] = "{"
    table[0x7C] = "|"
    table[0x7D] = "}"
    table[0x7E] = "~"
    table[0x7F] = "⌂"
    return tuple(table)


def _decode_glyph(raw: int) -> str:
    base = raw & 0x7F
    glyph = _PETSCII_BASE_GLYPHS[base]
    if 0xE0 <= raw <= 0xFA and "a" <= glyph <= "z":
        return glyph.upper()
    return glyph


def _resolve_reverse(code: int) -> bool:
    raw = int(code) & 0xFF
    if raw == 0xA0:
        return False
    return bool(raw & 0x80)


_PETSCII_BASE_GLYPHS: Final[tuple[str, ...]] = _build_base_glyphs()

_PETSCII_TRANSLATION_TABLE: Final[tuple[tuple[str, bool], ...]] = tuple(
    (_decode_glyph(index), _resolve_reverse(index)) for index in range(256)
)


def translate_petscii(code: int) -> tuple[str, bool]:
    """Return the glyph and reverse flag for a PETSCII ``code``."""

    return _PETSCII_TRANSLATION_TABLE[int(code) & 0xFF]


_PRINTABLE_ASCII: Final[set[int]] = set(range(0x20, 0x7F))
_PRINTABLE_EXTRA: Final[dict[int, str]] = {0x0D: "\n", 0x8D: "\n"}


def petscii_to_cli_glyph(byte: int) -> str:
    """Map ``byte`` to a printable glyph suitable for CLI output."""

    raw = int(byte) & 0xFF
    if raw in _PRINTABLE_EXTRA:
        return _PRINTABLE_EXTRA[raw]
    if raw in _PRINTABLE_ASCII:
        return chr(raw)
    candidate = raw & 0x7F
    if candidate in _PRINTABLE_ASCII:
        return chr(candidate)
    if candidate in _PRINTABLE_EXTRA:
        return _PRINTABLE_EXTRA[candidate]
    return f"{{CBM-${raw:02X}}}"


def decode_petscii_for_cli(payload: Iterable[int]) -> str:
    """Translate ``payload`` into the CLI's printable text representation."""

    return "".join(petscii_to_cli_glyph(byte) for byte in payload)


__all__ = [
    "translate_petscii",
    "petscii_to_cli_glyph",
    "decode_petscii_for_cli",
]
