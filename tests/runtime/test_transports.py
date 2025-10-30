"""Unit tests covering the native runtime transports."""

from __future__ import annotations

import asyncio
from collections import deque
from types import SimpleNamespace
from typing import Coroutine, Optional

from imagebbs.device_context import ConsoleService
from imagebbs.message_editor import EditorState
from imagebbs.runtime.console_ui import IdleTimerScheduler
from imagebbs.runtime.indicator_controller import IndicatorController
from imagebbs.runtime.session_instrumentation import SessionInstrumentation
from imagebbs.runtime.transports import TelnetModemTransport
from imagebbs.session_kernel import SessionState


class FakeClock:
    def __init__(self, values: list[float]):
        self.values = list(values)
        self._index = 0

    def __call__(self) -> float:
        if not self.values:
            raise AssertionError("fake clock requires at least one value")
        if self._index < len(self.values):
            value = self.values[self._index]
            self._index += 1
            return value
        return self.values[-1]


class FakeConsole:
    addresses = ConsoleService._IDLE_TIMER_SCREEN_ADDRESSES

    def __init__(self) -> None:
        self.screen: dict[int, int] = {address: 0x20 for address in self.addresses}
        self.digit_history: list[tuple[int, int, int]] = []

    def update_idle_timer_digits(self, digits: tuple[int, int, int], *, colours=None) -> None:
        self.digit_history.append(tuple(digits))
        for address, value in zip(self.addresses, digits):
            self.screen[address] = value


class StubIndicatorController:
    def __init__(self, console: object) -> None:
        self.console = console
        self.tick_count = 0
        self.carrier_states: list[bool] = []
        self.pause_states: list[bool] = []

    def set_carrier(self, active: bool) -> None:
        self.carrier_states.append(active)

    def on_idle_tick(self) -> None:
        self.tick_count += 1

    def set_pause(self, active: bool) -> None:
        self.pause_states.append(active)


class FakeWriter:
    def __init__(self) -> None:
        self.buffer: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.buffer.append(data)

    async def drain(self) -> None:
        await asyncio.sleep(0)


class RecordingTelnetTransport(TelnetModemTransport):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.scheduled_coroutines: list[Coroutine[object, object, None]] = []

    def _create_task(self, coro: Coroutine[object, object, None]) -> None:  # type: ignore[override]
        self.scheduled_coroutines.append(coro)


def test_telnet_transport_collects_editor_submission_with_custom_tokens() -> None:
    class EditorRunner:
        def __init__(self) -> None:
            self.console = object()
            self.state = SessionState.MESSAGE_EDITOR
            self.editor_context = SimpleNamespace(
                current_message="",
                draft_buffer=[],
                selected_message_id=None,
            )
            self._requires_submission = True
            self.submissions: list[tuple[str | None, list[str] | None]] = []
            self.abort_states: list[bool] = []
            self.commands: list[str] = []
            self.indicator_controller = None

        def requires_editor_submission(self) -> bool:
            if self._requires_submission and self.state is SessionState.MESSAGE_EDITOR:
                self._requires_submission = False
                return True
            return False

        def get_editor_state(self) -> EditorState | None:
            return EditorState.POST_MESSAGE

        def submit_editor_draft(
            self, *, subject: str | None, lines: list[str] | None
        ) -> None:
            self.submissions.append((subject, list(lines) if lines else None))
            self.state = SessionState.MAIN_MENU

        def abort_editor(self) -> None:
            self.state = SessionState.MAIN_MENU

        def set_abort_indicator_state(self, active: bool) -> None:
            self.abort_states.append(active)

        def set_indicator_controller(self, controller) -> None:
            self.indicator_controller = controller

        def read_output(self) -> str:
            return ""

        def send_command(self, command: str) -> SessionState:
            self.commands.append(command)
            if command == "EX":
                self.state = SessionState.EXIT
            return self.state

    class EditorReader:
        def __init__(self, payloads: list[bytes]) -> None:
            self._payloads = deque(payloads)

        async def readline(self) -> bytes:
            await asyncio.sleep(0)
            if self._payloads:
                return self._payloads.popleft()
            return b""

    async def _exercise() -> tuple[EditorRunner, str]:
        runner = EditorRunner()
        instrumentation = SessionInstrumentation(
            runner,
            indicator_controller_cls=StubIndicatorController,
            idle_timer_scheduler_cls=None,
        )
        reader = EditorReader(
            [
                b"Custom Subject\r\n",
                b"Body line\r\n",
                b"/save\r\n",
                b"EX\r\n",
            ]
        )
        writer = FakeWriter()
        transport = TelnetModemTransport(
            runner,
            reader,  # type: ignore[arg-type]
            writer,  # type: ignore[arg-type]
            poll_interval=0.0,
            instrumentation=instrumentation,
            editor_submit_command="/save",
            editor_abort_command="/cancel",
        )

        transport.open()
        await asyncio.wait_for(transport.wait_closed(), timeout=0.1)
        transcript = b"".join(writer.buffer).decode("latin-1", errors="ignore")
        return runner, transcript

    runner, transcript = asyncio.run(_exercise())
    assert runner.submissions == [("Custom Subject", ["Body line"])], runner.submissions
    assert runner.commands == ["EX"]
    assert runner.abort_states == [True, False]
    assert "Type /save to save or /cancel to cancel." in transcript


