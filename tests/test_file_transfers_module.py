from dataclasses import replace
from pathlib import Path

import pytest

from imagebbs.device_context import ConsoleService, DiskDrive, LoopbackModemTransport
from imagebbs.session_kernel import SessionKernel, SessionState
from imagebbs.runtime.file_transfers import (
    FileTransferEvent,
    FileTransferMenuState,
    FileTransfersModule,
    FileTransferError,
)
from imagebbs.runtime.indicator_controller import IndicatorController
from imagebbs.storage_config import DriveMapping, StorageConfig
from imagebbs.setup_defaults import IndicatorDefaults, SetupDefaults


# Why: centralise kernel bootstrap so tests can override defaults and reuse consistent module wiring.
def _bootstrap_kernel(
    module: FileTransfersModule | None = None,
    *,
    defaults: SetupDefaults | None = None,
) -> tuple[SessionKernel, FileTransfersModule]:
    module = module or FileTransfersModule()
    defaults = defaults or SetupDefaults.stub()
    kernel = SessionKernel(module=module, defaults=defaults)
    return kernel, module


def _register_drive_slot(context, slot: int, root: Path) -> DiskDrive:
    """Install a host-backed drive so tests can exercise slot switching."""

    device_name = context.drive_device_name(slot)
    drive = DiskDrive(root)
    context.register(device_name, drive)
    context.open(device_name, slot, 15)
    return drive


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


# Why: compute CRC16 signatures so tests can verify Xmodem framing logic.
def _crc16(payload: bytes) -> int:
    crc = 0
    for byte in payload:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc & 0xFFFF


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

    state = kernel.step(FileTransferEvent.COMMAND, " ed ")

    assert state is SessionState.FILE_TRANSFERS
    assert module.last_command == "ED"


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
    expected_alpha = DiskDrive._format_petscii_name("alpha.seq")
    expected_beta = DiskDrive._format_petscii_name("beta.seq")
    assert f'"{expected_alpha}"' in output
    assert f'"{expected_beta}"' in output
    assert module.rendered_slots[-1] == module.MENU_PROMPT_SLOT


def test_file_transfers_dr_cycles_to_next_drive(tmp_path) -> None:
    kernel, module = _bootstrap_kernel()
    transport = RecordingLoopbackTransport()
    kernel.context.register_modem_device(transport=transport)
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    root8 = tmp_path / "drive8"
    root9 = tmp_path / "drive9"
    _register_drive_slot(kernel.context, 8, root8)
    _register_drive_slot(kernel.context, 9, root9)
    (root8 / "slot8.seq").write_text("slot8")
    (root9 / "slot9.seq").write_text("slot9")

    module.active_drive_slot = 8
    kernel.step(FileTransferEvent.ENTER)
    module.rendered_slots.clear()
    transport.binary_modes.clear()
    console_service.device.output.clear()

    state = kernel.step(FileTransferEvent.COMMAND, "DR")

    assert state is SessionState.FILE_TRANSFERS
    assert module.last_command == "DR"
    assert module.active_drive_slot == 9
    assert module.rendered_slots[-1] == module.MENU_PROMPT_SLOT
    assert transport.binary_modes == [False]

    state = kernel.step(FileTransferEvent.COMMAND, "RD")

    assert state is SessionState.FILE_TRANSFERS
    output = "".join(console_service.device.output)
    assert "slot9.seq" in output
    assert "slot8.seq" not in output


def test_file_transfers_dr_selects_explicit_slot(tmp_path) -> None:
    kernel, module = _bootstrap_kernel()
    transport = RecordingLoopbackTransport()
    kernel.context.register_modem_device(transport=transport)

    root8 = tmp_path / "drive8"
    root9 = tmp_path / "drive9"
    _register_drive_slot(kernel.context, 8, root8)
    _register_drive_slot(kernel.context, 9, root9)

    module.active_drive_slot = 9
    kernel.step(FileTransferEvent.ENTER)
    module.rendered_slots.clear()
    transport.binary_modes.clear()

    state = kernel.step(FileTransferEvent.COMMAND, "DR 8")

    assert state is SessionState.FILE_TRANSFERS
    assert module.last_command == "DR"
    assert module.active_drive_slot == 8
    assert module.rendered_slots[-1] == module.MENU_PROMPT_SLOT
    assert transport.binary_modes == [False]


