from scripts.prototypes.device_context import Console, ConsoleService
from scripts.prototypes.runtime.indicator_controller import IndicatorController


def test_indicator_controller_updates_indicators_without_transcript() -> None:
    console = Console()
    service = ConsoleService(console)
    controller = IndicatorController(
        service,
        spinner_frames=(0x31, 0x32, 0x33),
        spinner_colour=0x03,
        carrier_leading_colour=0x04,
        carrier_indicator_colour=0x05,
    )

    controller.set_pause(True)
    assert console.screen.peek_screen_address(0x041E) == 0xD0

    controller.set_abort(True)
    assert console.screen.peek_screen_address(0x041F) == 0xC1

    controller.set_carrier(True)
    assert console.screen.peek_screen_address(0x0400) == 0xA0
    assert console.screen.peek_screen_address(0x0427) == 0xFA
    # Spinner enabled when carrier active
    assert console.screen.peek_screen_address(0x049C) == 0x31

    controller.on_idle_tick()
    assert console.screen.peek_screen_address(0x049C) == 0x32

    controller.set_pause(False)
    controller.set_abort(False)
    controller.set_carrier(False)

    assert console.screen.peek_screen_address(0x041E) == 0x20
    assert console.screen.peek_screen_address(0x041F) == 0x20
    assert console.screen.peek_screen_address(0x0400) == 0x20
    assert console.screen.peek_screen_address(0x0427) == 0x20
    assert console.screen.peek_screen_address(0x049C) == 0x20

    # Screen/colour writes should not populate the transcript buffer.
    assert console.transcript_bytes == b""


def test_indicator_controller_spinner_disables_cleanly() -> None:
    console = Console()
    service = ConsoleService(console)
    controller = IndicatorController(service, spinner_frames=(0x41,))

    controller.set_spinner_enabled(True)
    assert console.screen.peek_screen_address(0x049C) == 0x41

    controller.on_idle_tick()
    assert console.screen.peek_screen_address(0x049C) == 0x41

    controller.set_spinner_enabled(False)
    assert console.screen.peek_screen_address(0x049C) == 0x20
    assert console.transcript_bytes == b""
