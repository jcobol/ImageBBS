from __future__ import annotations
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.device_context import ConsoleService
from scripts.prototypes.runtime.console_ui import SysopConsoleApp, translate_petscii


@dataclass
class FakePetsciiScreen:
    width: int = 40
    height: int = 25


class FakeConsoleService:
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


@pytest.mark.parametrize(
    "code, expected_char, expected_reverse",
    [
        (0x01, "A", False),
        (0x1C, "£", False),
        (0x41, "A", False),
        (0x61, "a", False),
        (0x7F, "⌂", False),
        (0xA0, " ", False),
        (0xB0, "0", True),
        (0xC1, "A", True),
        (0xFA, "Z", True),
    ],
)
def test_translate_petscii_maps_screen_codes(
    code: int, expected_char: str, expected_reverse: bool
) -> None:
    char, reverse = translate_petscii(code)
    assert char == expected_char
    assert reverse is expected_reverse
