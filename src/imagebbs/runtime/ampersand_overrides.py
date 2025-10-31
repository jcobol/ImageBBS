"""Runtime ampersand overrides that mirror core ImageBBS hooks."""
from __future__ import annotations

from dataclasses import replace
from types import MappingProxyType
from typing import Mapping, MutableMapping, Optional, Sequence, TYPE_CHECKING, Tuple, cast

from ..ampersand.dispatcher import AmpersandDispatchContext, AmpersandInvocation
from ..ampersand.registry import AmpersandRegistry, AmpersandResult
from ..device_context import (
    ConsoleService,
    DeviceContext,
    DeviceError,
    MaskedPaneBuffers,
)
from .indicator_controller import IndicatorController
from .message_store import MessageRecord, MessageStore

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from ..message_editor import SessionContext

BUILTIN_AMPERSAND_OVERRIDES: Mapping[int, str] = MappingProxyType(
    {
        0x1C: f"{__name__}:handle_file_transfer_sequence",
        0x34: f"{__name__}:handle_chkflags",
        0x15: f"{__name__}:handle_disp3",
        0x32: f"{__name__}:handle_outscn",
        0x08: f"{__name__}:handle_dskdir",
        0x03: f"{__name__}:handle_read0",
    }
)

# PETSCII helper constants -----------------------------------------------------
_SPACE_GLYPH = 0x20
_PAUSE_GLYPH = 0xD0  # "P"
_ABORT_GLYPH = 0xC1  # "A"
_SPINNER_ACTIVE_GLYPH = 0xB0
_CARRIER_LEADING_ACTIVE_GLYPH = 0xA0
_CARRIER_INDICATOR_ACTIVE_GLYPH = 0xFA


def handle_chkflags(context: AmpersandDispatchContext) -> AmpersandResult:
    """Emulate ``chkflags`` (``&,52``) while keeping staging and indicators aligned."""

    registry = _require_registry(context)
    services = _resolve_services(context, registry)
    console = _resolve_console_service(services)

    if console is not None:
        staging_map = console.masked_pane_staging_map
        sequence_key = _normalise_ampersand_sequence_key(context.invocation)
        specs = staging_map.ampersand_sequence(sequence_key)
        for spec in specs:
            staging_map.stage_macro(console, spec.macro)

    result = registry.dispatch(context.invocation.routine, context, use_default=True)

    if console is not None:
        flag_index = context.invocation.argument_x
        operation = context.invocation.argument_y
        _update_indicator(console, flag_index, operation)
        _sync_indicator_controller(console, services)

    return result


def handle_dskdir(context: AmpersandDispatchContext | Mapping[str, object]) -> AmpersandResult:
    """Emulate ``dskdir`` (``&,8``) while honouring fallback text payloads."""

    registry = _require_registry(context)
    services = _resolve_services(context, registry)
    payload_mapping = _context_payload(context)
    invocation = _context_invocation(
        context, default_routine=0x08, default_expression="&,8"
    )

    result = registry.dispatch(invocation.routine, context, use_default=True)

    fallback_text = _extract_fallback_text(payload_mapping)
    if fallback_text is not None:
        return replace(result, rendered_text=fallback_text)

    device_context = _resolve_device_context(services, payload_mapping)
    if device_context is None:
        return result

    slot = context.invocation.argument_x or 8
    try:
        directory_lines = device_context.drive_directory_lines(slot, refresh=True)
    except DeviceError:
        return result

    listing_text = "\r".join(directory_lines)
    if not listing_text:
        return result

    macro_text = result.rendered_text or ""
    if macro_text:
        if macro_text.endswith("\r"):
            combined = f"{macro_text}{listing_text}"
        else:
            combined = f"{macro_text}\r{listing_text}"
    else:
        combined = listing_text
    return replace(result, rendered_text=combined)


