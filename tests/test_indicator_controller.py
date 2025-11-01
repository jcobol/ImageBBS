import pytest

from imagebbs.device_context import Console, ConsoleService
from imagebbs.runtime.indicator_controller import IndicatorController


def _colour_address(service: ConsoleService, screen_address: int) -> int:
    # Mirror the controller's address math so the tests verify identical colour slots.
    return service._COLOUR_BASE + (screen_address - service._SCREEN_BASE)


def test_indicator_controller_updates_indicators_without_transcript() -> None:
    console = Console()
    service = ConsoleService(console)
    # Verify manual indicator toggles respect cached colours while leaving transcript untouched.
    console.screen.poke_colour_address(
        _colour_address(service, service._PAUSE_SCREEN_ADDRESS), 0x02
    )
    console.screen.poke_colour_address(
        _colour_address(service, service._ABORT_SCREEN_ADDRESS), 0x08
    )
    console.screen.poke_colour_address(
        _colour_address(service, service._CARRIER_LEADING_SCREEN_ADDRESS), 0x00
    )
    console.screen.poke_colour_address(
        _colour_address(service, service._CARRIER_INDICATOR_SCREEN_ADDRESS), 0x02
    )
    controller = IndicatorController(
        service,
        spinner_frames=(0x31, 0x32, 0x33),
        spinner_colour=0x03,
        carrier_leading_colour=0x02,
        carrier_indicator_colour=0x08,
    )

    controller.set_pause(True)
    assert console.screen.peek_screen_address(0x041E) == 0xD0
    assert (
        console.screen.peek_colour_address(
            _colour_address(service, service._PAUSE_SCREEN_ADDRESS)
        )
        == 0x02
    )

    controller.set_abort(True)
    assert console.screen.peek_screen_address(0x041F) == 0xC1
    assert (
        console.screen.peek_colour_address(
            _colour_address(service, service._ABORT_SCREEN_ADDRESS)
        )
        == 0x08
    )

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
    assert (
        console.screen.peek_colour_address(
            _colour_address(service, service._CARRIER_LEADING_SCREEN_ADDRESS)
        )
        == 0x02
    )
    assert (
        console.screen.peek_colour_address(
            _colour_address(service, service._CARRIER_INDICATOR_SCREEN_ADDRESS)
        )
        == 0x08
    )

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


def test_indicator_controller_autodetects_indicator_colours() -> None:
    console = Console()
    service = ConsoleService(console)
    # Ensure the controller respects existing colour RAM when no overrides are supplied.
    console.screen.poke_colour_address(
        _colour_address(service, service._PAUSE_SCREEN_ADDRESS), 0x02
    )
    console.screen.poke_colour_address(
        _colour_address(service, service._ABORT_SCREEN_ADDRESS), 0x08
    )
    console.screen.poke_colour_address(
        _colour_address(service, service._CARRIER_LEADING_SCREEN_ADDRESS), 0x00
    )
    console.screen.poke_colour_address(
        _colour_address(service, service._CARRIER_INDICATOR_SCREEN_ADDRESS), 0x02
    )

    controller = IndicatorController(service)
    controller.set_pause(True)
    controller.set_abort(True)
    controller.set_carrier(True)

    assert (
        console.screen.peek_colour_address(
            _colour_address(service, service._PAUSE_SCREEN_ADDRESS)
        )
        == 0x02
    )
    assert (
        console.screen.peek_colour_address(
            _colour_address(service, service._ABORT_SCREEN_ADDRESS)
        )
        == 0x08
    )
    assert (
        console.screen.peek_colour_address(
            _colour_address(service, service._CARRIER_LEADING_SCREEN_ADDRESS)
        )
        == 0x00
    )
    assert (
        console.screen.peek_colour_address(
            _colour_address(service, service._CARRIER_INDICATOR_SCREEN_ADDRESS)
        )
        == 0x02
    )


def test_indicator_controller_refreshes_colour_cache_on_sync() -> None:
    console = Console()
    service = ConsoleService(console)
    # Confirm sync refresh picks up colour changes before subsequent writes.
    console.screen.poke_colour_address(
        _colour_address(service, service._PAUSE_SCREEN_ADDRESS), 0x08
    )
    controller = IndicatorController(service)
    controller.set_pause(True)
    assert (
        console.screen.peek_colour_address(
            _colour_address(service, service._PAUSE_SCREEN_ADDRESS)
        )
        == 0x08
    )

    console.screen.poke_colour_address(
        _colour_address(service, service._PAUSE_SCREEN_ADDRESS), 0x02
    )
    controller.sync_from_console()
    controller.set_pause(False)
    controller.set_pause(True)
    assert (
        console.screen.peek_colour_address(
            _colour_address(service, service._PAUSE_SCREEN_ADDRESS)
        )
        == 0x02
    )


@pytest.mark.parametrize("seed_glyph", (0x33, 0xB3))
def test_indicator_controller_syncs_spinner_phase(seed_glyph: int) -> None:
    console = Console()
    service = ConsoleService(console)
    controller = IndicatorController(service)

    console.poke_screen_byte(service._SPINNER_SCREEN_ADDRESS, seed_glyph)

    controller.sync_from_console()

    spinner_address = service._SPINNER_SCREEN_ADDRESS
    assert console.screen.peek_screen_address(spinner_address) == seed_glyph

    frames = tuple(int(code) & 0xFF for code in controller.spinner_frames)
    normalised_seed = seed_glyph & 0x7F
    matched_index = next(
        index
        for index, glyph in enumerate(frames)
        if (glyph & 0x7F) == normalised_seed
    )

    controller.on_idle_tick()

    expected_glyph = frames[(matched_index + 1) % len(frames)]
    assert (
        console.screen.peek_screen_address(spinner_address) == expected_glyph
    )
