import json
from pathlib import Path

import pytest

from imagebbs import SessionRunner, SessionState
from imagebbs.message_editor import EditorState, MessageEditor
from imagebbs.runtime.file_transfers import FileTransfersModule
from imagebbs.runtime.main_menu import MainMenuModule
from imagebbs.runtime.message_store import MessageStore
from imagebbs.runtime.sysop_options import SysopOptionsModule


@pytest.fixture()
def runner() -> SessionRunner:
    return SessionRunner()


class DummyIndicatorController:
    def __init__(self) -> None:
        # Why: record controller interactions so the tests can assert runtime wiring behaviour.
        self.sync_invocations = 0
        self.pause_updates: list[bool] = []
        self.abort_updates: list[bool] = []

    # Why: surface the synchronisation hook expected by SessionRunner during indicator registration.
    def sync_from_console(self) -> None:
        self.sync_invocations += 1

    # Why: capture pause toggles forwarded by the session runner for assertions.
    def set_pause(self, active: bool) -> None:
        self.pause_updates.append(active)

    # Why: capture abort toggles forwarded by the session runner for assertions.
    def set_abort(self, active: bool) -> None:
        self.abort_updates.append(active)


# Why: validate that indicator controllers are synchronised, exposed via the kernel context, and withdrawn from services when cleared.
def test_session_runner_registers_indicator_controller(runner: SessionRunner) -> None:
    controller = DummyIndicatorController()

    runner.set_indicator_controller(controller)

    assert controller.sync_invocations == 1
    context = runner.kernel.context
    assert context.get_service("indicator_controller") is controller

    runner.set_pause_indicator_state(True)
    runner.set_abort_indicator_state(True)

    assert controller.pause_updates == [True]
    assert controller.abort_updates == [True]

    runner.set_indicator_controller(controller)

    assert controller.sync_invocations == 2
    assert context.get_service("indicator_controller") is controller

    runner.set_pause_indicator_state(False)
    runner.set_abort_indicator_state(False)

    assert controller.pause_updates == [True, False]
    assert controller.abort_updates == [True, False]

    runner.set_indicator_controller(None)

    service_registry = context.service_registry
    assert "indicator_controller" not in service_registry
    assert "console" in service_registry


def test_session_runner_initialises_and_emits_enter(runner: SessionRunner) -> None:
    kernel = runner.kernel
    assert runner.state is SessionState.MAIN_MENU

    main_menu = kernel._modules[SessionState.MAIN_MENU]
    assert isinstance(main_menu, MainMenuModule)
    assert main_menu.rendered_slots[:4] == [
        main_menu.MENU_HEADER_SLOT,
        main_menu.MENU_PROMPT_SLOT,
        main_menu.MENU_HEADER_SLOT,
        main_menu.MENU_PROMPT_SLOT,
    ]

    flushed = runner.read_output()
    assert isinstance(flushed, str)
    assert runner.read_output() == ""


def test_session_runner_transitions_and_replays_enter(runner: SessionRunner) -> None:
    kernel = runner.kernel
    main_menu = kernel._modules[SessionState.MAIN_MENU]
    file_transfers = kernel._modules[SessionState.FILE_TRANSFERS]
    sysop_options = kernel._modules[SessionState.SYSOP_OPTIONS]

    runner.read_output()  # discard bootstrap output

    state = runner.send_command("UD")
    assert state is SessionState.FILE_TRANSFERS
    assert isinstance(file_transfers, FileTransfersModule)
    assert file_transfers.rendered_slots[:4] == [
        file_transfers.MENU_HEADER_SLOT,
        file_transfers.MENU_PROMPT_SLOT,
        file_transfers.MENU_HEADER_SLOT,
        file_transfers.MENU_PROMPT_SLOT,
    ]

    state = runner.send_command("Q")
    assert state is SessionState.MAIN_MENU
    assert main_menu.rendered_slots[-2:] == [
        main_menu.MENU_HEADER_SLOT,
        main_menu.MENU_PROMPT_SLOT,
    ]

    state = runner.send_command("SY")
    assert state is SessionState.SYSOP_OPTIONS
    assert isinstance(sysop_options, SysopOptionsModule)
    assert sysop_options.rendered_slots[:4] == [
        sysop_options.MENU_HEADER_SLOT,
        sysop_options.MENU_PROMPT_SLOT,
        sysop_options.MENU_HEADER_SLOT,
        sysop_options.MENU_PROMPT_SLOT,
    ]

    state = runner.send_command("Q")
    assert state is SessionState.MAIN_MENU
    assert main_menu.rendered_slots[-2:] == [
        main_menu.MENU_HEADER_SLOT,
        main_menu.MENU_PROMPT_SLOT,
    ]


