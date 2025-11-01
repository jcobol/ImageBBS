from unittest import mock

from imagebbs.device_context import Console, ConsoleService
from imagebbs.runtime.console_ui import SysopConsoleApp
from imagebbs.runtime.masked_input import (
    MaskedPaneKeystroke,
    apply_masked_pane_keystrokes,
)


def _resolve_palette_colour(value: int, palette: tuple[int, ...]) -> int:
    resolved = int(value) & 0xFF
    if resolved in palette:
        return resolved
    if 0 <= resolved < len(palette):
        return palette[resolved]
    return palette[0]


def test_apply_masked_pane_keystrokes_tracks_blink_cadence() -> None:
    console = Console()
    service = ConsoleService(console)

    keystrokes = [
        MaskedPaneKeystroke(offset=index, glyph=0x41 + index, colour=0x02)
        for index in range(5)
    ]

    payloads = apply_masked_pane_keystrokes(service, keystrokes)

    countdowns = [payload.countdown for payload in payloads]
    reverse_flags = [payload.reverse for payload in payloads]

    assert countdowns == [3, 2, 1, 0, 4]
    assert reverse_flags == [True, True, False, False, False]

    palette = console.screen.palette
    for index, payload in enumerate(payloads):
        screen_address = 0x0518 + index
        colour_address = 0xD918 + index
        assert console.screen.peek_screen_address(screen_address) == payload.glyph
        expected_colour = _resolve_palette_colour(payload.colour, palette)
        assert console.screen.peek_colour_address(colour_address) == expected_colour

    assert console.transcript_bytes == b""


def test_sysop_console_app_mirrors_masked_input_buffer() -> None:
    console = Console()
    service = ConsoleService(console)
    runner = mock.Mock()

    app = SysopConsoleApp(service, runner=runner)

    app._handle_key(ord("A"))
    app._handle_key(ord("B"))

    palette = console.screen.palette
    expected_colour = _resolve_palette_colour(service.screen_colour, palette)

    assert console.screen.peek_screen_address(0x0518) == 0xC1
    assert console.screen.peek_colour_address(0xD918) == expected_colour
    assert console.screen.peek_screen_address(0x0519) == 0xC2

    app._handle_key(127)

    assert console.screen.peek_screen_address(0x0519) == 0x20

    app._handle_key(10)

    runner.send_command.assert_called_with("A")
    assert console.screen.peek_screen_address(0x0518) == 0x20
    assert console.screen.peek_screen_address(0x0519) == 0x20

