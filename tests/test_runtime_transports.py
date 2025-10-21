import asyncio
from typing import Coroutine
from unittest import mock

from imagebbs.device_context import ConsoleService
from imagebbs.runtime.console_ui import IdleTimerScheduler
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
    def __init__(self) -> None:
        self.tick_count = 0
        self.carrier_states: list[bool] = []

    def set_carrier(self, active: bool) -> None:
        self.carrier_states.append(active)

    def on_idle_tick(self) -> None:
        self.tick_count += 1


class FakeRunner:
    def __init__(self, console: FakeConsole, idle_iterations: int) -> None:
        self.console = console
        self.state = SessionState.MAIN_MENU
        self._idle_iterations = idle_iterations
        self._opened = False
        self._calls = 0

    def read_output(self) -> str:
        if not self._opened:
            self._opened = True
            return ""
        self._calls += 1
        if self._calls > self._idle_iterations:
            self.state = SessionState.EXIT
        return ""


class FakeReader:
    async def readline(self) -> bytes:
        await asyncio.sleep(0)
        return b""


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


def test_telnet_transport_pump_console_updates_idle_timer() -> None:
    async def _exercise() -> None:
        fake_clock = FakeClock([0.0, 1.0, 2.0, 3.0, 4.0])
        console = FakeConsole()
        indicator = StubIndicatorController()
        runner = FakeRunner(console, idle_iterations=len(fake_clock.values))
        reader = FakeReader()
        writer = FakeWriter()
        transport = RecordingTelnetTransport(
            runner,
            reader,
            writer,
            poll_interval=0.0,
            indicator_controller=indicator,
        )

        class RecordingIdleTimerScheduler(IdleTimerScheduler):
            def __init__(self, console_service):
                super().__init__(console_service, time_source=fake_clock)

        with mock.patch(
            "scripts.prototypes.runtime.transports.IdleTimerScheduler",
            RecordingIdleTimerScheduler,
        ):
            transport.open()
            scheduler = transport._idle_timer_scheduler
            assert scheduler is not None
            assert transport.scheduled_coroutines

            pump_console = transport.scheduled_coroutines[0]
            try:
                await asyncio.wait_for(pump_console, timeout=0.1)
            finally:
                for coro in transport.scheduled_coroutines[1:]:
                    coro.close()

        addresses = ConsoleService._IDLE_TIMER_SCREEN_ADDRESSES
        digits = [console.screen[address] for address in addresses]
        assert digits == [0x30, 0x30, 0x34]
        assert console.digit_history[-1] == tuple(digits)
        assert indicator.tick_count >= len(fake_clock.values)

    asyncio.run(_exercise())
