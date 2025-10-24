"""Wrapper for the prototype runtime module."""
from __future__ import annotations

from .._compat import mirror_module
from ..device_context import ConsoleService
from .indicator_controller import IndicatorController

_TARGET = mirror_module(globals(), "scripts.prototypes.runtime.ampersand_overrides")

_PROTOTYPE_HANDLE_CHKFLAGS = _TARGET.handle_chkflags
BUILTIN_AMPERSAND_OVERRIDES = dict(_TARGET.BUILTIN_AMPERSAND_OVERRIDES)
BUILTIN_AMPERSAND_OVERRIDES[0x34] = f"{__name__}:handle_chkflags"


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
