from __future__ import annotations

import json
import pytest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Iterator, Tuple

from imagebbs.ampersand_dispatcher import AmpersandDispatcher
from imagebbs.device_context import (
    ConsoleService,
    MaskedPaneBuffers,
    bootstrap_device_context,
)
from imagebbs.runtime.ampersand_overrides import BUILTIN_AMPERSAND_OVERRIDES
from imagebbs.runtime.file_transfers import (
    FileTransferEvent,
    FileTransfersModule,
)
from imagebbs.runtime.main_menu import (
    MainMenuEvent,
    MainMenuModule,
)
from imagebbs.runtime.sysop_options import (
    SysopOptionsEvent,
    SysopOptionsModule,
)
from imagebbs.session_kernel import SessionKernel


def _resolve_palette_colour(value: int, palette: tuple[int, ...], *, default_index: int = 0) -> int:
    resolved = int(value) & 0xFF
    if resolved in palette:
        return resolved
    if 0 <= resolved < len(palette):
        return palette[resolved]
    if not 0 <= default_index < len(palette):
        raise ValueError("default_index must reference a palette entry")
    return palette[default_index]


@contextmanager
def _capture_macro_staging(
    console: ConsoleService, buffers: MaskedPaneBuffers
) -> Iterator[Dict[int, Tuple[Tuple[int, ...], Tuple[int, ...]]]]:
    """Capture staged glyph/colour spans keyed by macro slot."""

    original_stage_macro = console.stage_macro_slot
    original_stage_overlay = console.stage_masked_pane_overlay
    captured: Dict[int, Tuple[Tuple[int, ...], Tuple[int, ...]]] = {}
    pending_fallback_slot: int | None = None

    def _stage_macro(slot: int, *args, **kwargs):  # type: ignore[override]
        nonlocal pending_fallback_slot
        result = original_stage_macro(slot, *args, **kwargs)
        if result is not None:
            glyphs = tuple(buffers.staged_screen[: buffers.width])
            colours = tuple(buffers.staged_colour[: buffers.width])
            captured[slot] = (glyphs, colours)
            pending_fallback_slot = None
        else:
            pending_fallback_slot = slot
        return result

    def _stage_overlay(*args, **kwargs):  # type: ignore[override]
        nonlocal pending_fallback_slot
        result = original_stage_overlay(*args, **kwargs)
        if pending_fallback_slot is not None:
            slot = pending_fallback_slot
            glyphs = tuple(buffers.staged_screen[: buffers.width])
            colours = tuple(buffers.staged_colour[: buffers.width])
            captured[slot] = (glyphs, colours)
            pending_fallback_slot = None
        return result

    console.stage_macro_slot = _stage_macro  # type: ignore[assignment]
    console.stage_masked_pane_overlay = _stage_overlay  # type: ignore[assignment]
    try:
        yield captured
    finally:
        console.stage_macro_slot = original_stage_macro  # type: ignore[assignment]
        console.stage_masked_pane_overlay = original_stage_overlay  # type: ignore[assignment]


def _expected_macro_span(
    slot: int,
    console: ConsoleService,
) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """Return 40-byte glyph/colour spans mirrored from defaults or fallbacks."""

    width = 40
    defaults = console.defaults
    entry = defaults.macros_by_slot.get(slot)

    glyphs: Tuple[int, ...] | None = None
    colours: Tuple[int, ...] | None = None

    if entry is not None and entry.screen is not None:
        glyphs = tuple(entry.screen.glyph_bytes[:width])
        colours = tuple(entry.screen.colour_bytes[:width])
    else:
        run = console.glyph_lookup.macros_by_slot.get(slot)
        if run is not None:
            glyphs = tuple(run.rendered[:width])
            fill = console.screen_colour & 0xFF
            colours = tuple((fill,) * min(len(glyphs), width))
        else:
            fallback = console.masked_pane_staging_map.fallback_overlay_for_slot(slot)
            if fallback is not None:
                glyphs = tuple(fallback[0][:width])
                colours = tuple(fallback[1][:width])

    if glyphs is None or colours is None:
        raise AssertionError(f"no macro payload recovered for slot ${slot:02x}")

    if len(glyphs) < width:
        glyphs = glyphs + (0x20,) * (width - len(glyphs))
    if len(colours) < width:
        fill = console.screen_colour & 0xFF
        colours = colours + (fill,) * (width - len(colours))

    return glyphs[:width], colours[:width]


