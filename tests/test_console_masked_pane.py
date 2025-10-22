import pytest

from imagebbs.device_context import (
    Console,
    ConsoleService,
    MaskedPaneBuffers,
    bootstrap_device_context,
)
from imagebbs.runtime.masked_pane_staging import (
    MaskedPaneStagingMap,
    build_masked_pane_staging_map,
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


def test_masked_pane_staging_map_uses_runtime_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    console = Console()
    service = ConsoleService(console)

    calls: list[ConsoleService] = []
    sentinel = object()

    def fake_builder(argument: ConsoleService) -> object:
        calls.append(argument)
        return sentinel

    monkeypatch.setattr(
        "imagebbs.runtime.masked_pane_staging.build_masked_pane_staging_map",
        fake_builder,
    )

    result = service.masked_pane_staging_map
    assert result is sentinel
    assert calls == [service]

    result_again = service.masked_pane_staging_map
    assert result_again is sentinel
    assert calls == [service]


def test_masked_pane_staging_map_matches_native_runtime() -> None:
    console = Console()
    service = ConsoleService(console)

    staging_map = service.masked_pane_staging_map

    assert isinstance(staging_map, MaskedPaneStagingMap)
    assert staging_map == build_masked_pane_staging_map(service)


def test_masked_pane_buffers_expose_staging_views() -> None:
    buffers = MaskedPaneBuffers()

    assert buffers.live_screen is buffers.tempbott
    assert buffers.live_colour is buffers.colour_4050
    assert buffers.staged_screen is buffers.tempbott_next
    assert buffers.staged_colour is buffers.colour_var_4078
    assert buffers.dirty is False

    buffers.live_screen[:] = bytes((0x41,) * buffers.width)
    buffers.live_colour[:] = bytes((0x02,) * buffers.width)
    buffers.staged_screen[:] = bytes((0x51,) * buffers.width)
    buffers.staged_colour[:] = bytes((0x07,) * buffers.width)

    assert bytes(buffers.tempbott) == bytes((0x41,) * buffers.width)
    assert bytes(buffers.colour_4050) == bytes((0x02,) * buffers.width)
    assert bytes(buffers.tempbott_next) == bytes((0x51,) * buffers.width)
    assert bytes(buffers.colour_var_4078) == bytes((0x07,) * buffers.width)


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
    assert bytes(buffers.tempbott) == screen_payload
    assert bytes(buffers.colour_4050) == expected_colour
    assert console.transcript_bytes == b""


def test_clear_masked_pane_staging_defaults_to_screen_colour() -> None:
    console = Console()
    service = ConsoleService(console)
    buffers = MaskedPaneBuffers()

    buffers.staged_screen[:] = bytes(range(buffers.width))
    buffers.staged_colour[:] = bytes((value + 1) % 16 for value in range(buffers.width))
    buffers.recalculate_dirty()
    assert buffers.dirty is True

    service.clear_masked_pane_staging(buffers)

    expected_colour = service.screen_colour & 0xFF

    assert bytes(buffers.staged_screen) == bytes((0x20,) * buffers.width)
    assert bytes(buffers.staged_colour) == bytes((expected_colour,) * buffers.width)
    assert bytes(buffers.tempbott_next) == bytes((0x20,) * buffers.width)
    assert bytes(buffers.colour_var_4078) == bytes((expected_colour,) * buffers.width)
    assert buffers.dirty is False


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
    buffers.recalculate_dirty()
    assert buffers.dirty is True

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
    assert bytes(buffers.tempbott) == staged_screen
    assert bytes(buffers.colour_4050) == staged_colour
    assert bytes(buffers.staged_screen) == bytes((fill_glyph,) * buffers.width)
    assert bytes(buffers.staged_colour) == bytes((fill_colour,) * buffers.width)
    assert bytes(buffers.tempbott_next) == bytes((fill_glyph,) * buffers.width)
    assert bytes(buffers.colour_var_4078) == bytes((fill_colour,) * buffers.width)
    assert buffers.dirty is False
    assert console.transcript_bytes == b""


def test_masked_pane_staging_single_byte_writes_capture_buffers() -> None:
    console = Console()
    service = ConsoleService(console)
    buffers = MaskedPaneBuffers()
    service.set_masked_pane_buffers(buffers)

    stage_screen_address = ConsoleService._MASKED_STAGING_SCREEN_BASE
    stage_colour_address = ConsoleService._MASKED_STAGING_COLOUR_BASE

    assert buffers.dirty is False

    last_screen_address = (
        ConsoleService._SCREEN_BASE
        + console.screen.width * console.screen.height
        - 1
    )
    last_colour_address = (
        ConsoleService._COLOUR_BASE
        + console.screen.width * console.screen.height
        - 1
    )

    baseline_screen = console.screen.peek_screen_address(last_screen_address)
    baseline_colour = console.screen.peek_colour_address(last_colour_address)

    service.poke_screen_byte(stage_screen_address, 0x41)
    service.poke_colour_byte(stage_colour_address, 0x06)
    service.fill_colour(stage_colour_address, 0x07, 3)

    assert bytes(buffers.staged_screen[:1]) == b"A"
    assert bytes(buffers.staged_colour[:3]) == bytes((0x07,) * 3)
    assert buffers.dirty is True

    assert console.screen.peek_screen_address(last_screen_address) == baseline_screen
    assert console.screen.peek_colour_address(last_colour_address) == baseline_colour
    assert console.transcript_bytes == b""


def test_masked_pane_staging_block_writes_bypass_renderer() -> None:
    console = Console()
    service = ConsoleService(console)
    buffers = MaskedPaneBuffers()
    service.set_masked_pane_buffers(buffers)

    stage_screen_address = ConsoleService._MASKED_STAGING_SCREEN_BASE
    stage_colour_address = ConsoleService._MASKED_STAGING_COLOUR_BASE

    assert buffers.dirty is False

    screen_payload = bytes((0x30 + i) % 256 for i in range(buffers.width))
    colour_payload = bytes((i + 5) % 16 for i in range(buffers.width))

    service.poke_block(
        screen_address=stage_screen_address,
        screen_bytes=screen_payload,
        colour_address=stage_colour_address,
        colour_bytes=colour_payload,
    )

    assert bytes(buffers.staged_screen) == screen_payload
    assert bytes(buffers.staged_colour) == colour_payload
    assert buffers.dirty is True

    normal_screen_address = ConsoleService._SCREEN_BASE
    normal_colour_address = ConsoleService._COLOUR_BASE
    service.poke_block(
        screen_address=normal_screen_address,
        screen_bytes=b"AB",
        colour_address=normal_colour_address,
        colour_bytes=bytes((0x01, 0x02)),
    )

    assert _read_screen(service, normal_screen_address, 2) == b"AB"
    palette = service.screen.palette
    expected_colour = bytes(
        _resolve_palette_colour(value, palette) for value in (0x01, 0x02)
    )
    assert _read_colour(service, normal_colour_address, 2) == expected_colour
    assert console.transcript_bytes == b""


def test_commit_masked_pane_staging_flushes_overlay_and_resets_buffers() -> None:
    context = bootstrap_device_context(assignments=())
    service = context.get_service("console")
    assert isinstance(service, ConsoleService)

    buffers = context.get_service("masked_pane_buffers")
    assert isinstance(buffers, MaskedPaneBuffers)
    assert service._masked_pane_buffers is buffers

    screen_payload = bytes((0x60 + i) % 256 for i in range(buffers.width))
    colour_payload = bytes(((i + 3) % 16) for i in range(buffers.width))

    service.poke_block(
        screen_address=ConsoleService._MASKED_STAGING_SCREEN_BASE,
        screen_bytes=screen_payload,
        colour_address=ConsoleService._MASKED_STAGING_COLOUR_BASE,
        colour_bytes=colour_payload,
    )

    assert bytes(buffers.staged_screen) == screen_payload
    assert bytes(buffers.staged_colour) == colour_payload
    assert buffers.dirty is True

    service.commit_masked_pane_staging()

    palette = service.screen.palette
    expected_colour = bytes(
        _resolve_palette_colour(value, palette) for value in colour_payload
    )

    assert _read_screen(service, 0x0770, buffers.width) == screen_payload
    assert _read_colour(service, 0xDB70, buffers.width) == expected_colour

    expected_fill_colour = service.screen_colour & 0xFF
    assert bytes(buffers.staged_screen) == bytes((0x20,) * buffers.width)
    assert bytes(buffers.staged_colour) == bytes(
        (expected_fill_colour,) * buffers.width
    )
    assert buffers.dirty is False
    assert buffers.peek_pending_payload() is None


def test_stage_masked_pane_overlay_normalises_payloads_and_defers_commit() -> None:
    console = Console()
    service = ConsoleService(console)
    buffers = MaskedPaneBuffers()
    service.set_masked_pane_buffers(buffers)

    width = buffers.width
    baseline_screen = _read_screen(
        service, ConsoleService._MASKED_OVERLAY_SCREEN_BASE, width
    )
    baseline_colour = _read_colour(
        service, ConsoleService._MASKED_OVERLAY_COLOUR_BASE, width
    )

    screen_payload = bytes((0x41 + i) % 256 for i in range(10))
    colour_payload = bytes(((i + 3) % 16) for i in range(6))
    fill_colour = 0x0B

    service.stage_masked_pane_overlay(
        screen_payload, colour_payload, fill_colour=fill_colour
    )

    truncated_screen = screen_payload[:width]
    expected_screen = truncated_screen + bytes(
        (0x20,) * (width - len(truncated_screen))
    )

    truncated_colour = colour_payload[:width]
    expected_colour = truncated_colour + bytes(
        (fill_colour,) * (width - len(truncated_colour))
    )

    assert bytes(buffers.staged_screen) == expected_screen
    assert bytes(buffers.staged_colour) == expected_colour
    assert buffers.dirty is True
    pending_payload = buffers.peek_pending_payload()
    assert pending_payload is not None
    assert pending_payload[0] == expected_screen
    assert pending_payload[1] == expected_colour

    screen_overflow_payload = bytes((0x60 + i) % 256 for i in range(width + 5))
    service.stage_masked_pane_overlay(screen_overflow_payload)

    truncated_screen = screen_overflow_payload[:width]
    expected_colour = bytes(((service.screen_colour & 0xFF),) * width)

    assert bytes(buffers.staged_screen) == truncated_screen
    assert bytes(buffers.staged_colour) == expected_colour
    assert buffers.dirty is True
    pending_payload = buffers.peek_pending_payload()
    assert pending_payload is not None
    assert pending_payload[0] == truncated_screen
    assert pending_payload[1] == expected_colour

    assert (
        _read_screen(service, ConsoleService._MASKED_OVERLAY_SCREEN_BASE, width)
        == baseline_screen
    )
    assert (
        _read_colour(service, ConsoleService._MASKED_OVERLAY_COLOUR_BASE, width)
        == baseline_colour
    )
    assert console.transcript_bytes == b""


def test_stage_macro_slot_populates_staging_buffers() -> None:
    console = Console()
    service = ConsoleService(console)
    buffers = MaskedPaneBuffers()
    service.set_masked_pane_buffers(buffers)

    width = buffers.width
    overlay_screen_address = ConsoleService._MASKED_OVERLAY_SCREEN_BASE
    overlay_colour_address = ConsoleService._MASKED_OVERLAY_COLOUR_BASE
    baseline_screen = _read_screen(service, overlay_screen_address, width)
    baseline_colour = _read_colour(service, overlay_colour_address, width)

    slot = 0x29
    macro_entry = console.defaults.macros_by_slot[slot]
    assert macro_entry.screen is not None

    expected_screen = bytes(macro_entry.screen.glyph_bytes[:width])
    expected_colour = bytes(macro_entry.screen.colour_bytes[:width])

    run = service.macro_glyphs[slot]
    result = service.stage_macro_slot(slot)

    assert result is run
    assert bytes(buffers.staged_screen) == expected_screen
    assert bytes(buffers.staged_colour) == expected_colour
    assert buffers.dirty is True
    pending_payload = buffers.peek_pending_payload()
    assert pending_payload is not None
    assert pending_payload[0] == expected_screen
    assert pending_payload[1] == expected_colour
    assert _read_screen(service, overlay_screen_address, width) == baseline_screen
    assert _read_colour(service, overlay_colour_address, width) == baseline_colour
    assert console.transcript_bytes == b""


def test_stage_macro_slot_without_screen_uses_rendered_payload() -> None:
    console = Console()
    service = ConsoleService(console)
    buffers = MaskedPaneBuffers()
    service.set_masked_pane_buffers(buffers)

    width = buffers.width
    overlay_screen_address = ConsoleService._MASKED_OVERLAY_SCREEN_BASE
    overlay_colour_address = ConsoleService._MASKED_OVERLAY_COLOUR_BASE
    baseline_screen = _read_screen(service, overlay_screen_address, width)
    baseline_colour = _read_colour(service, overlay_colour_address, width)

    slot = 0x02
    run = service.macro_glyphs[slot]

    fill_colour = 0x0C
    result = service.stage_macro_slot(slot, fill_colour=fill_colour)

    rendered_bytes = bytes(run.rendered[:width])
    padding = bytes((0x20,) * (width - len(rendered_bytes)))
    expected_screen = rendered_bytes + padding
    expected_colour = bytes((fill_colour & 0xFF,) * width)

    assert result is run
    assert bytes(buffers.staged_screen) == expected_screen
    assert bytes(buffers.staged_colour) == expected_colour
    assert buffers.dirty is True
    pending_payload = buffers.peek_pending_payload()
    assert pending_payload is not None
    assert pending_payload[0] == expected_screen
    assert pending_payload[1] == expected_colour
    assert _read_screen(service, overlay_screen_address, width) == baseline_screen
    assert _read_colour(service, overlay_colour_address, width) == baseline_colour
    assert console.transcript_bytes == b""


def test_pending_masked_pane_payload_consumed_once() -> None:
    console = Console()
    service = ConsoleService(console)
    buffers = MaskedPaneBuffers()
    service.set_masked_pane_buffers(buffers)

    width = buffers.width
    screen_payload = bytes((0x41 + i) % 256 for i in range(width))
    colour_payload = bytes(((i + 2) % 16) for i in range(width))

    service.stage_masked_pane_overlay(screen_payload, colour_payload)

    pending_payload = buffers.peek_pending_payload()
    assert pending_payload is not None
    consumed = buffers.consume_pending_payload()
    assert consumed == pending_payload
    assert buffers.has_pending_payload() is False
    assert buffers.peek_pending_payload() is None

    assert bytes(buffers.staged_screen) == screen_payload
    assert bytes(buffers.staged_colour) == colour_payload

    assert consumed is not None
    service.stage_masked_pane_overlay(consumed[0], consumed[1])

    assert buffers.peek_pending_payload() is None
    assert bytes(buffers.staged_screen) == consumed[0]
    assert bytes(buffers.staged_colour) == consumed[1]

    buffers.clear_pending_payload()
    service.stage_masked_pane_overlay(screen_payload, colour_payload)
    restored_pending = buffers.peek_pending_payload()
    assert restored_pending is not None
    assert restored_pending[0] == screen_payload
    assert restored_pending[1] == colour_payload
