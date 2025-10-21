"""Asyncio modem transports for the runtime session prototypes."""

from __future__ import annotations

import asyncio
from collections import deque
from typing import Awaitable, Callable, Coroutine, Deque, Iterable, Optional

from ..device_context import ModemTransport
from ..message_editor import EditorState
from ..session_kernel import SessionState
from .session_runner import SessionRunner
from .indicator_controller import IndicatorController


SleepCallable = Callable[[float], Awaitable[object]]


_EDITOR_ABORT_COMMAND = "/abort"
_EDITOR_SUBMIT_COMMAND = "/send"


class _BaudBudget:
    """Token bucket that enforces a serial-style bits-per-second limit."""

    __slots__ = ("limit", "bits_per_character", "_time", "_last_time", "_available_bits")

    def __init__(
        self, limit: int, bits_per_character: int, time_provider: Callable[[], float]
    ) -> None:
        self.limit = float(limit)
        self.bits_per_character = float(bits_per_character)
        self._time = time_provider
        self._last_time: float | None = None
        self._available_bits: float = self.limit

    def available_chars(self, upper_bound: Optional[int] = None) -> int:
        now = self._time()
        if self._last_time is None:
            self._available_bits = self.limit
        else:
            delta = max(0.0, now - self._last_time)
            self._available_bits = min(
                self.limit, self._available_bits + (delta * self.limit)
            )
        self._last_time = now
        available = int(self._available_bits // self.bits_per_character)
        if upper_bound is not None:
            available = min(available, upper_bound)
        return available

    def consume(self, chars: int) -> None:
        self._available_bits = max(
            0.0, self._available_bits - (chars * self.bits_per_character)
        )

    def delay_until_available(self, chars: int = 1) -> float:
        required_bits = chars * self.bits_per_character
        deficit = max(0.0, required_bits - self._available_bits)
        if deficit <= 0.0:
            return 0.0
        return deficit / self.limit


class BaudLimitedTransport(ModemTransport):
    """Decorator that throttles a :class:`ModemTransport` by baud rate."""

    def __init__(
        self,
        transport: ModemTransport,
        baud_limit: Optional[int],
        *,
        bits_per_character: int = 8,
        time_provider: Callable[[], float] | None = None,
        sleep: SleepCallable | None = None,
    ) -> None:
        self.transport = transport
        if baud_limit is not None and baud_limit <= 0:
            baud_limit = None
        self._baud_limit = baud_limit
        self._bits_per_character = bits_per_character
        self._time_provider = time_provider
        self._sleep_fn = sleep

        self._loop: asyncio.AbstractEventLoop | None = None
        self._time_fn: Callable[[], float] | None = None
        self._send_queue: Deque[str] = deque()
        self._receive_buffer: Deque[str] = deque()
        self._send_event: asyncio.Event | None = None
        self._send_task: asyncio.Task[None] | None = None
        self._closing = False
        self._send_budget: _BaudBudget | None = None
        self._receive_budget: _BaudBudget | None = None

    # ModemTransport API -------------------------------------------------

    def open(self) -> None:
        if self._loop is not None:
            return
        loop = asyncio.get_running_loop()
        self._loop = loop
        self._time_fn = self._time_provider or loop.time
        self._sleep_fn = self._sleep_fn or asyncio.sleep  # type: ignore[assignment]
        self.transport.open()
        if self._baud_limit is None:
            return
        time_fn = self._time_fn
        assert time_fn is not None
        self._send_budget = _BaudBudget(self._baud_limit, self._bits_per_character, time_fn)
        self._receive_budget = _BaudBudget(
            self._baud_limit, self._bits_per_character, time_fn
        )
        self._send_event = asyncio.Event()
        self._send_task = loop.create_task(self._drain_outbound())

    def send(self, data: str) -> None:
        if not data:
            return
        if self._baud_limit is None:
            self.transport.send(data)
            return
        if self._send_event is None:
            raise RuntimeError("transport not opened")
        self._send_queue.extend(data)
        self._send_event.set()

    def receive(self, size: Optional[int] = None) -> str:
        if self._baud_limit is None or self._receive_budget is None:
            return self.transport.receive(size)

        max_chars = size if size is not None else None
        available = self._receive_budget.available_chars(max_chars)
        if available <= 0:
            return ""

        delivered: list[str] = []
        consumed = 0

        if self._receive_buffer:
            buffered = self._drain_queue(self._receive_buffer, min(len(self._receive_buffer), available))
            if buffered:
                delivered.append(buffered)
                consumed += len(buffered)
                available -= len(buffered)
                if max_chars is not None:
                    max_chars = max(0, max_chars - len(buffered))

        if available > 0 and (max_chars is None or max_chars > 0):
            request = available if max_chars is None else min(available, max_chars)
            if request > 0:
                chunk = self.transport.receive(request)
                if chunk:
                    if len(chunk) > request:
                        delivered.append(chunk[:request])
                        self._receive_buffer.extend(chunk[request:])
                        consumed += request
                    else:
                        delivered.append(chunk)
                        consumed += len(chunk)

        if consumed:
            self._receive_budget.consume(consumed)
        return "".join(delivered)

    def feed(self, data: str) -> None:
        self.transport.feed(data)

    def collect_transmit(self) -> str:
        return self.transport.collect_transmit()

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        if self._send_task is not None:
            self._send_task.cancel()
        if self._send_event is not None:
            self._send_event.set()
        self.transport.close()

    async def wait_closed(self) -> None:
        waiter = getattr(self.transport, "wait_closed", None)
        if callable(waiter):
            await waiter()

    # Lifecycle helpers --------------------------------------------------

    async def _drain_outbound(self) -> None:
        assert self._send_event is not None
        assert self._send_budget is not None
        try:
            while True:
                if not self._send_queue:
                    self._send_event.clear()
                    await self._send_event.wait()
                    if self._closing and not self._send_queue:
                        break
                if not self._send_queue:
                    continue
                allowance = self._send_budget.available_chars(len(self._send_queue))
                if allowance <= 0:
                    delay = self._send_budget.delay_until_available()
                    await self._sleep_fn(delay)
                    continue
                chunk = self._drain_queue(self._send_queue, allowance)
                if not chunk:
                    continue
                self.transport.send(chunk)
                self._send_budget.consume(len(chunk))
        except asyncio.CancelledError:
            pass

    @staticmethod
    def _drain_queue(queue: Deque[str], count: int) -> str:
        chars: list[str] = []
        for _ in range(min(count, len(queue))):
            chars.append(queue.popleft())
        return "".join(chars)

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
        indicator_controller: IndicatorController | None = None,
    ) -> None:
        self.runner = runner
        self.reader = reader
        self.writer = writer
        self.encoding = encoding
        self.poll_interval = poll_interval
        self.indicator_controller = indicator_controller

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
        if self.indicator_controller is not None:
            self.indicator_controller.set_carrier(True)
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
        if self.indicator_controller is not None:
            self.indicator_controller.set_carrier(False)

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
                    if self.indicator_controller is not None:
                        self.indicator_controller.on_idle_tick()
                    continue
                if self.runner.state is SessionState.EXIT:
                    break
                if self.indicator_controller is not None:
                    self.indicator_controller.on_idle_tick()
                await asyncio.sleep(self.poll_interval)
        finally:
            self._mark_closed()

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

    async def _maybe_collect_editor_submission(self) -> bool:
        runner = self.runner
        if runner.state is not SessionState.MESSAGE_EDITOR:
            return False
        if not runner.requires_editor_submission():
            return False
        try:
            await self._collect_editor_submission()
        except ConnectionError:
            self._mark_closed()
        return True

    async def _collect_editor_submission(self) -> None:
        runner = self.runner
        context = runner.editor_context
        editor_state = runner.get_editor_state()
        existing_subject = context.current_message if editor_state is not None else ""
        existing_lines = list(context.draft_buffer)

        def _write(line: str, *, newline: bool = True) -> None:
            payload = line + ("\r\n" if newline else "")
            self.send(payload)

        async def _readline() -> str:
            data = await self.reader.readline()
            if data == b"":
                raise ConnectionError
            text = data.decode(self.encoding, errors="ignore")
            return text.rstrip("\r\n")

        _write("")
        _write("-- Message Editor --")
        _write(
            f"Type {_EDITOR_SUBMIT_COMMAND} to save or {_EDITOR_ABORT_COMMAND} to cancel."
        )

        subject_text = existing_subject
        if editor_state is EditorState.POST_MESSAGE:
            prompt = "Subject"
            if existing_subject:
                prompt += f" [{existing_subject}]"
            prompt += ": "
            _write(prompt, newline=False)
            subject_line = await _readline()
            command = subject_line.strip().lower()
            if command == _EDITOR_ABORT_COMMAND:
                runner.abort_editor()
                return
            if subject_line:
                subject_text = subject_line

        if editor_state is EditorState.EDIT_DRAFT and existing_lines:
            _write("Current message lines:")
            for line in existing_lines:
                _write(f"> {line}")

        _write("Enter message body.")
        lines: list[str] = []
        while True:
            _write("> ", newline=False)
            line = await _readline()
            command = line.strip().lower()
            if command == _EDITOR_ABORT_COMMAND:
                runner.abort_editor()
                return
            if command == _EDITOR_SUBMIT_COMMAND:
                final_lines = lines if lines else existing_lines
                if editor_state is EditorState.POST_MESSAGE:
                    runner.submit_editor_draft(subject=subject_text, lines=final_lines)
                else:
                    runner.submit_editor_draft(subject=None, lines=final_lines)
                return
            lines.append(line)


__all__ = ["BaudLimitedTransport", "TelnetModemTransport"]