def test_telnet_transport_updates_idle_timer_via_instrumentation() -> None:
    class FakeRunner:
        def __init__(self, console: FakeConsole, iterations: int) -> None:
            self.console = console
            self.state = SessionState.MAIN_MENU
            self._iterations = iterations
            self._tick = 0
            self._indicator = None

        def read_output(self) -> str:
            self._tick += 1
            if self._tick > self._iterations:
                self.state = SessionState.EXIT
            return ""

        def send_command(self, command: str) -> SessionState:  # pragma: no cover - unused
            return self.state

        def set_indicator_controller(self, controller) -> None:
            self._indicator = controller

    async def _exercise() -> None:
        console = FakeConsole()
        fake_clock = FakeClock([0.0, 1.0, 2.0, 3.0, 4.0])

        class RecordingIdleTimerScheduler(IdleTimerScheduler):
            def __init__(self, console_service):
                super().__init__(console_service, time_source=fake_clock)

        runner = FakeRunner(console, iterations=len(fake_clock.values))
        reader = asyncio.StreamReader()
        writer = FakeWriter()
        instrumentation = SessionInstrumentation(
            runner,
            indicator_controller_cls=StubIndicatorController,
            idle_timer_scheduler_cls=RecordingIdleTimerScheduler,
        )

        transport = RecordingTelnetTransport(
            runner,
            reader,
            writer,  # type: ignore[arg-type]
            poll_interval=0.0,
            instrumentation=instrumentation,
        )

        transport.open()
        assert transport.scheduled_coroutines
        pump_console = transport.scheduled_coroutines[0]
        try:
            await asyncio.wait_for(pump_console, timeout=0.1)
        finally:
            for coro in transport.scheduled_coroutines[1:]:
                coro.close()

        digits = [console.screen[address] for address in console.addresses]
        assert digits == [0x30, 0x30, 0x33]
        controller = instrumentation.ensure_indicator_controller()
        assert controller is not None
        assert controller.tick_count >= len(fake_clock.values) - 1
        assert transport._idle_timer_scheduler is instrumentation.idle_timer_scheduler

    asyncio.run(_exercise())


