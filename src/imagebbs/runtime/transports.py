"""Runtime transports that extend the prototype implementations."""
from __future__ import annotations

from importlib import import_module

from .editor_submission import AsyncEditorIO, EditorSubmissionHandler

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
