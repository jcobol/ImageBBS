import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import petscii_glyphs


def _matrix(*rows: str) -> petscii_glyphs.GlyphMatrix:
    if any(len(row) != 8 for row in rows):
        raise ValueError("each glyph row must contain exactly eight cells")
    return tuple(tuple(1 if char == "#" else 0 for char in row) for row in rows)


def setup_function(function: object) -> None:
    petscii_glyphs.reset_character_rom()


def test_lowercase_a_matches_character_rom() -> None:
    glyph = petscii_glyphs.get_glyph(0x41, lowercase=True)
    expected = _matrix(
        "...##...",
        "..####..",
        ".##..##.",
        ".######.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        "........",
    )
    assert glyph == expected


def test_uppercase_graphic_s_matches_character_rom() -> None:
    glyph = petscii_glyphs.get_glyph(0x53)
    expected = _matrix(
        "..##.##.",
        ".#######",
        ".#######",
        ".#######",
        "..#####.",
        "...###..",
        "....#...",
        "........",
    )
    assert glyph == expected


def test_petscii_block_glyph_matches_character_rom() -> None:
    glyph = petscii_glyphs.get_glyph(0x6F)
    expected = _matrix(
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
        "########",
        "########",
    )
    assert glyph == expected


def test_invalid_length_rom_rejected() -> None:
    with pytest.raises(ValueError):
        petscii_glyphs.load_character_rom(b"\x00" * 1024)


def test_loading_alternate_rom_clears_cache() -> None:
    custom = bytes([0x00, 0xFF]) * 1024  # 2 KiB alternating rows
    petscii_glyphs.load_character_rom(custom)
    glyph = petscii_glyphs.get_glyph(0x00)
    assert glyph == _matrix(
        "........",
        "########",
        "........",
        "########",
        "........",
        "########",
        "........",
        "########",
    )
    petscii_glyphs.reset_character_rom()
    restored = petscii_glyphs.get_glyph(0x6F)
    assert restored == _matrix(
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
        "########",
        "########",
    )
