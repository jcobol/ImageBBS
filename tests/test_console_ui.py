from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

import pytest

from imagebbs.device_context import Console, ConsoleFramePayload, ConsoleService
from imagebbs.runtime.console_ui import (
    IdleTimerScheduler,
    SysopConsoleApp,
    translate_petscii,
)
from imagebbs.runtime.session_instrumentation import SessionInstrumentation
from imagebbs.session_kernel import SessionState


@dataclass
class FakePetsciiScreen:
    width: int = 40
    height: int = 25


class FakeConsoleService:
    _SCREEN_BASE = ConsoleService._SCREEN_BASE
    _COLOUR_BASE = ConsoleService._COLOUR_BASE
    _PAUSE_SCREEN_ADDRESS = ConsoleService._PAUSE_SCREEN_ADDRESS
    _ABORT_SCREEN_ADDRESS = ConsoleService._ABORT_SCREEN_ADDRESS
    _SPINNER_SCREEN_ADDRESS = ConsoleService._SPINNER_SCREEN_ADDRESS
    _CARRIER_LEADING_SCREEN_ADDRESS = ConsoleService._CARRIER_LEADING_SCREEN_ADDRESS
    _CARRIER_INDICATOR_SCREEN_ADDRESS = ConsoleService._CARRIER_INDICATOR_SCREEN_ADDRESS

    def __init__(
        self,
        *,
        screen_bytes: bytes,
        colour_bytes: bytes,
        pane_screen: bytes,
        pane_colour: bytes,
        overlay_screen: bytes,
        overlay_colour: bytes,
    ) -> None:
        # Supply fixed buffers so console UI tests can emulate overlay state without a live ConsoleService.
        self._screen_bytes = bytes(screen_bytes)
        self._colour_bytes = bytes(colour_bytes)
        self._pane_screen = bytes(pane_screen)
        self._pane_colour = bytes(pane_colour)
        self._overlay_screen = bytes(overlay_screen)
        self._overlay_colour = bytes(overlay_colour)
        self.screen = FakePetsciiScreen()

    def peek_block(
        self,
        *,
        screen_address: int | None = None,
        screen_length: int | None = None,
        colour_address: int | None = None,
        colour_length: int | None = None,
    ) -> tuple[bytes | None, bytes | None]:
        screen_result = None
        colour_result = None

        if screen_length is not None:
            if screen_length < 0:
                raise ValueError("screen_length must be non-negative")
            if screen_length == 0:
                screen_result = b""
            elif screen_length:
                if screen_address is None:
                    raise ValueError("screen_address required when peeking screen bytes")
                screen_result = self._slice_screen(screen_address, screen_length)

        if colour_length is not None:
            if colour_length < 0:
                raise ValueError("colour_length must be non-negative")
            if colour_length == 0:
                colour_result = b""
            elif colour_length:
                if colour_address is None:
                    raise ValueError("colour_address required when peeking colour bytes")
                colour_result = self._slice_colour(colour_address, colour_length)

        return screen_result, colour_result

    def export_frame_payload(
        self, screen_width: int, screen_height: int
    ) -> ConsoleFramePayload:
        width = max(0, int(screen_width))
        height = max(0, int(screen_height))
        total_cells = width * height

        def _normalise(payload: bytes | None, length: int, fill: int) -> bytes:
            if length <= 0:
                return b""
            fill_value = int(fill) & 0xFF
            if payload is None:
                return bytes((fill_value,) * length)
            data = bytes(payload)
            if len(data) < length:
                data += bytes((fill_value,) * (length - len(data)))
            elif len(data) > length:
                data = data[:length]
            return data

        screen_bytes, colour_bytes = self.peek_block(
            screen_address=ConsoleService._SCREEN_BASE,
            screen_length=total_cells,
            colour_address=ConsoleService._COLOUR_BASE,
            colour_length=total_cells,
        )

        screen_payload = _normalise(screen_bytes, total_cells, 0x20)
        colour_payload = _normalise(colour_bytes, total_cells, 0x00)

        def clamp_offset(address: int) -> int:
            offset = int(address) - ConsoleService._SCREEN_BASE
            if total_cells <= 0:
                return 0
            max_offset = total_cells - 1
            if offset < 0:
                return 0
            if offset > max_offset:
                return max_offset
            return offset

        def read_screen(address: int, default: int) -> int:
            if total_cells <= 0 or not screen_payload:
                return int(default) & 0xFF
            return screen_payload[clamp_offset(address)]

        def indicator_active(code: int) -> bool:
            value = int(code) & 0xFF
            return value not in (0x00, 0x20)

        pause_char = read_screen(ConsoleService._PAUSE_SCREEN_ADDRESS, 0x20)
        abort_char = read_screen(ConsoleService._ABORT_SCREEN_ADDRESS, 0x20)
        carrier_char = read_screen(
            ConsoleService._CARRIER_INDICATOR_SCREEN_ADDRESS, 0x20
        )
        spinner_char = read_screen(ConsoleService._SPINNER_SCREEN_ADDRESS, 0x20)

        idle_timer_digits = tuple(
            read_screen(address, 0x30)
            for address in ConsoleService._IDLE_TIMER_SCREEN_ADDRESSES
        )

        pane_length = ConsoleService._MASKED_PANE_WIDTH
        pane_screen, pane_colour = self.peek_block(
            screen_address=ConsoleService._MASKED_PANE_SCREEN_BASE,
            screen_length=pane_length,
            colour_address=ConsoleService._MASKED_PANE_COLOUR_BASE,
            colour_length=pane_length,
        )
        pane_chars = _normalise(pane_screen, pane_length, 0x20)
        pane_colours = _normalise(pane_colour, pane_length, 0x00)

        overlay_length = ConsoleService._MASKED_OVERLAY_WIDTH
        overlay_screen, overlay_colour = self.peek_block(
            screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
            screen_length=overlay_length,
            colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
            colour_length=overlay_length,
        )
        overlay_chars = _normalise(overlay_screen, overlay_length, 0x20)
        overlay_colours = _normalise(overlay_colour, overlay_length, 0x00)

        return ConsoleFramePayload(
            screen_glyphs=screen_payload,
            screen_colours=colour_payload,
            masked_pane_chars=pane_chars,
            masked_pane_colours=pane_colours,
            masked_overlay_chars=overlay_chars,
            masked_overlay_colours=overlay_colours,
            pause_char=pause_char,
            abort_char=abort_char,
            carrier_char=carrier_char,
            spinner_char=spinner_char,
            pause_active=indicator_active(pause_char),
            abort_active=indicator_active(abort_char),
            carrier_active=indicator_active(carrier_char),
            idle_timer_digits=tuple(int(digit) & 0xFF for digit in idle_timer_digits),
        )

    def _slice_screen(self, address: int, length: int) -> bytes:
        if address >= ConsoleService._MASKED_OVERLAY_SCREEN_BASE:
            base = ConsoleService._MASKED_OVERLAY_SCREEN_BASE
            payload = self._overlay_screen
        elif address >= ConsoleService._MASKED_PANE_SCREEN_BASE:
            base = ConsoleService._MASKED_PANE_SCREEN_BASE
            payload = self._pane_screen
        else:
            base = ConsoleService._SCREEN_BASE
            payload = self._screen_bytes
        start = address - base
        end = start + length
        return bytes(payload[start:end])

    def _slice_colour(self, address: int, length: int) -> bytes:
        if address >= ConsoleService._MASKED_OVERLAY_COLOUR_BASE:
            base = ConsoleService._MASKED_OVERLAY_COLOUR_BASE
            payload = self._overlay_colour
        elif address >= ConsoleService._MASKED_PANE_COLOUR_BASE:
            base = ConsoleService._MASKED_PANE_COLOUR_BASE
            payload = self._pane_colour
        else:
            base = ConsoleService._COLOUR_BASE
            payload = self._colour_bytes
        start = address - base
        end = start + length
        return bytes(payload[start:end])