def test_telnet_transport_forwards_indicator_controller_without_instrumentation() -> None:
    class RecordingConsoleService:
        def __init__(self) -> None:
            self.spinner_glyphs: list[int] = []
            self.carrier_updates: list[tuple[int, int]] = []

        def set_pause_indicator(self, glyph: int, *, colour=None) -> None:  # pragma: no cover - unused
            pass

        def set_carrier_indicator(
            self,
            *,
            leading_cell: int,
            indicator_cell: int,
            leading_colour=None,
            indicator_colour=None,
        ) -> None:
            self.carrier_updates.append((leading_cell & 0xFF, indicator_cell & 0xFF))

        def set_spinner_glyph(self, glyph: int, *, colour=None) -> None:
            self.spinner_glyphs.append(glyph & 0xFF)

    class IdleRunner:
        def __init__(self, console: RecordingConsoleService, iterations: int) -> None:
            self.console = console
            self.state = SessionState.MAIN_MENU
            self._iterations = iterations
            self._indicator = None
            self.editor_context = None

        def read_output(self) -> str:
            if self._iterations <= 0:
                self.state = SessionState.EXIT
                return ""
            self._iterations -= 1
            if self._iterations == 0:
                self.state = SessionState.EXIT
            return ""

        def send_command(self, command: str) -> SessionState:  # pragma: no cover - unused
            return self.state

        def set_indicator_controller(self, controller) -> None:  # pragma: no cover - unused
            self._indicator = controller

        def requires_editor_submission(self) -> bool:  # pragma: no cover - unused
            return False

        def set_abort_indicator_state(self, active: bool) -> None:  # pragma: no cover - unused
            pass

    class BlockingReader:
        def __init__(self) -> None:
            self._release = asyncio.Event()

        async def readline(self) -> bytes:
            await self._release.wait()
            return b""

        def release(self) -> None:
            self._release.set()

    async def _exercise() -> tuple[IndicatorController, RecordingConsoleService]:
        console = RecordingConsoleService()
        runner = IdleRunner(console, iterations=4)
        controller = IndicatorController(console)
        reader = BlockingReader()
        writer = FakeWriter()
        transport = RecordingTelnetTransport(
            runner,
            reader,  # type: ignore[arg-type]
            writer,  # type: ignore[arg-type]
            poll_interval=0.0,
            indicator_controller=controller,
            idle_timer_scheduler_cls=None,
        )

        transport.open()
        pump_console, pump_reader = transport.scheduled_coroutines
        try:
            await asyncio.wait_for(pump_console, timeout=0.1)
        finally:
            reader.release()
            await asyncio.wait_for(pump_reader, timeout=0.1)
            await asyncio.wait_for(transport.wait_closed(), timeout=0.1)
        return controller, console

    controller, console = asyncio.run(_exercise())
    assert console.carrier_updates, console.carrier_updates
    assert console.carrier_updates[0] == (0xA0, 0xFA)
    assert console.carrier_updates[-1] == (0x20, 0x20)
    assert controller is not None
    assert len(console.spinner_glyphs) >= 3
    assert console.spinner_glyphs[0] == 0xB0
    assert console.spinner_glyphs[1] == 0xAE
    assert console.spinner_glyphs[-1] == 0x20


def test_telnet_transport_filters_pause_tokens_and_updates_indicator() -> None:
    class ScriptedReader:
        def __init__(self, payloads: list[bytes]):
            self._payloads = list(payloads)

        async def readline(self) -> bytes:
            await asyncio.sleep(0)
            if self._payloads:
                return self._payloads.pop(0)
            return b""

    class RecordingRunner:
        def __init__(self) -> None:
            self.console = object()
            self.state = SessionState.MAIN_MENU
            self.commands: list[str] = []
            self.pause_states: list[bool] = []
            self.indicator_controller = None

        def read_output(self) -> str:
            return ""

        def send_command(self, text: str) -> SessionState:
            self.commands.append(text)
            if text == "EX":
                self.state = SessionState.EXIT
            return self.state

        def set_indicator_controller(self, controller) -> None:
            self.indicator_controller = controller

        def set_pause_indicator_state(self, active: bool) -> None:
            self.pause_states.append(active)

        def requires_editor_submission(self) -> bool:
            return False

    async def _exercise() -> tuple[RecordingRunner, StubIndicatorController]:
        runner = RecordingRunner()
        instrumentation = SessionInstrumentation(
            runner,
            indicator_controller_cls=StubIndicatorController,
            idle_timer_scheduler_cls=None,
        )
        reader = ScriptedReader([b"\x13HELLO\r\n", b"\x11EX\r\n"])
        writer = FakeWriter()
        transport = RecordingTelnetTransport(
            runner,
            reader,  # type: ignore[arg-type]
            writer,  # type: ignore[arg-type]
            poll_interval=0.0,
            instrumentation=instrumentation,
        )

        transport.open()
        pump_reader = transport.scheduled_coroutines[1]
        await asyncio.wait_for(pump_reader, timeout=0.1)
        transport.scheduled_coroutines[0].close()
        controller = instrumentation.ensure_indicator_controller()
        assert controller is not None
        return runner, controller

    runner, controller = asyncio.run(_exercise())
    assert runner.commands == ["HELLO", "EX"]
    assert runner.pause_states == [True, False]
    assert controller.pause_states == [True, False]
    assert controller.carrier_states == [True, False]