def handle_outscn(context: AmpersandDispatchContext | Mapping[str, object]) -> AmpersandResult:
    """Emulate ``outscn`` (``&,50``) by committing masked pane staging."""

    registry = _require_registry(context)
    services = _resolve_services(context, registry)
    console = _resolve_console_service(services)
    payload_mapping = _context_payload(context)
    buffers = _resolve_masked_pane_buffers(services, payload_mapping)

    invocation = _context_invocation(
        context, default_routine=0x32, default_expression="&,50"
    )

    result = registry.dispatch(invocation.routine, context, use_default=True)

    if console is None or buffers is None:
        return result

    has_payload, fill_glyph, fill_colour = _restage_masked_pane_payload(
        console, buffers
    )

    if has_payload:
        console.commit_masked_pane_staging(
            fill_glyph=fill_glyph, fill_colour=fill_colour
        )

    buffers.clear_pending_payload()

    return result


def handle_disp3(context: AmpersandDispatchContext | Mapping[str, object]) -> AmpersandResult:
    """Emulate ``disp3`` (``&,21``) while resetting masked-pane blink state."""

    registry = _require_registry(context)
    services = _resolve_services(context, registry)
    console = _resolve_console_service(services)
    payload_mapping = _context_payload(context)
    buffers = _resolve_masked_pane_buffers(services, payload_mapping)
    invocation = _context_invocation(
        context, default_routine=0x15, default_expression="&,21"
    )

    if console is None or buffers is None:
        return registry.dispatch(invocation.routine, context, use_default=True)

    has_payload, fill_glyph, fill_colour = _restage_masked_pane_payload(
        console, buffers
    )

    if has_payload:
        console.reset_masked_pane_blink()
        console.commit_masked_pane_staging(
            fill_glyph=fill_glyph, fill_colour=fill_colour
        )

    result = registry.dispatch(invocation.routine, context, use_default=True)

    buffers.clear_pending_payload()

    return result


def handle_read0(context: AmpersandDispatchContext | Mapping[str, object]) -> AmpersandResult:
    """Emulate ``read0`` (``&,3``) by staging editor output into the message store."""

    registry = _require_registry(context)
    services = _resolve_services(context, registry)
    payload_mapping = _context_payload(context)
    store = _resolve_message_store(services, payload_mapping)
    session = _resolve_session(payload_mapping)

    invocation = _context_invocation(
        context, default_routine=0x03, default_expression="&,3"
    )

    result = registry.dispatch(invocation.routine, context, use_default=True)

    if store is None or session is None:
        return result

    record = _append_session_message(store, session)
    session.selected_message_id = record.message_id
    result_context = {
        "record": record,
        "session": session,
    }
    return replace(result, context=result_context)


def handle_file_transfer_sequence(
    context: AmpersandDispatchContext,
) -> AmpersandResult:
    """Stage masked-pane macros for the ``&,28`` ampersand family."""

    registry = _require_registry(context)
    services = _resolve_services(context, registry)
    console = _resolve_console_service(services)

    if console is not None:
        staging_map = console.masked_pane_staging_map
        sequence_key = _normalise_ampersand_sequence_key(context.invocation)
        specs = staging_map.ampersand_sequence(sequence_key)
        if specs:
            for spec in specs:
                staging_map.stage_macro(console, spec.macro)

    return registry.dispatch(
        context.invocation.routine, context, use_default=True
    )


# Internal helpers -------------------------------------------------------------

_EMPTY_MAPPING: Mapping[str, object] = MappingProxyType({})


def _payload_mapping(payload: object | None) -> Mapping[str, object]:
    if isinstance(payload, Mapping):
        return payload
    return _EMPTY_MAPPING


def _context_payload(context: object) -> Mapping[str, object]:
    if isinstance(context, AmpersandDispatchContext):
        return _payload_mapping(context.payload)
    if isinstance(context, Mapping):
        return cast(Mapping[str, object], context)
    return _EMPTY_MAPPING


def _context_invocation(
    context: AmpersandDispatchContext | Mapping[str, object],
    *,
    default_routine: int,
    default_expression: str,
) -> AmpersandInvocation:
    if isinstance(context, AmpersandDispatchContext):
        return context.invocation
    return AmpersandInvocation(
        routine=default_routine,
        argument_x=0,
        argument_y=0,
        expression=default_expression,
    )


