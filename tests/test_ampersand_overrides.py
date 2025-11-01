from __future__ import annotations

from pathlib import Path

from unittest import mock

import pytest

from imagebbs.ampersand_dispatcher import (
    AmpersandDispatchContext,
    AmpersandDispatcher,
)
from imagebbs.device_context import (
    ConsoleService,
    DriveAssignment,
    FilesystemDriveLocator,
    MaskedPaneBuffers,
    bootstrap_device_context,
)
from imagebbs.message_editor import SessionContext
from imagebbs.runtime.ampersand_overrides import BUILTIN_AMPERSAND_OVERRIDES
from imagebbs.runtime.ampersand_overrides import handle_chkflags
from imagebbs.runtime.indicator_controller import IndicatorController
from imagebbs.runtime.message_store import MessageStore
from imagebbs.runtime.session_instrumentation import SessionInstrumentation
from imagebbs.runtime.session_runner import SessionRunner


def _resolve_palette_colour(value: int, palette: tuple[int, ...], *, default_index: int = 0) -> int:
    resolved = int(value) & 0xFF
    if resolved in palette:
        return resolved
    if 0 <= resolved < len(palette):
        return palette[resolved]
    if not 0 <= default_index < len(palette):
        raise ValueError("default_index must reference a palette entry")
    return palette[default_index]


def _build_dispatcher() -> AmpersandDispatcher:
    context = bootstrap_device_context(
        assignments=(), ampersand_overrides=BUILTIN_AMPERSAND_OVERRIDES
    )
    dispatcher = context.get_service("ampersand")
    assert isinstance(dispatcher, AmpersandDispatcher)
    return dispatcher


def _register_indicator_controller(registry) -> IndicatorController:
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)
    controller = IndicatorController(console_service)
    registry.register_service("indicator_controller", controller)
    return controller


def test_builtin_ampersand_overrides_reference_runtime_module() -> None:
    module_prefix = "imagebbs.runtime.ampersand_overrides:"
    for flag_index, import_path in BUILTIN_AMPERSAND_OVERRIDES.items():
        assert import_path.startswith(module_prefix)
    assert 0x1C in BUILTIN_AMPERSAND_OVERRIDES
    assert 0x15 in BUILTIN_AMPERSAND_OVERRIDES


def test_chkflags_syncs_indicator_controller_with_session_runtime() -> None:
    runner = SessionRunner()
    instrumentation = SessionInstrumentation(runner)
    ensured = instrumentation.ensure_indicator_controller()
    assert isinstance(ensured, IndicatorController)

    context = runner.kernel.context
    dispatcher = context.get_service("ampersand")
    assert isinstance(dispatcher, AmpersandDispatcher)
    dispatcher.registry.register_handler(0x34, handle_chkflags)
    controller = dispatcher.registry.services.get("indicator_controller")
    assert controller is ensured

    console = runner.console
    ensured.set_spinner_enabled(False)
    console.set_pause_indicator(0x20)
    spinner_frames = tuple(int(code) & 0xFF for code in ensured.spinner_frames)
    if spinner_frames:
        seed_index = 1 if len(spinner_frames) > 1 else 0
        console.set_spinner_glyph(spinner_frames[seed_index])
    else:
        console.set_spinner_glyph(0xAE)
    console.set_pause_indicator(0xD0)

    dispatcher.dispatch("&,52,2,1")
    dispatcher.dispatch("&,52,16,1")

    spinner_address = ConsoleService._SPINNER_SCREEN_ADDRESS
    pause_address = ConsoleService._PAUSE_SCREEN_ADDRESS
    assert console.screen.peek_screen_address(spinner_address) == 0xB0
    assert console.screen.peek_screen_address(pause_address) == 0xD0

    ensured.set_spinner_enabled(False)
    assert console.screen.peek_screen_address(spinner_address) == 0x20

    ensured.set_pause(False)
    assert console.screen.peek_screen_address(pause_address) == 0x20


