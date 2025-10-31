from __future__ import annotations
from imagebbs import MessageEditor
from imagebbs.device_context import ConsoleService
from imagebbs.runtime.main_menu import MainMenuEvent, MainMenuModule
from imagebbs.runtime.sysop_options import SysopOptionsModule
from imagebbs.session_kernel import SessionKernel, SessionState


def _bootstrap_kernel() -> tuple[SessionKernel, MainMenuModule]:
    module = MainMenuModule()
    kernel = SessionKernel(module=module)
    return kernel, module


def _expected_overlay(
    module: MainMenuModule, console: ConsoleService, slot: int
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    defaults = module.registry.defaults
    entry = defaults.macros_by_slot.get(slot)
    width = 40
    if entry is not None and entry.screen is not None:
        glyphs = tuple(entry.screen.glyph_bytes[:width])
        colours = tuple(entry.screen.colour_bytes[:width])
    else:
        run = console.glyph_lookup.macros_by_slot.get(slot)
        if run is None:  # pragma: no cover - defensive guard
            raise AssertionError(f"no glyph run for macro slot ${slot:02x}")
        glyphs = tuple(run.rendered[:width])
        colours = tuple((console.screen_colour,) * len(glyphs))
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


def test_main_menu_renders_macros_on_start_and_enter() -> None:
    kernel, module = _bootstrap_kernel()

    assert module.registry is kernel.dispatcher.registry

    defaults = module.registry.defaults
    assert module.MENU_HEADER_SLOT in defaults.macros_by_slot
    assert module.MENU_PROMPT_SLOT in defaults.macros_by_slot

    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)
    assert module.MENU_HEADER_SLOT in console_service.macro_glyphs
    assert module.MENU_PROMPT_SLOT in console_service.macro_glyphs

    assert module.rendered_slots[:2] == [
        module.MENU_HEADER_SLOT,
        module.MENU_PROMPT_SLOT,
    ]

    state = kernel.step(MainMenuEvent.ENTER)
    assert state is SessionState.MAIN_MENU
    assert module.rendered_slots[-2:] == [
        module.MENU_HEADER_SLOT,
        module.MENU_PROMPT_SLOT,
    ]

    buffers = kernel.context.get_service("masked_pane_buffers")
    assert tuple(buffers.staged_screen[:40]) == _expected_overlay(
        module, console_service, module.MENU_PROMPT_SLOT
    )[0]
    assert tuple(buffers.staged_colour[:40]) == _expected_overlay(
        module, console_service, module.MENU_PROMPT_SLOT
    )[1]
    overlay_screen, overlay_colour = _masked_overlay(console_service)
    expected_screen, expected_colour = _expected_overlay(
        module, console_service, module.MENU_PROMPT_SLOT
    )
    assert overlay_screen[:40] == expected_screen
    assert overlay_colour[:40] == expected_colour


def test_main_menu_macros_stage_masked_pane_buffers() -> None:
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
    kernel.step(MainMenuEvent.ENTER)
    buffers.clear_staging()
    kernel.step(MainMenuEvent.SELECTION, "??")
    glyphs, colours = _expected_overlay(
        module, console_service, module.INVALID_SELECTION_SLOT
    )
    assert tuple(buffers.staged_screen[:40]) == glyphs
    assert tuple(buffers.staged_colour[:40]) == colours
    overlay_screen, overlay_colour = _masked_overlay(console_service)
    assert overlay_screen[:40] == glyphs
    assert overlay_colour[:40] == colours


def test_main_menu_routes_to_message_editor() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(MainMenuEvent.ENTER)

    state = kernel.step(MainMenuEvent.SELECTION, "MF")

    assert state is SessionState.MESSAGE_EDITOR
    assert isinstance(kernel.module, MessageEditor)
    assert module.rendered_slots.count(module.MENU_PROMPT_SLOT) >= 2


def test_main_menu_routes_to_file_transfers() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(MainMenuEvent.ENTER)

    state = kernel.step(MainMenuEvent.SELECTION, "UD")

    assert state is SessionState.FILE_TRANSFERS
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)
    assert module.MENU_HEADER_SLOT in console_service.macro_glyphs


def test_main_menu_routes_to_sysop_options() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(MainMenuEvent.ENTER)

    state = kernel.step(MainMenuEvent.SELECTION, "SY")

    assert state is SessionState.SYSOP_OPTIONS
    assert isinstance(kernel.module, SysopOptionsModule)
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)
    assert module.MENU_HEADER_SLOT in console_service.macro_glyphs


def test_main_menu_exit_terminates_kernel() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(MainMenuEvent.ENTER)

    state = kernel.step(MainMenuEvent.SELECTION, "EX")

    assert state is SessionState.EXIT
    assert kernel.state is SessionState.EXIT


def test_main_menu_invalid_selection_renders_error_macro() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(MainMenuEvent.ENTER)
    module.rendered_slots.clear()

    state = kernel.step(MainMenuEvent.SELECTION, "??")

    assert state is SessionState.MAIN_MENU
    assert module.rendered_slots == [module.INVALID_SELECTION_SLOT]
