"""Asyncio modem transports for the runtime session prototypes."""

from __future__ import annotations

import asyncio
from collections import deque
from typing import Coroutine, Deque, Iterable, Optional

from ..device_context import ModemTransport
from ..session_kernel import SessionState
from .session_runner import SessionRunner


class TelnetModemTransport(ModemTransport):
    """Bridge :class:`SessionRunner` console traffic over asyncio streams."""

    def __init__(
        self,
        runner: SessionRunner,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        *,
        encoding: str = "latin-1",
        poll_interval: float = 0.02,
    ) -> None:
        self.runner = runner
        self.reader = reader
        self.writer = writer
        self.encoding = encoding
        self.poll_interval = poll_interval

        self._loop: asyncio.AbstractEventLoop | None = None
        self._close_event = asyncio.Event()
        self._tasks: set[asyncio.Task[None]] = set()
        self._inbound: Deque[str] = deque()
        self._outbound: Deque[str] = deque()
        self._closing = False

    # ModemTransport API -------------------------------------------------

    def open(self) -> None:
        if self._loop is not None:
            return
        self._loop = asyncio.get_running_loop()
        initial = self.runner.read_output()
        if initial:
            self.send(initial)
        self._create_task(self._pump_console())
        self._create_task(self._pump_reader())

    def send(self, data: str) -> None:
        if not data:
            return
        self._outbound.extend(data)
        payload = data.encode(self.encoding, errors="replace")
        self.writer.write(payload)
        if self._loop is None:
            return
        task = self._loop.create_task(self.writer.drain())
        self._track_task(task)

    def receive(self, size: Optional[int] = None) -> str:
        if size is None:
            size = len(self._inbound)
        chars: Iterable[str] = (
            self._inbound.popleft() for _ in range(min(size, len(self._inbound)))
        )
        return "".join(chars)

    def feed(self, data: str) -> None:
        self._inbound.extend(data)

    def collect_transmit(self) -> str:
        payload = "".join(self._outbound)
        self._outbound.clear()
        return payload

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._mark_closed()
        for task in list(self._tasks):
            task.cancel()

    # Lifecycle helpers --------------------------------------------------

    async def wait_closed(self) -> None:
        await self._close_event.wait()
        tasks = list(self._tasks)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _mark_closed(self) -> None:
        if not self._close_event.is_set():
            self._close_event.set()

    def _track_task(self, task: asyncio.Task[None]) -> None:
        def _on_done(completed: asyncio.Task[None]) -> None:
            self._tasks.discard(completed)
            if completed.cancelled():
                return
            exc = completed.exception()
            if isinstance(exc, ConnectionError):
                self._mark_closed()

        self._tasks.add(task)
        task.add_done_callback(_on_done)

    def _create_task(self, coro: Coroutine[object, object, None]) -> None:
        if self._loop is None:
            raise RuntimeError("transport not opened")
        task = self._loop.create_task(coro)
        self._track_task(task)

    async def _pump_console(self) -> None:
        try:
            while not self._close_event.is_set():
                flushed = self.runner.read_output()
                if flushed:
                    try:
                        self.send(flushed)
                    except ConnectionError:
                        self._mark_closed()
                        break
                    continue
                if self.runner.state is SessionState.EXIT:
                    break
                await asyncio.sleep(self.poll_interval)
        finally:
            self._mark_closed()

    async def _pump_reader(self) -> None:
        try:
            while not self._close_event.is_set():
                try:
                    data = await self.reader.readline()
                except ConnectionError:
                    self._mark_closed()
                    break
                if data == b"":
                    self._mark_closed()
                    break
                text = data.decode(self.encoding, errors="ignore")
                self.feed(text)
                command = text.rstrip("\r\n")
                if command or text:
                    state = self.runner.send_command(command)
                    if state is SessionState.EXIT:
                        # allow console pump to flush exit output
                        break
        finally:
            self._mark_closed()


__all__ = ["TelnetModemTransport"]

