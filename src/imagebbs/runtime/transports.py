"""Runtime transports that extend the prototype implementations."""
from __future__ import annotations

import asyncio
from importlib import import_module

from .editor_submission import AsyncEditorIO, EditorSubmissionHandler
from .session_instrumentation import SessionInstrumentation

_prototype = import_module("scripts.prototypes.runtime.transports")
SessionState = getattr(_prototype, "SessionState")


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

    _PAUSE_TOKENS: dict[int, bool] = {0x13: True, 0x11: False}

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

    def _update_pause_indicator(self, active: bool) -> None:
        runner = getattr(self, "runner", None)
        if runner is None:
            return
        if self._instrumentation is not None:
            self._instrumentation.ensure_indicator_controller()
        try:
            runner.set_pause_indicator_state(active)
        except AttributeError:
            controller = getattr(self, "indicator_controller", None)
            if controller is not None:
                controller.set_pause(active)

    def _strip_pause_tokens(self, payload: bytes) -> bytes:
        if not payload:
            return payload
        filtered = bytearray()
        tokens = self._PAUSE_TOKENS
        for byte in payload:
            if byte in tokens:
                self._update_pause_indicator(tokens[byte])
                continue
            filtered.append(byte)
        return bytes(filtered)

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

    async def _pump_reader(self) -> None:
        try:
            while not self._close_event.is_set():
                if await self._maybe_collect_editor_submission():
                    continue
                try:
                    data = await self.reader.readline()
                except ConnectionError:
                    self._mark_closed()
                    break
                if data == b"":
                    self._mark_closed()
                    break
                filtered = self._strip_pause_tokens(data)
                if not filtered:
                    continue
                text = filtered.decode(self.encoding, errors="ignore")
                self.feed(text)
                command = text.rstrip("\r\n")
                if command or text:
                    state = self.runner.send_command(command)
                    if state is SessionState.EXIT:
                        break
        finally:
            self._mark_closed()


__all__ = ["BaudLimitedTransport", "TelnetModemTransport"]
__doc__ = _prototype.__doc__
