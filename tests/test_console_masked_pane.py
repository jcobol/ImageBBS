import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.device_context import (  # noqa: E402
    Console,
    ConsoleService,
    MaskedPaneBuffers,
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


def test_masked_pane_blink_scheduler_cycles() -> None:
    console = Console()
    service = ConsoleService(console)

    countdowns: list[int] = []
    reverse_flags: list[bool] = []
    for _ in range(10):
        state = service.advance_masked_pane_blink()
        countdowns.append(state.countdown)
        reverse_flags.append(state.reverse)

    assert countdowns[:5] == [3, 2, 1, 0, 4]
    assert countdowns[5:] == [3, 2, 1, 0, 4]
    assert reverse_flags[:5] == [True, True, False, False, False]
    assert reverse_flags[5:] == [True, True, False, False, False]


def test_write_masked_pane_cell_applies_blink_and_preserves_transcript() -> None:
    console = Console()
    service = ConsoleService(console)

    reverse_pattern: list[bool] = []
    for _ in range(10):
        payload = service.write_masked_pane_cell(0, 0x41, 0x02)
        reverse_pattern.append(payload.reverse)

        expected_glyph = payload.glyph
        assert console.screen.peek_screen_address(0x0518) == expected_glyph

        palette = console.screen.palette
        expected_colour = _resolve_palette_colour(payload.colour, palette)
        assert console.screen.peek_colour_address(0xD918) == expected_colour

    assert reverse_pattern[:5] == [True, True, False, False, False]
    assert reverse_pattern[5:] == [True, True, False, False, False]
    assert console.transcript_bytes == b""


def test_capture_masked_pane_buffers_reads_live_overlay() -> None:
    console = Console()
    service = ConsoleService(console)
    buffers = MaskedPaneBuffers()

    screen_address = 0x0770
    colour_address = 0xDB70

    screen_payload = bytes((0x40 + i) % 256 for i in range(buffers.width))
    colour_payload = bytes(i % 16 for i in range(buffers.width))

    service.poke_block(
        screen_address=screen_address,
        screen_bytes=screen_payload,
        colour_address=colour_address,
        colour_bytes=colour_payload,
    )

    service.capture_masked_pane_buffers(buffers)

    palette = service.screen.palette
    expected_colour = bytes(
        _resolve_palette_colour(value, palette) for value in colour_payload
    )

    assert bytes(buffers.live_screen) == screen_payload
    assert bytes(buffers.live_colour) == expected_colour
    assert console.transcript_bytes == b""


def test_clear_masked_pane_staging_defaults_to_screen_colour() -> None:
    console = Console()
    service = ConsoleService(console)
    buffers = MaskedPaneBuffers()

    buffers.staged_screen[:] = bytes(range(buffers.width))
    buffers.staged_colour[:] = bytes((value + 1) % 16 for value in range(buffers.width))

    service.clear_masked_pane_staging(buffers)

    expected_colour = service.screen_colour & 0xFF

    assert bytes(buffers.staged_screen) == bytes((0x20,) * buffers.width)
    assert bytes(buffers.staged_colour) == bytes((expected_colour,) * buffers.width)


def test_masked_pane_buffer_rotation_matches_loopb94e() -> None:
    console = Console()
    service = ConsoleService(console)
    buffers = MaskedPaneBuffers()

    live_screen = bytes((0x30 + i) % 256 for i in range(buffers.width))
    live_colour = bytes(i % 16 for i in range(buffers.width))
    staged_screen = bytes((0x70 + i) % 256 for i in range(buffers.width))
    staged_colour = bytes(((i + 5) % 16) for i in range(buffers.width))

    buffers.live_screen[:] = live_screen
    buffers.live_colour[:] = live_colour
    buffers.staged_screen[:] = staged_screen
    buffers.staged_colour[:] = staged_colour

    fill_glyph = 0x20
    fill_colour = 0x0A

    service.rotate_masked_pane_buffers(
        buffers, fill_glyph=fill_glyph, fill_colour=fill_colour
    )

    palette = service.screen.palette
    expected_live_colour = bytes(
        _resolve_palette_colour(value, palette) for value in live_colour
    )

    assert _read_screen(service, 0x0770, buffers.width) == live_screen
    assert _read_colour(service, 0xDB70, buffers.width) == expected_live_colour

    assert bytes(buffers.live_screen) == staged_screen
    assert bytes(buffers.live_colour) == staged_colour
    assert bytes(buffers.staged_screen) == bytes((fill_glyph,) * buffers.width)
    assert bytes(buffers.staged_colour) == bytes((fill_colour,) * buffers.width)
    assert console.transcript_bytes == b""
