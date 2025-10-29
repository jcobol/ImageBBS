"""Focused tests for :mod:`imagebbs.runtime.editor_submission`."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace

from imagebbs.message_editor import EditorState
from imagebbs.runtime.editor_submission import EditorSubmissionHandler
from imagebbs.session_kernel import SessionState


@dataclass
class StubRunner:
    state: SessionState = SessionState.MESSAGE_EDITOR
    editor_context: SimpleNamespace = field(
        default_factory=lambda: SimpleNamespace(
            current_message="",
            draft_buffer=[],
            selected_message_id=None,
        )
    )
    _editor_state: EditorState = EditorState.POST_MESSAGE
    _requires_submission: bool = True
    abort_indicator_states: list[bool] = field(default_factory=list)
    submitted: list[tuple[str | None, list[str] | None]] = field(default_factory=list)
    aborted: bool = False

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


def test_collect_sync_sets_abort_indicator_state() -> None:
    runner = StubRunner()
    io = StubSyncIO(["Subject", "Body line", "/send"])
    handler = EditorSubmissionHandler(runner)

    handled = handler.collect_sync(io)

    assert handled is True
    assert runner.abort_indicator_states == [True, False]
    assert runner.submitted == [("Subject", ["Body line"])], runner.submitted
    assert runner.aborted is False


def test_collect_async_restores_abort_indicator_on_abort() -> None:
    context = SimpleNamespace(
        current_message="Existing",
        draft_buffer=["Existing body"],
        selected_message_id=1,
    )
    runner = StubRunner(editor_context=context, _editor_state=EditorState.EDIT_DRAFT)
    io = StubAsyncIO(["/abort"])
    handler = EditorSubmissionHandler(runner)

    handled = asyncio.run(handler.collect_async(io))

    assert handled is True
    assert runner.abort_indicator_states == [True, False]
    assert runner.submitted == []
    assert runner.aborted is True