def build_console(
    *,
    pause: int,
    abort: int,
    spinner: int,
    carrier: int,
    idle_timer: tuple[int, int, int],
) -> FakeConsoleService:
    screen = FakePetsciiScreen()
    width = screen.width
    height = screen.height
    total_cells = width * height
    screen_payload = bytearray([0x20] * total_cells)
    colour_payload = bytearray([0x02] * total_cells)

    def set_cell(address: int, value: int) -> None:
        offset = address - ConsoleService._SCREEN_BASE
        screen_payload[offset] = value

    set_cell(ConsoleService._PAUSE_SCREEN_ADDRESS, pause)
    set_cell(ConsoleService._ABORT_SCREEN_ADDRESS, abort)
    set_cell(ConsoleService._SPINNER_SCREEN_ADDRESS, spinner)
    set_cell(ConsoleService._CARRIER_INDICATOR_SCREEN_ADDRESS, carrier)

    for digit, address in zip(idle_timer, ConsoleService._IDLE_TIMER_SCREEN_ADDRESSES):
        set_cell(address, digit)

    pane_screen = bytes(range(0x41, 0x41 + ConsoleService._MASKED_PANE_WIDTH))
    pane_colour = bytes(range(ConsoleService._MASKED_PANE_WIDTH))
    overlay_screen = bytes(range(0x61, 0x61 + ConsoleService._MASKED_OVERLAY_WIDTH))
    overlay_colour = bytes(range(0x10, 0x10 + ConsoleService._MASKED_OVERLAY_WIDTH))

    return FakeConsoleService(
        screen_bytes=bytes(screen_payload),
        colour_bytes=bytes(colour_payload),
        pane_screen=pane_screen,
        pane_colour=pane_colour,
        overlay_screen=overlay_screen,
        overlay_colour=overlay_colour,
    )