def _require_registry(
    context: AmpersandDispatchContext | Mapping[str, object]
) -> AmpersandRegistry:
    payload = _context_payload(context)
    registry = payload.get("registry")
    if isinstance(registry, AmpersandRegistry):
        return registry
    raise RuntimeError("ampersand override requires the registry in the payload")


def _resolve_services(
    context: AmpersandDispatchContext | Mapping[str, object],
    registry: AmpersandRegistry,
) -> Mapping[str, object]:
    payload = _context_payload(context)
    services = payload.get("services")
    if isinstance(services, Mapping):
        return services
    return registry.services


def _resolve_console_service(
    services: Mapping[str, object]
) -> ConsoleService | None:
    service = services.get("console")
    if isinstance(service, ConsoleService):
        return service
    return None


def _resolve_device_context(
    services: Mapping[str, object], payload: object | None
) -> DeviceContext | None:
    service = services.get("device_context")
    if isinstance(service, DeviceContext):
        return service
    payload_mapping = _payload_mapping(payload)
    candidate = payload_mapping.get("device_context")
    if isinstance(candidate, DeviceContext):
        return candidate
    return None


def _resolve_masked_pane_buffers(
    services: Mapping[str, object], payload: object | None
) -> MaskedPaneBuffers | None:
    buffers = services.get("masked_pane_buffers")
    if isinstance(buffers, MaskedPaneBuffers):
        return buffers
    payload_mapping = _payload_mapping(payload)
    candidate = payload_mapping.get("masked_pane_buffers")
    if isinstance(candidate, MaskedPaneBuffers):
        return candidate
    return None


def _masked_pane_has_payload(
    buffers: MaskedPaneBuffers, fill_glyph: int, fill_colour: int
) -> bool:
    if buffers.has_pending_payload():
        return True
    if buffers.dirty:
        return True
    glyph_byte = int(fill_glyph) & 0xFF
    colour_byte = int(fill_colour) & 0xFF
    if any(byte != glyph_byte for byte in buffers.staged_screen):
        return True
    if any(byte != colour_byte for byte in buffers.staged_colour):
        return True
    return False


def _update_indicator(
    console: ConsoleService, flag_index: int, operation: int
) -> None:
    if flag_index == 0x02:  # spinner indicator bit
        _update_spinner(console, operation)
        return
    if flag_index == 0x04:  # carrier indicator bit
        _update_carrier(console, operation)
        return

    enabled = bool(operation)
    if flag_index == 0x10:  # pause indicator
        glyph = _PAUSE_GLYPH if enabled else _SPACE_GLYPH
        console.set_pause_indicator(glyph, colour=0x01)
    elif flag_index == 0x11:  # abort indicator
        glyph = _ABORT_GLYPH if enabled else _SPACE_GLYPH
        console.set_abort_indicator(glyph, colour=0x02)


def _update_spinner(console: ConsoleService, operation: int) -> None:
    if operation not in (0, 1, 2):
        return

    current = console.screen.peek_screen_address(ConsoleService._SPINNER_SCREEN_ADDRESS)
    if operation == 0:  # clear
        glyph = _SPACE_GLYPH
    elif operation == 1:  # set
        glyph = _SPINNER_ACTIVE_GLYPH
    else:  # toggle
        glyph = _SPINNER_ACTIVE_GLYPH if current == _SPACE_GLYPH else _SPACE_GLYPH

    console.set_spinner_glyph(glyph)


def _update_carrier(console: ConsoleService, operation: int) -> None:
    if operation not in (0, 1, 2):
        return

    leading = console.screen.peek_screen_address(
        ConsoleService._CARRIER_LEADING_SCREEN_ADDRESS
    )
    indicator = console.screen.peek_screen_address(
        ConsoleService._CARRIER_INDICATOR_SCREEN_ADDRESS
    )

    if operation == 0:  # clear
        leading_glyph = _SPACE_GLYPH
        indicator_glyph = _SPACE_GLYPH
    elif operation == 1:  # set
        leading_glyph = _CARRIER_LEADING_ACTIVE_GLYPH
        indicator_glyph = _CARRIER_INDICATOR_ACTIVE_GLYPH
    else:  # toggle
        is_active = (leading != _SPACE_GLYPH) or (indicator != _SPACE_GLYPH)
        if is_active:
            leading_glyph = _SPACE_GLYPH
            indicator_glyph = _SPACE_GLYPH
        else:
            leading_glyph = _CARRIER_LEADING_ACTIVE_GLYPH
            indicator_glyph = _CARRIER_INDICATOR_ACTIVE_GLYPH

    console.set_carrier_indicator(
        leading_cell=leading_glyph, indicator_cell=indicator_glyph
    )