# Ensure chkflags delegates indicator toggles into the controller so overrides observe them.
def test_chkflags_routes_updates_through_indicator_controller() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    controller = _register_indicator_controller(registry)

    original_sync = IndicatorController.sync_from_console
    original_set_pause = IndicatorController.set_pause
    original_set_abort = IndicatorController.set_abort
    original_set_spinner = IndicatorController.set_spinner_enabled
    original_set_carrier = IndicatorController.set_carrier

    with (
        mock.patch.object(
            IndicatorController,
            "sync_from_console",
            autospec=True,
            side_effect=lambda self, *a, **kw: original_sync(self, *a, **kw),
        ) as sync_mock,
        mock.patch.object(
            IndicatorController,
            "set_pause",
            autospec=True,
            side_effect=lambda self, *a, **kw: original_set_pause(
                self, *a, **kw
            ),
        ) as set_pause,
        mock.patch.object(
            IndicatorController,
            "set_abort",
            autospec=True,
            side_effect=lambda self, *a, **kw: original_set_abort(
                self, *a, **kw
            ),
        ) as set_abort,
        mock.patch.object(
            IndicatorController,
            "set_spinner_enabled",
            autospec=True,
            side_effect=lambda self, *a, **kw: original_set_spinner(
                self, *a, **kw
            ),
        ) as set_spinner,
        mock.patch.object(
            IndicatorController,
            "set_carrier",
            autospec=True,
            side_effect=lambda self, *a, **kw: original_set_carrier(
                self, *a, **kw
            ),
        ) as set_carrier,
    ):
        dispatcher.dispatch("&,52,16,1")
        set_pause.assert_called_once()
        assert set_pause.call_args[0][0] is controller
        assert set_pause.call_args[0][1] is True
        assert sync_mock.call_count >= 1

        sync_mock.reset_mock()
        set_pause.reset_mock()
        dispatcher.dispatch("&,52,17,1")
        set_abort.assert_called_once()
        assert set_abort.call_args[0][0] is controller
        assert set_abort.call_args[0][1] is True
        assert sync_mock.call_count >= 1

        console_service.set_spinner_glyph(0x20)
        sync_mock.reset_mock()
        set_abort.reset_mock()
        dispatcher.dispatch("&,52,2,1")
        set_spinner.assert_called()
        assert set_spinner.call_args[0][0] is controller
        assert set_spinner.call_args[0][1] is True
        assert sync_mock.call_count >= 1

        sync_mock.reset_mock()
        set_spinner.reset_mock()
        dispatcher.dispatch("&,52,2,2")
        set_spinner.assert_called_once()
        assert set_spinner.call_args[0][0] is controller
        assert set_spinner.call_args[0][1] is False
        assert sync_mock.call_count >= 1

        console_service.set_carrier_indicator(
            leading_cell=0x20, indicator_cell=0x20
        )
        sync_mock.reset_mock()
        set_spinner.reset_mock()
        dispatcher.dispatch("&,52,4,1")
        set_carrier.assert_called_once()
        assert set_carrier.call_args[0][0] is controller
        assert set_carrier.call_args[0][1] is True
        assert sync_mock.call_count >= 1

        sync_mock.reset_mock()
        set_carrier.reset_mock()
        dispatcher.dispatch("&,52,4,2")
        set_carrier.assert_called_once()
        assert set_carrier.call_args[0][0] is controller
        assert set_carrier.call_args[0][1] is False
        assert sync_mock.call_count >= 1


@pytest.fixture()
def dispatcher_with_temp_drive(tmp_path: Path) -> AmpersandDispatcher:
    drive_root = tmp_path / "drive8"
    drive_root.mkdir()
    (drive_root / "FIRST.SEQ").write_text("hello", encoding="latin-1")
    (drive_root / "SECOND.SEQ").write_text("world", encoding="latin-1")

    assignment = DriveAssignment(
        slot=8, locator=FilesystemDriveLocator(path=drive_root)
    )
    context = bootstrap_device_context(
        assignments=(assignment,),
        ampersand_overrides=BUILTIN_AMPERSAND_OVERRIDES,
    )
    dispatcher = context.get_service("ampersand")
    assert isinstance(dispatcher, AmpersandDispatcher)
    return dispatcher


