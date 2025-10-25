"""Asyncio modem transports for the ImageBBS runtime."""

from __future__ import annotations

import asyncio
from collections import deque
from typing import Awaitable, Callable, Coroutine, Deque, Iterable, Optional

from ..device_context import ModemTransport
from ..session_kernel import SessionState
from .console_ui import IdleTimerScheduler
from .editor_submission import AsyncEditorIO, EditorSubmissionHandler
from .indicator_controller import IndicatorController
from .session_instrumentation import SessionInstrumentation


SleepCallable = Callable[[float], Awaitable[object]]


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
            buffered = self._drain_queue(
                self._receive_buffer, min(len(self._receive_buffer), available)
            )
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


class _TelnetEditorIO(AsyncEditorIO):
    """Adapter that exposes :class:`TelnetModemTransport` as editor I/O."""

    def __init__(self, transport: "TelnetModemTransport") -> None:
        self._transport = transport
        self._reader = transport.reader
        self._encoding = transport.encoding
        self._line_ending = "\r\n"

    async def write_line(self, text: str = "") -> None:
        self._transport.send(text + self._line_ending)

    async def write_prompt(self, prompt: str) -> None:
        self._transport.send(prompt)

    async def readline(self) -> str | None:
        data = await self._reader.readline()
        if data == b"":
            return None
        return data.decode(self._encoding, errors="ignore").rstrip("\r\n")


class TelnetModemTransport(ModemTransport):
    """Bridge :class:`SessionRunner` console traffic over asyncio streams."""

    _PAUSE_TOKENS: dict[int, bool] = {0x13: True, 0x11: False}

    def __init__(
        self,
        runner,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        *,
        encoding: str = "latin-1",
        poll_interval: float = 0.02,
        indicator_controller: IndicatorController | None = None,
        instrumentation: SessionInstrumentation | None = None,
        idle_timer_scheduler_cls: type[IdleTimerScheduler] | None = IdleTimerScheduler,
    ) -> None:
        self.runner = runner
        self.reader = reader
        self.writer = writer
        self.encoding = encoding
        self.poll_interval = poll_interval
        self._instrumentation = instrumentation
        self._idle_timer_scheduler_cls = idle_timer_scheduler_cls

        if instrumentation is not None:
            indicator_controller = instrumentation.ensure_indicator_controller()

        self.indicator_controller = indicator_controller
        self._idle_timer_scheduler: IdleTimerScheduler | None = None

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

        instrumentation = self._instrumentation
        if instrumentation is not None:
            instrumentation.set_carrier(True)
            instrumentation.reset_idle_timer()
            self._idle_timer_scheduler = instrumentation.ensure_idle_timer_scheduler()
        else:
            controller = self.indicator_controller
            if controller is not None:
                controller.set_carrier(True)
            scheduler = self._idle_timer_scheduler
            if scheduler is None:
                scheduler_cls = self._idle_timer_scheduler_cls
                console = getattr(self.runner, "console", None)
                if scheduler_cls is not None and console is not None:
                    scheduler = scheduler_cls(console)
            self._idle_timer_scheduler = scheduler
            if scheduler is not None:
                scheduler.reset()

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

    async def wait_closed(self) -> None:
        await self._close_event.wait()
        tasks = list(self._tasks)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # Lifecycle helpers --------------------------------------------------

    def _mark_closed(self) -> None:
        if not self._close_event.is_set():
            self._close_event.set()
        instrumentation = self._instrumentation
        if instrumentation is not None:
            instrumentation.set_carrier(False)
        else:
            controller = self.indicator_controller
            if controller is not None:
                controller.set_carrier(False)

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

    def _resolve_indicator_controller(self) -> IndicatorController | None:
        instrumentation = self._instrumentation
        if instrumentation is not None:
            controller = instrumentation.ensure_indicator_controller()
            if controller is not None:
                self.indicator_controller = controller
            return controller
        return self.indicator_controller

    def _on_idle_cycle(self) -> None:
        instrumentation = self._instrumentation
        if instrumentation is not None:
            instrumentation.on_idle_cycle()
            return
        controller = self.indicator_controller
        if controller is not None:
            controller.on_idle_tick()
        scheduler = self._idle_timer_scheduler
        if scheduler is not None:
            scheduler.tick()

    def _update_pause_indicator(self, active: bool) -> None:
        runner = getattr(self, "runner", None)
        if runner is not None:
            setter = getattr(runner, "set_pause_indicator_state", None)
            if callable(setter):
                setter(active)
        controller = self._resolve_indicator_controller()
        if controller is not None:
            toggle = getattr(controller, "set_pause", None)
            if callable(toggle):
                toggle(active)

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
                    self._on_idle_cycle()
                    continue
                if self.runner.state is SessionState.EXIT:
                    break
                self._on_idle_cycle()
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

    async def _maybe_collect_editor_submission(self) -> bool:
        handler = EditorSubmissionHandler(self.runner)
        io = _TelnetEditorIO(self)
        try:
            return await handler.collect_async(io)
        except ConnectionError:
            self._mark_closed()
            return True


__all__ = ["BaudLimitedTransport", "TelnetModemTransport"]

