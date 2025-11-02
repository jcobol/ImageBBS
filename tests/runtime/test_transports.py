"""Unit tests covering the native runtime transports."""

from __future__ import annotations

import asyncio
from collections import deque
from types import SimpleNamespace
from typing import Coroutine, Optional, cast

import pytest

from imagebbs.device_context import Console, ConsoleService
from imagebbs.message_editor import EditorState
from imagebbs.runtime.console_ui import IdleTimerScheduler
from imagebbs.runtime.indicator_controller import IndicatorController
from imagebbs.runtime.session_instrumentation import SessionInstrumentation
from imagebbs.runtime.session_runner import SessionRunner
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


# Why: exercise Telnet editor submissions without bootstrapping the full session runner.
class _TelnetEditorRunner:
    def __init__(self) -> None:
        self.console = object()
        self.state = SessionState.MESSAGE_EDITOR
        self.editor_context = SimpleNamespace(
            current_message="",
            draft_buffer=[],
            selected_message_id=None,
            modem_buffer=[],
            line_numbers_enabled=False,
        )
        self._requires_submission = True
        self.submissions: list[tuple[str | None, list[str] | None]] = []
        self.abort_states: list[bool] = []
        self.commands: list[str] = []
        self.indicator_controller = None

    # Why: trigger the handler once so the test can observe subject/body capture.
    def requires_editor_submission(self) -> bool:
        if self._requires_submission and self.state is SessionState.MESSAGE_EDITOR:
            self._requires_submission = False
            return True
        return False

    # Why: advertise the posting state so the handler gathers both subject and body text.
    def get_editor_state(self) -> EditorState | None:
        return EditorState.POST_MESSAGE

    # Why: capture the saved payload and transition back to the menu state.
    def submit_editor_draft(
        self, *, subject: str | None, lines: list[str] | None
    ) -> None:
        self.submissions.append((subject, list(lines) if lines else None))
        self.state = SessionState.MAIN_MENU

    # Why: simulate abort cycles invoked by the submission handler.
    def abort_editor(self) -> None:
        self.state = SessionState.MAIN_MENU

    # Why: record abort indicator toggles raised during the submission workflow.
    def set_abort_indicator_state(self, active: bool) -> None:
        self.abort_states.append(active)

    # Why: accept instrumentation-provided indicator controllers without exercising their behaviour.
    def set_indicator_controller(self, controller) -> None:
        self.indicator_controller = controller
        self._indicator_controller = controller

    # Why: the transport drains screen output, so the stub exposes an empty buffer.
    def read_output(self) -> str:
        return ""

    # Why: record commands forwarded by the transport, exiting when "EX" is encountered.
    def send_command(self, command: str) -> SessionState:
        self.commands.append(command)
        if command == "EX":
            self.state = SessionState.EXIT
        return self.state


# Why: feed scripted payloads into the Telnet transport coroutine.
class _TelnetEditorReader:
    def __init__(self, payloads: list[bytes]) -> None:
        self._payloads = deque(payloads)

    # Why: present queued modem lines to the transport while yielding control to the event loop.
    async def readline(self) -> bytes:
        await asyncio.sleep(0)
        if self._payloads:
            return self._payloads.popleft()
        return b""