def test_file_transfers_dr_rejects_invalid_slot(tmp_path) -> None:
    kernel, module = _bootstrap_kernel()
    transport = RecordingLoopbackTransport()
    kernel.context.register_modem_device(transport=transport)

    root8 = tmp_path / "drive8"
    _register_drive_slot(kernel.context, 8, root8)

    module.active_drive_slot = 8
    kernel.step(FileTransferEvent.ENTER)
    module.rendered_slots.clear()
    transport.binary_modes.clear()

    state = kernel.step(FileTransferEvent.COMMAND, "DR 99")

    assert state is SessionState.FILE_TRANSFERS
    assert module.active_drive_slot == 8
    assert module.rendered_slots[-2:] == [
        module.INVALID_SELECTION_SLOT,
        module.MENU_PROMPT_SLOT,
    ]
    assert transport.binary_modes == [False]


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

# Why: ensure streaming commands enable binary mode during protocol execution.
def test_file_transfers_toggles_binary_mode_for_stream_commands() -> None:
    module = FileTransfersModule(default_protocol="Xmodem CRC")
    kernel, module = _bootstrap_kernel(module)
    transport = RecordingLoopbackTransport()
    modem = kernel.context.register_modem_device(transport=transport)

    kernel.step(FileTransferEvent.ENTER)
    transport.binary_modes.clear()
    module.transfer_state.upload_payloads["UL"] = b"!"
    transport.feed("C" + chr(0x06) + chr(0x06))
    modem.collect_transmit()

    state = kernel.step(FileTransferEvent.COMMAND, "UL")
    assert state is SessionState.FILE_TRANSFERS
    assert transport.binary_modes == [True, False]
    modem.collect_transmit()

    state = kernel.step(FileTransferEvent.COMMAND, "ED")
    assert state is SessionState.FILE_TRANSFERS
    assert transport.binary_modes[-1] is False

    state = kernel.step(FileTransferEvent.COMMAND, "Q")
    assert state is SessionState.MAIN_MENU
    assert transport.binary_modes[-1] is False


# Why: expose abort toggles through the service registry for front-end loops.
def test_file_transfers_registers_abort_service() -> None:
    kernel, module = _bootstrap_kernel()

    service = kernel.context.get_service("file_transfer_abort")
    request = getattr(service, "request_abort", None)

    assert callable(request)

    request(True)
    assert module.transfer_state.abort_requested is True

    module.request_abort(False)
    assert module.transfer_state.abort_requested is False


# Why: confirm uploads use the selected protocol and update transfer bookkeeping.
def test_file_transfers_upload_streams_payload_and_updates_state() -> None:
    module = FileTransfersModule(default_protocol="Xmodem CRC")
    kernel, module = _bootstrap_kernel(module)
    transport = RecordingLoopbackTransport()
    modem = kernel.context.register_modem_device(transport=transport)
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    kernel.step(FileTransferEvent.ENTER)
    payload = b"DATA"
    state = module.transfer_state
    state.upload_payloads["UL"] = payload
    state.progress_events.clear()
    transport.feed("C" + chr(0x06) + chr(0x06))
    modem.collect_transmit()
    console_service.device.output.clear()

    result_state = kernel.step(FileTransferEvent.COMMAND, "UL")

    assert result_state is SessionState.FILE_TRANSFERS
    assert state.completed_uploads["UL"] == payload
    assert state.credits == 1
    assert state.progress_events[-1] == ("UL", len(payload), len(payload))
    output = "".join(console_service.device.output)
    assert "Upload complete." in output
    assert "UL via Xmodem CRC" in output
    transmissions = modem.collect_transmit().encode("latin-1")
    padded = payload + bytes((0x1A,)) * (128 - len(payload))
    crc = _crc16(padded)
    expected_frame = (
        bytes((0x01, 0x01, 0xFE))
        + padded
        + bytes(((crc >> 8) & 0xFF, crc & 0xFF))
        + b"\x04"
    )
    assert transmissions == expected_frame
    assert kernel.defaults.last_file_transfer_protocol == "Xmodem CRC"