def _parse_overlay_hex(value: str) -> int:
    value = value.strip()
    if value.startswith("$"):
        return int(value[1:], 16)
    if value.lower().startswith("0x"):
        return int(value, 16)
    return int(value, 10)


def test_ampersand_dispatcher_stages_masked_pane_flag_entries() -> None:
    metadata_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "porting"
        / "artifacts"
        / "ml-extra-overlay-metadata.json"
    )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata_entries = metadata["flag_dispatch"]["entries"]

    context = bootstrap_device_context(
        assignments=(), ampersand_overrides=BUILTIN_AMPERSAND_OVERRIDES
    )
    console = context.get_service("console")
    assert isinstance(console, ConsoleService)
    buffers = context.get_service("masked_pane_buffers")
    assert isinstance(buffers, MaskedPaneBuffers)
    dispatcher = context.get_service("ampersand")
    assert isinstance(dispatcher, AmpersandDispatcher)

    masked_slots = set(console._MASKED_OVERLAY_FLAG_SLOTS)
    metadata_pairs = [
        (
            _parse_overlay_hex(entry["flag_index"]),
            _parse_overlay_hex(entry["slot"]),
        )
        for entry in metadata_entries
    ]
    actual_pairs = [
        (entry.flag_index, entry.slot)
        for entry in console.device.flag_dispatch.entries
    ]
    assert actual_pairs == metadata_pairs

    expected_staging_slots = {slot for _, slot in metadata_pairs if slot in masked_slots}
    assert expected_staging_slots == masked_slots

    last_staged_slot: int | None = None
    with _capture_macro_staging(console, buffers) as captured:
        assert buffers.dirty is False
        for flag_index, slot in metadata_pairs:
            before_keys = set(captured)
            staged_screen_snapshot = tuple(buffers.staged_screen)
            staged_colour_snapshot = tuple(buffers.staged_colour)

            dispatcher.dispatch(f"&,{flag_index}")

            if slot in masked_slots:
                last_staged_slot = slot
                assert set(captured) == before_keys | {slot}
                glyphs, colours = captured[slot]
                expected_glyphs, expected_colours = _expected_macro_span(slot, console)
                assert glyphs == expected_glyphs
                assert colours == expected_colours
                assert tuple(buffers.staged_screen) == glyphs
                assert tuple(buffers.staged_colour) == expected_colours
            else:
                assert set(captured) == before_keys
                assert tuple(buffers.staged_screen) == staged_screen_snapshot
                assert tuple(buffers.staged_colour) == staged_colour_snapshot

        assert set(captured) == masked_slots
        assert last_staged_slot is not None
        loop_last_screen = tuple(buffers.staged_screen)
        loop_last_colour = tuple(buffers.staged_colour)

    assert last_staged_slot is not None
    assert loop_last_screen == captured[last_staged_slot][0]
    assert loop_last_colour == captured[last_staged_slot][1]

    fill_glyph = 0x20
    fill_colour = console.screen_colour & 0xFF
    populated_flag: int | None = None
    populated_slot: int | None = None
    for flag_index, slot in metadata_pairs:
        payload = captured.get(slot)
        if payload is None:
            continue
        glyphs, colours = payload
        if any(byte != fill_glyph for byte in glyphs) or any(
            byte != fill_colour for byte in colours
        ):
            populated_flag = flag_index
            populated_slot = slot
            break

    assert populated_flag is not None
    assert populated_slot is not None

    dispatcher.dispatch(f"&,{populated_flag}")

    assert buffers.dirty is True
    final_staged_screen = tuple(buffers.staged_screen)
    final_staged_colour = tuple(buffers.staged_colour)
    assert final_staged_screen == captured[populated_slot][0]
    assert final_staged_colour == captured[populated_slot][1]

    dispatcher.dispatch("&,50")

    assert buffers.dirty is False
    assert tuple(buffers.live_screen) == final_staged_screen
    assert tuple(buffers.live_colour) == final_staged_colour
    assert tuple(buffers.staged_screen) == (0x20,) * buffers.width
    assert tuple(buffers.staged_colour) == (fill_colour,) * buffers.width


