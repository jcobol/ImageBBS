"""PETSCII glyph helper that mirrors the Commodore 64 character ROM layout."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, MutableMapping, Sequence

GlyphMatrix = tuple[tuple[int, ...], ...]


def _pattern(*rows: str) -> tuple[int, ...]:
    """Return the byte pattern for an 8×8 glyph described by ``rows``."""

    if len(rows) != 8:
        raise ValueError("glyph definitions must supply eight rows")
    encoded: list[int] = []
    for row in rows:
        if len(row) != 8:
            raise ValueError("each glyph row must contain exactly eight cells")
        bits = 0
        for index, char in enumerate(row):
            if char in {"█", "#"}:
                bits |= 1 << (7 - index)
        encoded.append(bits)
    return tuple(encoded)


def _install_default_patterns() -> MutableMapping[tuple[int, int], tuple[int, ...]]:
    patterns: MutableMapping[tuple[int, int], tuple[int, ...]] = {}

    def register(code: int, rows: Sequence[str], *, banks: Iterable[int]) -> None:
        glyph = _pattern(*rows)
        for bank in banks:
            patterns[(bank & 0x01, code & 0xFF)] = glyph

    def register_with_high_bit(code: int, rows: Sequence[str]) -> None:
        register(code, rows, banks=(0, 1))
        register(code | 0x80, rows, banks=(1,))

    blank = (
        "        ",
        "        ",
        "        ",
        "        ",
        "        ",
        "        ",
        "        ",
        "        ",
    )
    register(0x20, blank, banks=(0, 1))

    register_with_high_bit(0x2E, (
        "        ",
        "        ",
        "        ",
        "        ",
        "        ",
        "   ██   ",
        "   ██   ",
        "        ",
    ))
    register_with_high_bit(0x30, (
        "  ████  ",
        " ██  ██ ",
        "██ ██ ██",
        "██ ██ ██",
        "██ ██ ██",
        " ██  ██ ",
        "  ████  ",
        "        ",
    ))
    register_with_high_bit(0x31, (
        "   ██   ",
        "  ███   ",
        "   ██   ",
        "   ██   ",
        "   ██   ",
        "   ██   ",
        " ██████ ",
        "        ",
    ))
    register_with_high_bit(0x32, (
        " ██████ ",
        "██    ██",
        "     ██ ",
        "   ███  ",
        "  ██    ",
        " ██     ",
        "████████",
        "        ",
    ))

    register_with_high_bit(0x41, (
        "   ██   ",
        "  ████  ",
        " ██  ██ ",
        " ██  ██ ",
        " ██████ ",
        " ██  ██ ",
        " ██  ██ ",
        "        ",
    ))
    register(0xC1, (
        "   ██   ",
        "  ████  ",
        " ██  ██ ",
        " ██  ██ ",
        " ██████ ",
        " ██  ██ ",
        " ██  ██ ",
        "        ",
    ), banks=(1,))
    register_with_high_bit(0x45, (
        "████████",
        "██      ",
        "██      ",
        "███████ ",
        "██      ",
        "██      ",
        "████████",
        "        ",
    ))
    register_with_high_bit(0x47, (
        "  ████  ",
        " ██  ██ ",
        "██      ",
        "██ ████ ",
        "██    ██",
        " ██  ██ ",
        "  ████ █",
        "        ",
    ))
    register_with_high_bit(0x49, (
        " ██████ ",
        "   ██   ",
        "   ██   ",
        "   ██   ",
        "   ██   ",
        "   ██   ",
        " ██████ ",
        "        ",
    ))
    register(0xC9, (
        " ██████ ",
        "   ██   ",
        "   ██   ",
        "   ██   ",
        "   ██   ",
        "   ██   ",
        " ██████ ",
        "        ",
    ), banks=(1,))

    register(0x5E, (
        "   ██   ",
        "  ████  ",
        " ██████ ",
        "   ██   ",
        "   ██   ",
        "   ██   ",
        "   ██   ",
        "        ",
    ), banks=(0, 1))

    register(0x61, (
        "        ",
        "        ",
        "  ████  ",
        "     ██ ",
        " ██████ ",
        "██   ██ ",
        " ██████ ",
        "        ",
    ), banks=(1,))
    register(0xE1, (
        "        ",
        "        ",
        "  ████  ",
        "     ██ ",
        " ██████ ",
        "██   ██ ",
        " ██████ ",
        "        ",
    ), banks=(1,))
    register(0x65, (
        "        ",
        "        ",
        "  ████  ",
        " ██  ██ ",
        "███████ ",
        "██      ",
        " ██████ ",
        "        ",
    ), banks=(1,))
    register(0xE5, (
        "        ",
        "        ",
        "  ████  ",
        " ██  ██ ",
        "███████ ",
        "██      ",
        " ██████ ",
        "        ",
    ), banks=(1,))
    register(0x67, (
        "        ",
        "        ",
        "  ████ █",
        " ██   ██",
        " ██   ██",
        "  ██████",
        "      ██",
        " ██████ ",
    ), banks=(1,))
    register(0xE7, (
        "        ",
        "        ",
        "  ████ █",
        " ██   ██",
        " ██   ██",
        "  ██████",
        "      ██",
        " ██████ ",
    ), banks=(1,))
    register(0x6D, (
        "        ",
        "        ",
        "██ ████ ",
        "██ ██ ██",
        "██ ██ ██",
        "██ ██ ██",
        "██ ██ ██",
        "        ",
    ), banks=(1,))
    register(0xED, (
        "        ",
        "        ",
        "██ ████ ",
        "██ ██ ██",
        "██ ██ ██",
        "██ ██ ██",
        "██ ██ ██",
        "        ",
    ), banks=(1,))

    return patterns


_DEFAULT_GLYPHS = _install_default_patterns()
_CHAR_ROM: bytes = b""


def _build_default_rom() -> bytes:
    data = bytearray(4096)
    for (bank, code), rows in _DEFAULT_GLYPHS.items():
        offset = (bank * 256 + code) * 8
        data[offset : offset + 8] = rows
    return bytes(data)


def _ensure_rom() -> None:
    global _CHAR_ROM
    if not _CHAR_ROM:
        _CHAR_ROM = _build_default_rom()


def load_character_rom(payload: bytes | bytearray | memoryview | Iterable[int] | str | Path) -> None:
    """Load a complete 4 KiB character ROM into the helper."""

    global _CHAR_ROM

    if isinstance(payload, (str, Path)):
        data = Path(payload).read_bytes()
    else:
        data = bytes(payload)

    if len(data) == 2048:
        data = data + data
    if len(data) != 4096:
        raise ValueError("character ROM must be 2 KiB or 4 KiB long")

    _CHAR_ROM = data


def reset_character_rom() -> None:
    """Restore the bundled character ROM patterns."""

    global _CHAR_ROM
    _CHAR_ROM = b""
    _ensure_rom()


def get_glyph_index(code: int, *, lowercase: bool = False) -> int:
    """Return the glyph index within the combined ROM for ``code``."""

    if not 0 <= code <= 0xFF:
        raise ValueError("PETSCII code must be in range(256)")
    bank = 1 if lowercase else 0
    return bank * 256 + code


def get_glyph(code: int, *, lowercase: bool = False) -> GlyphMatrix:
    """Return the 8×8 bitmap for ``code``."""

    if not 0 <= code <= 0xFF:
        raise ValueError("PETSCII code must be in range(256)")
    _ensure_rom()
    bank = 1 if lowercase else 0
    offset = (bank * 256 + code) * 8
    rows = _CHAR_ROM[offset : offset + 8]
    matrix: list[tuple[int, ...]] = []
    for row in rows:
        matrix.append(tuple(1 if row & (1 << (7 - bit)) else 0 for bit in range(8)))
    return tuple(matrix)


__all__ = [
    "GlyphMatrix",
    "get_glyph",
    "get_glyph_index",
    "load_character_rom",
    "reset_character_rom",
]
