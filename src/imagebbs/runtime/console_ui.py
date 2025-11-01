"""Curses-based sysop console display for the runtime session."""

from __future__ import annotations

import curses
import time
from dataclasses import dataclass
from typing import Callable, Tuple, TYPE_CHECKING

from ..device_context import ConsoleService
from ..petscii import translate_petscii
from .editor_submission import (
    DEFAULT_EDITOR_ABORT_COMMAND,
    DEFAULT_EDITOR_SUBMIT_COMMAND,
    EditorSubmissionHandler,
    SyncEditorIO,
)
from .indicator_controller import IndicatorController
from .masked_input import MaskedPaneKeystroke, apply_masked_pane_keystrokes

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from .session_instrumentation import SessionInstrumentation
    from .session_runner import SessionRunner


__all__ = ["ConsoleFrame", "IdleTimerScheduler", "SysopConsoleApp", "translate_petscii"]


@dataclass(slots=True)
class ConsoleFrame:
    """Snapshot of console state decoded for curses rendering."""

    screen_chars: Tuple[Tuple[int, ...], ...]
    screen_colours: Tuple[Tuple[int, ...], ...]
    masked_pane_chars: Tuple[int, ...]
    masked_pane_colours: Tuple[int, ...]
    masked_overlay_chars: Tuple[int, ...]
    masked_overlay_colours: Tuple[int, ...]
    pause_active: bool
    abort_active: bool
    carrier_active: bool
    spinner_char: int
    pause_colour: int
    abort_colour: int
    carrier_colour: int
    spinner_colour: int
    pause_position: Tuple[int, int]
    abort_position: Tuple[int, int]
    carrier_position: Tuple[int, int]
    spinner_position: Tuple[int, int]
    idle_timer_digits: Tuple[int, int, int]
    idle_timer_positions: Tuple[Tuple[int, int], ...]


class IdleTimerScheduler:
    """Track elapsed session time and refresh the idle timer digits."""

    def __init__(
        self,
        console: ConsoleService,
        *,
        idle_tick_interval: float = 1.0,
        time_source: Callable[[], float] | None = None,
    ) -> None:
        # Why: stash configuration so UI refresh code can translate elapsed time into timer digits.
        self.console = console
        self._time_source = time_source or time.monotonic
        self._epoch: float | None = None
        self._last_second: int | None = None
        interval = float(idle_tick_interval)
        if interval <= 0.0:
            interval = 1.0
        self._tick_interval = interval

    def reset(self) -> None:
        """Clear cached timing state so a new session can start at ``0:00``."""

        # Why: reset guards ensure each session restart begins with a clean timer display.
        self._epoch = None
        self._last_second = None

    def tick(self) -> None:
        """Advance the idle timer when the elapsed second changes."""

        # Why: honour custom tick cadences so throttled loops still update the timer accurately.
        now = self._time_source()
        if self._epoch is None:
            self._epoch = now
        elapsed_ticks = int(max(0.0, (now - self._epoch) / self._tick_interval))
        if self._last_second == elapsed_ticks:
            return
        elapsed_seconds = int(max(0.0, now - self._epoch))
        digits = self._format_digits(elapsed_seconds)
        self.console.update_idle_timer_digits(digits)
        self._last_second = elapsed_ticks

    def _format_digits(self, elapsed_seconds: int) -> Tuple[int, int, int]:
        minutes, seconds = divmod(max(0, elapsed_seconds), 60)
        minutes_digit = minutes % 10
        tens_digit, ones_digit = divmod(seconds, 10)
        return (
            0x30 + minutes_digit,
            0x30 + tens_digit,
            0x30 + ones_digit,
        )