def test_ampersand_28_sequence_stages_and_commits_once() -> None:
    context = bootstrap_device_context(
        assignments=(), ampersand_overrides=BUILTIN_AMPERSAND_OVERRIDES
    )
    console = context.get_service("console")
    assert isinstance(console, ConsoleService)
    buffers = context.get_service("masked_pane_buffers")
    assert isinstance(buffers, MaskedPaneBuffers)
    dispatcher = context.get_service("ampersand")
    assert isinstance(dispatcher, AmpersandDispatcher)

    staging = console.masked_pane_staging_map
    sequence = staging.ampersand_sequence("&,28")
    assert sequence

    with _capture_macro_staging(console, buffers) as captured:
        dispatcher.dispatch("&,28")

    expected_slots = {spec.slot for spec in sequence}
    assert expected_slots <= captured.keys()

    for spec in sequence:
        expected_glyphs, expected_colours = _expected_macro_span(spec.slot, console)
        staged_glyphs, staged_colours = captured[spec.slot]
        assert staged_glyphs == expected_glyphs
        assert staged_colours == expected_colours

    last_spec = sequence[-1]
    expected_last = _expected_macro_span(last_spec.slot, console)
    expected_screen_bytes = bytes(expected_last[0])
    expected_colour_bytes = bytes(expected_last[1])

    pending = buffers.peek_pending_payload()
    assert pending is not None
    assert pending[0] == expected_screen_bytes
    assert pending[1] == expected_colour_bytes
    assert buffers.dirty is True

    dispatcher.dispatch("&,50")

    assert buffers.peek_pending_payload() is None
    assert buffers.dirty is False
    assert tuple(buffers.live_screen) == expected_last[0]
    assert tuple(buffers.live_colour) == expected_last[1]
    fill_colour = console.screen_colour & 0xFF
    assert tuple(buffers.staged_screen) == (0x20,) * buffers.width
    assert tuple(buffers.staged_colour) == (fill_colour,) * buffers.width

    screen_bytes, colour_bytes = console.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=buffers.width,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=buffers.width,
    )

    assert screen_bytes == expected_screen_bytes
    assert colour_bytes == expected_colour_bytes

    dispatcher.dispatch("&,50")

    assert buffers.peek_pending_payload() is None
    screen_bytes_again, colour_bytes_again = console.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=buffers.width,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=buffers.width,
    )
    assert screen_bytes_again == expected_screen_bytes
    assert colour_bytes_again == expected_colour_bytes


