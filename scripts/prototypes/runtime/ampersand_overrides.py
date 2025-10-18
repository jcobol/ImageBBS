"""Runtime ampersand overrides that mirror core ImageBBS hooks."""
from __future__ import annotations

from dataclasses import replace
from types import MappingProxyType
from typing import Mapping, MutableMapping, Sequence, TYPE_CHECKING, cast

from ..ampersand_dispatcher import AmpersandDispatchContext
from ..ampersand_registry import AmpersandRegistry, AmpersandResult
from ..device_context import ConsoleService, DeviceContext, DeviceError
from .message_store import MessageRecord, MessageStore

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from ..message_editor import SessionContext


BUILTIN_AMPERSAND_OVERRIDES: Mapping[int, str] = MappingProxyType(
    {
        0x34: "scripts.prototypes.runtime.ampersand_overrides:handle_chkflags",
        0x08: "scripts.prototypes.runtime.ampersand_overrides:handle_dskdir",
        0x03: "scripts.prototypes.runtime.ampersand_overrides:handle_read0",
    }
)

# PETSCII helper constants -----------------------------------------------------
_SPACE_GLYPH = 0x20
_PAUSE_GLYPH = 0xD0  # "P"
_ABORT_GLYPH = 0xC1  # "A"
_SPINNER_ACTIVE_GLYPH = 0xB0
_CARRIER_LEADING_ACTIVE_GLYPH = 0xA0
_CARRIER_INDICATOR_ACTIVE_GLYPH = 0xFA

_SPINNER_SCREEN_ADDRESS = 0x049C
_CARRIER_LEADING_SCREEN_ADDRESS = 0x0400
_CARRIER_INDICATOR_SCREEN_ADDRESS = 0x0427


def handle_chkflags(context: AmpersandDispatchContext) -> AmpersandResult:
    """Emulate ``chkflags`` (``&,52``) for lightbar and indicator toggles."""

    registry = _require_registry(context)
    services = _resolve_services(context, registry)
    console = _resolve_console_service(services)

    result = registry.dispatch(context.invocation.routine, context, use_default=True)

    if console is not None:
        flag_index = context.invocation.argument_x
        operation = context.invocation.argument_y
        _update_indicator(console, flag_index, operation)

    return result


def handle_dskdir(context: AmpersandDispatchContext) -> AmpersandResult:
    """Emulate ``dskdir`` (``&,8``) while honouring fallback text payloads."""

    registry = _require_registry(context)
    services = _resolve_services(context, registry)
    result = registry.dispatch(context.invocation.routine, context, use_default=True)
    fallback_text = _extract_fallback_text(context.payload)
    if fallback_text is not None:
        return replace(result, rendered_text=fallback_text)

    device_context = _resolve_device_context(services, context.payload)
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


def handle_read0(context: AmpersandDispatchContext) -> AmpersandResult:
    """Emulate ``read0`` (``&,3``) by staging editor output into the message store."""

    registry = _require_registry(context)
    services = _resolve_services(context, registry)
    store = _resolve_message_store(services, context.payload)
    session = _resolve_session(context.payload)

    result = registry.dispatch(context.invocation.routine, context, use_default=True)

    if store is None or session is None:
        return result

    record = _append_session_message(store, session)
    session.selected_message_id = record.message_id
    result_context = {
        "record": record,
        "session": session,
    }
    return replace(result, context=result_context)


# Internal helpers -------------------------------------------------------------

_EMPTY_MAPPING: Mapping[str, object] = MappingProxyType({})


def _payload_mapping(payload: object) -> Mapping[str, object]:
    if isinstance(payload, Mapping):
        return payload
    return _EMPTY_MAPPING


def _require_registry(context: AmpersandDispatchContext) -> AmpersandRegistry:
    payload = _payload_mapping(context.payload)
    registry = payload.get("registry")
    if isinstance(registry, AmpersandRegistry):
        return registry
    raise RuntimeError("ampersand override requires the registry in the payload")


def _resolve_services(
    context: AmpersandDispatchContext, registry: AmpersandRegistry
) -> Mapping[str, object]:
    payload = _payload_mapping(context.payload)
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
    services: Mapping[str, object], payload: object
) -> DeviceContext | None:
    service = services.get("device_context")
    if isinstance(service, DeviceContext):
        return service
    payload_mapping = _payload_mapping(payload)
    candidate = payload_mapping.get("device_context")
    if isinstance(candidate, DeviceContext):
        return candidate
    return None


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

    current = console.screen.peek_screen_address(_SPINNER_SCREEN_ADDRESS)
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

    leading = console.screen.peek_screen_address(_CARRIER_LEADING_SCREEN_ADDRESS)
    indicator = console.screen.peek_screen_address(_CARRIER_INDICATOR_SCREEN_ADDRESS)

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


def _extract_fallback_text(payload: object) -> str | None:
    payload_mapping = _payload_mapping(payload)
    fallback = payload_mapping.get("fallback_text")
    if fallback is not None:
        return str(fallback)
    return None


def _resolve_message_store(
    services: Mapping[str, object], payload: object
) -> MessageStore | None:
    service = services.get("message_store")
    if isinstance(service, MessageStore):
        return service
    payload_mapping = _payload_mapping(payload)
    candidate = payload_mapping.get("message_store")
    if isinstance(candidate, MessageStore):
        return candidate
    return None


def _resolve_session(payload: object) -> "SessionContext" | None:
    payload_mapping = _payload_mapping(payload)
    session = payload_mapping.get("session")
    if session is not None and _is_session_like(session):
        return cast("SessionContext", session)
    return None


def _is_session_like(value: object) -> bool:
    required = ("board_id", "user_id", "draft_buffer", "command_buffer", "selected_message_id")
    return all(hasattr(value, attribute) for attribute in required)


def _append_session_message(store: MessageStore, session: "SessionContext") -> MessageRecord:
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


__all__ = [
    "BUILTIN_AMPERSAND_OVERRIDES",
    "handle_chkflags",
    "handle_dskdir",
    "handle_read0",
]
