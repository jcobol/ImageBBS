from __future__ import annotations

from pathlib import Path
from typing import Iterable

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.ampersand_dispatcher import AmpersandDispatcher
from scripts.prototypes.device_context import ConsoleService, bootstrap_device_context
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


def test_chkflags_updates_pause_indicator() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    pause_address = 0x041E
    colour_address = 0xD81E
    before = console_service.device.screen.peek_screen_address(pause_address)
    before_colour = console_service.device.screen.peek_colour_address(colour_address)

    dispatcher.dispatch(
        "&,52,16,1", payload={"registry": registry, "services": registry.services}
    )

    after = console_service.device.screen.peek_screen_address(pause_address)
    colour = console_service.device.screen.peek_colour_address(colour_address)
    assert after != before
    assert after == 0xD0
    assert colour != before_colour


def test_read0_appends_session_message() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    store = MessageStore()
    registry.register_service("message_store", store)

    session = SessionContext(board_id="board", user_id="alice")
    session.draft_buffer = ["Line one", "Line two"]
    session.command_buffer = "Greetings"

    result = dispatcher.dispatch(
        "&,3",
        payload={
            "registry": registry,
            "services": registry.services,
            "session": session,
        },
    )

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
    result = dispatcher.dispatch(
        "&,8",
        payload={
            "registry": registry,
            "services": registry.services,
            "fallback_text": fallback,
        },
    )

    assert result.rendered_text == fallback