def test_ampersand_28_sequences_survive_bare_ampersand_and_toggle_staging() -> None:
    context = bootstrap_device_context(
        assignments=(), ampersand_overrides=BUILTIN_AMPERSAND_OVERRIDES
    )
    console = context.get_service("console")
    assert isinstance(console, ConsoleService)
    buffers = context.get_service("masked_pane_buffers")
    assert isinstance(buffers, MaskedPaneBuffers)
    dispatcher = context.get_service("ampersand")
    assert isinstance(dispatcher, AmpersandDispatcher)

    staging = console.masked_pane_staging_map
    transfer_sequence = staging.ampersand_sequence("&,28")
    assert transfer_sequence
    sayings_toggle_sequence = staging.ampersand_sequence("&,52,20,3")
    assert sayings_toggle_sequence
    prompt_toggle_sequence = staging.ampersand_sequence("&,52,24,3")
    assert prompt_toggle_sequence

    sayings_slot = sayings_toggle_sequence[0].slot
    prompt_slot = prompt_toggle_sequence[0].slot
    prompt_slot_from_transfer = transfer_sequence[-1].slot
    prompt_transfer_expected = _expected_macro_span(
        prompt_slot_from_transfer, console
    )

    with _capture_macro_staging(console, buffers) as captured:
        dispatcher.dispatch("&,28")

        for spec in transfer_sequence:
            expected = _expected_macro_span(spec.slot, console)
            assert spec.slot in captured
            assert captured[spec.slot][0] == expected[0]
            assert captured[spec.slot][1] == expected[1]

        pending_before = buffers.peek_pending_payload()
        assert pending_before is not None
        assert pending_before[0] == bytes(prompt_transfer_expected[0])
        assert pending_before[1] == bytes(prompt_transfer_expected[1])
        assert tuple(buffers.staged_screen) == prompt_transfer_expected[0]
        assert tuple(buffers.staged_colour) == prompt_transfer_expected[1]
        assert buffers.dirty is True

        with pytest.raises(ValueError):
            dispatcher.dispatch("&")

        pending_after = buffers.peek_pending_payload()
        assert pending_after is not None
        assert pending_after[0] == bytes(prompt_transfer_expected[0])
        assert pending_after[1] == bytes(prompt_transfer_expected[1])
        assert buffers.dirty is True

        dispatcher.dispatch("&,52,20,3")
        assert sayings_slot in captured
        sayings_expected = _expected_macro_span(sayings_slot, console)
        assert captured[sayings_slot][0] == sayings_expected[0]
        assert captured[sayings_slot][1] == sayings_expected[1]

        dispatcher.dispatch("&,52,24,3")
        assert prompt_slot in captured
        prompt_toggle_expected = _expected_macro_span(prompt_slot, console)
        assert captured[prompt_slot][0] == prompt_toggle_expected[0]
        assert captured[prompt_slot][1] == prompt_toggle_expected[1]

        dispatcher.dispatch("&,28")

        for spec in transfer_sequence:
            expected = _expected_macro_span(spec.slot, console)
            assert spec.slot in captured
            assert captured[spec.slot][0] == expected[0]
            assert captured[spec.slot][1] == expected[1]

        pending_before_commit = buffers.peek_pending_payload()
        assert pending_before_commit is not None
        assert pending_before_commit[0] == bytes(prompt_transfer_expected[0])
        assert pending_before_commit[1] == bytes(prompt_transfer_expected[1])
        assert tuple(buffers.staged_screen) == prompt_transfer_expected[0]
        assert tuple(buffers.staged_colour) == prompt_transfer_expected[1]

        dispatcher.dispatch("&,50")

        assert buffers.peek_pending_payload() is None
        assert buffers.dirty is False
        assert tuple(buffers.live_screen) == prompt_transfer_expected[0]
        assert tuple(buffers.live_colour) == prompt_transfer_expected[1]
        fill_colour = console.screen_colour & 0xFF
        assert tuple(buffers.staged_screen) == (0x20,) * buffers.width
        assert tuple(buffers.staged_colour) == (fill_colour,) * buffers.width


def test_masked_pane_buffers_pending_payload_helpers() -> None:
    buffers = MaskedPaneBuffers()

    glyphs = bytes(range(buffers.width))
    colours = bytes((index % 16) for index in range(buffers.width))

    buffers.cache_pending_payload(glyphs, colours)
    assert buffers.has_pending_payload() is True
    peeked = buffers.peek_pending_payload()
    assert peeked == (glyphs, colours)

    consumed = buffers.consume_pending_payload()
    assert consumed == (glyphs, colours)
    assert buffers.has_pending_payload() is False

    # The first cache after a consume is intentionally suppressed to mirror
    # the overlay's staging loop.
    buffers.cache_pending_payload(glyphs, colours)
    assert buffers.has_pending_payload() is False
    buffers.cache_pending_payload(glyphs, colours)
    assert buffers.peek_pending_payload() == (glyphs, colours)

    buffers.clear_pending_payload()
    assert buffers.has_pending_payload() is False