def _sync_indicator_controller(
    console: ConsoleService, services: Mapping[str, object]
) -> None:
    controller = services.get("indicator_controller")
    if not isinstance(controller, IndicatorController):
        return

    spinner_value = console.screen.peek_screen_address(
        ConsoleService._SPINNER_SCREEN_ADDRESS
    )
    spinner_enabled = bool(
        spinner_value is not None and spinner_value != _SPACE_GLYPH
    )

    pause_value = console.screen.peek_screen_address(
        ConsoleService._PAUSE_SCREEN_ADDRESS
    )
    pause_active = bool(pause_value == _PAUSE_GLYPH)

    abort_value = console.screen.peek_screen_address(
        ConsoleService._ABORT_SCREEN_ADDRESS
    )
    abort_active = bool(abort_value == _ABORT_GLYPH)

    carrier_leading = console.screen.peek_screen_address(
        ConsoleService._CARRIER_LEADING_SCREEN_ADDRESS
    )
    carrier_indicator = console.screen.peek_screen_address(
        ConsoleService._CARRIER_INDICATOR_SCREEN_ADDRESS
    )
    carrier_active = bool(
        (carrier_leading is not None and carrier_leading != _SPACE_GLYPH)
        or (
            carrier_indicator is not None and carrier_indicator != _SPACE_GLYPH
        )
    )

    controller.sync_from_console(
        pause_active=pause_active,
        abort_active=abort_active,
        spinner_enabled=spinner_enabled,
        spinner_glyph=spinner_value,
        carrier_active=carrier_active,
    )


def _extract_fallback_text(payload: object | None) -> str | None:
    payload_mapping = _payload_mapping(payload)
    fallback = payload_mapping.get("fallback_text")
    if fallback is not None:
        return str(fallback)
    return None


def _resolve_message_store(
    services: Mapping[str, object], payload: object | None
) -> MessageStore | None:
    service = services.get("message_store")
    if isinstance(service, MessageStore):
        return service
    payload_mapping = _payload_mapping(payload)
    candidate = payload_mapping.get("message_store")
    if isinstance(candidate, MessageStore):
        return candidate
    return None


def _resolve_session(payload: object | None) -> "SessionContext" | None:
    payload_mapping = _payload_mapping(payload)
    session = payload_mapping.get("session")
    if session is not None and _is_session_like(session):
        return cast("SessionContext", session)
    return None


def _is_session_like(value: object) -> bool:
    required = (
        "board_id",
        "user_id",
        "draft_buffer",
        "command_buffer",
        "selected_message_id",
    )
    return all(hasattr(value, attribute) for attribute in required)


def _append_session_message(
    store: MessageStore, session: "SessionContext"
) -> MessageRecord:
    subject = getattr(session, "command_buffer", "") or "Untitled"
    lines: Sequence[str] = getattr(session, "draft_buffer", ()) or ()
    record = store.append(
        board_id=getattr(session, "board_id", ""),
        subject=subject,
        author_handle=getattr(session, "user_id", ""),
        lines=list(lines),
    )
    if hasattr(session, "cache_draft"):
        session.cache_draft(record.message_id)
    if hasattr(session, "clear_draft"):
        session.clear_draft()
    return record


