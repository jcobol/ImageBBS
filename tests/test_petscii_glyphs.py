"""Tests for the PETSCII glyph atlas helper."""
from __future__ import annotations

from scripts.prototypes import petscii_glyphs


def _rows_from_matrix(matrix: petscii_glyphs.GlyphMatrix) -> tuple[int, ...]:
    return tuple(
        int("".join(str(bit) for bit in row), 2)
        for row in matrix
    )


def test_uppercase_a_matches_default_pattern() -> None:
    glyph = petscii_glyphs.get_glyph(0x41)
    assert _rows_from_matrix(glyph) == (
        0x18,
        0x3C,
        0x66,
        0x66,
        0x7E,
        0x66,
        0x66,
        0x00,
    )


def test_lowercase_a_uses_lowercase_bank() -> None:
    glyph = petscii_glyphs.get_glyph(0x61, lowercase=True)
    assert _rows_from_matrix(glyph) == (
        0x00,
        0x00,
        0x3C,
        0x06,
        0x7E,
        0xC6,
        0x7E,
        0x00,
    )


def test_arrow_up_graphic_matches_expected_pattern() -> None:
    glyph = petscii_glyphs.get_glyph(0x5E)
    assert _rows_from_matrix(glyph) == (
        0x18,
        0x3C,
        0x7E,
        0x18,
        0x18,
        0x18,
        0x18,
        0x00,
    )


def test_custom_character_rom_overrides_default() -> None:
    payload = bytearray(4096)
    offset = petscii_glyphs.get_glyph_index(0x41) * 8
    for index, value in enumerate(range(8)):
        payload[offset + index] = value

    try:
        petscii_glyphs.load_character_rom(payload)
        glyph = petscii_glyphs.get_glyph(0x41)
        assert _rows_from_matrix(glyph) == tuple(range(8))
    finally:
        petscii_glyphs.reset_character_rom()

