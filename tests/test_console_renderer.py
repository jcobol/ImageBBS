"""Console rendering tests for the PETSCII host shim."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import ml_extra_defaults
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
    rows = screen.characters
    assert len(rows) == screen.height

    expected_row = rows[11]
    assert expected_row[15:24] == "Image 1.2"
    assert expected_row[:15] == " " * 15

    colours = screen.colour_matrix[11]
    for index in range(15, 24):
        assert colours[index] == console.screen_colour

    assert console.screen_colour == 1  # PETSCII white
    assert console.background_colour == editor_defaults.palette.colours[2]
    assert console.border_colour == editor_defaults.palette.colours[3]
    assert console.transcript_bytes == banner_sequence
    assert console.transcript == banner_sequence.decode("latin-1")
