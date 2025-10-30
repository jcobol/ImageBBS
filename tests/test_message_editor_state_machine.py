from __future__ import annotations

from types import SimpleNamespace
from typing import Iterable, List, Mapping, MutableMapping, Tuple

from imagebbs.ampersand_registry import AmpersandResult
from imagebbs.message_editor import EditorState, Event, MessageEditor, SessionContext
from imagebbs.runtime.message_store import MessageStore


class StubAmpersandRegistry:
    """Registry stub that records dispatched macro indices."""

    def __init__(self) -> None:
        self.calls: List[Tuple[int, object]] = []
        self._services: MutableMapping[str, object] = {}
        self.defaults = SimpleNamespace(macros_by_slot={})

    @property
    def services(self) -> Mapping[str, object]:
        return self._services

    def dispatch(
        self, flag_index: int, context: object, *, use_default: bool = False
    ) -> AmpersandResult:
        self.calls.append((flag_index, context))
        return AmpersandResult(
            flag_index=flag_index,
            slot=flag_index,
            handler_address=flag_index,
            flag_records=tuple(),
            flag_directory_block=tuple(),
            flag_directory_tail=tuple(),
            flag_directory_text="",
            context=context,
            rendered_text=f"MACRO:{flag_index}",
            services=self.services,
        )

    def register_service(self, name: str, service: object) -> None:
        self._services[name] = service


def _bootstrap_editor() -> tuple[MessageEditor, SessionContext, StubAmpersandRegistry, MessageStore]:
    registry = StubAmpersandRegistry()
    store = MessageStore()
    editor = MessageEditor(registry=registry, store=store)
    session = SessionContext(
        board_id="mb1",
        user_id="sysop",
        store=store,
        services=registry.services,
    )
    return editor, session, registry, store


def _advance_to_main_menu(editor: MessageEditor, session: SessionContext) -> None:
    editor.dispatch(Event.ENTER, session)
    editor.dispatch(Event.ENTER, session)


def test_intro_uses_fallback_text_when_handler_omits_rendered_text() -> None:
    class NullRenderRegistry(StubAmpersandRegistry):
        def dispatch(
            self, flag_index: int, context: object, *, use_default: bool = False
        ) -> AmpersandResult:
            self.calls.append((flag_index, context))
            return AmpersandResult(
                flag_index=flag_index,
                slot=flag_index,
                handler_address=flag_index,
                flag_records=tuple(),
                flag_directory_block=tuple(),
                flag_directory_tail=tuple(),
                flag_directory_text="",
                context=context,
                rendered_text=None,
                services=self.services,
            )

    registry = NullRenderRegistry()
    editor = MessageEditor(registry=registry)
    session = SessionContext(board_id="mb1", user_id="sysop", services=registry.services)

    editor.dispatch(Event.ENTER, session)

    assert session.modem_buffer[-1].startswith("\r*** IMAGE MESSAGE EDITOR")


def test_read_flow_fetches_message_and_emits_macro() -> None:
    editor, session, registry, store = _bootstrap_editor()
    store.append(board_id="mb1", subject="Subject", author_handle="SYSOP", lines=["Line 1", "Line 2"])

    _advance_to_main_menu(editor, session)

    session.command_buffer = "R"
    state = editor.dispatch(Event.COMMAND_SELECTED, session)
    assert state is EditorState.READ_MESSAGES

    session.modem_buffer.clear()
    editor.dispatch(Event.ENTER, session)

    assert registry.calls[-1][0] == editor.READ_MESSAGE_MACRO_INDEX
    assert session.modem_buffer[0] == f"MACRO:{editor.READ_MESSAGE_MACRO_INDEX}"
    assert session.modem_buffer[1].startswith("#001 Subject")

    session.modem_buffer.clear()
    session.command_buffer = "1"
    editor.dispatch(Event.MESSAGE_SELECTED, session)

    assert session.selected_message_id == 1
    assert session.modem_buffer[0] == f"MACRO:{editor.READ_MESSAGE_MACRO_INDEX}"
    assert session.modem_buffer[1:] == ["Line 1\r", "Line 2\r"]


def test_read_flow_quit_returns_to_main_menu() -> None:
    editor, session, registry, store = _bootstrap_editor()
    store.append(board_id="mb1", subject="Subject", author_handle="SYSOP", lines=["Body"])

    _advance_to_main_menu(editor, session)

    session.command_buffer = "R"
    editor.dispatch(Event.COMMAND_SELECTED, session)
    editor.dispatch(Event.ENTER, session)

    session.modem_buffer.clear()
    session.command_buffer = "Q"
    state = editor.dispatch(Event.MESSAGE_SELECTED, session)

    assert state is EditorState.MAIN_MENU
    assert session.selected_message_id is None
    assert registry.calls[-1][0] == editor.MAIN_MENU_MACRO_INDEX
    assert session.modem_buffer == [f"MACRO:{editor.MAIN_MENU_MACRO_INDEX}"]
    assert all("?INVALID MESSAGE SELECTION" not in line for line in session.modem_buffer)


def test_post_flow_appends_message_and_records_macro() -> None:
    editor, session, registry, store = _bootstrap_editor()

    _advance_to_main_menu(editor, session)

    session.command_buffer = "P"
    state = editor.dispatch(Event.COMMAND_SELECTED, session)
    assert state is EditorState.POST_MESSAGE

    session.modem_buffer.clear()
    editor.dispatch(Event.ENTER, session)

    session.command_buffer = "My Subject"
    session.draft_buffer = ["New post line"]
    session.modem_buffer.clear()
    state = editor.dispatch(Event.DRAFT_SUBMITTED, session)

    assert state is EditorState.MAIN_MENU
    assert session.selected_message_id == 1
    assert session.modem_buffer == [f"MACRO:{editor.POST_MESSAGE_MACRO_INDEX}"]

    stored = store.fetch("mb1", 1)
    assert stored.subject == "My Subject"
    assert stored.lines == ("New post line",)


def test_edit_flow_updates_existing_message() -> None:
    editor, session, registry, store = _bootstrap_editor()
    original = store.append(
        board_id="mb1",
        subject="Subject",
        author_handle="SYSOP",
        lines=["Original line"],
    )

    _advance_to_main_menu(editor, session)

    session.command_buffer = "E"
    state = editor.dispatch(Event.COMMAND_SELECTED, session)
    assert state is EditorState.EDIT_DRAFT

    session.command_buffer = str(original.message_id)
    session.modem_buffer.clear()
    editor.dispatch(Event.ENTER, session)

    assert session.draft_buffer == ["Original line"]
    assert session.selected_message_id == original.message_id
    assert session.modem_buffer == [f"MACRO:{editor.EDIT_DRAFT_MACRO_INDEX}"]

    session.draft_buffer = ["Updated text"]
    session.modem_buffer.clear()
    state = editor.dispatch(Event.DRAFT_SUBMITTED, session)

    assert state is EditorState.MAIN_MENU
    assert session.modem_buffer == [f"MACRO:{editor.EDIT_DRAFT_MACRO_INDEX}"]

    updated = store.fetch("mb1", original.message_id)
    assert updated.lines == ("Updated text",)
    assert session.drafts[original.message_id] == ["Updated text"]

