from __future__ import annotations

from pathlib import Path

import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.ampersand_dispatcher import (
    AmpersandDispatchContext,
    AmpersandDispatcher,
)
from scripts.prototypes.device_context import (
    ConsoleService,
    DriveAssignment,
    FilesystemDriveLocator,
    bootstrap_device_context,
)
from scripts.prototypes.message_editor import SessionContext
from scripts.prototypes.runtime.ampersand_overrides import BUILTIN_AMPERSAND_OVERRIDES
from scripts.prototypes.runtime.message_store import MessageStore


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
