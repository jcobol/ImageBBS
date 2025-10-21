from __future__ import annotations

from pathlib import Path

import pytest

from imagebbs.ampersand_dispatcher import (
    AmpersandDispatchContext,
    AmpersandDispatcher,
)
from imagebbs.device_context import (
    ConsoleService,
    DriveAssignment,
    FilesystemDriveLocator,
    MaskedPaneBuffers,
    bootstrap_device_context,
)
from imagebbs.message_editor import SessionContext
from imagebbs.runtime.ampersand_overrides import BUILTIN_AMPERSAND_OVERRIDES
from imagebbs.runtime.message_store import MessageStore


def _resolve_palette_colour(value: int, palette: tuple[int, ...], *, default_index: int = 0) -> int:
    resolved = int(value) & 0xFF
    if resolved in palette:
        return resolved
    if 0 <= resolved < len(palette):
        return palette[resolved]
    if not 0 <= default_index < len(palette):
        raise ValueError("default_index must reference a palette entry")
    return palette[default_index]


def _build_dispatcher() -> AmpersandDispatcher:
    context = bootstrap_device_context(
        assignments=(), ampersand_overrides=BUILTIN_AMPERSAND_OVERRIDES
    )
    dispatcher = context.get_service("ampersand")
    assert isinstance(dispatcher, AmpersandDispatcher)
    return dispatcher


@pytest.fixture()
def dispatcher_with_temp_drive(tmp_path: Path) -> AmpersandDispatcher:
    drive_root = tmp_path / "drive8"
    drive_root.mkdir()
    (drive_root / "FIRST.SEQ").write_text("hello", encoding="latin-1")
    (drive_root / "SECOND.SEQ").write_text("world", encoding="latin-1")

    assignment = DriveAssignment(
        slot=8, locator=FilesystemDriveLocator(path=drive_root)
    )
    context = bootstrap_device_context(
        assignments=(assignment,),
        ampersand_overrides=BUILTIN_AMPERSAND_OVERRIDES,
    )
    dispatcher = context.get_service("ampersand")
    assert isinstance(dispatcher, AmpersandDispatcher)
    return dispatcher


def test_chkflags_updates_pause_indicator() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    pause_address = 0x041E
    colour_address = 0xD81E
    before = console_service.device.screen.peek_screen_address(pause_address)
    before_colour = console_service.device.screen.peek_colour_address(colour_address)

    dispatcher.dispatch("&,52,16,1")

    after = console_service.device.screen.peek_screen_address(pause_address)
    colour = console_service.device.screen.peek_colour_address(colour_address)
    assert after != before
    assert after == 0xD0
    assert colour != before_colour


@pytest.mark.parametrize(
    "operation,prepare_spinner,prepare_carrier",
    [
        (
            0,
            lambda console: console.set_spinner_glyph(0xB0),
            lambda console: console.set_carrier_indicator(
                leading_cell=0xA0, indicator_cell=0xFA
            ),
        ),
        (
            1,
            lambda console: console.set_spinner_glyph(0x20),
            lambda console: console.set_carrier_indicator(
                leading_cell=0x20, indicator_cell=0x20
            ),
        ),
        (
            2,
            lambda console: console.set_spinner_glyph(0x20),
            lambda console: console.set_carrier_indicator(
                leading_cell=0x20, indicator_cell=0x20
            ),
        ),
    ],
)
def test_chkflags_updates_spinner_and_carrier(
    operation: int,
    prepare_spinner,
    prepare_carrier,
) -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    prepare_spinner(console_service)
    spinner_before = console_service.device.screen.peek_screen_address(0x049C)
    dispatcher.dispatch(f"&,52,2,{operation}")
    spinner_after = console_service.device.screen.peek_screen_address(0x049C)
    assert spinner_after != spinner_before

    prepare_carrier(console_service)
    leading_before = console_service.device.screen.peek_screen_address(0x0400)
    indicator_before = console_service.device.screen.peek_screen_address(0x0427)
    dispatcher.dispatch(f"&,52,4,{operation}")
    leading_after = console_service.device.screen.peek_screen_address(0x0400)
    indicator_after = console_service.device.screen.peek_screen_address(0x0427)
    assert leading_after != leading_before
    assert indicator_after != indicator_before


def test_read0_appends_session_message() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    store = MessageStore()
    registry.register_service("message_store", store)

    session = SessionContext(board_id="board", user_id="alice")
    session.draft_buffer = ["Line one", "Line two"]
    session.command_buffer = "Greetings"

    result = dispatcher.dispatch("&,3", payload={"session": session})

    summaries = store.list("board")
    assert len(summaries) == 1
    record = store.fetch("board", summaries[0].message_id)
    assert record.subject == "Greetings"
    assert record.lines == tuple(session.drafts.get(record.message_id, []))
    assert result.context["record"] is record
    assert session.selected_message_id == record.message_id