def test_chkflags_updates_pause_indicator() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    controller = _register_indicator_controller(registry)

    pause_address = 0x041E
    colour_address = 0xD81E
    before = console_service.device.screen.peek_screen_address(pause_address)
    before_colour = console_service.device.screen.peek_colour_address(colour_address)

    dispatcher.dispatch("&,52,16,1")

    after = console_service.device.screen.peek_screen_address(pause_address)
    colour = console_service.device.screen.peek_colour_address(colour_address)
    assert after != before
    assert after == 0xD0
    assert colour == before_colour

    controller.set_pause(False)
    cleared = console_service.device.screen.peek_screen_address(pause_address)
    assert cleared == 0x20


# Prove chkflags manipulates indicator glyphs when no controller service is available.
def test_chkflags_updates_indicators_without_controller() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    assert "indicator_controller" not in registry.services

    dispatcher.dispatch("&,52,16,1")
    assert (
        console_service.screen.peek_screen_address(ConsoleService._PAUSE_SCREEN_ADDRESS)
        == 0xD0
    )
    dispatcher.dispatch("&,52,16,0")
    assert (
        console_service.screen.peek_screen_address(ConsoleService._PAUSE_SCREEN_ADDRESS)
        == 0x20
    )

    dispatcher.dispatch("&,52,17,1")
    assert (
        console_service.screen.peek_screen_address(ConsoleService._ABORT_SCREEN_ADDRESS)
        == 0xC1
    )
    dispatcher.dispatch("&,52,17,0")
    assert (
        console_service.screen.peek_screen_address(ConsoleService._ABORT_SCREEN_ADDRESS)
        == 0x20
    )

    console_service.set_spinner_glyph(0x20)
    dispatcher.dispatch("&,52,2,1")
    assert (
        console_service.screen.peek_screen_address(
            ConsoleService._SPINNER_SCREEN_ADDRESS
        )
        == 0xB0
    )
    dispatcher.dispatch("&,52,2,2")
    assert (
        console_service.screen.peek_screen_address(
            ConsoleService._SPINNER_SCREEN_ADDRESS
        )
        == 0x20
    )

    console_service.set_carrier_indicator(leading_cell=0x20, indicator_cell=0x20)
    dispatcher.dispatch("&,52,4,1")
    assert (
        console_service.screen.peek_screen_address(
            ConsoleService._CARRIER_LEADING_SCREEN_ADDRESS
        )
        == 0xA0
    )
    assert (
        console_service.screen.peek_screen_address(
            ConsoleService._CARRIER_INDICATOR_SCREEN_ADDRESS
        )
        == 0xFA
    )
    dispatcher.dispatch("&,52,4,2")
    assert (
        console_service.screen.peek_screen_address(
            ConsoleService._CARRIER_LEADING_SCREEN_ADDRESS
        )
        == 0x20
    )
    assert (
        console_service.screen.peek_screen_address(
            ConsoleService._CARRIER_INDICATOR_SCREEN_ADDRESS
        )
        == 0x20
    )