# Why: ensure upload commands read host-backed files when filenames are provided.
def test_file_transfers_upload_reads_host_file_when_available(tmp_path: Path) -> None:
    module = FileTransfersModule(default_protocol="Xmodem CRC")
    kernel, module = _bootstrap_kernel(module)
    transport = RecordingLoopbackTransport()
    modem = kernel.context.register_modem_device(transport=transport)
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    drive_root = tmp_path / "drive8"
    _register_drive_slot(kernel.context, 8, drive_root)
    module.active_drive_slot = 8
    payload = b"HOSTPAYLOAD"
    target = drive_root / "PAYLOAD.SEQ"
    target.write_bytes(payload)

    kernel.step(FileTransferEvent.ENTER)
    state = module.transfer_state
    state.progress_events.clear()
    transport.feed("C" + chr(0x06) + chr(0x06))
    modem.collect_transmit()
    console_service.device.output.clear()

    result = kernel.step(FileTransferEvent.COMMAND, "UL PAYLOAD.SEQ")

    assert result is SessionState.FILE_TRANSFERS
    assert state.completed_uploads["UL"] == payload
    assert state.credits == 1
    assert state.progress_events[-1] == ("UL", len(payload), len(payload))
    transmissions = modem.collect_transmit().encode("latin-1")
    padded = payload + bytes((0x1A,)) * (128 - len(payload))
    crc = _crc16(padded)
    expected_frame = (
        bytes((0x01, 0x01, 0xFE))
        + padded
        + bytes(((crc >> 8) & 0xFF, crc & 0xFF))
        + b"\x04"
    )
    assert transmissions == expected_frame


# Why: raise FileTransferError when the requested upload target does not exist.
def test_file_transfers_upload_missing_host_file_raises(tmp_path: Path) -> None:
    kernel, module = _bootstrap_kernel()
    drive_root = tmp_path / "drive8"
    _register_drive_slot(kernel.context, 8, drive_root)
    module.active_drive_slot = 8
    kernel.step(FileTransferEvent.ENTER)

    with pytest.raises(FileTransferError, match="not found"):
        module._upload_payload_for(
            kernel,
            module.transfer_state,
            "UL",
            "UL MISSING.SEQ",
        )


# Why: block uploads sourced from read-only drive mappings.
def test_file_transfers_upload_read_only_drive_raises(tmp_path: Path) -> None:
    kernel, module = _bootstrap_kernel()
    drive_root = tmp_path / "drive8"
    _register_drive_slot(kernel.context, 8, drive_root)
    module.active_drive_slot = 8
    storage = StorageConfig(
        drives={8: DriveMapping(drive=8, root=drive_root, read_only=True)},
        default_drive=8,
    )
    object.__setattr__(kernel.defaults, "storage_config", storage)
    (drive_root / "PAYLOAD.SEQ").write_bytes(b"data")
    kernel.step(FileTransferEvent.ENTER)

    with pytest.raises(FileTransferError, match="read-only"):
        module._upload_payload_for(
            kernel,
            module.transfer_state,
            "UL",
            "UL PAYLOAD.SEQ",
        )

# Why: confirm downloads adjust credits and persist the chosen protocol.
def test_file_transfers_download_streams_payload_and_persists_protocol() -> None:
    module = FileTransfersModule()
    kernel, module = _bootstrap_kernel(module)
    transport = RecordingLoopbackTransport()
    modem = kernel.context.register_modem_device(transport=transport)
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    kernel.step(FileTransferEvent.ENTER)
    state = module.transfer_state
    state.credits = 2
    payload = b"ABC"
    checksum = sum(payload) & 0xFF
    frame = b"!" + bytes((0x00, len(payload))) + payload + bytes((checksum,))
    transport.feed((frame + b"E").decode("latin-1"))
    modem.collect_transmit()
    console_service.device.output.clear()
    state.progress_events.clear()

    result_state = kernel.step(FileTransferEvent.COMMAND, "VB")

    assert result_state is SessionState.FILE_TRANSFERS
    assert state.completed_downloads["VB"] == payload
    assert state.credits == 1
    assert state.progress_events[-1] == ("VB", len(payload), len(payload))
    output = "".join(console_service.device.output)
    assert "Download complete." in output
    assert "VB via Punter" in output
    transmissions = modem.collect_transmit()
    assert transmissions == "S" + "K"
    assert kernel.defaults.last_file_transfer_protocol == "Punter"