def test_console_masked_pane_rotation_applies_pending_payload() -> None:
    context = bootstrap_device_context(assignments=())
    console = context.get_service("console")
    assert isinstance(console, ConsoleService)
    buffers = context.get_service("masked_pane_buffers")
    assert isinstance(buffers, MaskedPaneBuffers)

    glyphs = bytes((0x60 + index) % 256 for index in range(buffers.width))
    colours = bytes((index % 16) for index in range(buffers.width))

    buffers.clear_pending_payload()
    console.clear_masked_pane_staging(buffers, glyph=0x20, colour=0x01)
    console.stage_masked_pane_overlay(glyphs, colours)

    pending = buffers.peek_pending_payload()
    assert pending is not None
    assert pending[0][: len(glyphs)] == glyphs[: len(pending[0])]
    assert pending[1][: len(colours)] == colours[: len(pending[1])]
    assert buffers.dirty is True

    console.commit_masked_pane_staging()

    assert buffers.dirty is False
    assert buffers.has_pending_payload() is False
    assert tuple(buffers.live_screen)[: len(glyphs)] == tuple(glyphs[: buffers.width])
    assert tuple(buffers.live_colour)[: len(colours)] == tuple(
        colours[: buffers.width]
    )
    assert tuple(buffers.staged_screen) == (0x20,) * buffers.width

def test_ampersand_52_flag_sequences_stage_masked_slots() -> None:
    context = bootstrap_device_context(
        assignments=(), ampersand_overrides=BUILTIN_AMPERSAND_OVERRIDES
    )
    console = context.get_service("console")
    assert isinstance(console, ConsoleService)
    buffers = context.get_service("masked_pane_buffers")
    assert isinstance(buffers, MaskedPaneBuffers)
    dispatcher = context.get_service("ampersand")
    assert isinstance(dispatcher, AmpersandDispatcher)

    staging = console.masked_pane_staging_map
    sequence_expectations = [
        ("&,52,4,3", 0x04),
        ("&,52,9,3", 0x09),
        ("&,52,13,3", 0x0D),
        ("&,52,20,3", 0x14),
        ("&,52,20,2", 0x14),
        ("&,52,21,3", 0x15),
        ("&,52,22,3", 0x16),
        ("&,52,23,3", 0x17),
        ("&,52,24,3", 0x18),
        ("&,52,25,3", 0x19),
    ]

    with _capture_macro_staging(console, buffers) as captured:
        for key, expected_slot in sequence_expectations:
            sequence = staging.ampersand_sequence(key)
            assert sequence, f"expected masked pane staging for {key}"
            assert sequence[0].slot == expected_slot

            dispatcher.dispatch(key)

            assert expected_slot in captured
            staged_glyphs, staged_colours = captured[expected_slot]
            expected_glyphs, expected_colours = _expected_macro_span(
                expected_slot, console
            )
            assert staged_glyphs == expected_glyphs
            assert staged_colours == expected_colours
            assert tuple(buffers.staged_screen) == expected_glyphs
            assert tuple(buffers.staged_colour) == expected_colours
            console.clear_masked_pane_staging(buffers)
            captured.clear()


def test_main_menu_macro_staging_sequences() -> None:
    module = MainMenuModule()
    kernel = SessionKernel(module=module)

    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)
    buffers = kernel.context.get_service("masked_pane_buffers")
    assert isinstance(buffers, MaskedPaneBuffers)

    with _capture_macro_staging(console, buffers) as captured:
        kernel.step(MainMenuEvent.ENTER)
        kernel.step(MainMenuEvent.SELECTION, "??")

    staging = console.masked_pane_staging_map
    expected_slots = {
        staging.slot(module.MENU_HEADER_MACRO),
        staging.slot(module.MENU_PROMPT_MACRO),
        staging.slot(module.INVALID_SELECTION_MACRO),
    }

    assert expected_slots <= captured.keys()

    for slot in expected_slots:
        expected = _expected_macro_span(slot, console)
        staged = captured[slot]
        assert staged[0] == expected[0]
        assert staged[1] == expected[1]