def test_chkflags_preserves_indicator_palette_without_controller() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    registry.register_handler(0x34, handle_chkflags)

    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)
    assert "indicator_controller" not in registry.services

    pause_colour_address = console_service._colour_address_for(
        ConsoleService._PAUSE_SCREEN_ADDRESS
    )
    abort_colour_address = console_service._colour_address_for(
        ConsoleService._ABORT_SCREEN_ADDRESS
    )

    console_service.set_pause_indicator(0x20, colour=0x07)
    console_service.set_abort_indicator(0x20, colour=0x0C)

    # Capture palette bytes so assertions confirm toggles keep customised colours.
    def _peek_colour(address: int) -> int:
        _, colour_span = console_service.peek_block(
            colour_address=address,
            colour_length=1,
        )
        assert colour_span is not None
        return colour_span[0]

    pause_colour_value = _peek_colour(pause_colour_address)
    abort_colour_value = _peek_colour(abort_colour_address)

    dispatcher.dispatch("&,52,16,1")
    assert (
        console_service.screen.peek_screen_address(
            ConsoleService._PAUSE_SCREEN_ADDRESS
        )
        == 0xD0
    )
    assert _peek_colour(pause_colour_address) == pause_colour_value

    dispatcher.dispatch("&,52,16,0")
    assert (
        console_service.screen.peek_screen_address(
            ConsoleService._PAUSE_SCREEN_ADDRESS
        )
        == 0x20
    )
    assert _peek_colour(pause_colour_address) == pause_colour_value

    dispatcher.dispatch("&,52,17,1")
    assert (
        console_service.screen.peek_screen_address(
            ConsoleService._ABORT_SCREEN_ADDRESS
        )
        == 0xC1
    )
    assert _peek_colour(abort_colour_address) == abort_colour_value

    dispatcher.dispatch("&,52,17,0")
    assert (
        console_service.screen.peek_screen_address(
            ConsoleService._ABORT_SCREEN_ADDRESS
        )
        == 0x20
    )
    assert _peek_colour(abort_colour_address) == abort_colour_value


@pytest.mark.parametrize(
    "operation,prepare_spinner,prepare_carrier",
    [
        (
            0,
            lambda console: console.set_spinner_glyph(0xB0),
            lambda console: console.set_carrier_indicator(
                leading_cell=0xA0, indicator_cell=0xFA
            ),
        ),
        (
            1,
            lambda console: console.set_spinner_glyph(0x20),
            lambda console: console.set_carrier_indicator(
                leading_cell=0x20, indicator_cell=0x20
            ),
        ),
        (
            2,
            lambda console: console.set_spinner_glyph(0x20),
            lambda console: console.set_carrier_indicator(
                leading_cell=0x20, indicator_cell=0x20
            ),
        ),
    ],
)
def test_chkflags_updates_spinner_and_carrier(
    operation: int,
    prepare_spinner,
    prepare_carrier,
) -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    controller = _register_indicator_controller(registry)

    prepare_spinner(console_service)
    spinner_before = console_service.device.screen.peek_screen_address(0x049C)
    dispatcher.dispatch(f"&,52,2,{operation}")
    spinner_after = console_service.device.screen.peek_screen_address(0x049C)
    assert spinner_after != spinner_before

    frames = tuple(int(code) & 0xFF for code in controller.spinner_frames)
    controller.on_idle_tick()
    spinner_tick = console_service.device.screen.peek_screen_address(0x049C)
    if spinner_after in frames:
        expected_index = (frames.index(spinner_after) + 1) % len(frames)
        assert spinner_tick == frames[expected_index]
    else:
        assert spinner_tick == spinner_after

    prepare_carrier(console_service)
    leading_before = console_service.device.screen.peek_screen_address(0x0400)
    indicator_before = console_service.device.screen.peek_screen_address(0x0427)
    dispatcher.dispatch(f"&,52,4,{operation}")
    leading_after = console_service.device.screen.peek_screen_address(0x0400)
    indicator_after = console_service.device.screen.peek_screen_address(0x0427)
    assert leading_after != leading_before
    assert indicator_after != indicator_before

    carrier_active = bool(
        (leading_after is not None and leading_after != 0x20)
        or (indicator_after is not None and indicator_after != 0x20)
    )
    if carrier_active:
        controller.set_carrier(False)
        leading_cleared = console_service.device.screen.peek_screen_address(0x0400)
        indicator_cleared = console_service.device.screen.peek_screen_address(0x0427)
        spinner_cleared = console_service.device.screen.peek_screen_address(0x049C)
        assert leading_cleared == 0x20
        assert indicator_cleared == 0x20
        assert spinner_cleared == 0x20
    else:
        controller.set_carrier(True)
        leading_set = console_service.device.screen.peek_screen_address(0x0400)
        indicator_set = console_service.device.screen.peek_screen_address(0x0427)
        spinner_set = console_service.device.screen.peek_screen_address(0x049C)
        assert leading_set == 0xA0
        assert indicator_set == 0xFA
        assert spinner_set != 0x20


