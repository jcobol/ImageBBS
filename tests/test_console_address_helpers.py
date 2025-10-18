"""Tests for direct screen/colour address helpers on the console."""

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.device_context import Console, ConsoleService


def _resolve_palette_colour(value: int, palette: tuple[int, ...], *, default_index: int = 0) -> int:
    resolved = int(value) & 0xFF
    if resolved in palette:
        return resolved
    if 0 <= resolved < len(palette):
        return palette[resolved]
    if not 0 <= default_index < len(palette):
        raise ValueError("default_index must reference a palette entry")
    return palette[default_index]


def test_poke_screen_byte_updates_screen_without_transcript() -> None:
    console = Console()

    console.poke_screen_byte(0x0400, 0x41)

    assert console.screen.peek_screen_address(0x0400) == 0x41
    assert console.transcript_bytes == b""


def test_poke_colour_byte_updates_colour_ram() -> None:
    console = Console()

    console.poke_colour_byte(0xD800, 0x02)

    palette = console.screen.palette
    expected = _resolve_palette_colour(0x02, palette)
    assert console.screen.peek_colour_address(0xD800) == expected


def test_poke_block_streams_screen_and_colour_bytes() -> None:
    console = Console()

    console.poke_block(
        screen_address=0x041E,
        screen_bytes=bytes([0x20, 0x21, 0x22]),
        colour_address=0xD81E,
        colour_bytes=[0x07, 0x08, 0x09],
    )

    for offset, expected in enumerate((0x20, 0x21, 0x22)):
        assert console.screen.peek_screen_address(0x041E + offset) == expected

    palette = console.screen.palette
    for offset, expected in enumerate((0x07, 0x08, 0x09)):
        resolved = _resolve_palette_colour(expected, palette)
        assert console.screen.peek_colour_address(0xD81E + offset) == resolved


def test_pause_indicator_helper_sets_target_cell() -> None:
    console = Console()
    service = ConsoleService(console)

    service.set_pause_indicator(0xD0)

    assert console.screen.peek_screen_address(0x041E) == 0xD0
    assert console.transcript_bytes == b""


def test_abort_indicator_helper_allows_colour_override() -> None:
    console = Console()
    service = ConsoleService(console)

    service.set_abort_indicator(0xC1, colour=0x02)

    assert console.screen.peek_screen_address(0x041F) == 0xC1
    palette = console.screen.palette
    expected_colour = _resolve_palette_colour(0x02, palette)
    assert console.screen.peek_colour_address(0xD81F) == expected_colour
    assert console.transcript_bytes == b""


def test_idle_timer_helper_updates_three_cells() -> None:
    console = Console()
    service = ConsoleService(console)

    sentinel = console.screen.peek_screen_address(0x04DF)

    service.update_idle_timer_digits([0xB1, 0xB2, 0xB3])

    assert console.screen.peek_screen_address(0x04DE) == 0xB1
    assert console.screen.peek_screen_address(0x04E0) == 0xB2
    assert console.screen.peek_screen_address(0x04E1) == 0xB3
    assert console.screen.peek_screen_address(0x04DF) == sentinel
    assert console.transcript_bytes == b""


def test_idle_timer_helper_requires_three_digits() -> None:
    console = Console()
    service = ConsoleService(console)

    with pytest.raises(ValueError):
        service.update_idle_timer_digits([0xB0, 0xB1])


def test_spinner_helper_updates_screen_and_colour() -> None:
    console = Console()
    service = ConsoleService(console)

    service.set_spinner_glyph(0xC8, colour=0x01)

    assert console.screen.peek_screen_address(0x049C) == 0xC8
    palette = console.screen.palette
    expected_colour = _resolve_palette_colour(0x01, palette)
    assert console.screen.peek_colour_address(0xD89C) == expected_colour
    assert console.transcript_bytes == b""


def test_carrier_indicator_helper_updates_both_cells() -> None:
    console = Console()
    service = ConsoleService(console)

    service.set_carrier_indicator(
        leading_cell=0x20,
        indicator_cell=0xC7,
        leading_colour=0x03,
        indicator_colour=0x02,
    )

    assert console.screen.peek_screen_address(0x0400) == 0x20
    assert console.screen.peek_screen_address(0x0427) == 0xC7
    palette = console.screen.palette
    leading_colour = _resolve_palette_colour(0x03, palette)
    indicator_colour = _resolve_palette_colour(0x02, palette)
    assert console.screen.peek_colour_address(0xD800) == leading_colour
    assert console.screen.peek_colour_address(0xD827) == indicator_colour
    assert console.transcript_bytes == b""

