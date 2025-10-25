"""Unit tests covering the native runtime transports."""

from __future__ import annotations

import asyncio
from typing import Coroutine, Optional

from imagebbs.device_context import ConsoleService
from imagebbs.runtime.console_ui import IdleTimerScheduler
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