def test_read0_appends_session_message() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    store = MessageStore()
    registry.register_service("message_store", store)

    session = SessionContext(board_id="board", user_id="alice")
    session.draft_buffer = ["Line one", "Line two"]
    session.command_buffer = "Greetings"

    result = dispatcher.dispatch("&,3", payload={"session": session})

    summaries = store.list("board")
    assert len(summaries) == 1
    record = store.fetch("board", summaries[0].message_id)
    assert record.subject == "Greetings"
    assert record.lines == tuple(session.drafts.get(record.message_id, []))
    assert result.context["record"] is record
    assert session.selected_message_id == record.message_id


def test_dskdir_uses_payload_fallback_text() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry

    fallback = "DIRECTORY\r"
    result = dispatcher.dispatch("&,8", payload={"fallback_text": fallback})

    assert result.rendered_text == fallback


def test_dskdir_renders_drive_listing_when_no_fallback(
    dispatcher_with_temp_drive: AmpersandDispatcher,
) -> None:
    result = dispatcher_with_temp_drive.dispatch("&,8")

    assert result.rendered_text is not None
    assert "FIRST.SEQ" in result.rendered_text
    assert "SECOND.SEQ" in result.rendered_text


def test_dispatcher_injects_registry_and_services_into_payload() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    controller = _register_indicator_controller(registry)

    pause_address = 0x041E
    colour_address = 0xD81E
    before = console_service.device.screen.peek_screen_address(pause_address)
    before_colour = console_service.device.screen.peek_colour_address(colour_address)

    dispatcher.dispatch("&,52,16,1")

    after = console_service.device.screen.peek_screen_address(pause_address)
    colour = console_service.device.screen.peek_colour_address(colour_address)
    assert after != before
    assert colour == before_colour

    controller.set_pause(False)
    cleared = console_service.device.screen.peek_screen_address(pause_address)
    assert cleared == 0x20

    store = MessageStore()
    registry.register_service("message_store", store)

    session = SessionContext(board_id="board", user_id="bob")
    session.draft_buffer = ["Payload"]
    session.command_buffer = "Injected"

    dispatcher.dispatch("&,3", payload={"session": session})

    summaries = store.list("board")
    assert len(summaries) == 1
    record = store.fetch("board", summaries[0].message_id)
    assert record.subject == "Injected"
    assert session.selected_message_id == record.message_id

    result = dispatcher.dispatch("&,8")

    assert isinstance(result.context, AmpersandDispatchContext)
    payload = result.context.payload
    assert isinstance(payload, dict)
    assert payload["registry"] is registry
    assert payload["services"] is registry.services
    assert result.services["console"] is console_service


def test_outscn_commits_masked_pane_staging_when_data_present() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    buffers = registry.services["masked_pane_buffers"]
    assert isinstance(buffers, MaskedPaneBuffers)

    screen_payload = bytes((0x60 + i) % 256 for i in range(buffers.width))
    colour_payload = bytes(((i + 3) % 16) for i in range(buffers.width))

    console_service.poke_block(
        screen_address=ConsoleService._MASKED_STAGING_SCREEN_BASE,
        screen_bytes=screen_payload,
        colour_address=ConsoleService._MASKED_STAGING_COLOUR_BASE,
        colour_bytes=colour_payload,
    )

    assert buffers.dirty is True

    dispatcher.dispatch("&,50")

    assert bytes(buffers.live_screen) == screen_payload
    assert bytes(buffers.live_colour) == colour_payload

    fill_colour = console_service.screen_colour & 0xFF
    assert bytes(buffers.staged_screen) == bytes((0x20,) * buffers.width)
    assert bytes(buffers.staged_colour) == bytes((fill_colour,) * buffers.width)

    screen_bytes, colour_bytes = console_service.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=buffers.width,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=buffers.width,
    )

    assert screen_bytes == screen_payload
    palette = console_service.screen.palette
    expected_colour = bytes(
        _resolve_palette_colour(value, palette) for value in colour_payload
    )
    assert colour_bytes == expected_colour
    assert buffers.dirty is False