def test_sysop_options_macro_staging_sequences() -> None:
    module = SysopOptionsModule()
    kernel = SessionKernel(module=module)

    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)
    buffers = kernel.context.get_service("masked_pane_buffers")
    assert isinstance(buffers, MaskedPaneBuffers)

    with _capture_macro_staging(console, buffers) as captured:
        kernel.step(SysopOptionsEvent.ENTER)
        kernel.step(SysopOptionsEvent.COMMAND, "??")
        kernel.step(SysopOptionsEvent.COMMAND, "SY")
        kernel.step(SysopOptionsEvent.COMMAND, "A")

    staging = console.masked_pane_staging_map
    expected_slots = {
        staging.slot(module.MENU_HEADER_MACRO),
        staging.slot(module.MENU_PROMPT_MACRO),
        staging.slot(module.SAYING_PREAMBLE_MACRO),
        staging.slot(module.SAYING_OUTPUT_MACRO),
        staging.slot(module.INVALID_SELECTION_MACRO),
        staging.slot(module.ABORT_MACRO),
    }

    assert expected_slots <= captured.keys()

    for slot in expected_slots:
        expected = _expected_macro_span(slot, console)
        staged = captured[slot]
        assert staged[0] == expected[0]
        assert staged[1] == expected[1]


def test_file_transfers_macro_staging_sequences() -> None:
    module = FileTransfersModule()
    kernel = SessionKernel(module=module)

    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)
    buffers = kernel.context.get_service("masked_pane_buffers")
    assert isinstance(buffers, MaskedPaneBuffers)

    with _capture_macro_staging(console, buffers) as captured:
        kernel.step(FileTransferEvent.ENTER)
        kernel.step(FileTransferEvent.COMMAND, "??")

    staging = console.masked_pane_staging_map
    expected_slots = {
        staging.slot(module.MENU_HEADER_MACRO),
        staging.slot(module.MENU_PROMPT_MACRO),
        staging.slot(module.INVALID_SELECTION_MACRO),
    }

    assert expected_slots <= captured.keys()

    for slot in expected_slots:
        expected = _expected_macro_span(slot, console)
        staged = captured[slot]
        assert staged[0] == expected[0]
        assert staged[1] == expected[1]


def test_commit_masked_pane_staging_swaps_live_buffers() -> None:
    module = FileTransfersModule()
    kernel = SessionKernel(module=module)

    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)
    buffers = kernel.context.get_service("masked_pane_buffers")
    assert isinstance(buffers, MaskedPaneBuffers)

    kernel.step(FileTransferEvent.ENTER)

    staged_screen = tuple(buffers.staged_screen[: buffers.width])
    staged_colour = tuple(buffers.staged_colour[: buffers.width])

    console.commit_masked_pane_staging()

    live_screen = tuple(buffers.live_screen[: buffers.width])
    live_colour = tuple(buffers.live_colour[: buffers.width])
    assert live_screen == staged_screen
    assert live_colour == staged_colour

    screen_bytes, colour_bytes = console.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=buffers.width,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=buffers.width,
    )

    assert screen_bytes == bytes(staged_screen)
    assert colour_bytes == bytes(staged_colour)

    fill_colour = console.screen_colour & 0xFF
    assert tuple(buffers.staged_screen[: buffers.width]) == (0x20,) * buffers.width
    assert tuple(buffers.staged_colour[: buffers.width]) == (
        fill_colour,
    ) * buffers.width
    assert buffers.peek_pending_payload() is None


