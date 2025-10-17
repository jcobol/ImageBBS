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


def _resolve_vic_registers(
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> dict[int, int | None]:
    registers: dict[int, int | None] = {}
    for entry in defaults.hardware.vic_registers:
        last_value: int | None = None
        for _, value in entry.writes:
            if value is not None:
                last_value = value
        registers[entry.address] = last_value
    return registers


def test_screen_seeds_overlay_palette(editor_defaults: ml_extra_defaults.MLExtraDefaults) -> None:
    screen = PetsciiScreen()
    assert screen.palette == editor_defaults.palette.colours
    assert screen.screen_colour == editor_defaults.palette.colours[0]
    assert screen.background_colour == editor_defaults.palette.colours[2]
    assert screen.border_colour == editor_defaults.palette.colours[3]


def test_screen_replays_hardware_colour_defaults(
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    screen = PetsciiScreen()
    registers = _resolve_vic_registers(editor_defaults)

    assert screen.vic_registers == registers

    screen_register = registers.get(0xD405)
    if screen_register is not None:
        assert screen.screen_colour == screen_register

    background_register = registers.get(0xD403)
    if background_register is not None:
        assert screen.background_colour == background_register

    border_register = registers.get(0xD404)
    if border_register is not None:
        assert screen.border_colour == border_register


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

    reverse_flags = snapshot["reverse_matrix"][11]
    assert reverse_flags == screen.reverse_matrix[11]
    assert all(flag is False for flag in reverse_flags)

    resolved_colours = snapshot["resolved_colour_matrix"][11]
    assert resolved_colours == screen.resolved_colour_matrix[11]
    for index in range(15, 24):
        foreground, background = resolved_colours[index]
        assert foreground == colours[index]
        assert background == console.background_colour

    assert console.screen_colour == 1  # PETSCII white
    assert snapshot["screen_colour"] == console.screen_colour
    assert console.background_colour == editor_defaults.palette.colours[2]
    assert snapshot["background_colour"] == console.background_colour
    assert console.border_colour == editor_defaults.palette.colours[3]
    assert snapshot["border_colour"] == console.border_colour
    hardware = snapshot["hardware"]
    registers = _resolve_vic_registers(editor_defaults)
    assert hardware["vic_registers"] == registers
    assert hardware["sid_volume"] == editor_defaults.hardware.sid_volume

    assert console.transcript_bytes == banner_sequence
    assert console.transcript == banner_sequence.decode("latin-1")


def test_console_exposes_overlay_defaults(
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    console = Console()

    assert console.defaults == editor_defaults
    assert console.lightbar_defaults == editor_defaults.lightbar
    assert console.flag_dispatch == editor_defaults.flag_dispatch
    assert console.macros == editor_defaults.macros


def test_console_exposes_hardware_defaults(
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    console = Console()
    registers = _resolve_vic_registers(editor_defaults)

    assert console.vic_registers == registers
    assert console.sid_volume == editor_defaults.hardware.sid_volume

    background = registers.get(0xD403)
    if background is not None:
        assert console.background_colour == background

    border = registers.get(0xD404)
    if border is not None:
        assert console.border_colour == border

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


def test_reverse_mode_swaps_render_colours(editor_defaults: ml_extra_defaults.MLExtraDefaults) -> None:
    console = Console()
    console.write(bytes([0x93]))  # clear
    console.write(bytes([0x05]))  # white foreground
    initial_background = console.background_colour

    console.write(bytes([0x12]))  # reverse on
    console.write(b"A")
    console.write(bytes([0x92]))  # reverse off
    console.write(b"B")

    snapshot = console.snapshot()
    characters = snapshot["characters"][0]
    assert characters[:2] == "AB"

    colour_row = snapshot["colour_matrix"][0]
    assert colour_row[0] == colour_row[1] == console.screen_colour

    reverse_row = snapshot["reverse_matrix"][0]
    assert reverse_row[0] is True
    assert reverse_row[1] is False

    resolved_row = snapshot["resolved_colour_matrix"][0]
    assert resolved_row[0] == (initial_background, colour_row[0])
    assert resolved_row[1] == (colour_row[1], initial_background)

    assert snapshot["background_colour"] == initial_background == editor_defaults.palette.colours[2]
    assert snapshot["screen_colour"] == console.screen_colour
