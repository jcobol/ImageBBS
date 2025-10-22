"""Utilities for collecting message editor submissions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generator, Protocol

from ..message_editor import EditorState
from ..session_kernel import SessionState
from .session_runner import SessionRunner

_EDITOR_ABORT_COMMAND = "/abort"
_EDITOR_SUBMIT_COMMAND = "/send"


class SyncEditorIO(Protocol):
    """Minimal synchronous stream interface used by the editor handler."""

    def write_line(self, text: str = "") -> None:
        """Emit ``text`` followed by a newline."""

    def write_prompt(self, prompt: str) -> None:
        """Emit ``prompt`` without appending a newline."""

    def readline(self) -> str | None:
        """Return the next line of input, or ``None`` on EOF."""


class AsyncEditorIO(Protocol):
    """Asynchronous counterpart to :class:`SyncEditorIO`."""

    async def write_line(self, text: str = "") -> None:
        """Emit ``text`` followed by a newline."""

    async def write_prompt(self, prompt: str) -> None:
        """Emit ``prompt`` without appending a newline."""

    async def readline(self) -> str | None:
        """Return the next line of input, or ``None`` on EOF."""


@dataclass(frozen=True)
class _WriteLine:
    text: str


@dataclass(frozen=True)
class _WritePrompt:
    text: str


class _ReadLine:
    pass


@dataclass(frozen=True)
class _SubmissionResult:
    action: str
    subject: str | None
    lines: list[str] | None


class EditorSubmissionHandler:
    """Drive the message editor submission flow for a :class:`SessionRunner`."""

    def __init__(
        self,
        runner: SessionRunner,
        *,
        submit_command: str = _EDITOR_SUBMIT_COMMAND,
        abort_command: str = _EDITOR_ABORT_COMMAND,
    ) -> None:
        self._runner = runner
        self._submit_command = submit_command
        self._abort_command = abort_command

    def should_handle(self) -> bool:
        """Return ``True`` if the runner requires a submission cycle."""

        runner = self._runner
        if runner.state is not SessionState.MESSAGE_EDITOR:
            return False
        return runner.requires_editor_submission()

    def collect_sync(self, io: SyncEditorIO) -> bool:
        """Collect an editor submission using synchronous streams."""

        if not self.should_handle():
            return False
        result = self._drive_flow(self._flow(), io)
        self._apply_result(result)
        return True

    async def collect_async(self, io: AsyncEditorIO) -> bool:
        """Collect an editor submission using asynchronous streams."""

        if not self.should_handle():
            return False
        result = await self._drive_flow_async(self._flow(), io)
        self._apply_result(result)
        return True

    def _flow(self) -> Generator[_WriteLine | _WritePrompt | _ReadLine, str | None, _SubmissionResult]:
        runner = self._runner
        context = runner.editor_context
        if context is None:
            raise RuntimeError("editor context is unavailable")
        editor_state = runner.get_editor_state()
        existing_subject = context.current_message if editor_state is not None else ""
        existing_lines = list(context.draft_buffer)

        yield _WriteLine("")
        yield _WriteLine("-- Message Editor --")
        yield _WriteLine(
            f"Type {self._submit_command} to save or {self._abort_command} to cancel."
        )

        subject_text = existing_subject
        if editor_state is EditorState.POST_MESSAGE:
            prompt = "Subject"
            if existing_subject:
                prompt += f" [{existing_subject}]"
            prompt += ": "
            yield _WritePrompt(prompt)
            subject_line = yield _ReadLine()
            if subject_line is None:
                return _SubmissionResult("abort", None, None)
            if subject_line.strip().lower() == self._abort_command:
                return _SubmissionResult("abort", None, None)
            if subject_line:
                subject_text = subject_line

        if editor_state is EditorState.EDIT_DRAFT and existing_lines:
            yield _WriteLine("Current message lines:")
            for line in existing_lines:
                yield _WriteLine(f"> {line}")

        yield _WriteLine("Enter message body.")
        lines: list[str] = []
        while True:
            yield _WritePrompt("> ")
            line = yield _ReadLine()
            if line is None:
                return _SubmissionResult("abort", None, None)
            command = line.strip().lower()
            if command == self._abort_command:
                return _SubmissionResult("abort", None, None)
            if command == self._submit_command:
                final_lines = list(lines) if lines else list(existing_lines)
                subject: str | None
                if editor_state is EditorState.POST_MESSAGE:
                    subject = subject_text
                else:
                    subject = None
                return _SubmissionResult("submit", subject, final_lines)
            lines.append(line)

    def _apply_result(self, result: _SubmissionResult) -> None:
        runner = self._runner
        if result.action == "submit":
            assert result.lines is not None
            runner.submit_editor_draft(subject=result.subject, lines=result.lines)
            return
        runner.abort_editor()

    @staticmethod
    def _drive_flow(
        flow: Generator[_WriteLine | _WritePrompt | _ReadLine, str | None, _SubmissionResult],
        io: SyncEditorIO,
    ) -> _SubmissionResult:
        op = next(flow)
        while True:
            try:
                if isinstance(op, _WriteLine):
                    io.write_line(op.text)
                    op = flow.send(None)
                elif isinstance(op, _WritePrompt):
                    io.write_prompt(op.text)
                    op = flow.send(None)
                else:  # _ReadLine
                    line = io.readline()
                    op = flow.send(line)
            except StopIteration as stop:
                return stop.value

    @staticmethod
    async def _drive_flow_async(
        flow: Generator[_WriteLine | _WritePrompt | _ReadLine, str | None, _SubmissionResult],
        io: AsyncEditorIO,
    ) -> _SubmissionResult:
        op = next(flow)
        while True:
            try:
                if isinstance(op, _WriteLine):
                    await io.write_line(op.text)
                    op = flow.send(None)
                elif isinstance(op, _WritePrompt):
                    await io.write_prompt(op.text)
                    op = flow.send(None)
                else:  # _ReadLine
                    line = await io.readline()
                    op = flow.send(line)
            except StopIteration as stop:
                return stop.value


__all__ = ["EditorSubmissionHandler", "SyncEditorIO", "AsyncEditorIO"]