class SysopConsoleApp:
    """Drive :class:`SessionRunner` inside a curses-based console window."""

    SCREEN_WIDTH = 40
    SCREEN_HEIGHT = 25
    _PAUSE_ACTIVATE_KEY = 19  # Ctrl+S
    _PAUSE_RELEASE_KEY = 17  # Ctrl+Q
    _ABORT_ACTIVATE_KEY = 24  # Ctrl+X
    _ABORT_RELEASE_KEY = 7  # Ctrl+G

    def __init__(
        self,
        console: ConsoleService,
        *,
        runner: "SessionRunner" | None = None,
        instrumentation: "SessionInstrumentation" | None = None,
        refresh_interval: float = 0.05,
    ) -> None:
        self.console = console
        self.runner = runner
        self.refresh_interval = float(refresh_interval)
        screen = getattr(console, "screen", None)
        self.screen_width = getattr(screen, "width", self.SCREEN_WIDTH)
        self.screen_height = getattr(screen, "height", self.SCREEN_HEIGHT)
        self._default_prompt = "CMD> "
        self._input_prompt = self._default_prompt
        self._input_buffer: list[str] = []
        self._stop = False
        self._instrumentation = instrumentation
        self._editor_submit_command = DEFAULT_EDITOR_SUBMIT_COMMAND
        self._editor_abort_command = DEFAULT_EDITOR_ABORT_COMMAND
        self._pause_hotkey_state = False
        self._pause_hotkey_synced = False
        self._abort_hotkey_state = False
        self._abort_hotkey_synced = False

        masked_width = getattr(console, "masked_pane_width", None)
        if masked_width is None:
            masked_width = getattr(console, "_MASKED_PANE_WIDTH", self.SCREEN_WIDTH)
        self._masked_input_width = int(masked_width)
        raw_colour = getattr(console, "screen_colour", None)
        if raw_colour is None:
            raw_colour = getattr(console, "_screen_colour", 0)
        try:
            default_colour = int(raw_colour) & 0xFF
        except TypeError:
            default_colour = 0
        self._masked_default_colour = default_colour
        self._masked_input_state: list[int] = [0x20] * self._masked_input_width
        self._masked_input_colours: list[int] = [default_colour] * self._masked_input_width

        controller = self._resolve_indicator_controller(instrumentation)
        scheduler = self._resolve_idle_timer_scheduler(instrumentation)

        self.indicator_controller = controller
        self.idle_timer_scheduler = scheduler

        if runner is not None:
            instrumentation_controller = (
                instrumentation.indicator_controller
                if instrumentation is not None
                else None
            )
            if instrumentation_controller is None:
                runner.set_indicator_controller(controller)

        self._reset_idle_timer()

    # Frame capture helpers -------------------------------------------------

    def capture_frame(self) -> ConsoleFrame:
        """Poll :class:`ConsoleService` and translate spans into matrices."""

        payload = self.console.export_frame_payload(
            self.screen_width, self.screen_height
        )

        screen_matrix = self._rows_from_linear(
            payload.screen_glyphs, self.screen_width
        )
        colour_matrix = self._rows_from_linear(
            payload.screen_colours, self.screen_width
        )

        pause_position = self._address_to_row_col(ConsoleService._PAUSE_SCREEN_ADDRESS)
        abort_position = self._address_to_row_col(ConsoleService._ABORT_SCREEN_ADDRESS)
        spinner_position = self._address_to_row_col(ConsoleService._SPINNER_SCREEN_ADDRESS)
        carrier_position = self._address_to_row_col(
            ConsoleService._CARRIER_INDICATOR_SCREEN_ADDRESS
        )

        idle_timer_positions = tuple(
            self._address_to_row_col(address)
            for address in ConsoleService._IDLE_TIMER_SCREEN_ADDRESSES
        )

        return ConsoleFrame(
            screen_chars=screen_matrix,
            screen_colours=colour_matrix,
            masked_pane_chars=tuple(payload.masked_pane_chars),
            masked_pane_colours=tuple(payload.masked_pane_colours),
            masked_overlay_chars=tuple(payload.masked_overlay_chars),
            masked_overlay_colours=tuple(payload.masked_overlay_colours),
            pause_active=payload.pause_active,
            abort_active=payload.abort_active,
            carrier_active=payload.carrier_active,
            spinner_char=payload.spinner_char,
            pause_colour=int(payload.pause_colour),
            abort_colour=int(payload.abort_colour),
            carrier_colour=int(payload.carrier_colour),
            spinner_colour=int(payload.spinner_colour),
            pause_position=pause_position,
            abort_position=abort_position,
            carrier_position=carrier_position,
            spinner_position=spinner_position,
            idle_timer_digits=tuple(int(digit) for digit in payload.idle_timer_digits),
            idle_timer_positions=idle_timer_positions,
        )

    # Rendering -------------------------------------------------------------

    def run(self) -> "SessionState":
        """Enter the curses event loop until the runner exits."""

        return curses.wrapper(self._run_loop)

    def _run_loop(self, stdscr: "curses._CursesWindow") -> "SessionState":
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(0)
        self._reset_idle_timer()
        state = SessionState.EXIT if self.runner is None else self.runner.state

        while not self._stop:
            frame = self.capture_frame()
            self.render_frame(stdscr, frame)

            if self.runner is not None:
                self.runner.read_output()
                state = self.runner.state
                if state is SessionState.EXIT:
                    break
                if state is SessionState.MESSAGE_EDITOR and self.runner.requires_editor_submission():
                    if self._collect_editor_submission(stdscr):
                        state = self.runner.state
                        if state is SessionState.EXIT:
                            break
                        continue

            self._poll_input(stdscr)
            self._run_idle_cycle()
            time.sleep(self.refresh_interval)

        return state

    def render_frame(self, stdscr: "curses._CursesWindow", frame: ConsoleFrame) -> None:
        """Translate ``frame`` into curses window updates."""

        indicator_positions = set()
        if frame.pause_active:
            indicator_positions.add(frame.pause_position)
        if frame.abort_active:
            indicator_positions.add(frame.abort_position)
        if frame.carrier_active:
            indicator_positions.add(frame.carrier_position)
        spinner_active = self._indicator_active(frame.spinner_char)
        if spinner_active:
            indicator_positions.add(frame.spinner_position)

        for row_index, row in enumerate(frame.screen_chars):
            for col_index, code in enumerate(row):
                char, reverse = translate_petscii(code)
                attrs = curses.A_REVERSE if reverse else curses.A_NORMAL
                if (row_index, col_index) in indicator_positions:
                    attrs |= curses.A_REVERSE
                try:
                    stdscr.addch(row_index, col_index, char, attrs)
                except curses.error:
                    continue

        pane_row = self.screen_height + 1
        for col_index, code in enumerate(frame.masked_pane_chars):
            char, reverse = translate_petscii(code)
            attrs = curses.A_DIM | (curses.A_REVERSE if reverse else curses.A_NORMAL)
            try:
                stdscr.addch(pane_row, col_index, char, attrs)
            except curses.error:
                continue

        overlay_row = pane_row + 1
        for col_index, code in enumerate(frame.masked_overlay_chars):
            char, reverse = translate_petscii(code)
            attrs = curses.A_DIM | (curses.A_REVERSE if reverse else curses.A_NORMAL)
            try:
                stdscr.addch(overlay_row, col_index, char, attrs)
            except curses.error:
                continue

        input_row = self._input_row_index()
        self._render_input(stdscr, input_row)
        stdscr.refresh()

    # Internal helpers ------------------------------------------------------

    def _resolve_indicator_controller(
        self, instrumentation: "SessionInstrumentation" | None
    ) -> IndicatorController:
        if instrumentation is not None:
            controller = instrumentation.ensure_indicator_controller()
            if controller is not None:
                return controller
        controller = IndicatorController(self.console)
        if instrumentation is not None:
            controller.set_carrier(False)
        return controller

    def _resolve_idle_timer_scheduler(
        self, instrumentation: "SessionInstrumentation" | None
    ) -> IdleTimerScheduler:
        if instrumentation is not None:
            scheduler = instrumentation.ensure_idle_timer_scheduler()
            if scheduler is not None:
                return scheduler
        return IdleTimerScheduler(self.console)

    def _reset_idle_timer(self) -> None:
        instrumentation = self._instrumentation
        if (
            instrumentation is not None
            and instrumentation.idle_timer_scheduler is not None
        ):
            instrumentation.reset_idle_timer()
            return
        if self.idle_timer_scheduler is not None:
            self.idle_timer_scheduler.reset()

    def _run_idle_cycle(self) -> None:
        self._sync_control_indicators()  # Why: flush pending control-key toggles before timers advance their cadence.
        instrumentation = self._instrumentation
        if (
            instrumentation is not None
            and (
                instrumentation.indicator_controller is not None
                or instrumentation.idle_timer_scheduler is not None
            )
        ):
            instrumentation.on_idle_cycle()
            missing_controller = instrumentation.indicator_controller is None
            missing_scheduler = instrumentation.idle_timer_scheduler is None
            if not missing_controller and not missing_scheduler:
                return
            if missing_controller and self.indicator_controller is not None:
                self.indicator_controller.on_idle_tick()
            if missing_scheduler and self.idle_timer_scheduler is not None:
                self.idle_timer_scheduler.tick()
            return
        if self.indicator_controller is not None:
            self.indicator_controller.on_idle_tick()
        if self.idle_timer_scheduler is not None:
            self.idle_timer_scheduler.tick()

    def _resolve_masked_input_colour(self, override: int | None = None) -> int:
        # Why: Track the BASIC ``mcolor`` equivalent so staged glyphs retain the sysop tint.
        if override is None:
            colour = self.console.screen_colour & 0xFF
        else:
            colour = int(override) & 0xFF
        self._masked_default_colour = colour
        return colour

    def _stage_masked_input_character(
        self, offset: int, glyph: int, *, colour: int | None = None
    ) -> None:
        # Why: Route buffered keystrokes through ``write_masked_pane_cell`` before staging commits.
        if not 0 <= offset < self._masked_input_width:
            return
        glyph_byte = int(glyph) & 0xFF
        colour_value = self._resolve_masked_input_colour(colour)
        current_glyph = self._masked_input_state[offset]
        current_colour = self._masked_input_colours[offset]
        if glyph_byte == current_glyph and colour_value == current_colour:
            return
        keystroke = MaskedPaneKeystroke(
            offset=offset,
            glyph=glyph_byte,
            colour=colour_value,
        )
        apply_masked_pane_keystrokes(self.console, (keystroke,))
        self._masked_input_state[offset] = glyph_byte
        self._masked_input_colours[offset] = colour_value

    def _reset_masked_pane_input(self) -> None:
        # Why: Clear the masked pane once the buffered command hands off to the kernel.
        colour = self._resolve_masked_input_colour()
        for offset, glyph in enumerate(self._masked_input_state):
            if glyph != 0x20 or self._masked_input_colours[offset] != colour:
                self._stage_masked_input_character(offset, 0x20, colour=colour)

    def _glyph_for_char(self, char: str) -> int:
        # Why: Approximate BASIC key echoes by mirroring printable ASCII into PETSCII codes.
        return ord(char) & 0xFF

    def _input_row_index(self) -> int:
        # Why: Anchor the command/input row so editor prompts reuse the same viewport slot.
        return self.screen_height + 4

    def _set_input_prompt(self, prompt: str) -> None:
        # Why: Allow editor flows to replace the default "CMD> " prefix while staging user input.
        self._input_prompt = str(prompt)

    def _restore_default_prompt(self) -> None:
        # Why: Reset the command prompt after editor submissions hand control back to BASIC loops.
        self._input_prompt = self._default_prompt

    def _poll_input(self, stdscr: "curses._CursesWindow") -> None:
        if self.runner is None:
            return

        poll_delay = max(0.001, min(self.refresh_interval, 0.01))
        while True:
            key = stdscr.getch()
            if key == -1:
                time.sleep(poll_delay)
                break
            if not self._handle_key(key):
                break
            time.sleep(poll_delay)

    def _handle_key(self, key: int) -> bool:
        # Why: Mirror sysop keystrokes through the masked pane before ``&,50`` commits flush staging.
        if key in (curses.KEY_EXIT, 27):
            self._stop = True
            return False
        if key in (curses.KEY_ENTER, 10, 13):
            command = "".join(self._input_buffer)
            if self.runner is not None:
                self.runner.send_command(command)
            self._input_buffer.clear()
            self._reset_masked_pane_input()
            return True
        if key in (curses.KEY_BACKSPACE, 127, 8):
            if self._input_buffer:
                self._input_buffer.pop()
                self._stage_masked_input_character(len(self._input_buffer), 0x20)
            return True
        if key == 3:  # Ctrl+C
            self._stop = True
            return False
        if key == self._PAUSE_ACTIVATE_KEY:
            # Why: surface the sysop pause toggle immediately when the control-key arrives.
            self._pause_hotkey_state = True
            self._sync_control_indicators()
            return True
        if key == self._PAUSE_RELEASE_KEY:
            # Why: release the pause indicator when the resume control-key is pressed.
            self._pause_hotkey_state = False
            self._sync_control_indicators()
            return True
        if key == self._ABORT_ACTIVATE_KEY:
            # Why: expose a local abort lamp while the sysop holds the configured shortcut.
            self._abort_hotkey_state = True
            self._sync_control_indicators()
            return True
        if key == self._ABORT_RELEASE_KEY:
            # Why: reset the abort indicator once the shortcut sequence is released.
            self._abort_hotkey_state = False
            self._sync_control_indicators()
            return True
        if 0 <= key < 256:
            char = chr(key)
            if char.isprintable():
                self._input_buffer.append(char)
                offset = len(self._input_buffer) - 1
                glyph = self._glyph_for_char(char)
                self._stage_masked_input_character(offset, glyph)
        return True

    def _sync_control_indicators(self) -> None:
        # Why: keep pause/abort indicator toggles aligned with the most recent control-key state before each idle tick.
        runner = self.runner
        if runner is None:
            return
        pause_setter = getattr(runner, "set_pause_indicator_state", None)
        if (
            callable(pause_setter)
            and self._pause_hotkey_state != self._pause_hotkey_synced
        ):
            pause_setter(self._pause_hotkey_state)
            self._pause_hotkey_synced = self._pause_hotkey_state
        abort_setter = getattr(runner, "set_abort_indicator_state", None)
        if (
            callable(abort_setter)
            and self._abort_hotkey_state != self._abort_hotkey_synced
        ):
            abort_setter(self._abort_hotkey_state)
            self._abort_hotkey_synced = self._abort_hotkey_state

    def _render_input(self, stdscr: "curses._CursesWindow", row: int) -> None:
        prompt = self._input_prompt
        text = prompt + "".join(self._input_buffer)
        try:
            stdscr.move(row, 0)
            stdscr.clrtoeol()
        except curses.error:
            return
        for index, char in enumerate(text[: self.screen_width]):
            try:
                stdscr.addch(row, index, char)
            except curses.error:
                break

    def _indicator_active(self, code: int) -> bool:
        return int(code) not in (0x00, 0x20)

    def _rows_from_linear(
        self, payload: bytes, width: int
    ) -> Tuple[Tuple[int, ...], ...]:
        if width <= 0:
            return tuple()
        cells = len(payload)
        height, remainder = divmod(cells, width)
        if remainder:
            height += 1
            payload += bytes([0x20] * (width - remainder))
        rows = []
        for row in range(height):
            start = row * width
            end = start + width
            rows.append(tuple(payload[start:end]))
        return tuple(rows[: self.screen_height])

    def _offset_for(self, address: int) -> int:
        offset = address - ConsoleService._SCREEN_BASE
        max_offset = self.screen_width * self.screen_height - 1
        if offset < 0:
            return 0
        if offset > max_offset:
            return max_offset
        return offset

    def _address_to_row_col(self, address: int) -> Tuple[int, int]:
        offset = self._offset_for(address)
        row = offset // self.screen_width
        col = offset % self.screen_width
        return row, col

    def _collect_editor_submission(self, stdscr: "curses._CursesWindow") -> bool:
        # Why: Bridge editor submission prompts into the curses UI whenever the runner requests input.
        runner = self.runner
        if runner is None:
            return False
        if not runner.requires_editor_submission():
            return False
        handler = EditorSubmissionHandler(
            runner,
            submit_command=self._editor_submit_command,
            abort_command=self._editor_abort_command,
        )
        io = _CursesEditorIO(self, stdscr)
        stdscr.nodelay(False)
        stdscr.timeout(-1)
        try:
            handled = handler.collect_sync(io)
        finally:
            stdscr.nodelay(True)
            stdscr.timeout(0)
            self._input_buffer.clear()
            self._reset_masked_pane_input()
            self._restore_default_prompt()
            self._render_input(stdscr, self._input_row_index())
            try:
                stdscr.refresh()
            except curses.error:
                pass
        return handled

    def _begin_editor_prompt(
        self,
        stdscr: "curses._CursesWindow",
        prompt: str,
    ) -> None:
        # Why: Present editor prompts on the command row so keystrokes mirror BASIC's cadence.
        self._set_input_prompt(prompt)
        self._input_buffer.clear()
        self._reset_masked_pane_input()
        self._render_input(stdscr, self._input_row_index())
        try:
            stdscr.refresh()
        except curses.error:
            pass

    def _readline_from_editor(
        self,
        stdscr: "curses._CursesWindow",
    ) -> str | None:
        # Why: Capture synchronous editor input while echoing characters through the masked pane.
        row = self._input_row_index()
        self._render_input(stdscr, row)
        buffer = self._input_buffer
        while True:
            key = stdscr.getch()
            if key == -1:
                continue
            if key in (curses.KEY_EXIT, 27):
                self._stop = True
                self._reset_masked_pane_input()
                buffer.clear()
                self._render_input(stdscr, row)
                return None
            if key in (curses.KEY_ENTER, 10, 13):
                line = "".join(buffer)
                buffer.clear()
                self._reset_masked_pane_input()
                self._render_input(stdscr, row)
                return line
            if key in (curses.KEY_BACKSPACE, 127, 8):
                if buffer:
                    buffer.pop()
                    self._stage_masked_input_character(len(buffer), 0x20)
                self._render_input(stdscr, row)
                continue
            if key == 3:
                self._stop = True
                self._reset_masked_pane_input()
                buffer.clear()
                self._render_input(stdscr, row)
                return None
            if 0 <= key < 256:
                char = chr(key)
                if char.isprintable():
                    buffer.append(char)
                    offset = len(buffer) - 1
                    glyph = self._glyph_for_char(char)
                    self._stage_masked_input_character(offset, glyph)
                    self._render_input(stdscr, row)
        return None


from ..session_kernel import SessionState  # noqa: E402  (circular import guard)


class _CursesEditorIO(SyncEditorIO):
    """Bridge :class:`EditorSubmissionHandler` prompts into the curses UI."""

    def __init__(
        self,
        app: SysopConsoleApp,
        stdscr: "curses._CursesWindow",
    ) -> None:
        # Why: capture shared state so synchronous handler calls can manipulate the console UI.
        self._app = app
        self._stdscr = stdscr

    def write_line(self, text: str = "") -> None:
        # Why: no-op placeholder because the runtime already renders the main screen contents.
        _ = text

    def write_prompt(self, prompt: str) -> None:
        # Why: delegate prompt rendering so the command row mirrors BASIC message entry prompts.
        self._app._begin_editor_prompt(self._stdscr, prompt)

    def readline(self) -> str | None:
        # Why: translate blocking keyboard reads into masked-pane aware text submissions.
        return self._app._readline_from_editor(
            self._stdscr,
        )

