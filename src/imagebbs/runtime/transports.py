"""Runtime transports that extend the prototype implementations."""
from __future__ import annotations

import asyncio
from importlib import import_module

from .editor_submission import AsyncEditorIO, EditorSubmissionHandler
from .session_instrumentation import SessionInstrumentation

_prototype = import_module("scripts.prototypes.runtime.transports")


class BaudLimitedTransport(_prototype.BaudLimitedTransport):
    """Subclass to preserve compatibility with the prototype transport."""

    pass


class _TelnetEditorIO(AsyncEditorIO):
    def __init__(self, transport: "TelnetModemTransport") -> None:
        self._transport = transport
        self._reader = transport.reader
        self._encoding = transport.encoding
        self._line_ending = "\r\n"

    async def write_line(self, text: str = "") -> None:
        self._transport.send(text + self._line_ending)

    async def write_prompt(self, prompt: str) -> None:
        self._transport.send(prompt)

    async def readline(self) -> str:
        data = await self._reader.readline()
        if data == b"":
            raise ConnectionError
        return data.decode(self._encoding, errors="ignore").rstrip("\r\n")


class TelnetModemTransport(_prototype.TelnetModemTransport):
    """Override the editor submission path to reuse :class:`EditorSubmissionHandler`."""

    def __init__(
        self,
        runner,
        reader,
        writer,
        *,
        instrumentation: SessionInstrumentation | None = None,
        **kwargs,
    ) -> None:
        indicator_controller = kwargs.pop("indicator_controller", None)
        self._instrumentation = instrumentation
        if instrumentation is not None:
            indicator_controller = instrumentation.ensure_indicator_controller()
        super().__init__(
            runner,
            reader,
            writer,
            indicator_controller=indicator_controller,
            **kwargs,
        )

    def open(self) -> None:
        if self._instrumentation is None:
            super().open()
            return
        if self._loop is not None:
            return
        self._loop = asyncio.get_running_loop()
        self._instrumentation.set_carrier(True)
        initial = self.runner.read_output()
        if initial:
            self.send(initial)
        scheduler = self._instrumentation.ensure_idle_timer_scheduler()
        self._idle_timer_scheduler = scheduler
        self._instrumentation.reset_idle_timer()
        self._create_task(self._pump_console())
        self._create_task(self._pump_reader())

    async def _maybe_collect_editor_submission(self) -> bool:
        handler = EditorSubmissionHandler(self.runner)
        io = _TelnetEditorIO(self)
        try:
            return await handler.collect_async(io)
        except ConnectionError:
            self._mark_closed()
            return True


__all__ = ["BaudLimitedTransport", "TelnetModemTransport"]
__doc__ = _prototype.__doc__