def test_outscn_ignores_empty_masked_pane_staging() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    buffers = registry.services["masked_pane_buffers"]
    assert isinstance(buffers, MaskedPaneBuffers)

    fill_colour = console_service.screen_colour & 0xFF
    live_screen_payload = bytes((0x33,) * buffers.width)
    live_colour_payload = bytes((0x04,) * buffers.width)

    buffers.live_screen[:] = live_screen_payload
    buffers.live_colour[:] = live_colour_payload
    buffers.clear_staging(glyph=0x20, colour=fill_colour)

    console_service.poke_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_bytes=live_screen_payload,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_bytes=live_colour_payload,
    )

    before_screen, before_colour = console_service.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=buffers.width,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=buffers.width,
    )

    assert buffers.dirty is False

    dispatcher.dispatch("&,50")

    assert bytes(buffers.live_screen) == live_screen_payload
    assert bytes(buffers.live_colour) == live_colour_payload
    assert bytes(buffers.staged_screen) == bytes((0x20,) * buffers.width)
    assert bytes(buffers.staged_colour) == bytes((fill_colour,) * buffers.width)
    assert buffers.dirty is False

    after_screen, after_colour = console_service.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=buffers.width,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=buffers.width,
    )

    assert after_screen == before_screen
    assert after_colour == before_colour


def test_disp3_commits_pending_payload_and_resets_blink() -> None:
    dispatcher = _build_dispatcher()
    registry = dispatcher.registry
    console_service = registry.services["console"]
    assert isinstance(console_service, ConsoleService)

    buffers = registry.services["masked_pane_buffers"]
    assert isinstance(buffers, MaskedPaneBuffers)

    width = buffers.width
    screen_payload = bytes((0x55 + i) % 256 for i in range(width))
    colour_payload = bytes(((i + 7) % 16) for i in range(width))

    console_service.stage_masked_pane_overlay(screen_payload, colour_payload)

    pending = buffers.peek_pending_payload()
    assert pending is not None
    pending_screen, pending_colour = pending
    assert pending_screen == screen_payload
    assert pending_colour == colour_payload
    assert buffers.peek_pending_slot() is None

    console_service.advance_masked_pane_blink()
    before_state = console_service._masked_pane_blink.peek()  # type: ignore[attr-defined]
    assert before_state.countdown != console_service._masked_pane_blink._reset_value  # type: ignore[attr-defined]

    with mock.patch.object(
        console_service,
        "rotate_masked_pane_buffers",
        wraps=console_service.rotate_masked_pane_buffers,
    ) as rotate_spy:
        result = dispatcher.dispatch("&,21")

    assert result.flag_index == 0x15
    assert rotate_spy.call_count == 1

    screen_bytes, colour_bytes = console_service.peek_block(
        screen_address=ConsoleService._MASKED_OVERLAY_SCREEN_BASE,
        screen_length=width,
        colour_address=ConsoleService._MASKED_OVERLAY_COLOUR_BASE,
        colour_length=width,
    )

    palette = console_service.screen.palette
    resolved_colour = bytes(
        _resolve_palette_colour(value, palette) for value in colour_payload
    )

    assert screen_bytes == screen_payload
    assert colour_bytes == resolved_colour
    assert tuple(buffers.live_screen[:width]) == tuple(screen_payload)
    assert tuple(buffers.live_colour[:width]) == tuple(colour_payload)

    fill_colour = console_service.screen_colour & 0xFF
    assert tuple(buffers.staged_screen[:width]) == (0x20,) * width
    assert tuple(buffers.staged_colour[:width]) == (fill_colour,) * width
    assert buffers.peek_pending_payload() is None
    assert buffers.has_pending_payload() is False
    assert buffers.dirty is False

    blink_state = console_service._masked_pane_blink.peek()  # type: ignore[attr-defined]
    reset_value = console_service._masked_pane_blink._reset_value  # type: ignore[attr-defined]
    assert blink_state.countdown == reset_value
