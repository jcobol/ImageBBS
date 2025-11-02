"""Utilities for collecting message editor submissions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generator, Protocol

from ..message_editor import EditorState, MessageEditor
from ..session_kernel import SessionState
from .session_runner import SessionRunner

DEFAULT_EDITOR_ABORT_COMMAND = ".A"
DEFAULT_EDITOR_SUBMIT_COMMAND = ".S"
DOT_HELP_COMMAND = ".H"
DOT_LINE_NUMBER_COMMAND = ".O"


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
        submit_command: str = DEFAULT_EDITOR_SUBMIT_COMMAND,
        abort_command: str = DEFAULT_EDITOR_ABORT_COMMAND,
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
        runner = self._runner
        runner.set_abort_indicator_state(True)
        try:
            result = self._drive_flow(self._flow(), io)
            self._apply_result(result)
        finally:
            runner.set_abort_indicator_state(False)
        return True

    async def collect_async(self, io: AsyncEditorIO) -> bool:
        """Collect an editor submission using asynchronous streams."""

        if not self.should_handle():
            return False
        runner = self._runner
        runner.set_abort_indicator_state(True)
        try:
            result = await self._drive_flow_async(self._flow(), io)
            self._apply_result(result)
        finally:
            runner.set_abort_indicator_state(False)
        return True

    def _flow(self) -> Generator[_WriteLine | _WritePrompt | _ReadLine, str | None, _SubmissionResult]:
        runner = self._runner
        context = runner.editor_context
        if context is None:
            raise RuntimeError("editor context is unavailable")
        editor_state = runner.get_editor_state()
        existing_subject = context.current_message if editor_state is not None else ""
        existing_lines = list(context.draft_buffer)
        submit_aliases = {
            DEFAULT_EDITOR_SUBMIT_COMMAND.upper(),
            self._submit_command.upper(),
            *MessageEditor.DOT_SAVE_COMMANDS,
        }
        abort_aliases = {
            DEFAULT_EDITOR_ABORT_COMMAND.upper(),
            self._abort_command.upper(),
            *MessageEditor.DOT_ABORT_COMMANDS,
        }
        help_aliases = {
            DOT_HELP_COMMAND.upper(),
            *MessageEditor.DOT_HELP_COMMANDS,
        }
        line_aliases = {
            DOT_LINE_NUMBER_COMMAND.upper(),
            *MessageEditor.DOT_LINE_NUMBER_COMMANDS,
        }
        submit_aliases = {alias.upper() for alias in submit_aliases}
        abort_aliases = {alias.upper() for alias in abort_aliases}
        help_aliases = {alias.upper() for alias in help_aliases}
        line_aliases = {alias.upper() for alias in line_aliases}
        output_cursor = len(context.modem_buffer)

        yield _WriteLine("")
        yield _WriteLine("-- Message Editor --")
        instructions = (
            "Type .S to save, .A to abort, .H for help, .O toggles line numbers."
        )
        extra_aliases: list[str] = []
        if self._submit_command.upper() not in MessageEditor.DOT_SAVE_COMMANDS:
            extra_aliases.append(f"{self._submit_command} also saves")
        if self._abort_command.upper() not in MessageEditor.DOT_ABORT_COMMANDS:
            extra_aliases.append(f"{self._abort_command} also aborts")
        if extra_aliases:
            instructions += " (" + ", ".join(extra_aliases) + ".)"
        yield _WriteLine(instructions)

        subject_text = existing_subject
        if editor_state is EditorState.POST_MESSAGE:
            while True:
                prompt = "Subject"
                if existing_subject:
                    prompt += f" [{existing_subject}]"
                prompt += ": "
                yield _WritePrompt(prompt)
                subject_line = yield _ReadLine()
                if subject_line is None:
                    return _SubmissionResult("abort", None, None)
                stripped_subject = subject_line.strip()
                upper_subject = stripped_subject.upper()
                if upper_subject in help_aliases:
                    output_cursor, feedback = self._invoke_editor_inline(
                        DOT_HELP_COMMAND, output_cursor
                    )
                    for message in feedback:
                        yield _WriteLine(message)
                    continue
                if upper_subject in line_aliases:
                    output_cursor, feedback = self._invoke_editor_inline(
                        DOT_LINE_NUMBER_COMMAND, output_cursor
                    )
                    for message in feedback:
                        yield _WriteLine(message)
                    continue
                if upper_subject in abort_aliases:
                    return _SubmissionResult("abort", None, None)
                if upper_subject in submit_aliases:
                    final_lines = list(existing_lines)
                    return _SubmissionResult("submit", subject_text, final_lines)
                if subject_line:
                    subject_text = subject_line
                break

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
            stripped = line.strip()
            upper = stripped.upper()
            if upper in help_aliases:
                output_cursor, feedback = self._invoke_editor_inline(
                    DOT_HELP_COMMAND, output_cursor
                )
                for message in feedback:
                    yield _WriteLine(message)
                continue
            if upper in line_aliases:
                output_cursor, feedback = self._invoke_editor_inline(
                    DOT_LINE_NUMBER_COMMAND, output_cursor
                )
                for message in feedback:
                    yield _WriteLine(message)
                continue
            if upper in abort_aliases:
                return _SubmissionResult("abort", None, None)
            if upper in submit_aliases:
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

    # Why: relay inline dot commands to the editor module and expose any resulting feedback to the caller.
    def _invoke_editor_inline(
        self, command: str, cursor: int
    ) -> tuple[int, list[str]]:
        runner = self._runner
        state = runner.send_command(command)
        context = runner.editor_context
        if context is None:
            return cursor, []
        buffer = getattr(context, "modem_buffer", None)
        if buffer is None:
            buffer = []
            setattr(context, "modem_buffer", buffer)
        if cursor > len(buffer):
            cursor = len(buffer)
        new_segments = list(buffer[cursor:])
        cursor = len(buffer)
        feedback: list[str] = []
        for segment in new_segments:
            pieces = segment.split("\r")
            for piece in pieces:
                text = piece.rstrip()
                if not text:
                    continue
                feedback.append(text)
        if state is not SessionState.MESSAGE_EDITOR:
            return cursor, feedback
        return cursor, feedback

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


__all__ = [
    "AsyncEditorIO",
    "DEFAULT_EDITOR_ABORT_COMMAND",
    "DEFAULT_EDITOR_SUBMIT_COMMAND",
    "DOT_HELP_COMMAND",
    "DOT_LINE_NUMBER_COMMAND",
    "EditorSubmissionHandler",
    "SyncEditorIO",
]