# Why: verify the abort flag cancels active transfers and leaves state unchanged.
def test_file_transfers_respects_abort_flag() -> None:
    module = FileTransfersModule(default_protocol="Xmodem CRC")
    kernel, module = _bootstrap_kernel(module)
    transport = RecordingLoopbackTransport()
    modem = kernel.context.register_modem_device(transport=transport)
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    kernel.step(FileTransferEvent.ENTER)
    state = module.transfer_state
    state.upload_payloads["UL"] = b"AB"
    service = kernel.context.get_service("file_transfer_abort")
    request = getattr(service, "request_abort", None)
    assert callable(request)
    request(True)
    assert state.abort_requested is True
    transport.feed("C")
    modem.collect_transmit()
    console_service.device.output.clear()

    result_state = kernel.step(FileTransferEvent.COMMAND, "UL")

    assert result_state is SessionState.FILE_TRANSFERS
    assert "Transfer aborted." in "".join(console_service.device.output)
    assert "Upload complete." not in "".join(console_service.device.output)
    assert "UL" not in state.completed_uploads
    assert kernel.defaults.last_file_transfer_protocol == "Xmodem CRC"
    assert state.abort_requested is False

class RecordingIndicatorController(IndicatorController):
    def __init__(self, console: ConsoleService, **kwargs) -> None:
        # Why: capture controller toggles while preserving the console wiring and recording injected palette overrides.
        super().__init__(console, **kwargs)
        self.pause_states: list[bool] = []
        self.abort_states: list[bool] = []
        self.pause_colours: list[int | None] = []
        self.abort_colours: list[int | None] = []

    # Why: retain pause transitions so tests can assert controller usage over console fallbacks.
    def set_pause(self, active: bool) -> None:  # type: ignore[override]
        self.pause_states.append(active)
        self.pause_colours.append(self.pause_colour)
        super().set_pause(active)

    # Why: record abort transitions to ensure colour overrides propagate through the controller path.
    def set_abort(self, active: bool) -> None:  # type: ignore[override]
        self.abort_states.append(active)
        self.abort_colours.append(self.abort_colour)
        super().set_abort(active)


# Why: ensure indicator controllers receive transfer toggles and colour overrides.
def test_file_transfers_prefers_indicator_controller_when_available() -> None:
    defaults = SetupDefaults.stub()
    overrides = IndicatorDefaults(pause_colour=0x0E, abort_colour=0x05)
    defaults = replace(defaults, indicator=overrides)
    kernel, module = _bootstrap_kernel(defaults=defaults)
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    controller = RecordingIndicatorController(console_service)
    kernel.context.register_service("indicator_controller", controller)

    module.start(kernel)

    controller.pause_states.clear()
    controller.abort_states.clear()
    controller.pause_colours.clear()
    controller.abort_colours.clear()

    module._set_transfer_indicators(True)
    module._set_transfer_indicators(False)

    assert controller.pause_states == [True, False]
    assert controller.abort_states == [True, False]
    assert controller.pause_colours == [0x0E, None]
    assert controller.abort_colours == [0x05, None]
    assert controller.pause_colour is None
    assert controller.abort_colour is None