def test_capture_frame_reports_indicator_states_and_layout():
    pause_value = 0x50
    abort_value = 0x41
    spinner_value = 0x5C
    carrier_value = 0x43
    idle_digits = (0x31, 0x32, 0x33)
    console = build_console(
        pause=pause_value,
        abort=abort_value,
        spinner=spinner_value,
        carrier=carrier_value,
        idle_timer=idle_digits,
    )
    app = SysopConsoleApp(console)

    frame = app.capture_frame()

    assert frame.pause_active is True
    assert frame.abort_active is True
    assert frame.carrier_active is True
    assert frame.spinner_char == spinner_value

    pause_offset = ConsoleService._PAUSE_SCREEN_ADDRESS - ConsoleService._SCREEN_BASE
    expected_pause_position = (pause_offset // console.screen.width, pause_offset % console.screen.width)
    assert frame.pause_position == expected_pause_position
    assert frame.screen_chars[expected_pause_position[0]][expected_pause_position[1]] == pause_value

    assert frame.idle_timer_digits == tuple(int(value) for value in idle_digits)
    assert frame.masked_pane_chars[:5] == tuple(range(0x41, 0x46))
    assert frame.masked_overlay_chars[:5] == tuple(range(0x61, 0x66))

    first_cell_colour = frame.screen_colours[0][0]
    assert first_cell_colour == 0x02


def test_capture_frame_disables_indicators_when_blank():
    console = build_console(
        pause=0x20,
        abort=0x20,
        spinner=0x20,
        carrier=0x20,
        idle_timer=(0x30, 0x30, 0x30),
    )
    app = SysopConsoleApp(console)

    frame = app.capture_frame()

    assert frame.pause_active is False
    assert frame.abort_active is False
    assert frame.carrier_active is False
    assert frame.spinner_char == 0x20

    for digit in frame.idle_timer_digits:
        assert digit == 0x30


def test_console_service_export_matches_console_frame() -> None:
    pause_value = 0x50
    abort_value = 0x41
    spinner_value = 0x5C
    carrier_value = 0x43
    idle_digits = (0x31, 0x32, 0x33)
    console = build_console(
        pause=pause_value,
        abort=abort_value,
        spinner=spinner_value,
        carrier=carrier_value,
        idle_timer=idle_digits,
    )
    app = SysopConsoleApp(console)

    payload = console.export_frame_payload(
        console.screen.width, console.screen.height
    )
    frame = app.capture_frame()

    frame_screen_flat = tuple(
        code for row in frame.screen_chars for code in row
    )
    frame_colour_flat = tuple(
        code for row in frame.screen_colours for code in row
    )

    assert payload.screen_glyphs == bytes(frame_screen_flat)
    assert payload.screen_colours == bytes(frame_colour_flat)
    assert tuple(payload.masked_pane_chars) == frame.masked_pane_chars
    assert tuple(payload.masked_pane_colours) == frame.masked_pane_colours
    assert tuple(payload.masked_overlay_chars) == frame.masked_overlay_chars
    assert tuple(payload.masked_overlay_colours) == frame.masked_overlay_colours

    assert payload.pause_active is frame.pause_active
    assert payload.abort_active is frame.abort_active
    assert payload.carrier_active is frame.carrier_active
    assert payload.spinner_char == frame.spinner_char

    pause_row, pause_col = frame.pause_position
    assert payload.pause_char == frame.screen_chars[pause_row][pause_col]

    assert payload.idle_timer_digits == tuple(frame.idle_timer_digits)


@pytest.mark.parametrize(
    "code, expected_char, expected_reverse",
    [
        (0x01, "A", False),
        (0x1C, "£", False),
        (0x41, "A", False),
        (0x61, "▌", False),
        (0x63, "▔", False),
        (0x6B, "├", False),
        (0x72, "┬", False),
        (0x7D, "┌", False),
        (0x7F, "▚", False),
        (0xA0, " ", False),
        (0xB0, "0", True),
        (0xC1, "A", True),
        (0xE1, "A", True),
        (0xFA, "Z", True),
    ],
)
def test_translate_petscii_maps_screen_codes(
    code: int, expected_char: str, expected_reverse: bool
) -> None:
    char, reverse = translate_petscii(code)
    assert char == expected_char
    assert reverse is expected_reverse


class FakeMonotonic:
    def __init__(self) -> None:
        self._value = 0.0

    def advance(self, seconds: float) -> None:
        self._value += seconds

    def __call__(self) -> float:
        return self._value


class RecordingConsoleService(ConsoleService):
    def __init__(self) -> None:
        super().__init__(Console())
        self.digit_history: list[tuple[int, int, int]] = []

    def update_idle_timer_digits(
        self,
        digits: Sequence[int],
        *,
        colours: Sequence[int] | None = None,
    ) -> None:
        digits_tuple = tuple(int(value) & 0xFF for value in digits)
        self.digit_history.append(digits_tuple)
        super().update_idle_timer_digits(digits_tuple, colours=colours)


def _read_idle_digits(console: RecordingConsoleService) -> tuple[int, int, int]:
    addresses = ConsoleService._IDLE_TIMER_SCREEN_ADDRESSES
    return tuple(console.screen.peek_screen_address(address) for address in addresses)


class DummyRunner:
    def __init__(self, console: ConsoleService) -> None:
        self.console = console
        self.state = SessionState.MAIN_MENU
        self._indicator_controller = None

    def set_indicator_controller(self, controller) -> None:
        self._indicator_controller = controller

    def read_output(self) -> str:
        return ""

    def send_command(self, command: str) -> None:
        pass

    def set_pause_indicator_state(self, active: bool) -> None:
        if self._indicator_controller is not None:
            self._indicator_controller.set_pause(active)


def test_idle_timer_scheduler_updates_digits_and_preserves_colon() -> None:
    console = RecordingConsoleService()
    console.device.poke_screen_byte(0x04DF, 0x3A)
    timer_source = FakeMonotonic()
    timer = IdleTimerScheduler(console, time_source=timer_source)

    timer.tick()

    assert _read_idle_digits(console) == (0x30, 0x30, 0x30)
    assert console.screen.peek_screen_address(0x04DF) == 0x3A

    timer_source.advance(65)
    timer.tick()

    assert _read_idle_digits(console) == (0x31, 0x30, 0x35)
    assert console.screen.peek_screen_address(0x04DF) == 0x3A


def test_idle_timer_scheduler_overwrites_digits_without_transcript() -> None:
    console = RecordingConsoleService()
    timer_source = FakeMonotonic()
    timer = IdleTimerScheduler(console, time_source=timer_source)

    timer.tick()
    timer_source.advance(1.0)
    timer.tick()
    timer_source.advance(1.0)
    timer.tick()

    assert console.digit_history == [
        (0x30, 0x30, 0x30),
        (0x30, 0x30, 0x31),
        (0x30, 0x30, 0x32),
    ]
    assert console.device.transcript_bytes == b""


def test_sysop_console_app_frame_loop_updates_idle_timer_without_touching_colon() -> None:
    console = RecordingConsoleService()
    colon_address = 0x04DF
    console.device.poke_screen_byte(colon_address, 0x3A)

    timer_source = FakeMonotonic()
    app = SysopConsoleApp(console)

    scheduler = IdleTimerScheduler(console, time_source=timer_source)
    scheduler.reset()
    app.idle_timer_scheduler = scheduler
    console.digit_history.clear()

    def _run_frame() -> None:
        app.capture_frame()
        app._run_idle_cycle()

    _run_frame()
    assert _read_idle_digits(console) == (0x30, 0x30, 0x30)
    assert console.screen.peek_screen_address(colon_address) == 0x3A

    timer_source.advance(1.0)
    _run_frame()

    timer_source.advance(9.0)
    _run_frame()

    timer_source.advance(50.0)
    _run_frame()

    assert console.digit_history == [
        (0x30, 0x30, 0x30),
        (0x30, 0x30, 0x31),
        (0x30, 0x31, 0x30),
        (0x31, 0x30, 0x30),
    ]
    assert console.screen.peek_screen_address(colon_address) == 0x3A
    assert console.device.transcript_bytes == b""


def test_sysop_console_app_reuses_instrumentation_instances() -> None:
    console = RecordingConsoleService()
    runner = DummyRunner(console)
    instrumentation = SessionInstrumentation(runner)
    instrumentation.ensure_indicator_controller()
    instrumentation.reset_idle_timer()

    app = SysopConsoleApp(
        console,
        runner=runner,
        instrumentation=instrumentation,
    )

    assert app.indicator_controller is instrumentation.indicator_controller
    assert app.idle_timer_scheduler is instrumentation.idle_timer_scheduler


def test_sysop_console_app_idle_cycle_uses_instrumentation(monkeypatch) -> None:
    console = RecordingConsoleService()
    runner = DummyRunner(console)
    instrumentation = SessionInstrumentation(runner)
    instrumentation.ensure_indicator_controller()
    instrumentation.reset_idle_timer()

    app = SysopConsoleApp(
        console,
        runner=runner,
        instrumentation=instrumentation,
    )

    calls: list[str] = []

    def _record_idle_cycle() -> None:
        calls.append("idle")

    monkeypatch.setattr(instrumentation, "on_idle_cycle", _record_idle_cycle)

    app._run_idle_cycle()

    assert calls == ["idle"]


def test_sysop_console_app_shares_pause_indicator_with_instrumentation() -> None:
    console = RecordingConsoleService()
    runner = DummyRunner(console)
    instrumentation = SessionInstrumentation(runner)
    instrumentation.ensure_indicator_controller()
    instrumentation.reset_idle_timer()

    app = SysopConsoleApp(
        console,
        runner=runner,
        instrumentation=instrumentation,
    )

    runner.set_pause_indicator_state(True)
    frame = app.capture_frame()
    assert frame.pause_active is True

    runner.set_pause_indicator_state(False)
    frame = app.capture_frame()
    assert frame.pause_active is False
