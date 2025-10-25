"""Focused tests for the native :mod:`imagebbs.runtime.session_runner`."""

from __future__ import annotations

import pytest

from imagebbs.runtime.session_runner import SessionRunner
from imagebbs.session_kernel import SessionState
from imagebbs.message_editor import EditorState


@pytest.fixture()
def runner() -> SessionRunner:
    session_runner = SessionRunner()
    session_runner.read_output()  # flush bootstrap output for deterministic tests
    return session_runner


def test_send_command_transitions_between_modules(runner: SessionRunner) -> None:
    state = runner.send_command("MF")
    assert state is SessionState.MESSAGE_EDITOR
    assert runner.get_editor_state() is EditorState.MAIN_MENU

    state = runner.send_command("Q")
    assert state is SessionState.MAIN_MENU


class StubIndicatorController:
    def __init__(self) -> None:
        self.pause_states: list[bool] = []
        self.abort_states: list[bool] = []

    def set_pause(self, active: bool) -> None:
        self.pause_states.append(active)

    def set_abort(self, active: bool) -> None:
        self.abort_states.append(active)


def test_indicator_controller_forwarding(runner: SessionRunner) -> None:
    controller = StubIndicatorController()
    runner.set_indicator_controller(controller)

    runner.set_pause_indicator_state(True)
    runner.set_pause_indicator_state(False)
    runner.set_abort_indicator_state(True)

    assert controller.pause_states == [True, False]
    assert controller.abort_states == [True]


def test_submit_editor_draft_populates_context(runner: SessionRunner) -> None:
    state = runner.send_command("MF")
    assert state is SessionState.MESSAGE_EDITOR

    state = runner.send_command("P")
    assert state is SessionState.MESSAGE_EDITOR

    editor = runner.kernel._modules[SessionState.MESSAGE_EDITOR]
    assert editor.state is EditorState.POST_MESSAGE

    result_state = runner.submit_editor_draft(
        subject="My Subject", lines=["Body line one", "Body line two"]
    )
    assert result_state is SessionState.MESSAGE_EDITOR

    record = runner.message_store.fetch(runner.board_id, 1)
    assert record.subject == "My Subject"
    assert record.lines == ("Body line one", "Body line two")