def test_telnet_transport_applies_custom_idle_interval() -> None:
    # Why: ensure the asynchronous Telnet entry point propagates idle cadence overrides.

    class RecordingScheduler(IdleTimerScheduler):
        def __init__(
            self,
            console: ConsoleService,
            *,
            idle_tick_interval: float = 1.0,
            time_source=None,
        ) -> None:
            # Why: capture the interval so the test can confirm transport configuration.
            self.recorded_interval = idle_tick_interval
            super().__init__(
                console,
                idle_tick_interval=idle_tick_interval,
                time_source=time_source,
            )

    class RecordingRunner:
        def __init__(self) -> None:
            # Why: expose the console expected by the transport without running full sessions.
            self.console = FakeConsole()
            self.state = SessionState.MAIN_MENU

        def read_output(self) -> str:
            # Why: keep the transport idle during the check.
            return ""

        def set_indicator_controller(self, controller) -> None:
            # Why: accept controller wiring performed during transport start-up.
            self.indicator_controller = controller
            self._indicator_controller = controller

        def set_pause_indicator_state(self, active: bool) -> None:
            # Why: provide the hook consumed by Telnet pause tokens.
            self.pause_state = active

        def send_command(self, command: str) -> SessionState:
            # Why: echo state transitions without progressing a real runner.
            return self.state

    async def _exercise() -> float:
        runner = RecordingRunner()
        reader = asyncio.StreamReader()
        writer = FakeWriter()
        transport = TelnetModemTransport(
            runner,
            reader,
            writer,  # type: ignore[arg-type]
            poll_interval=0.0,
            idle_timer_scheduler_cls=RecordingScheduler,
            idle_tick_interval=0.3,
        )
        transport.open()
        await asyncio.sleep(0)
        scheduler = transport._idle_timer_scheduler
        assert scheduler is not None
        interval = getattr(scheduler, "recorded_interval", None)
        transport.close()
        await transport.wait_closed()
        assert interval is not None
        return float(interval)

    recorded_interval = asyncio.run(_exercise())
    assert recorded_interval == 0.3


# Why: verify Telnet transports store poll interval overrides for downstream diagnostics.
def test_telnet_transport_records_poll_interval() -> None:
    runner = SimpleNamespace(console=None)
    reader = cast(asyncio.StreamReader, object())
    writer = FakeWriter()

    transport = TelnetModemTransport(
        runner,
        reader,
        writer,  # type: ignore[arg-type]
        poll_interval=0.15,
    )

    assert transport.poll_interval == pytest.approx(0.15)


class StubIndicatorController:
    def __init__(self, console: object, **kwargs) -> None:
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


NEGOTIATION_FRAMES = [
    bytes([0xFF, 0xFB, 0x01]),
    bytes([0xFF, 0xFB, 0x03]),
    bytes([0xFF, 0xFD, 0x03]),
    bytes([0xFF, 0xFD, 0x00]),
    bytes([0xFF, 0xFB, 0x00]),
]


class RecordingTelnetTransport(TelnetModemTransport):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.scheduled_coroutines: list[Coroutine[object, object, None]] = []

    def _create_task(self, coro: Coroutine[object, object, None]) -> None:  # type: ignore[override]
        self.scheduled_coroutines.append(coro)