def test_telnet_transport_pauses_outbound_until_resume() -> None:
    class QueueReader:
        def __init__(self) -> None:
            self.queue: asyncio.Queue[bytes] = asyncio.Queue()

        async def readline(self) -> bytes:
            return await self.queue.get()

    class PausingRunner:
        def __init__(self) -> None:
            self.console = object()
            self.state = SessionState.MAIN_MENU
            self._outputs: deque[str] = deque()
            self.pause_states: list[bool] = []
            self.commands: list[str] = []
            self.indicator_controller = None

        def queue_output(self, text: str) -> None:
            self._outputs.append(text)

        def read_output(self) -> str:
            if self._outputs:
                return self._outputs.popleft()
            return ""

        def send_command(self, text: str) -> SessionState:
            self.commands.append(text)
            if text == "EX":
                self.state = SessionState.EXIT
            return self.state

        def set_indicator_controller(self, controller) -> None:
            self.indicator_controller = controller

        def set_pause_indicator_state(self, active: bool) -> None:
            self.pause_states.append(active)

        def requires_editor_submission(self) -> bool:
            return False

    async def _exercise() -> tuple[list[str], PausingRunner, StubIndicatorController]:
        runner = PausingRunner()
        instrumentation = SessionInstrumentation(
            runner,
            indicator_controller_cls=StubIndicatorController,
            idle_timer_scheduler_cls=None,
        )
        reader = QueueReader()
        writer = FakeWriter()
        transport = TelnetModemTransport(
            runner,
            reader,  # type: ignore[arg-type]
            writer,  # type: ignore[arg-type]
            poll_interval=0.0,
            instrumentation=instrumentation,
        )

        transport.open()

        transmissions: list[str] = []

        runner.queue_output("READY")
        await asyncio.sleep(0)
        transmissions.append(transport.collect_transmit())

        await reader.queue.put(b"\x13")
        await asyncio.sleep(0)
        transmissions.append(transport.collect_transmit())

        runner.queue_output("PAUSED")
        await asyncio.sleep(0)
        transmissions.append(transport.collect_transmit())

        await reader.queue.put(b"\x11")
        await asyncio.sleep(0)
        transmissions.append(transport.collect_transmit())

        runner.queue_output("AFTER")
        await asyncio.sleep(0)
        transmissions.append(transport.collect_transmit())

        await reader.queue.put(b"EX\r\n")
        await asyncio.sleep(0)
        await asyncio.wait_for(transport.wait_closed(), timeout=0.1)

        controller = instrumentation.ensure_indicator_controller()
        assert controller is not None
        transmissions.append(transport.collect_transmit())
        return transmissions, runner, controller

    transmissions, runner, controller = asyncio.run(_exercise())
    assert transmissions == ["READY", "", "", "PAUSED", "AFTER", ""]
    assert runner.pause_states == [True, False]
    assert runner.commands == ["EX"]
    assert controller.pause_states == [True, False]


def test_telnet_transport_handles_negotiation_sequences() -> None:
    class NegotiationReader:
        def __init__(self, payloads: list[bytes]):
            self._payloads = list(payloads)

        async def readline(self) -> bytes:
            await asyncio.sleep(0)
            if self._payloads:
                return self._payloads.pop(0)
            return b""

    class NegotiationRunner:
        def __init__(self) -> None:
            self.console = object()
            self.state = SessionState.MAIN_MENU
            self.commands: list[str] = []

        def read_output(self) -> str:
            return ""

        def send_command(self, text: str) -> SessionState:
            self.commands.append(text)
            if text == "BYE":
                self.state = SessionState.EXIT
            return self.state

        def requires_editor_submission(self) -> bool:
            return False

    async def _exercise() -> tuple[NegotiationRunner, FakeWriter]:
        reader = NegotiationReader(
            [
                b"\xff\xfb\x01\xff\xfd\x03HELLO\r\n",
                b"\xff\xfe\x23\xff\xfc\x05BYE\r\n",
            ]
        )
        runner = NegotiationRunner()
        writer = FakeWriter()
        transport = RecordingTelnetTransport(
            runner,
            reader,  # type: ignore[arg-type]
            writer,  # type: ignore[arg-type]
            poll_interval=0.0,
            idle_timer_scheduler_cls=None,
        )

        transport.open()
        pump_reader = transport.scheduled_coroutines[1]
        await asyncio.wait_for(pump_reader, timeout=0.1)
        transport.scheduled_coroutines[0].close()
        return runner, writer

    runner, writer = asyncio.run(_exercise())
    assert runner.commands == ["HELLO", "BYE"]
    assert writer.buffer == [
        b"\xff\xfe\x01",
        b"\xff\xfc\x03",
        b"\xff\xfc\x23",
        b"\xff\xfe\x05",
    ]


