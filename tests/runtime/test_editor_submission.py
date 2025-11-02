"""Focused tests for :mod:`imagebbs.runtime.editor_submission`."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace

from imagebbs.message_editor import EditorState, MessageEditor
from imagebbs.runtime.editor_submission import (
    DEFAULT_EDITOR_ABORT_COMMAND,
    DEFAULT_EDITOR_SUBMIT_COMMAND,
    DOT_HELP_COMMAND,
    DOT_LINE_NUMBER_COMMAND,
    EditorSubmissionHandler,
)
from imagebbs.session_kernel import SessionState


@dataclass
class StubRunner:
    state: SessionState = SessionState.MESSAGE_EDITOR
    editor_context: SimpleNamespace = field(
        default_factory=lambda: SimpleNamespace(
            current_message="",
            draft_buffer=[],
            selected_message_id=None,
            modem_buffer=[],
            line_numbers_enabled=False,
        )
    )
    _editor_state: EditorState = EditorState.POST_MESSAGE
    _requires_submission: bool = True
    abort_indicator_states: list[bool] = field(default_factory=list)
    submitted: list[tuple[str | None, list[str] | None]] = field(default_factory=list)
    aborted: bool = False
    last_command: str | None = None

    def requires_editor_submission(self) -> bool:
        return self._requires_submission

    def get_editor_state(self) -> EditorState | None:
        return self._editor_state

    def submit_editor_draft(self, *, subject: str | None, lines: list[str] | None) -> None:
        self.submitted.append((subject, list(lines) if lines is not None else None))

    def abort_editor(self) -> None:
        self.aborted = True

    def set_abort_indicator_state(self, active: bool) -> None:
        self.abort_indicator_states.append(active)

    # Why: emulate inline editor commands so the handler can surface help and line-number toggles.
    def send_command(self, text: str) -> SessionState:
        self.last_command = text
        context = self.editor_context
        buffer = getattr(context, "modem_buffer", None)
        if buffer is None:
            buffer = []
            context.modem_buffer = buffer
        upper = (text or "").upper()
        if upper == DOT_HELP_COMMAND:
            buffer.append(MessageEditor.DOT_COMMAND_HELP_TEXT)
            buffer.append(MessageEditor.DOT_COMMAND_PROMPT)
        elif upper == DOT_LINE_NUMBER_COMMAND:
            current = getattr(context, "line_numbers_enabled", False)
            toggled = not current
            context.line_numbers_enabled = toggled
            status = " LINE NUMBERS ON.\r" if toggled else " LINE NUMBERS OFF.\r"
            buffer.append(status)
            buffer.append(MessageEditor.DOT_COMMAND_PROMPT)
        return self.state


class StubSyncIO:
    def __init__(self, inputs: list[str]) -> None:
        self._inputs = iter(inputs)
        self.lines: list[str] = []
        self.prompts: list[str] = []

    def write_line(self, text: str = "") -> None:
        self.lines.append(text)

    def write_prompt(self, prompt: str) -> None:
        self.prompts.append(prompt)

    def readline(self) -> str | None:
        return next(self._inputs, None)


class StubAsyncIO:
    def __init__(self, inputs: list[str]) -> None:
        self._inputs = iter(inputs)
        self.lines: list[str] = []
        self.prompts: list[str] = []

    async def write_line(self, text: str = "") -> None:
        self.lines.append(text)

    async def write_prompt(self, prompt: str) -> None:
        self.prompts.append(prompt)

    async def readline(self) -> str | None:
        return next(self._inputs, None)


# Why: confirm synchronous collection honours abort toggles while advertising dot commands.
def test_collect_sync_sets_abort_indicator_state() -> None:
    runner = StubRunner()
    io = StubSyncIO(["Subject", "Body line", DEFAULT_EDITOR_SUBMIT_COMMAND])
    handler = EditorSubmissionHandler(runner)

    handled = handler.collect_sync(io)

    assert handled is True
    assert runner.abort_indicator_states == [True, False]
    assert runner.submitted == [("Subject", ["Body line"])], runner.submitted
    assert runner.aborted is False
    assert (
        "Type .S to save, .A to abort, .H for help, .O toggles line numbers." in io.lines
    )


# Why: verify asynchronous collection restores abort indicators and still surfaces legacy alias hints.
def test_collect_async_restores_abort_indicator_on_abort() -> None:
    context = SimpleNamespace(
        current_message="Existing",
        draft_buffer=["Existing body"],
        selected_message_id=1,
        modem_buffer=[],
        line_numbers_enabled=False,
    )
    runner = StubRunner(editor_context=context, _editor_state=EditorState.EDIT_DRAFT)
    io = StubAsyncIO(["/cancel"])
    handler = EditorSubmissionHandler(runner, abort_command="/cancel")

    handled = asyncio.run(handler.collect_async(io))

    assert handled is True
    assert runner.abort_indicator_states == [True, False]
    assert runner.submitted == []
    assert runner.aborted is True
    assert (
        "Type .S to save, .A to abort, .H for help, .O toggles line numbers. (/cancel also aborts.)"
        in io.lines
    )


# Why: ensure configured command aliases continue to function alongside the legacy dot vocabulary.
def test_collect_sync_uses_custom_commands() -> None:
    runner = StubRunner()
    io = StubSyncIO(["Subject", "Body line", "/save"])
    handler = EditorSubmissionHandler(
        runner, submit_command="/save", abort_command="/cancel"
    )

    handled = handler.collect_sync(io)

    assert handled is True
    assert runner.submitted == [("Subject", ["Body line"])], runner.submitted
    assert (
        "Type .S to save, .A to abort, .H for help, .O toggles line numbers. (/save also saves, /cancel also aborts.)"
        in io.lines
    )


# Why: surface inline help requests and confirm the handler loops re-prompt for the subject line.
def test_collect_sync_handles_help_command() -> None:
    runner = StubRunner()
    io = StubSyncIO([DOT_HELP_COMMAND, "Subject", "Line", DEFAULT_EDITOR_SUBMIT_COMMAND])
    handler = EditorSubmissionHandler(runner)

    handled = handler.collect_sync(io)

    assert handled is True
    assert runner.last_command == DOT_HELP_COMMAND
    assert any(".A aborts without saving" in line for line in io.lines)
    assert io.prompts.count("Subject: ") == 2


# Why: propagate line-number toggles from the handler into the runner's context.
def test_collect_sync_toggles_line_numbers() -> None:
    runner = StubRunner()
    io = StubSyncIO(["Subject", DOT_LINE_NUMBER_COMMAND, "Body", DEFAULT_EDITOR_SUBMIT_COMMAND])
    handler = EditorSubmissionHandler(runner)

    handled = handler.collect_sync(io)

    assert handled is True
    assert runner.last_command == DOT_LINE_NUMBER_COMMAND
    assert runner.editor_context.line_numbers_enabled is True
    assert any("LINE NUMBERS ON." in line for line in io.lines)
