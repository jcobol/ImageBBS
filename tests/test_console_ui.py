from __future__ import annotations
import io
from dataclasses import dataclass
from typing import Sequence

import pytest

from imagebbs.device_context import Console, ConsoleFramePayload, ConsoleService
from imagebbs.message_editor import EditorState
from imagebbs.runtime.cli import drive_session
from imagebbs.runtime.console_ui import IdleTimerScheduler, SysopConsoleApp, translate_petscii
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


def test_idle_timer_scheduler_honours_custom_interval() -> None:
    # Why: verify non-default intervals still drive digit updates at the requested cadence.
    console = RecordingConsoleService()
    timer_source = FakeMonotonic()
    timer = IdleTimerScheduler(
        console,
        idle_tick_interval=0.5,
        time_source=timer_source,
    )

    timer.tick()
    assert console.digit_history[-1] == (0x30, 0x30, 0x30)

    timer_source.advance(0.4)
    timer.tick()
    assert len(console.digit_history) == 1

    timer_source.advance(0.1)
    timer.tick()
    assert len(console.digit_history) == 2
    assert console.digit_history[-1] == (0x30, 0x30, 0x30)

    timer_source.advance(0.6)
    timer.tick()
    assert console.digit_history[-1] == (0x30, 0x30, 0x31)


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


def test_drive_session_threads_idle_interval(monkeypatch) -> None:
    # Why: ensure the synchronous CLI path applies custom idle intervals to scheduler instances.
    captured: list[float] = []

    class RecordingScheduler(IdleTimerScheduler):
        def __init__(
            self,
            console: ConsoleService,
            *,
            idle_tick_interval: float = 1.0,
            time_source=None,
        ) -> None:
            # Why: capture the configured interval so the test can assert correct propagation.
            captured.append(idle_tick_interval)
            super().__init__(
                console,
                idle_tick_interval=idle_tick_interval,
                time_source=time_source,
            )

    monkeypatch.setattr(
        "imagebbs.runtime.cli._resolve_idle_timer_scheduler_cls",
        lambda: RecordingScheduler,
    )

    class RecordingRunner:
        def __init__(self) -> None:
            # Why: provide a minimal runner facade so drive_session can instantiate instrumentation.
            self.console = ConsoleService(Console())
            self.state = SessionState.MAIN_MENU

        def set_indicator_controller(self, controller) -> None:
            # Why: record the controller assignment expected by the CLI wiring.
            self.indicator_controller = controller

        def read_output(self) -> str:
            # Why: emulate the runner interface without producing output during the loop.
            return ""

        def set_pause_indicator_state(self, active: bool) -> None:
            # Why: accept pause toggle requests even though the test never uses them.
            self.pause_state = active

        def send_command(self, command: str) -> SessionState:
            # Why: flip to EXIT on any command so drive_session terminates promptly.
            self.state = SessionState.EXIT
            return self.state

    runner = RecordingRunner()
    input_stream = io.StringIO("")
    output_stream = io.StringIO()

    result = drive_session(
        runner,
        input_stream=input_stream,
        output_stream=output_stream,
        idle_tick_interval=0.25,
    )

    assert result is SessionState.MAIN_MENU
    assert captured == [0.25]


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


class FakeCursesWindow:
    def __init__(self, inputs: Sequence[int], input_row: int) -> None:
        # Why: retain scripted keystrokes and capture rendered prompts without relying on real curses.
        self._inputs = list(inputs)
        self._nodelay = True
        self._timeout = 0
        self._cursor = (0, 0)
        self._input_row = input_row
        self._current_input_render: list[str] = []
        self.render_history: list[str] = []

    def nodelay(self, flag: bool) -> None:
        # Why: toggle blocking behaviour so editor reads can consume scripted keystrokes.
        self._nodelay = bool(flag)

    def timeout(self, value: int) -> None:
        # Why: maintain compatibility with curses' timeout API even though tests ignore the value.
        self._timeout = int(value)

    def getch(self) -> int:
        # Why: feed keystrokes to the adapter when blocking mode is enabled.
        if self._nodelay:
            return -1
        if not self._inputs:
            return -1
        return self._inputs.pop(0)

    def move(self, row: int, col: int) -> None:
        # Why: track cursor positioning so ``clrtoeol`` affects the intended command row snapshot.
        self._cursor = (row, col)

    def clrtoeol(self) -> None:
        # Why: clear the cached command-row string before new characters are painted.
        row, _ = self._cursor
        if row == self._input_row:
            self._current_input_render = []

    def addch(self, row: int, col: int, char, attrs: int = 0) -> None:
        # Why: accumulate the characters shown on the command row for later assertions.
        if row != self._input_row:
            return
        if isinstance(char, int):
            glyph = chr(char)
        else:
            glyph = char
        self._current_input_render.append(glyph)

    def refresh(self) -> None:
        # Why: snapshot the most recent command prompt rendering as the UI flushes to screen.
        if self._current_input_render:
            self.render_history.append("".join(self._current_input_render))


