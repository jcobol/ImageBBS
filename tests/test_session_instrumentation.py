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
