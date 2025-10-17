"""Console rendering tests for the PETSCII host shim."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import ml_extra_defaults, petscii_glyphs
from scripts.prototypes.console_renderer import PetsciiScreen
from scripts.prototypes.device_context import Console


@pytest.fixture(scope="module")
def editor_defaults() -> ml_extra_defaults.MLExtraDefaults:
    return ml_extra_defaults.MLExtraDefaults.from_overlay()


def test_screen_seeds_overlay_palette(editor_defaults: ml_extra_defaults.MLExtraDefaults) -> None:
    screen = PetsciiScreen()
    assert screen.palette == editor_defaults.palette.colours
    assert screen.screen_colour == editor_defaults.palette.colours[0]
    assert screen.background_colour == editor_defaults.palette.colours[2]
    assert screen.border_colour == editor_defaults.palette.colours[3]


def test_console_renders_startup_banner(editor_defaults: ml_extra_defaults.MLExtraDefaults) -> None:
    console = Console()
    banner_sequence = bytes([0x93])  # {clear}
    banner_sequence += bytes([0x11] * 11)  # move cursor down
    banner_sequence += bytes([0x1D] * 15)  # move cursor right
    banner_sequence += bytes([0x05, 0x0E])  # set white, lowercase
    banner_sequence += bytes([0xC9, 0x6D, 0x61, 0x67, 0x65, 0x20, 0x31, 0x2E, 0x32])

    console.write(banner_sequence)

    screen = console.screen
    snapshot = console.snapshot()
    rows = snapshot["characters"]
    assert rows == screen.characters
    assert len(rows) == screen.height

    expected_row = rows[11]
    assert expected_row[15:24] == "Image 1.2"
    assert expected_row[:15] == " " * 15

    colours = snapshot["colour_matrix"][11]
    assert colours == screen.colour_matrix[11]
    for index in range(15, 24):
        assert colours[index] == console.screen_colour

    codes = snapshot["code_matrix"][11]
    assert codes == screen.code_matrix[11]
    expected_codes = (0xC9, 0x6D, 0x61, 0x67, 0x65, 0x20, 0x31, 0x2E, 0x32)
    assert tuple(codes[15:24]) == expected_codes

    glyph_indices = snapshot["glyph_indices"][11]
    assert glyph_indices == screen.glyph_index_matrix[11]
    expected_indices = tuple(
        petscii_glyphs.get_glyph_index(code, lowercase=True)
        for code in expected_codes
    )
    assert tuple(glyph_indices[15:24]) == expected_indices

    glyphs = snapshot["glyphs"][11]
    assert glyphs == screen.glyph_matrix[11]
    expected_glyphs = tuple(
        petscii_glyphs.get_glyph(code, lowercase=True)
        for code in expected_codes
    )
    assert tuple(glyphs[15:24]) == expected_glyphs

    assert console.screen_colour == 1  # PETSCII white
    assert snapshot["screen_colour"] == console.screen_colour
    assert console.background_colour == editor_defaults.palette.colours[2]
    assert snapshot["background_colour"] == console.background_colour
    assert console.border_colour == editor_defaults.palette.colours[3]
    assert snapshot["border_colour"] == console.border_colour
    assert console.transcript_bytes == banner_sequence
    assert console.transcript == banner_sequence.decode("latin-1")


def test_screen_tracks_glyph_banks() -> None:
    screen = PetsciiScreen()
    screen.write(bytes([0x41, 0x0E, 0x61]))

    assert screen.characters[0][:2] == "Aa"

    codes = screen.code_matrix[0]
    assert codes[0] == 0x41
    assert codes[1] == 0x61

    glyph_indices = screen.glyph_index_matrix[0]
    assert glyph_indices[0] == petscii_glyphs.get_glyph_index(0x41)
    assert glyph_indices[1] == petscii_glyphs.get_glyph_index(0x61, lowercase=True)

    glyphs = screen.glyph_matrix[0]
    assert glyphs[0] == petscii_glyphs.get_glyph(0x41)
    assert glyphs[1] == petscii_glyphs.get_glyph(0x61, lowercase=True)
