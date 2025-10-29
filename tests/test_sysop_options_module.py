import sys
from imagebbs import SessionKernel, SessionState
from imagebbs.device_context import ConsoleService
from imagebbs.runtime.sysop_options import (
    SysopOptionsEvent,
    SysopOptionsModule,
    SysopOptionsState,
)


class _DummySysopOptionsEvent:
    def __init__(self, name: str) -> None:
        self.name = name


def _bootstrap_kernel() -> tuple[SessionKernel, SysopOptionsModule]:
    module = SysopOptionsModule()
    kernel = SessionKernel(module=module)
    return kernel, module


def _expected_overlay(
    module: SysopOptionsModule, console: ConsoleService, slot: int
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    defaults = module.registry.defaults
    entry = defaults.macros_by_slot.get(slot)
    width = 40
    if entry is not None and entry.screen is not None:
        glyphs = tuple(entry.screen.glyph_bytes[:width])
        colours = tuple(entry.screen.colour_bytes[:width])
    else:
        run = console.glyph_lookup.macros_by_slot.get(slot)
        if run is not None:
            glyphs = tuple(run.rendered[:width])
            colours = tuple((console.screen_colour,) * len(glyphs))
        else:
            fallback = console.masked_pane_staging_map.fallback_overlay_for_slot(slot)
            if fallback is None:  # pragma: no cover - defensive guard
                raise AssertionError(f"no glyph run for macro slot ${slot:02x}")
            glyphs, colours = fallback
    if len(glyphs) < width:
        glyphs = glyphs + (0x20,) * (width - len(glyphs))
    if len(colours) < width:
        colours = colours + (console.screen_colour,) * (width - len(colours))
    return glyphs[:width], colours[:width]


def _masked_overlay(
    console: ConsoleService,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    screen_bytes, colour_bytes = console.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=ConsoleService._MASKED_OVERLAY_WIDTH,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=ConsoleService._MASKED_OVERLAY_WIDTH,
    )
    if screen_bytes is None or colour_bytes is None:  # pragma: no cover - guard
        raise AssertionError("masked overlay snapshot failed")
    return tuple(screen_bytes), tuple(colour_bytes)


def test_sysop_options_renders_macros_on_start_and_enter() -> None:
    kernel, module = _bootstrap_kernel()

    assert module.registry is kernel.dispatcher.registry

    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    assert module.rendered_slots[:2] == [
        module.MENU_HEADER_SLOT,
        module.MENU_PROMPT_SLOT,
    ]

    state = kernel.step(SysopOptionsEvent.ENTER)

    assert state is SessionState.SYSOP_OPTIONS
    assert module.state is SysopOptionsState.READY
    assert module.rendered_slots[-2:] == [
        module.MENU_HEADER_SLOT,
        module.MENU_PROMPT_SLOT,
    ]

    buffers = kernel.context.get_service("masked_pane_buffers")
    glyphs, colours = _expected_overlay(
        module, console_service, module.MENU_PROMPT_SLOT
    )
    assert tuple(buffers.staged_screen[:40]) == glyphs
    assert tuple(buffers.staged_colour[:40]) == colours
    overlay_screen, overlay_colour = _masked_overlay(console_service)
    assert overlay_screen[:40] == glyphs
    assert overlay_colour[:40] == colours


def test_sysop_options_macros_stage_masked_pane_buffers() -> None:
    kernel, module = _bootstrap_kernel()
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)
    buffers = kernel.context.get_service("masked_pane_buffers")

    buffers.clear_staging()
    module._render_macro(module.MENU_HEADER_MACRO)
    glyphs, colours = _expected_overlay(
        module, console_service, module.MENU_HEADER_SLOT
    )
    assert tuple(buffers.staged_screen[:40]) == glyphs
    assert tuple(buffers.staged_colour[:40]) == colours
    overlay_screen, overlay_colour = _masked_overlay(console_service)
    assert overlay_screen[:40] == glyphs
    assert overlay_colour[:40] == colours

    buffers.clear_staging()
    module._render_macro(module.MENU_PROMPT_MACRO)
    glyphs, colours = _expected_overlay(
        module, console_service, module.MENU_PROMPT_SLOT
    )
    assert tuple(buffers.staged_screen[:40]) == glyphs
    assert tuple(buffers.staged_colour[:40]) == colours
    overlay_screen, overlay_colour = _masked_overlay(console_service)
    assert overlay_screen[:40] == glyphs
    assert overlay_colour[:40] == colours

    buffers.clear_staging()
    module._render_macro(module.INVALID_SELECTION_MACRO)
    glyphs, colours = _expected_overlay(
        module, console_service, module.INVALID_SELECTION_SLOT
    )
    assert tuple(buffers.staged_screen[:40]) == glyphs
    assert tuple(buffers.staged_colour[:40]) == colours
    overlay_screen, overlay_colour = _masked_overlay(console_service)
    assert overlay_screen[:40] == glyphs
    assert overlay_colour[:40] == colours

    buffers.clear_staging()
    module._render_macro(module.ABORT_MACRO)
    glyphs, colours = _expected_overlay(module, console_service, module.ABORT_SLOT)
    assert tuple(buffers.staged_screen[:40]) == glyphs
    assert tuple(buffers.staged_colour[:40]) == colours
    overlay_screen, overlay_colour = _masked_overlay(console_service)
    assert overlay_screen[:40] == glyphs
    assert overlay_colour[:40] == colours


def test_sysop_options_saying_command_renders_text() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(SysopOptionsEvent.ENTER)

    state = kernel.step(SysopOptionsEvent.COMMAND, " sy ")

    assert state is SessionState.SYSOP_OPTIONS
    assert module.last_command == "SY"
    assert module.last_saying == module.sayings[0]
    assert module.rendered_slots[-3:] == [
        module.SAYING_PREAMBLE_SLOT,
        module.SAYING_OUTPUT_SLOT,
        module.MENU_PROMPT_SLOT,
    ]

    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)
    transcript = "".join(console_service.device.output)
    assert module.last_saying in transcript


def test_sysop_options_abort_returns_to_main_menu() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(SysopOptionsEvent.ENTER)
    module.rendered_slots.clear()

    state = kernel.step(SysopOptionsEvent.COMMAND, "abort")

    assert state is SessionState.MAIN_MENU
    assert module.last_command == "A"
    assert module.rendered_slots == [module.ABORT_SLOT]


def test_sysop_options_exit_terminates_session() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(SysopOptionsEvent.ENTER)

    state = kernel.step(SysopOptionsEvent.COMMAND, "exit")

    assert state is SessionState.EXIT
    assert module.last_command == "EX"


def test_sysop_options_handles_dummy_events_by_name() -> None:
    kernel, module = _bootstrap_kernel()

    state = kernel.step(_DummySysopOptionsEvent("ENTER"))

    assert state is SessionState.SYSOP_OPTIONS
    assert module.state is SysopOptionsState.READY

    module.rendered_slots.clear()

    state = kernel.step(_DummySysopOptionsEvent("COMMAND"), "sy")

    assert state is SessionState.SYSOP_OPTIONS
    assert module.last_command == "SY"
    assert module.rendered_slots[-3:] == [
        module.SAYING_PREAMBLE_SLOT,
        module.SAYING_OUTPUT_SLOT,
        module.MENU_PROMPT_SLOT,
    ]