# Why: confirm console writes remain the fallback when no controller is registered.
def test_file_transfers_falls_back_to_console_when_controller_absent() -> None:
    kernel, module = _bootstrap_kernel()
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    pause_address = ConsoleService._PAUSE_SCREEN_ADDRESS
    abort_address = ConsoleService._ABORT_SCREEN_ADDRESS
    pause_colour_address = ConsoleService._colour_address_for(pause_address)
    abort_colour_address = ConsoleService._colour_address_for(abort_address)
    baseline_pause_glyph = console_service.device.screen.peek_screen_address(
        pause_address
    )
    baseline_abort_glyph = console_service.device.screen.peek_screen_address(
        abort_address
    )
    baseline_pause_colour = console_service.device.screen.peek_colour_address(
        pause_colour_address
    )
    baseline_abort_colour = console_service.device.screen.peek_colour_address(
        abort_colour_address
    )

    module._set_transfer_indicators(True)

    pause_value = console_service.device.screen.peek_screen_address(pause_address)
    abort_value = console_service.device.screen.peek_screen_address(abort_address)
    pause_colour = console_service.device.screen.peek_colour_address(
        pause_colour_address
    )
    abort_colour = console_service.device.screen.peek_colour_address(
        abort_colour_address
    )

    assert pause_value == ord("P")
    assert abort_value == ord("A")
    assert pause_colour == baseline_pause_colour
    assert abort_colour == baseline_abort_colour

    module._set_transfer_indicators(False)

    cleared_pause = console_service.device.screen.peek_screen_address(pause_address)
    cleared_abort = console_service.device.screen.peek_screen_address(abort_address)
    restored_pause_colour = console_service.device.screen.peek_colour_address(
        pause_colour_address
    )
    restored_abort_colour = console_service.device.screen.peek_colour_address(
        abort_colour_address
    )

    assert cleared_pause == baseline_pause_glyph
    assert cleared_abort == baseline_abort_glyph
    assert restored_pause_colour == baseline_pause_colour
    assert restored_abort_colour == baseline_abort_colour


# Why: confirm configured indicator overrides propagate when toggling without a controller.
def test_file_transfers_console_respects_indicator_overrides() -> None:
    defaults = SetupDefaults.stub()
    overrides = IndicatorDefaults(pause_colour=0x0E, abort_colour=0x05)
    defaults = replace(defaults, indicator=overrides)
    kernel, module = _bootstrap_kernel(defaults=defaults)
    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    pause_address = ConsoleService._PAUSE_SCREEN_ADDRESS
    abort_address = ConsoleService._ABORT_SCREEN_ADDRESS
    pause_colour_address = ConsoleService._colour_address_for(pause_address)
    abort_colour_address = ConsoleService._colour_address_for(abort_address)

    baseline_pause_colour = console_service.device.screen.peek_colour_address(
        pause_colour_address
    )
    baseline_abort_colour = console_service.device.screen.peek_colour_address(
        abort_colour_address
    )

    pause_calls: list[int | None] = []
    abort_calls: list[int | None] = []
    original_pause = console_service.set_pause_indicator
    original_abort = console_service.set_abort_indicator

    def recording_pause(glyph: int, *, colour: int | None = None) -> None:
        pause_calls.append(colour)
        original_pause(glyph, colour=colour)

    def recording_abort(glyph: int, *, colour: int | None = None) -> None:
        abort_calls.append(colour)
        original_abort(glyph, colour=colour)

    console_service.set_pause_indicator = recording_pause  # type: ignore[assignment]
    console_service.set_abort_indicator = recording_abort  # type: ignore[assignment]

    module._set_transfer_indicators(True)

    active_pause_colour = console_service.device.screen.peek_colour_address(
        pause_colour_address
    )
    active_abort_colour = console_service.device.screen.peek_colour_address(
        abort_colour_address
    )

    assert pause_calls[0] == 0x0E
    assert abort_calls[0] == 0x05

    module._set_transfer_indicators(False)

    restored_pause_colour = console_service.device.screen.peek_colour_address(
        pause_colour_address
    )
    restored_abort_colour = console_service.device.screen.peek_colour_address(
        abort_colour_address
    )

    assert restored_pause_colour == baseline_pause_colour
    assert restored_abort_colour == baseline_abort_colour
    assert pause_calls[-1] == baseline_pause_colour
    assert abort_calls[-1] == baseline_abort_colour

    console_service.set_pause_indicator = original_pause  # type: ignore[assignment]
    console_service.set_abort_indicator = original_abort  # type: ignore[assignment]