def test_dskdir_uses_payload_fallback_text() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry

    fallback = "DIRECTORY\r"
    result = dispatcher.dispatch("&,8", payload={"fallback_text": fallback})

    assert result.rendered_text == fallback


def test_dskdir_renders_drive_listing_when_no_fallback(
    dispatcher_with_temp_drive: AmpersandDispatcher,
) -> None:
    result = dispatcher_with_temp_drive.dispatch("&,8")

    assert result.rendered_text is not None
    assert "FIRST.SEQ" in result.rendered_text
    assert "SECOND.SEQ" in result.rendered_text


def test_dispatcher_injects_registry_and_services_into_payload() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    pause_address = 0x041E
    colour_address = 0xD81E
    before = console_service.device.screen.peek_screen_address(pause_address)
    before_colour = console_service.device.screen.peek_colour_address(colour_address)

    dispatcher.dispatch("&,52,16,1")

    after = console_service.device.screen.peek_screen_address(pause_address)
    colour = console_service.device.screen.peek_colour_address(colour_address)
    assert after != before
    assert colour != before_colour

    store = MessageStore()
    registry.register_service("message_store", store)

    session = SessionContext(board_id="board", user_id="bob")
    session.draft_buffer = ["Payload"]
    session.command_buffer = "Injected"

    dispatcher.dispatch("&,3", payload={"session": session})

    summaries = store.list("board")
    assert len(summaries) == 1
    record = store.fetch("board", summaries[0].message_id)
    assert record.subject == "Injected"
    assert session.selected_message_id == record.message_id

    result = dispatcher.dispatch("&,8")

    assert isinstance(result.context, AmpersandDispatchContext)
    payload = result.context.payload
    assert isinstance(payload, dict)
    assert payload["registry"] is registry
    assert payload["services"] is registry.services
    assert result.services["console"] is console_service


def test_outscn_commits_masked_pane_staging_when_data_present() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    buffers = registry.services["masked_pane_buffers"]
    assert isinstance(buffers, MaskedPaneBuffers)

    screen_payload = bytes((0x60 + i) % 256 for i in range(buffers.width))
    colour_payload = bytes(((i + 3) % 16) for i in range(buffers.width))

    console_service.poke_block(
        screen_address=ConsoleService._MASKED_STAGING_SCREEN_BASE,
        screen_bytes=screen_payload,
        colour_address=ConsoleService._MASKED_STAGING_COLOUR_BASE,
        colour_bytes=colour_payload,
    )

    assert buffers.dirty is True

    dispatcher.dispatch("&,50")

    assert bytes(buffers.live_screen) == screen_payload
    assert bytes(buffers.live_colour) == colour_payload

    fill_colour = console_service.screen_colour & 0xFF
    assert bytes(buffers.staged_screen) == bytes((0x20,) * buffers.width)
    assert bytes(buffers.staged_colour) == bytes((fill_colour,) * buffers.width)

    screen_bytes, colour_bytes = console_service.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=buffers.width,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=buffers.width,
    )

    assert screen_bytes == screen_payload
    palette = console_service.screen.palette
    expected_colour = bytes(
        _resolve_palette_colour(value, palette) for value in colour_payload
    )
    assert colour_bytes == expected_colour
    assert buffers.dirty is False


def test_outscn_ignores_empty_masked_pane_staging() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    buffers = registry.services["masked_pane_buffers"]
    assert isinstance(buffers, MaskedPaneBuffers)

    fill_colour = console_service.screen_colour & 0xFF
    live_screen_payload = bytes((0x33,) * buffers.width)
    live_colour_payload = bytes((0x04,) * buffers.width)

    buffers.live_screen[:] = live_screen_payload
    buffers.live_colour[:] = live_colour_payload
    buffers.clear_staging(glyph=0x20, colour=fill_colour)

    console_service.poke_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_bytes=live_screen_payload,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_bytes=live_colour_payload,
    )

    before_screen, before_colour = console_service.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=buffers.width,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=buffers.width,
    )

    assert buffers.dirty is False

    dispatcher.dispatch("&,50")

    assert bytes(buffers.live_screen) == live_screen_payload
    assert bytes(buffers.live_colour) == live_colour_payload
    assert bytes(buffers.staged_screen) == bytes((0x20,) * buffers.width)
    assert bytes(buffers.staged_colour) == bytes((fill_colour,) * buffers.width)
    assert buffers.dirty is False

    after_screen, after_colour = console_service.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=buffers.width,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=buffers.width,
    )

    assert after_screen == before_screen
    assert after_colour == before_colour