def _resolve_staging_map_spec_for_payload(
    console: ConsoleService,
    staging_map,
    screen_payload: bytes,
    colour_payload: bytes,
    *,
    width: int,
) -> Optional[object]:
    glyph_bytes = bytes(screen_payload[:width])
    colour_bytes = bytes(colour_payload[:width])

    for spec in staging_map.macros_by_slot.values():
        expected = _expected_macro_overlay(console, staging_map, spec.slot, width)
        if expected is None:
            continue
        expected_glyphs, expected_colours = expected
        if expected_glyphs == glyph_bytes and expected_colours == colour_bytes:
            return spec
    return None


def _expected_macro_overlay(
    console: ConsoleService,
    staging_map,
    slot: int,
    width: int,
) -> Optional[Tuple[bytes, bytes]]:
    defaults = console.defaults
    entry = defaults.macros_by_slot.get(slot)
    glyph_bytes: Optional[bytes] = None
    colour_bytes: Optional[bytes] = None

    if entry is not None:
        screen = getattr(entry, "screen", None)
        glyph_sequence = getattr(screen, "glyph_bytes", None) if screen is not None else None
        colour_sequence = (
            getattr(screen, "colour_bytes", None) if screen is not None else None
        )
        if glyph_sequence is not None and colour_sequence is not None:
            glyph_bytes = bytes(glyph_sequence[:width])
            colour_bytes = bytes(colour_sequence[:width])

    if glyph_bytes is None or colour_bytes is None:
        run = console.glyph_lookup.macros_by_slot.get(slot)
        if run is not None:
            rendered = bytes(run.rendered[:width])
            fill_colour = console.screen_colour & 0xFF
            glyph_bytes = rendered
            colour_bytes = bytes((fill_colour,) * len(rendered))

    if glyph_bytes is None or colour_bytes is None:
        fallback = staging_map.fallback_overlay_for_slot(slot)
        if fallback is not None:
            glyph_bytes = bytes(fallback[0][:width])
            colour_bytes = bytes(fallback[1][:width])

    if glyph_bytes is None or colour_bytes is None:
        return None

    if len(glyph_bytes) < width:
        glyph_bytes = glyph_bytes + bytes((_SPACE_GLYPH,) * (width - len(glyph_bytes)))
    if len(colour_bytes) < width:
        fill_colour = console.screen_colour & 0xFF
        colour_bytes = colour_bytes + bytes(
            (fill_colour,) * (width - len(colour_bytes))
        )

    return glyph_bytes[:width], colour_bytes[:width]


def _restage_masked_pane_payload(
    console: ConsoleService, buffers: MaskedPaneBuffers
) -> Tuple[bool, int, int]:
    """Restage cached masked-pane payloads prior to a commit."""

    pending_payload = buffers.consume_pending_payload()
    staged = False

    if pending_payload is not None:
        console.capture_masked_pane_buffers(buffers)
        screen_payload, colour_payload = pending_payload
        staging_map = console.masked_pane_staging_map
        spec = _resolve_staging_map_spec_for_payload(
            console,
            staging_map,
            screen_payload,
            colour_payload,
            width=buffers.width,
        )
        if spec is not None:
            staging_map.stage_macro(console, spec.macro)
            staged = True
        if not staged:
            console.stage_masked_pane_overlay(screen_payload, colour_payload)

    fill_glyph = _SPACE_GLYPH
    fill_colour = console.screen_colour & 0xFF

    has_payload = (pending_payload is not None) or _masked_pane_has_payload(
        buffers, fill_glyph, fill_colour
    )

    return has_payload, fill_glyph, fill_colour


def _normalise_ampersand_sequence_key(
    invocation: AmpersandInvocation,
) -> str:
    expression = "".join(invocation.expression.split())
    if expression:
        if expression.startswith("&"):
            return expression
        return f"&,{expression}"

    parts = [f"&,{invocation.routine}"]
    if invocation.argument_x or invocation.argument_y:
        parts.append(str(invocation.argument_x))
        if invocation.argument_y:
            parts.append(str(invocation.argument_y))
    return ",".join(parts)


__all__ = [
    "BUILTIN_AMPERSAND_OVERRIDES",
    "handle_chkflags",
    "handle_dskdir",
    "handle_disp3",
    "handle_outscn",
    "handle_read0",
    "handle_file_transfer_sequence",
]