def test_telnet_transport_collects_editor_submission_with_custom_tokens() -> None:
    async def _exercise() -> tuple[_TelnetEditorRunner, str]:
        runner = _TelnetEditorRunner()
        instrumentation = SessionInstrumentation(
            runner,
            indicator_controller_cls=StubIndicatorController,
            idle_timer_scheduler_cls=None,
        )
        reader = _TelnetEditorReader(
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
    assert (
        "Type .S to save, .A to abort, .H for help, .O toggles line numbers. (/save also saves, /cancel also aborts.)"
        in transcript
    )


# Why: ensures Telnet sessions expose the board banner as soon as the transport opens.
def test_telnet_transport_bootstrap_writes_board_banner() -> None:
    # Why: isolate the asynchronous run loop while capturing the initial transcript.
    async def _exercise() -> tuple[str, SessionRunner]:
        runner = SessionRunner()
        reader = asyncio.StreamReader()
        writer = FakeWriter()
        transport = TelnetModemTransport(
            runner,
            reader,
            writer,  # type: ignore[arg-type]
            poll_interval=0.0,
        )
        transport.open()
        await asyncio.sleep(0)
        transport.close()
        await transport.wait_closed()
        payload = writer.buffer[len(NEGOTIATION_FRAMES) :]
        transcript = b"".join(payload).decode("latin-1", errors="ignore")
        return transcript, runner

    transcript, runner = asyncio.run(_exercise())
    defaults = runner.defaults
    assert transcript.startswith(defaults.board_name)
    segments = transcript.split("\r")
    assert len(segments) >= 3
    assert segments[1] == defaults.prompt
    assert segments[2] == defaults.copyright_notice


# Why: confirm the telnet negotiation frames precede the initial transcript and only emit once per session.
def test_telnet_transport_writes_telnet_negotiation_on_open() -> None:
    # Why: capture the writer buffer immediately after the transport opens.
    async def _exercise() -> list[bytes]:
        runner = SessionRunner()
        reader = asyncio.StreamReader()
        writer = FakeWriter()
        transport = TelnetModemTransport(
            runner,
            reader,
            writer,  # type: ignore[arg-type]
            poll_interval=0.0,
        )
        transport.open()
        return list(writer.buffer)

    buffer = asyncio.run(_exercise())
    assert buffer[: len(NEGOTIATION_FRAMES)] == NEGOTIATION_FRAMES
    remainder = buffer[len(NEGOTIATION_FRAMES) :]
    for frame in NEGOTIATION_FRAMES:
        assert frame not in remainder


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
            # Why: expose controller swaps so instrumentation honours idle loop configuration.
            self._indicator = controller
            self._indicator_controller = controller

    async def _exercise() -> None:
        console = FakeConsole()
        fake_clock = FakeClock([0.0, 1.0, 2.0, 3.0, 4.0])

        class RecordingIdleTimerScheduler(IdleTimerScheduler):
            def __init__(
                self,
                console_service,
                *,
                idle_tick_interval: float = 1.0,
            ):
                # Why: adapt the legacy test harness to the extended scheduler signature.
                super().__init__(
                    console_service,
                    idle_tick_interval=idle_tick_interval,
                    time_source=fake_clock,
                )

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
    class RecordingConsoleService(ConsoleService):
        def __init__(self) -> None:
            super().__init__(Console())
            # Preload distinct indicator colours so autodetection can be asserted in transport tests.
            self.spinner_glyphs: list[int] = []
            self.carrier_updates: list[tuple[int, int]] = []
            self.pause_colours: list[int | None] = []
            self.abort_colours: list[int | None] = []
            self.carrier_colour_updates: list[tuple[int | None, int | None]] = []
            colour_plan = {
                self._PAUSE_SCREEN_ADDRESS: 0x02,
                self._ABORT_SCREEN_ADDRESS: 0x08,
                self._CARRIER_LEADING_SCREEN_ADDRESS: 0x00,
                self._CARRIER_INDICATOR_SCREEN_ADDRESS: 0x02,
            }
            for screen_address, value in colour_plan.items():
                colour_address = self._COLOUR_BASE + (
                    screen_address - self._SCREEN_BASE
                )
                self.device.screen.poke_colour_address(colour_address, value)

        def set_pause_indicator(self, glyph: int, *, colour=None) -> None:  # pragma: no cover - exercised via IndicatorController
            # Record pause colours so autodetected palettes surface through instrumentation.
            super().set_pause_indicator(glyph, colour=colour)
            self.pause_colours.append(colour)

        def set_abort_indicator(self, glyph: int, *, colour=None) -> None:  # pragma: no cover - exercised via IndicatorController
            # Track abort colours to ensure autodetection propagates during transport setup.
            super().set_abort_indicator(glyph, colour=colour)
            self.abort_colours.append(colour)

        def set_carrier_indicator(
            self,
            *,
            leading_cell: int,
            indicator_cell: int,
            leading_colour=None,
            indicator_colour=None,
        ) -> None:
            # Mirror carrier colours so we can assert autodetected values survive transport mediation.
            super().set_carrier_indicator(
                leading_cell=leading_cell,
                indicator_cell=indicator_cell,
                leading_colour=leading_colour,
                indicator_colour=indicator_colour,
            )
            self.carrier_updates.append((leading_cell & 0xFF, indicator_cell & 0xFF))
            self.carrier_colour_updates.append((leading_colour, indicator_colour))

        def set_spinner_glyph(self, glyph: int, *, colour=None) -> None:
            # Capture spinner frames so the test can confirm idle ticks ran as expected.
            super().set_spinner_glyph(glyph, colour=colour)
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
            # Why: record controller bindings so instrumentation cache comparisons succeed in tests.
            self._indicator = controller
            self._indicator_controller = controller

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
    assert console.carrier_colour_updates
    assert console.carrier_colour_updates[0] == (0x00, 0x02)
    assert controller is not None
    assert len(console.spinner_glyphs) >= 3
    assert console.spinner_glyphs[0] == 0xB0
    assert console.spinner_glyphs[1] == 0xB1
    assert console.spinner_glyphs[-1] == 0x20


def test_telnet_transport_updates_indicator_on_first_idle_tick() -> None:
    # Why: ensure direct-controller transports refresh carrier and spinner state immediately after opening.

    class RecordingConsole(ConsoleService):
        def __init__(self) -> None:
            # Why: expose carrier and spinner writes so the test can inspect the first idle tick.
            super().__init__(Console())
            self.carrier_updates: list[tuple[int, int]] = []
            self.spinner_glyphs: list[int] = []

        def set_carrier_indicator(
            self,
            *,
            leading_cell: int,
            indicator_cell: int,
            leading_colour=None,
            indicator_colour=None,
        ) -> None:
            # Why: capture carrier glyphs so the test can confirm immediate synchronisation.
            super().set_carrier_indicator(
                leading_cell=leading_cell,
                indicator_cell=indicator_cell,
                leading_colour=leading_colour,
                indicator_colour=indicator_colour,
            )
            self.carrier_updates.append((leading_cell & 0xFF, indicator_cell & 0xFF))

        def set_spinner_glyph(self, glyph: int, *, colour=None) -> None:
            # Why: record spinner frames emitted by the first idle cycle.
            super().set_spinner_glyph(glyph, colour=colour)
            self.spinner_glyphs.append(glyph & 0xFF)

    class SingleIdleRunner:
        def __init__(self, console: RecordingConsole) -> None:
            # Why: expose the console and initial state required by the transport pumps.
            self.console = console
            self.state = SessionState.MAIN_MENU
            self._indicator = None
            self._cycles = 0

        def read_output(self) -> str:
            # Why: allow exactly one idle iteration before signalling exit to the transport loop.
            self._cycles += 1
            if self._cycles >= 5:
                self.state = SessionState.EXIT
            return ""

        def send_command(self, command: str) -> SessionState:  # pragma: no cover - unused
            # Why: satisfy the transport interface when pause tokens are forwarded.
            return self.state

        def set_indicator_controller(self, controller) -> None:  # pragma: no cover - unused
            # Why: record bindings so instrumentation compatibility checks continue to succeed.
            self._indicator = controller
            self._indicator_controller = controller

        def requires_editor_submission(self) -> bool:  # pragma: no cover - unused
            # Why: maintain the editor interface contract without triggering submissions.
            return False

        def set_pause_indicator_state(self, active: bool) -> None:  # pragma: no cover - unused
            # Why: accept pause toggles even though the test never exercises them.
            pass

    class BlockingReader:
        def __init__(self) -> None:
            # Why: keep the reader coroutine idle until the test releases it during shutdown.
            self._release = asyncio.Event()

        async def readline(self) -> bytes:
            # Why: mimic a telnet reader that stalls until the transport closes the connection.
            await self._release.wait()
            return b""

        def release(self) -> None:
            # Why: allow the pump to exit once the transport finishes its idle tick.
            self._release.set()

    async def _exercise() -> tuple[RecordingConsole, IndicatorController | None, IndicatorController | None]:
        console = RecordingConsole()
        runner = SingleIdleRunner(console)
        controller = IndicatorController(console)
        reader = BlockingReader()
        writer = FakeWriter()
        transport = TelnetModemTransport(
            runner,
            reader,  # type: ignore[arg-type]
            writer,  # type: ignore[arg-type]
            poll_interval=0.05,
            indicator_controller=controller,
            idle_timer_scheduler_cls=None,
        )

        transport.open()
        await asyncio.sleep(0.01)
        indicator_during = transport.indicator_controller
        reader.release()
        transport.close()
        await transport.wait_closed()
        indicator_after = transport.indicator_controller
        return console, indicator_during, indicator_after

    console, indicator_during, indicator_after = asyncio.run(_exercise())
    assert indicator_during is not None
    assert indicator_after is None
    assert console.carrier_updates
    assert console.carrier_updates[0] == (0xA0, 0xFA)
    assert console.spinner_glyphs
    assert console.spinner_glyphs[0] == 0xB0


def test_telnet_transport_ensures_indicator_controller_on_open_and_clears_cache() -> None:
    # Why: confirm instrumentation-backed transports synchronise controllers on open and drop cached instances on close.

    class IdleRunner:
        def __init__(self) -> None:
            # Why: provide the minimal hooks the transport expects while avoiding prolonged idle loops.
            self.console = object()
            self.state = SessionState.MAIN_MENU
            self._indicator = None
            self._cycles = 0

        def read_output(self) -> str:
            # Why: keep the pump idle while allowing the transport to remain open for observation.
            self._cycles += 1
            if self._cycles >= 5:
                self.state = SessionState.EXIT
            return ""

        def send_command(self, command: str) -> SessionState:  # pragma: no cover - unused
            # Why: satisfy the transport interface contract during shutdown.
            return self.state

        def set_indicator_controller(self, controller) -> None:
            # Why: expose bindings so instrumentation cache comparisons remain valid.
            self._indicator = controller
            self._indicator_controller = controller

        def requires_editor_submission(self) -> bool:  # pragma: no cover - unused
            # Why: prevent editor handshakes from triggering in the idle-only harness.
            return False

        def set_pause_indicator_state(self, active: bool) -> None:  # pragma: no cover - unused
            # Why: accept pause toggles to satisfy the transport interface.
            pass

    class BlockingReader:
        def __init__(self) -> None:
            # Why: let the reader task block until the test signals shutdown.
            self._release = asyncio.Event()

        async def readline(self) -> bytes:
            # Why: emulate a telnet stream that remains idle until the transport closes.
            await self._release.wait()
            return b""

        def release(self) -> None:
            # Why: allow the reader coroutine to exit once the transport begins closing.
            self._release.set()

    class RecordingInstrumentation:
        def __init__(self, controller: StubIndicatorController) -> None:
            # Why: capture controller lifecycle calls so the test can assert ordering.
            self.controller = controller
            self.calls: list[object] = []

        def ensure_indicator_controller(self) -> StubIndicatorController:
            # Why: record ensure invocations triggered by the transport on open.
            self.calls.append("ensure")
            return self.controller

        def set_carrier(self, active: bool) -> None:
            # Why: mirror instrumentation behaviour while keeping an audit trail for assertions.
            self.calls.append(("carrier", bool(active)))

        def reset_idle_timer(self) -> None:
            # Why: log reset requests so ordering can be checked.
            self.calls.append("reset")

        def ensure_idle_timer_scheduler(self):  # type: ignore[override]
            # Why: confirm transports request schedulers even when instrumentation supplies them.
            self.calls.append("scheduler")
            return None

    class TrackingTelnetTransport(TelnetModemTransport):
        def __init__(self, *args, **kwargs) -> None:
            # Why: expose ensure counters so the test can confirm open-time synchronisation.
            self.ensure_calls = 0
            super().__init__(*args, **kwargs)

        def _indicator_ensure_controller(self) -> IndicatorController | None:  # type: ignore[override]
            # Why: count ensure invocations before delegating to the mixin implementation.
            self.ensure_calls += 1
            return super()._indicator_ensure_controller()

    async def _exercise() -> tuple[list[object], int, IndicatorController | None, IndicatorController | None]:
        runner = IdleRunner()
        controller = StubIndicatorController(console=object())
        instrumentation = RecordingInstrumentation(controller)
        reader = BlockingReader()
        writer = FakeWriter()
        transport = TrackingTelnetTransport(
            runner,
            reader,  # type: ignore[arg-type]
            writer,  # type: ignore[arg-type]
            poll_interval=0.05,
            instrumentation=instrumentation,  # type: ignore[arg-type]
            idle_timer_scheduler_cls=None,
        )

        instrumentation.calls.clear()
        transport.ensure_calls = 0
        transport.open()
        indicator_before_close = transport.indicator_controller
        await asyncio.sleep(0.01)
        reader.release()
        transport.close()
        await transport.wait_closed()
        indicator_after_close = transport.indicator_controller
        return instrumentation.calls, transport.ensure_calls, indicator_before_close, indicator_after_close

    calls, ensure_count, indicator_before_close, indicator_after_close = asyncio.run(_exercise())
    assert calls
    assert calls[0] == "ensure"
    assert ("carrier", True) in calls
    assert calls[-1] == ("carrier", False)
    assert ensure_count == 1
    assert indicator_before_close is not None
    assert indicator_after_close is None


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
            # Why: retain instrumentation controllers so pause signals surface during assertions.
            self.indicator_controller = controller
            self._indicator_controller = controller

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


# Why: confirm Telnet transports raise abort requests when control bytes arrive.
def test_telnet_transport_requests_abort_service_on_control_token() -> None:
    class RecordingAbortService:
        def __init__(self) -> None:
            self.requests: list[bool] = []

        # Why: capture abort toggles triggered by the transport for assertions.
        def request_abort(self, abort: bool = True) -> None:
            self.requests.append(bool(abort))

    abort_service = RecordingAbortService()
    context = SimpleNamespace(service_registry={"file_transfer_abort": abort_service})

    class AbortAwareRunner:
        def __init__(self) -> None:
            self.console = object()
            self.state = SessionState.MAIN_MENU
            self.kernel = SimpleNamespace(context=context)

    runner = AbortAwareRunner()
    reader = SimpleNamespace()
    writer = SimpleNamespace(write=lambda payload: None)
    transport = TelnetModemTransport(
        runner,
        reader,  # type: ignore[arg-type]
        writer,  # type: ignore[arg-type]
        poll_interval=0.0,
    )

    filtered = transport._strip_pause_tokens(b"\x18HELLO")

    assert filtered == b"HELLO"
    assert abort_service.requests == [True]


# Why: ensure Telnet transports fall back to the console pause cell when no controller is available.
def test_telnet_pause_handling_without_controller() -> None:
    class RecordingConsole(ConsoleService):
        def __init__(self) -> None:
            # Why: preload the console and seed the pause colour for preservation checks.
            super().__init__(Console())
            self.glyphs: list[int] = []
            self.colours: list[int | None] = []
            colour_address = self._COLOUR_BASE + (
                self._PAUSE_SCREEN_ADDRESS - self._SCREEN_BASE
            )
            self.device.screen.poke_colour_address(colour_address, 0x05)

        def set_pause_indicator(self, glyph: int, *, colour=None) -> None:
            # Why: record glyph writes so the test can confirm fallback signalling.
            super().set_pause_indicator(glyph, colour=colour)
            self.glyphs.append(glyph & 0xFF)
            self.colours.append(colour)

    class FallbackRunner:
        def __init__(self, console: RecordingConsole) -> None:
            # Why: expose the console expected by the transport while tracking pause states.
            self.console = console
            self.state = SessionState.MAIN_MENU
            self.pause_states: list[bool] = []

        def read_output(self) -> str:
            # Why: keep the transport idle so pause tokens are the only inputs under test.
            return ""

        def set_pause_indicator_state(self, active: bool) -> None:
            # Why: mirror runner pause tracking without installing an indicator controller.
            self.pause_states.append(active)

    console = RecordingConsole()
    runner = FallbackRunner(console)
    reader = SimpleNamespace()
    writer = SimpleNamespace(write=lambda payload: None)
    transport = TelnetModemTransport(
        runner,
        reader,  # type: ignore[arg-type]
        writer,  # type: ignore[arg-type]
        poll_interval=0.0,
    )

    colour_address = console._COLOUR_BASE + (
        console._PAUSE_SCREEN_ADDRESS - console._SCREEN_BASE
    )
    initial_colour = console.device.screen.peek_colour_address(colour_address)

    filtered_pause = transport._strip_pause_tokens(b"\x13READY")
    filtered_resume = transport._strip_pause_tokens(b"\x11SET")

    assert filtered_pause == b"READY"
    assert filtered_resume == b"SET"
    assert runner.pause_states == [True, False]
    assert console.glyphs == [0xD0, 0x20]
    assert console.colours == [initial_colour, initial_colour]
    assert (
        console.device.screen.peek_colour_address(colour_address) == initial_colour
    )


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
            # Why: mirror transport wiring so cached instrumentation controllers remain authoritative.
            self.indicator_controller = controller
            self._indicator_controller = controller

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
    assert writer.buffer[: len(NEGOTIATION_FRAMES)] == NEGOTIATION_FRAMES
    assert writer.buffer[len(NEGOTIATION_FRAMES) :] == [
        b"\xff\xfe\x01",
        b"\xff\xfc#",
        b"\xff\xfe\x05",
    ]


def test_telnet_transport_discards_subnegotiation_sequences() -> None:
    class SubnegotiationReader:
        def __init__(self, payloads: list[bytes]) -> None:
            self._payloads = list(payloads)

        async def readline(self) -> bytes:
            await asyncio.sleep(0)
            if self._payloads:
                return self._payloads.pop(0)
            return b""

    class SubnegotiationRunner:
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

    async def _exercise() -> tuple[SubnegotiationRunner, FakeWriter]:
        reader = SubnegotiationReader(
            [
                b"\xff\xfa\x18\x01\x02\xff\xf0\xff\xfb\x01HELLO\r\n",
                b"",
            ]
        )
        runner = SubnegotiationRunner()
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
    assert runner.commands == ["HELLO"]
    assert writer.buffer[: len(NEGOTIATION_FRAMES)] == NEGOTIATION_FRAMES
    assert writer.buffer[len(NEGOTIATION_FRAMES) :] == [b"\xff\xfe\x01"]


def test_telnet_transport_discards_split_subnegotiation_sequences() -> None:
    class SplitSubnegReader:
        def __init__(self, payloads: list[bytes]) -> None:
            self._payloads = list(payloads)

        async def readline(self) -> bytes:
            await asyncio.sleep(0)
            if self._payloads:
                return self._payloads.pop(0)
            return b""

    class SplitSubnegRunner:
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

    async def _exercise() -> tuple[SplitSubnegRunner, FakeWriter]:
        reader = SplitSubnegReader(
            [
                b"\xff\xfa\x18\x01\x02",
                b"\xff\xf0\xff\xfd\x07BYE\r\n",
                b"",
            ]
        )
        runner = SplitSubnegRunner()
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
    assert runner.commands == ["BYE"]
    assert writer.buffer[: len(NEGOTIATION_FRAMES)] == NEGOTIATION_FRAMES
    assert writer.buffer[len(NEGOTIATION_FRAMES) :] == [b"\xff\xfc\x07"]


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
            # Why: surface instrumentation controller state so carrier assertions reflect transport activity.
            self.indicator_controller = controller
            self._indicator_controller = controller

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

