"""Tests for direct screen/colour address helpers on the console."""

from scripts.prototypes.device_context import Console


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