def test_telnet_transport_binary_mode_preserves_payload() -> None:
    class BinaryReader:
        def __init__(self, payloads: list[bytes]):
            self._payloads = deque(payloads)

        async def read(self, _size: int = -1) -> bytes:
            await asyncio.sleep(0)
            if self._payloads:
                return self._payloads.popleft()
            return b""

        async def readline(self) -> bytes:  # pragma: no cover - should not be called
            raise AssertionError("binary mode should not invoke readline()")

    class BinaryRunner:
        def __init__(self) -> None:
            self.console = object()
            self.state = SessionState.MAIN_MENU
            self.commands: list[str] = []

        def read_output(self) -> str:
            return ""

        def send_command(self, text: str) -> SessionState:
            self.commands.append(text)
            return self.state

        def requires_editor_submission(self) -> bool:
            return False

    async def _exercise() -> tuple[str, list[str]]:
        payload = b"\x00\x13BIN\x11\xfeDATA\r\n\x00"
        reader = BinaryReader([payload, b""])
        writer = FakeWriter()
        runner = BinaryRunner()
        transport = RecordingTelnetTransport(
            runner,
            reader,  # type: ignore[arg-type]
            writer,  # type: ignore[arg-type]
            poll_interval=0.0,
            idle_timer_scheduler_cls=None,
        )
        transport.set_binary_mode(True)
        transport.open()
        pump_reader = transport.scheduled_coroutines[1]
        await asyncio.wait_for(pump_reader, timeout=0.1)
        transport.scheduled_coroutines[0].close()
        received = transport.receive()
        return received, runner.commands

    received, commands = asyncio.run(_exercise())
    assert received.encode("latin-1") == b"\x00\x13BIN\x11\xfeDATA\r\n\x00"
    assert commands == []


def test_telnet_transport_handles_empty_editor_cycles_gracefully() -> None:
    class EmptyReader:
        async def readline(self) -> bytes:
            await asyncio.sleep(0)
            return b""

    class IdleRunner:
        def __init__(self, console: Optional[FakeConsole] = None) -> None:
            self.console = console
            self.state = SessionState.MAIN_MENU
            self.editor_context = None
            self.indicator_controller = None

        def read_output(self) -> str:
            return ""

        def send_command(self, text: str) -> SessionState:
            return self.state

        def requires_editor_submission(self) -> bool:
            return False

        def set_indicator_controller(self, controller) -> None:
            self.indicator_controller = controller

    async def _exercise() -> StubIndicatorController:
        console = FakeConsole()
        runner = IdleRunner(console)
        instrumentation = SessionInstrumentation(
            runner,
            indicator_controller_cls=StubIndicatorController,
            idle_timer_scheduler_cls=IdleTimerScheduler,
        )
        writer = FakeWriter()
        transport = RecordingTelnetTransport(
            runner,
            EmptyReader(),  # type: ignore[arg-type]
            writer,  # type: ignore[arg-type]
            instrumentation=instrumentation,
        )

        transport.open()
        pump_reader = transport.scheduled_coroutines[1]
        await asyncio.wait_for(pump_reader, timeout=0.1)
        transport.scheduled_coroutines[0].close()
        controller = instrumentation.ensure_indicator_controller()
        assert controller is not None
        return controller

    controller = asyncio.run(_exercise())
    assert controller.carrier_states[0] is True
    assert controller.carrier_states[-1] is False

