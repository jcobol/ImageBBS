"""Wrapper for the prototype runtime module."""
from __future__ import annotations

from typing import Optional, Tuple

from .._compat import mirror_module
from ..device_context import ConsoleService
from .indicator_controller import IndicatorController
from .message_store import (
    MessageRecord as _RuntimeMessageRecord,
    MessageStore as _RuntimeMessageStore,
)

_TARGET = mirror_module(globals(), "scripts.prototypes.runtime.ampersand_overrides")

_PROTOTYPE_HANDLE_CHKFLAGS = _TARGET.handle_chkflags
BUILTIN_AMPERSAND_OVERRIDES = dict(_TARGET.BUILTIN_AMPERSAND_OVERRIDES)
BUILTIN_AMPERSAND_OVERRIDES[0x1C] = f"{__name__}:handle_file_transfer_sequence"
BUILTIN_AMPERSAND_OVERRIDES[0x34] = f"{__name__}:handle_chkflags"
BUILTIN_AMPERSAND_OVERRIDES[0x32] = f"{__name__}:handle_outscn"

# Ensure ampersand overrides recognise the runtime message store types.
MessageRecord = _RuntimeMessageRecord
MessageStore = _RuntimeMessageStore
_TARGET.MessageRecord = MessageRecord
_TARGET.MessageStore = MessageStore


def handle_chkflags(context: _TARGET.AmpersandDispatchContext):
    """Emulate ``chkflags`` while keeping the indicator controller in sync."""

    result = _PROTOTYPE_HANDLE_CHKFLAGS(context)

    try:
        registry = _TARGET._require_registry(context)
    except RuntimeError:
        return result

    services = _TARGET._resolve_services(context, registry)
    console = _TARGET._resolve_console_service(services)
    if console is None:
        return result

    spinner_value = console.screen.peek_screen_address(
        ConsoleService._SPINNER_SCREEN_ADDRESS
    )
    spinner_enabled = bool(
        spinner_value is not None and spinner_value != _TARGET._SPACE_GLYPH
    )

    pause_value = console.screen.peek_screen_address(
        ConsoleService._PAUSE_SCREEN_ADDRESS
    )
    pause_active = bool(pause_value == _TARGET._PAUSE_GLYPH)

    abort_value = console.screen.peek_screen_address(
        ConsoleService._ABORT_SCREEN_ADDRESS
    )
    abort_active = bool(abort_value == _TARGET._ABORT_GLYPH)

    carrier_leading = console.screen.peek_screen_address(
        ConsoleService._CARRIER_LEADING_SCREEN_ADDRESS
    )
    carrier_indicator = console.screen.peek_screen_address(
        ConsoleService._CARRIER_INDICATOR_SCREEN_ADDRESS
    )
    carrier_active = bool(
        (carrier_leading is not None and carrier_leading != _TARGET._SPACE_GLYPH)
        or (
            carrier_indicator is not None
            and carrier_indicator != _TARGET._SPACE_GLYPH
        )
    )

    controller = registry.services.get("indicator_controller")
    if isinstance(controller, IndicatorController):
        controller.sync_from_console(
            pause_active=pause_active,
            abort_active=abort_active,
            spinner_enabled=spinner_enabled,
            spinner_glyph=spinner_value,
            carrier_active=carrier_active,
        )

    return result


def handle_outscn(context: _TARGET.AmpersandDispatchContext):
    """Emulate ``outscn`` while staging masked-pane payloads via the runtime map."""

    registry = _TARGET._require_registry(context)
    services = _TARGET._resolve_services(context, registry)
    console = _TARGET._resolve_console_service(services)
    buffers = _TARGET._resolve_masked_pane_buffers(services, context.payload)

    result = registry.dispatch(context.invocation.routine, context, use_default=True)

    if console is None or buffers is None:
        return result

    pending_payload = buffers.consume_pending_payload()
    if pending_payload is not None:
        console.capture_masked_pane_buffers(buffers)
        screen_payload, colour_payload = pending_payload
        staged = False

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

    fill_glyph = 0x20
    fill_colour = console.screen_colour & 0xFF

    has_payload = (pending_payload is not None) or _TARGET._masked_pane_has_payload(
        buffers, fill_glyph, fill_colour
    )

    if has_payload:
        console.commit_masked_pane_staging(
            fill_glyph=fill_glyph, fill_colour=fill_colour
        )

    buffers.clear_pending_payload()

    return result


def handle_file_transfer_sequence(
    context: _TARGET.AmpersandDispatchContext,
):
    """Stage masked-pane macros for the ``&,28`` ampersand family."""

    registry = _TARGET._require_registry(context)
    services = _TARGET._resolve_services(context, registry)
    console = _TARGET._resolve_console_service(services)

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
        colour_sequence = getattr(screen, "colour_bytes", None) if screen is not None else None
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
        glyph_bytes = glyph_bytes + bytes((0x20,) * (width - len(glyph_bytes)))
    if len(colour_bytes) < width:
        fill_colour = console.screen_colour & 0xFF
        colour_bytes = colour_bytes + bytes(
            (fill_colour,) * (width - len(colour_bytes))
        )

    return glyph_bytes[:width], colour_bytes[:width]


def _normalise_ampersand_sequence_key(
    invocation: _TARGET.AmpersandInvocation,
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
