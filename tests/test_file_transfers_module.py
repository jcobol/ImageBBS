from imagebbs.device_context import ConsoleService, DiskDrive, LoopbackModemTransport
from imagebbs.session_kernel import SessionKernel, SessionState
from imagebbs.runtime.file_transfers import (
    FileTransferEvent,
    FileTransferMenuState,
    FileTransfersModule,
)


def _bootstrap_kernel() -> tuple[SessionKernel, FileTransfersModule]:
    module = FileTransfersModule()
    kernel = SessionKernel(module=module)
    return kernel, module


def _expected_overlay(
    module: FileTransfersModule, console: ConsoleService, slot: int
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
    screen = tuple(screen_bytes)
    colours = tuple(colour_bytes)
    return screen, colours


def test_file_transfers_renders_macros_on_start_and_enter() -> None:
    kernel, module = _bootstrap_kernel()

    assert module.registry is kernel.dispatcher.registry

    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    assert module.rendered_slots[:2] == [
        module.MENU_HEADER_SLOT,
        module.MENU_PROMPT_SLOT,
    ]

    state = kernel.step(FileTransferEvent.ENTER)

    assert state is SessionState.FILE_TRANSFERS
    assert module.state is FileTransferMenuState.READY
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


def test_file_transfers_macros_stage_masked_pane_buffers() -> None:
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


def test_file_transfers_accepts_known_command() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(FileTransferEvent.ENTER)
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    state = kernel.step(FileTransferEvent.COMMAND, " ud ")

    assert state is SessionState.FILE_TRANSFERS
    assert module.last_command == "UD"
    assert module.rendered_slots[-1] == module.MENU_PROMPT_SLOT

    glyphs, colours = _expected_overlay(
        module, console_service, module.MENU_PROMPT_SLOT
    )
    overlay_screen, overlay_colour = _masked_overlay(console_service)
    assert overlay_screen[:40] == glyphs
    assert overlay_colour[:40] == colours


def test_file_transfers_rejects_unknown_command() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(FileTransferEvent.ENTER)
    module.rendered_slots.clear()
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    state = kernel.step(FileTransferEvent.COMMAND, "??")

    assert state is SessionState.FILE_TRANSFERS
    assert module.rendered_slots[-2:] == [
        module.INVALID_SELECTION_SLOT,
        module.MENU_PROMPT_SLOT,
    ]

    glyphs, colours = _expected_overlay(
        module, console_service, module.MENU_PROMPT_SLOT
    )
    overlay_screen, overlay_colour = _masked_overlay(console_service)
    assert overlay_screen[:40] == glyphs
    assert overlay_colour[:40] == colours


def test_file_transfers_rd_lists_drive_directory(tmp_path) -> None:
    kernel, module = _bootstrap_kernel()
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    drive_slot = module.active_drive_slot
    drive_name = kernel.context.drive_device_name(drive_slot)
    kernel.context.register(drive_name, DiskDrive(tmp_path))
    kernel.context.open(drive_name, drive_slot, 15)

    (tmp_path / "alpha.seq").write_text("alpha")
    (tmp_path / "beta.seq").write_text("beta")

    kernel.step(FileTransferEvent.ENTER)
    console_service.device.output.clear()
    module.rendered_slots.clear()

    state = kernel.step(FileTransferEvent.COMMAND, "RD")

    assert state is SessionState.FILE_TRANSFERS
    assert module.last_command == "RD"
    output = "".join(console_service.device.output)
    assert "alpha.seq" in output
    assert "beta.seq" in output
    assert module.rendered_slots[-1] == module.MENU_PROMPT_SLOT


def test_file_transfers_exit_returns_to_main_menu() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(FileTransferEvent.ENTER)

    state = kernel.step(FileTransferEvent.COMMAND, "q")

    assert state is SessionState.MAIN_MENU
    assert kernel.state is SessionState.MAIN_MENU
    assert module.last_command == "Q"


class RecordingLoopbackTransport(LoopbackModemTransport):
    def __init__(self) -> None:
        super().__init__()
        self.binary_modes: list[bool] = []

    def set_binary_mode(self, enabled: bool) -> None:  # type: ignore[override]
        self.binary_modes.append(bool(enabled))


def test_file_transfers_toggles_binary_mode_for_stream_commands() -> None:
    kernel, module = _bootstrap_kernel()
    transport = RecordingLoopbackTransport()
    kernel.context.register_modem_device(transport=transport)

    kernel.step(FileTransferEvent.ENTER)
    transport.binary_modes.clear()

    state = kernel.step(FileTransferEvent.COMMAND, "UL")
    assert state is SessionState.FILE_TRANSFERS
    assert transport.binary_modes == [True]

    state = kernel.step(FileTransferEvent.COMMAND, "ED")
    assert state is SessionState.FILE_TRANSFERS
    assert transport.binary_modes[-1] is False

    state = kernel.step(FileTransferEvent.COMMAND, "Q")
    assert state is SessionState.MAIN_MENU
    assert transport.binary_modes[-1] is False