def test_outscn_commits_cached_payload_once_per_swap() -> None:
    module = FileTransfersModule()
    kernel = SessionKernel(module=module)

    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)
    buffers = kernel.context.get_service("masked_pane_buffers")
    assert isinstance(buffers, MaskedPaneBuffers)

    kernel.step(FileTransferEvent.ENTER)
    console.commit_masked_pane_staging()

    width = buffers.width
    screen_payload = bytes((0x71 + i) % 256 for i in range(width))
    colour_payload = bytes(((i + 5) % 16) for i in range(width))

    console.stage_masked_pane_overlay(screen_payload, colour_payload)

    pending = buffers.peek_pending_payload()
    assert pending is not None
    assert pending[0] == screen_payload
    assert pending[1] == colour_payload

    kernel.dispatcher.dispatch("&,50")

    screen_bytes, colour_bytes = console.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=width,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=width,
    )

    palette = console.screen.palette
    resolved_colour = bytes(
        _resolve_palette_colour(value, palette) for value in colour_payload
    )

    assert screen_bytes == screen_payload
    assert colour_bytes == resolved_colour
    assert tuple(buffers.live_screen[: width]) == tuple(screen_payload)
    assert tuple(buffers.live_colour[: width]) == tuple(colour_payload)

    fill_colour = console.screen_colour & 0xFF
    assert tuple(buffers.staged_screen[: width]) == (0x20,) * width
    assert tuple(buffers.staged_colour[: width]) == (fill_colour,) * width
    assert buffers.peek_pending_payload() is None

    live_snapshot = tuple(buffers.live_screen[: width])
    colour_snapshot = tuple(buffers.live_colour[: width])

    kernel.dispatcher.dispatch("&,50")

    assert tuple(buffers.live_screen[: width]) == live_snapshot
    assert tuple(buffers.live_colour[: width]) == colour_snapshot
    assert tuple(buffers.staged_screen[: width]) == (0x20,) * width
    assert tuple(buffers.staged_colour[: width]) == (fill_colour,) * width
    assert buffers.peek_pending_payload() is None


def test_basic_poke_commits_masked_pane_payload_via_ampersand() -> None:
    module = FileTransfersModule()
    kernel = SessionKernel(module=module)

    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)
    buffers = kernel.context.get_service("masked_pane_buffers")
    assert isinstance(buffers, MaskedPaneBuffers)

    kernel.step(FileTransferEvent.ENTER)
    console.commit_masked_pane_staging()

    assert buffers.dirty is False

    custom_screen = bytes((0x41 + i) % 256 for i in range(buffers.width))
    custom_colour = bytes(((i + 6) % 16) for i in range(buffers.width))

    console.poke_block(
        screen_address=ConsoleService._MASKED_STAGING_SCREEN_BASE,
        screen_bytes=custom_screen,
        colour_address=ConsoleService._MASKED_STAGING_COLOUR_BASE,
        colour_bytes=custom_colour,
    )

    assert bytes(buffers.staged_screen) == custom_screen
    assert bytes(buffers.staged_colour) == custom_colour
    assert buffers.dirty is True

    cached_screen = bytes(buffers.staged_screen)
    cached_colour = bytes(buffers.staged_colour)

    kernel.dispatcher.dispatch("&,50")

    assert bytes(buffers.live_screen) == cached_screen
    assert bytes(buffers.live_colour) == cached_colour

    screen_bytes, colour_bytes = console.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=buffers.width,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=buffers.width,
    )

    assert screen_bytes == cached_screen
    palette = console.screen.palette
    expected_colour = bytes(
        _resolve_palette_colour(value, palette) for value in cached_colour
    )
    assert colour_bytes == expected_colour

    fill_colour = console.screen_colour & 0xFF
    assert bytes(buffers.staged_screen) == bytes((0x20,) * buffers.width)
    assert bytes(buffers.staged_colour) == bytes((fill_colour,) * buffers.width)
    assert buffers.dirty is False
    assert buffers.peek_pending_payload() is None


