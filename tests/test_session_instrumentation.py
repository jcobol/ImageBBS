from imagebbs.runtime.indicator_controller import IndicatorController
from imagebbs.runtime.session_instrumentation import SessionInstrumentation
from imagebbs.runtime.session_runner import SessionRunner


def test_session_instrumentation_syncs_indicator_controller_from_console() -> None:
    runner = SessionRunner()
    console = runner.console

    temp_controller = IndicatorController(console)
    spinner_frames = tuple(int(code) & 0xFF for code in temp_controller.spinner_frames)
    spinner_seed_index = 1 if len(spinner_frames) > 1 else 0
    spinner_seed = spinner_frames[spinner_seed_index] if spinner_frames else 0x20

    console.set_pause_indicator(0xD0)
    console.set_abort_indicator(0xC1)
    console.set_carrier_indicator(leading_cell=0xA0, indicator_cell=0xFA)
    console.set_spinner_glyph(spinner_seed)

    instrumentation = SessionInstrumentation(runner)
    controller = instrumentation.ensure_indicator_controller()
    assert controller is not None

    services = runner.kernel.context.services
    assert services.get("indicator_controller") is controller

    console_pause = console.screen.peek_screen_address(0x041E)
    assert console_pause == 0xD0
    controller.set_pause(False)
    assert console.screen.peek_screen_address(0x041E) == 0x20

    frames = tuple(int(code) & 0xFF for code in controller.spinner_frames)
    if frames:
        expected_after_tick = frames[(spinner_seed_index + 1) % len(frames)]
        controller.on_idle_tick()
        assert console.screen.peek_screen_address(0x049C) == expected_after_tick

        controller.set_spinner_enabled(False)
        assert console.screen.peek_screen_address(0x049C) == 0x20

        controller.set_spinner_enabled(True)
        assert console.screen.peek_screen_address(0x049C) == frames[0]


def test_session_instrumentation_reuses_controller_and_refreshes_cache() -> None:
    # Why: ensure instrumentation reuse re-synchronises indicator caches after console changes.
    runner = SessionRunner()
    console = runner.console

    instrumentation = SessionInstrumentation(runner)
    controller = instrumentation.ensure_indicator_controller()
    assert controller is not None

    controller.set_pause(True)
    controller.set_spinner_enabled(False)
    assert controller._spinner_enabled is False

    frames = tuple(int(code) & 0xFF for code in controller.spinner_frames)
    if frames:
        spinner_index = (len(frames) - 1) if len(frames) > 1 else 0
        console.set_spinner_glyph(frames[spinner_index])
    else:
        spinner_index = 0

    console.set_pause_indicator(0xD0, colour=0x07)
    pause_colour_address = console._colour_address_for(console._PAUSE_SCREEN_ADDRESS)
    new_pause_colour = console.screen.peek_colour_address(pause_colour_address)

    reused_instrumentation = SessionInstrumentation(runner)
    reused_controller = reused_instrumentation.ensure_indicator_controller()
    assert reused_controller is controller

    assert reused_controller._pause_colour_cache == new_pause_colour

    if frames:
        assert reused_controller._spinner_enabled is True
        assert reused_controller._spinner_index == spinner_index
