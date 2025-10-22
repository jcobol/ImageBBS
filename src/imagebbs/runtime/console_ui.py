"""Curses-based sysop console display for the runtime session."""

from __future__ import annotations

import curses
import time
from dataclasses import dataclass
from typing import Callable, Tuple, TYPE_CHECKING

from ..device_context import ConsoleService
from ..petscii import translate_petscii
from .indicator_controller import IndicatorController

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
        time_source: Callable[[], float] | None = None,
    ) -> None:
        self.console = console
        self._time_source = time_source or time.monotonic
        self._epoch: float | None = None
        self._last_second: int | None = None

    def reset(self) -> None:
        """Clear cached timing state so a new session can start at ``0:00``."""

        self._epoch = None
        self._last_second = None

    def tick(self) -> None:
        """Advance the idle timer when the elapsed second changes."""

        now = self._time_source()
        if self._epoch is None:
            self._epoch = now
        elapsed_seconds = int(max(0.0, now - self._epoch))
        if self._last_second == elapsed_seconds:
            return
        digits = self._format_digits(elapsed_seconds)
        self.console.update_idle_timer_digits(digits)
        self._last_second = elapsed_seconds

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
        self._input_buffer: list[str] = []
        self._stop = False
        self._instrumentation = instrumentation

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

        total_cells = self.screen_width * self.screen_height
        screen_bytes, colour_bytes = self.console.peek_block(
            screen_address=ConsoleService._SCREEN_BASE,
            screen_length=total_cells,
            colour_address=ConsoleService._COLOUR_BASE,
            colour_length=total_cells,
        )

        screen_payload = self._normalise_payload(screen_bytes, total_cells, fill=0x20)
        colour_payload = self._normalise_payload(colour_bytes, total_cells, fill=0x00)

        screen_matrix = self._rows_from_linear(screen_payload, self.screen_width)
        colour_matrix = self._rows_from_linear(colour_payload, self.screen_width)

        pause_position = self._address_to_row_col(ConsoleService._PAUSE_SCREEN_ADDRESS)
        abort_position = self._address_to_row_col(ConsoleService._ABORT_SCREEN_ADDRESS)
        spinner_position = self._address_to_row_col(ConsoleService._SPINNER_SCREEN_ADDRESS)
        carrier_position = self._address_to_row_col(
            ConsoleService._CARRIER_INDICATOR_SCREEN_ADDRESS
        )

        pause_char = screen_payload[self._offset_for(ConsoleService._PAUSE_SCREEN_ADDRESS)]
        abort_char = screen_payload[self._offset_for(ConsoleService._ABORT_SCREEN_ADDRESS)]
        spinner_char = screen_payload[
            self._offset_for(ConsoleService._SPINNER_SCREEN_ADDRESS)
        ]
        carrier_char = screen_payload[
            self._offset_for(ConsoleService._CARRIER_INDICATOR_SCREEN_ADDRESS)
        ]

        idle_timer_digits = tuple(
            screen_payload[self._offset_for(address)]
            for address in ConsoleService._IDLE_TIMER_SCREEN_ADDRESSES
        )
        idle_timer_positions = tuple(
            self._address_to_row_col(address)
            for address in ConsoleService._IDLE_TIMER_SCREEN_ADDRESSES
        )

        pane_length = ConsoleService._MASKED_PANE_WIDTH
        pane_screen, pane_colour = self.console.peek_block(
            screen_address=ConsoleService._MASKED_PANE_SCREEN_BASE,
            screen_length=pane_length,
            colour_address=ConsoleService._MASKED_PANE_COLOUR_BASE,
            colour_length=pane_length,
        )
        pane_chars = tuple(self._normalise_payload(pane_screen, pane_length, fill=0x20))
        pane_colours = tuple(self._normalise_payload(pane_colour, pane_length, fill=0x00))

        overlay_length = ConsoleService._MASKED_OVERLAY_WIDTH
        overlay_screen, overlay_colour = self.console.peek_block(
            screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
            screen_length=overlay_length,
            colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
            colour_length=overlay_length,
        )
        overlay_chars = tuple(
            self._normalise_payload(overlay_screen, overlay_length, fill=0x20)
        )
        overlay_colours = tuple(
            self._normalise_payload(overlay_colour, overlay_length, fill=0x00)
        )

        return ConsoleFrame(
            screen_chars=screen_matrix,
            screen_colours=colour_matrix,
            masked_pane_chars=pane_chars,
            masked_pane_colours=pane_colours,
            masked_overlay_chars=overlay_chars,
            masked_overlay_colours=overlay_colours,
            pause_active=self._indicator_active(pause_char),
            abort_active=self._indicator_active(abort_char),
            carrier_active=self._indicator_active(carrier_char),
            spinner_char=spinner_char,
            pause_position=pause_position,
            abort_position=abort_position,
            carrier_position=carrier_position,
            spinner_position=spinner_position,
            idle_timer_digits=tuple(int(digit) for digit in idle_timer_digits),
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

        input_row = overlay_row + 2
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
        if key in (curses.KEY_EXIT, 27):
            self._stop = True
            return False
        if key in (curses.KEY_ENTER, 10, 13):
            command = "".join(self._input_buffer)
            if self.runner is not None:
                self.runner.send_command(command)
            self._input_buffer.clear()
            return True
        if key in (curses.KEY_BACKSPACE, 127, 8):
            if self._input_buffer:
                self._input_buffer.pop()
            return True
        if key == 3:  # Ctrl+C
            self._stop = True
            return False
        if 0 <= key < 256:
            char = chr(key)
            if char.isprintable():
                self._input_buffer.append(char)
        return True

    def _render_input(self, stdscr: "curses._CursesWindow", row: int) -> None:
        prompt = "CMD> "
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

    def _normalise_payload(
        self, payload: bytes | None, length: int, *, fill: int
    ) -> bytes:
        if length <= 0:
            return b""
        if payload is None:
            return bytes([fill] * length)
        data = bytes(payload)
        if len(data) < length:
            data += bytes([fill] * (length - len(data)))
        elif len(data) > length:
            data = data[:length]
        return data

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


from ..session_kernel import SessionState  # noqa: E402  (circular import guard)