class FakeEditorContext:
    def __init__(self) -> None:
        # Why: supply the minimal attributes accessed by the editor submission handler.
        self.current_message = ""
        self.draft_buffer: list[str] = []
        self.selected_message_id: int | None = None


class FakeEditorRunner:
    def __init__(self, console: ConsoleService) -> None:
        # Why: emulate ``SessionRunner`` behaviour without invoking the full kernel stack.
        self.console = console
        self.state = SessionState.MESSAGE_EDITOR
        self._editor_state: EditorState | None = EditorState.POST_MESSAGE
        self._requires_submission = True
        self._context = FakeEditorContext()
        self.abort_indicator_history: list[bool] = []
        self.submissions: list[tuple[str | None, list[str]]] = []
        self.abort_calls = 0
        self._indicator_controller = None

    def set_indicator_controller(self, controller) -> None:
        # Why: accept the indicator controller assignment that ``SysopConsoleApp`` performs on start-up.
        self._indicator_controller = controller

    @property
    def editor_context(self) -> FakeEditorContext:
        # Why: expose the editor context consumed by ``EditorSubmissionHandler``.
        return self._context

    def read_output(self) -> str:
        # Why: mimic the runner's output drain without producing additional screen data.
        return ""

    def requires_editor_submission(self) -> bool:
        # Why: advertise when the submission handler should collect subject/body text.
        return self._requires_submission

    def get_editor_state(self) -> EditorState | None:
        # Why: surface the editor state so the handler can branch between POST and EDIT flows.
        return self._editor_state

    def submit_editor_draft(
        self,
        *,
        subject: str | None = None,
        lines: Sequence[str] | None = None,
    ) -> SessionState:
        # Why: capture submitted subject/body pairs and transition back to the menu state.
        payload_lines = list(lines or [])
        self.submissions.append((subject, payload_lines))
        if subject is not None:
            self._context.current_message = subject
        self._context.draft_buffer = payload_lines
        self._requires_submission = False
        self._editor_state = None
        self.state = SessionState.MAIN_MENU
        return self.state

    def abort_editor(self) -> SessionState:
        # Why: flag abort cycles so tests can confirm ``/abort`` handling clears the draft.
        self.abort_calls += 1
        self._requires_submission = False
        self._editor_state = None
        self.state = SessionState.MAIN_MENU
        return self.state

    def set_abort_indicator_state(self, active: bool) -> None:
        # Why: record the indicator toggles initiated by the submission handler.
        self.abort_indicator_history.append(active)


def test_sysop_console_app_collects_editor_submission() -> None:
    console = RecordingConsoleService()
    runner = FakeEditorRunner(console)
    app = SysopConsoleApp(console, runner=runner)

    input_row = app._input_row_index()
    inputs = [
        ord("T"),
        ord("e"),
        ord("s"),
        ord("t"),
        10,
        ord("H"),
        ord("e"),
        ord("l"),
        ord("l"),
        ord("o"),
        10,
        ord("/"),
        ord("s"),
        ord("e"),
        ord("n"),
        ord("d"),
        10,
    ]
    window = FakeCursesWindow(inputs, input_row)

    handled = app._collect_editor_submission(window)

    assert handled is True
    assert runner.submissions == [("Test", ["Hello"])]
    assert runner.state is SessionState.MAIN_MENU
    assert runner.requires_editor_submission() is False
    assert runner.abort_indicator_history == [True, False]
    assert app._input_buffer == []
    assert app._input_prompt == app._default_prompt
    assert all(code == 0x20 for code in app._masked_input_state)
    assert window.render_history and window.render_history[-1] == app._default_prompt


def test_sysop_console_app_editor_abort_clears_masked_buffer() -> None:
    console = RecordingConsoleService()
    runner = FakeEditorRunner(console)
    app = SysopConsoleApp(console, runner=runner)

    input_row = app._input_row_index()
    inputs = [
        ord("/"),
        ord("a"),
        ord("b"),
        ord("o"),
        ord("r"),
        ord("t"),
        10,
    ]
    window = FakeCursesWindow(inputs, input_row)

    handled = app._collect_editor_submission(window)

    assert handled is True
    assert runner.abort_calls == 1
    assert runner.submissions == []
    assert runner.state is SessionState.MAIN_MENU
    assert runner.requires_editor_submission() is False
    assert runner.abort_indicator_history == [True, False]
    assert app._input_buffer == []
    assert app._input_prompt == app._default_prompt
    assert all(code == 0x20 for code in app._masked_input_state)
    assert window.render_history and window.render_history[-1] == app._default_prompt