def test_session_runner_reuses_editor_context(runner: SessionRunner) -> None:
    context = runner.editor_context

    state = runner.send_command("MF")
    assert state is SessionState.MESSAGE_EDITOR
    assert len(context.modem_buffer) >= 1
    assert context.modem_buffer[-1]

    before = len(context.modem_buffer)
    state = runner.send_command("Q")
    assert state is SessionState.MAIN_MENU

    state = runner.send_command("MF")
    assert state is SessionState.MESSAGE_EDITOR
    assert runner.editor_context is context
    assert len(context.modem_buffer) >= before + 1
    assert context.modem_buffer[-1]


def _enter_message_editor(runner: SessionRunner) -> SessionState:
    runner.read_output()
    state = runner.send_command("MF")
    assert state is SessionState.MESSAGE_EDITOR
    return state


def test_session_runner_lists_and_reads_messages(runner: SessionRunner) -> None:
    store = runner.message_store
    store.append(
        board_id=runner.board_id,
        subject="Subject",
        author_handle="SYSOP",
        lines=["Line 1", "Line 2"],
    )

    _enter_message_editor(runner)
    context = runner.editor_context
    context.modem_buffer.clear()

    state = runner.send_command("R")
    assert state is SessionState.MESSAGE_EDITOR
    assert context.modem_buffer
    assert any("#001" in output for output in context.modem_buffer)

    context.modem_buffer.clear()
    state = runner.send_command("1")
    assert state is SessionState.MESSAGE_EDITOR
    assert context.selected_message_id == 1
    assert any("Line 1" in output for output in context.modem_buffer)
    assert any("Line 2" in output for output in context.modem_buffer)


def test_session_runner_posts_message(runner: SessionRunner) -> None:
    _enter_message_editor(runner)
    context = runner.editor_context
    context.modem_buffer.clear()

    state = runner.send_command("P")
    assert state is SessionState.MESSAGE_EDITOR
    assert context.modem_buffer
    assert context.draft_buffer == []

    context.modem_buffer.clear()
    submission = "My Subject\nNew post line"
    state = runner.send_command(submission)
    assert state is SessionState.MESSAGE_EDITOR
    assert context.selected_message_id == 1
    assert context.modem_buffer

    record = runner.message_store.fetch(runner.board_id, 1)
    assert record.subject == "My Subject"
    assert record.lines == ("New post line",)


def test_session_runner_edits_existing_message(runner: SessionRunner) -> None:
    original = runner.message_store.append(
        board_id=runner.board_id,
        subject="Subject",
        author_handle="SYSOP",
        lines=["Original line"],
    )

    _enter_message_editor(runner)
    context = runner.editor_context
    context.modem_buffer.clear()

    state = runner.send_command("E")
    assert state is SessionState.MESSAGE_EDITOR
    editor = runner.kernel._modules[SessionState.MESSAGE_EDITOR]
    assert isinstance(editor, MessageEditor)
    assert editor.state is EditorState.EDIT_DRAFT

    context.modem_buffer.clear()
    state = runner.send_command(str(original.message_id))
    assert state is SessionState.MESSAGE_EDITOR
    editor = runner.kernel._modules[SessionState.MESSAGE_EDITOR]
    assert isinstance(editor, MessageEditor)
    assert editor.state is EditorState.EDIT_DRAFT
    assert context.selected_message_id == original.message_id
    assert context.draft_buffer == ["Original line"]
    assert context.modem_buffer

    context.modem_buffer.clear()
    state = runner.send_command("Updated text")
    assert state is SessionState.MESSAGE_EDITOR
    assert context.modem_buffer

    updated = runner.message_store.fetch(runner.board_id, original.message_id)
    assert updated.lines == ("Updated text",)


def test_session_runner_persists_message_store(tmp_path: Path) -> None:
    path = tmp_path / "messages.json"
    runner = SessionRunner(message_store=MessageStore(), message_store_path=path)

    runner.read_output()
    state = runner.send_command("MF")
    assert state is SessionState.MESSAGE_EDITOR

    state = runner.send_command("P")
    assert state is SessionState.MESSAGE_EDITOR

    state = runner.submit_editor_draft(subject="Subject", lines=["Line 1"])
    assert state is SessionState.MESSAGE_EDITOR
    assert path.exists()

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert payload["records"]
    assert payload["records"][0]["subject"] == "Subject"
    assert payload["records"][0]["lines"] == ["Line 1"]

    context = runner.editor_context
    context.reset_selection()

    state = runner.send_command("E")
    assert state is SessionState.MESSAGE_EDITOR
    state = runner.send_command("1")
    assert state is SessionState.MESSAGE_EDITOR
    state = runner.submit_editor_draft(lines=["Edited line"])
    assert state is SessionState.MESSAGE_EDITOR

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["records"]
    assert len(payload["records"]) == 1
    assert payload["records"][0]["lines"] == ["Edited line"]
