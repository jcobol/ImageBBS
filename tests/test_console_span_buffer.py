"""Regression tests for ConsoleRegionBuffer swaps."""

from imagebbs.device_context import (
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


def test_console_transcript_records_ascii_and_binary_payloads() -> None:
    console = Console()
    service = ConsoleService(console)

    console.write("HELLO\r")
    console.write(b"\x93GOODBYE\r")

    assert console.transcript == "HELLO\r\nGOODBYE\n"
    assert console.transcript_bytes == b"HELLO\r\x93GOODBYE\r"
    assert list(service.device.output) == ["HELLO\r", "\nGOODBYE\n"]


def test_fill_colour_span_writes_resolved_palette_without_transcript() -> None:
    console = Console()
    service = ConsoleService(console)

    colour_address = 0xDBCC
    span_length = 0x10
    colour_value = 0x0E

    service.fill_colour(colour_address, colour_value, span_length)

    palette = service.screen.palette
    expected_colour = _resolve_palette_colour(colour_value, palette)
    resolved_span = _read_colour(service, colour_address, span_length)

    assert resolved_span == bytes((expected_colour,) * span_length)
    assert service.device.transcript_bytes == b""


def test_peek_block_snapshots_masked_pane_span() -> None:
    console = Console()
    service = ConsoleService(console)

    screen_address = 0x0770
    colour_address = 0xDB70
    span_length = 0x28

    original_screen = bytes((0x60 + i) % 256 for i in range(span_length))
    original_colour = bytes((i % 16) for i in range(span_length))

    service.poke_block(
        screen_address=screen_address,
        screen_bytes=original_screen,
        colour_address=colour_address,
        colour_bytes=original_colour,
    )

    expected_screen = _read_screen(service, screen_address, span_length)
    expected_colour = _read_colour(service, colour_address, span_length)

    captured_screen, captured_colour = service.peek_block(
        screen_address=screen_address,
        screen_length=span_length,
        colour_address=colour_address,
        colour_length=span_length,
    )

    assert captured_screen == expected_screen
    assert captured_colour == expected_colour

    mutated_screen = bytes((0x10 + i) % 256 for i in range(span_length))
    mutated_colour = bytes(((i + 7) % 16) for i in range(span_length))

    service.poke_block(
        screen_address=screen_address,
        screen_bytes=mutated_screen,
        colour_address=colour_address,
        colour_bytes=mutated_colour,
    )

    refreshed_screen, refreshed_colour = service.peek_block(
        screen_address=screen_address,
        screen_length=span_length,
        colour_address=colour_address,
        colour_length=span_length,
    )

    assert refreshed_screen == _read_screen(service, screen_address, span_length)
    assert refreshed_colour == _read_colour(service, colour_address, span_length)
    assert captured_screen == expected_screen
    assert captured_colour == expected_colour
    assert service.device.transcript_bytes == b""


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


def test_partial_restore_honours_requested_lengths() -> None:
    console = Console()
    service = ConsoleService(console)

    screen_address = 0x0580
    colour_address = service._colour_address_for(screen_address)

    full_screen_length = 0x20
    full_colour_length = 0x20

    base_screen = bytes((0x30 + i) % 256 for i in range(full_screen_length))
    base_colour = bytes((0x02 for _ in range(full_colour_length)))

    palette = service.screen.palette
    expected_base_colour = bytes(
        _resolve_palette_colour(value, palette) for value in base_colour
    )

    service.poke_block(
        screen_address=screen_address,
        screen_bytes=base_screen,
        colour_address=colour_address,
        colour_bytes=base_colour,
    )

    overlay_screen = bytes((0x70 + i) % 256 for i in range(full_screen_length))
    overlay_colour = bytes((0x0A for _ in range(full_colour_length)))

    partial_screen_length = 0x0C
    partial_colour_length = 0x08

    expected_overlay_colour = bytes(
        _resolve_palette_colour(value, palette)
        for value in overlay_colour[:partial_colour_length]
    )

    service.poke_block(
        screen_address=screen_address,
        screen_bytes=overlay_screen,
        screen_length=partial_screen_length,
        colour_address=colour_address,
        colour_bytes=overlay_colour,
        colour_length=partial_colour_length,
    )

    resulting_screen = _read_screen(service, screen_address, full_screen_length)
    resulting_colour = _read_colour(service, colour_address, full_colour_length)

    assert resulting_screen[:partial_screen_length] == overlay_screen[:partial_screen_length]
    assert resulting_screen[partial_screen_length:] == base_screen[partial_screen_length:]

    assert resulting_colour[:partial_colour_length] == expected_overlay_colour
    assert (
        resulting_colour[partial_colour_length:]
        == expected_base_colour[partial_colour_length:]
    )

    assert service.device.transcript_bytes == b""
