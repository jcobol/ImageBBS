"""Regression tests for ConsoleRegionBuffer swaps."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.device_context import (
    Console,
    ConsoleRegionBuffer,
    ConsoleService,
)


def _resolve_palette_colour(value: int, palette: tuple[int, ...], *, default_index: int = 0) -> int:
    resolved = int(value) & 0xFF
    if resolved in palette:
        return resolved
    if 0 <= resolved < len(palette):
        return palette[resolved]
    if not 0 <= default_index < len(palette):
        raise ValueError("default_index must reference a palette entry")
    return palette[default_index]


def _read_screen(service: ConsoleService, address: int, length: int) -> bytes:
    screen = service.screen
    return bytes(
        screen.peek_screen_address(address + offset) for offset in range(length)
    )


def _read_colour(service: ConsoleService, address: int, length: int) -> bytes:
    screen = service.screen
    return bytes(
        screen.peek_colour_address(address + offset) for offset in range(length)
    )


def test_swap_region_exchanges_screen_and_colour_payloads() -> None:
    console = Console()
    service = ConsoleService(console)
    buffer = ConsoleRegionBuffer(screen_length=0xF0, colour_length=0x50)

    screen_address = 0x0428
    colour_address = 0xDB98

    original_screen = bytes((0x20 + i) % 256 for i in range(buffer.screen_length))
    original_colour = bytes(i % 16 for i in range(buffer.colour_length))

    service.poke_block(
        screen_address=screen_address,
        screen_bytes=original_screen,
        colour_address=colour_address,
        colour_bytes=original_colour,
    )

    overlay_screen = bytes((0x80 + i) % 256 for i in range(buffer.screen_length))
    overlay_colour = bytes(((i + 8) % 16) for i in range(buffer.colour_length))

    palette = service.screen.palette
    expected_original_colour = bytes(
        _resolve_palette_colour(value, palette) for value in original_colour
    )
    expected_overlay_colour = bytes(
        _resolve_palette_colour(value, palette) for value in overlay_colour
    )

    buffer.screen_bytes[:] = overlay_screen
    buffer.colour_bytes[:] = overlay_colour

    service.swap_region(
        buffer,
        screen_address=screen_address,
        colour_address=colour_address,
    )

    assert _read_screen(service, screen_address, buffer.screen_length) == overlay_screen
    assert _read_colour(service, colour_address, buffer.colour_length) == expected_overlay_colour
    assert bytes(buffer.screen_bytes) == original_screen
    assert bytes(buffer.colour_bytes) == expected_original_colour
    assert service.device.transcript_bytes == b""


def test_capture_and_restore_roundtrip() -> None:
    console = Console()
    service = ConsoleService(console)
    buffer = ConsoleRegionBuffer(screen_length=0x50, colour_length=0x50)

    screen_address = 0x0798
    colour_address = 0xDB98

    original_screen = bytes((0x40 + i) % 256 for i in range(buffer.screen_length))
    original_colour = bytes((i * 3) % 16 for i in range(buffer.colour_length))

    palette = service.screen.palette
    expected_original_colour = bytes(
        _resolve_palette_colour(value, palette) for value in original_colour
    )

    service.poke_block(
        screen_address=screen_address,
        screen_bytes=original_screen,
        colour_address=colour_address,
        colour_bytes=original_colour,
    )

    service.capture_region(
        buffer,
        screen_address=screen_address,
        colour_address=colour_address,
    )

    assert _read_screen(service, screen_address, buffer.screen_length) == original_screen
    assert _read_colour(service, colour_address, buffer.colour_length) == expected_original_colour

    mutated_screen = bytes((0x10 + i) % 256 for i in range(buffer.screen_length))
    mutated_colour = bytes((i + 5) % 16 for i in range(buffer.colour_length))

    expected_mutated_colour = bytes(
        _resolve_palette_colour(value, palette) for value in mutated_colour
    )

    service.poke_block(
        screen_address=screen_address,
        screen_bytes=mutated_screen,
        colour_address=colour_address,
        colour_bytes=mutated_colour,
    )

    assert _read_screen(service, screen_address, buffer.screen_length) == mutated_screen
    assert _read_colour(service, colour_address, buffer.colour_length) == expected_mutated_colour

    service.restore_region(
        buffer,
        screen_address=screen_address,
        colour_address=colour_address,
    )

    assert _read_screen(service, screen_address, buffer.screen_length) == original_screen
    assert _read_colour(service, colour_address, buffer.colour_length) == expected_original_colour
    assert bytes(buffer.screen_bytes) == original_screen
    assert bytes(buffer.colour_bytes) == expected_original_colour
    assert service.device.transcript_bytes == b""
