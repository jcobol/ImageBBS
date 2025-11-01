"""Shared masked-pane staging metadata derived from overlay defaults."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

from ..device_context import ConsoleService

MaskOverlayPayload = Tuple[Tuple[int, ...], Tuple[int, ...]]


# Sysop macro fallbacks recovered from ImageBBS BASIC overlays.  The ``ml.extra``
# dump omits these slots, so host tooling mirrors the recovered PETSCII payloads
# here to keep staging aligned with the 1.2B runtime.
_SYSOP_FALLBACK_PAYLOADS: Mapping[int, MaskOverlayPayload] = MappingProxyType(
    {
        0x20: (
            (0x68, 0xC3, 0x85, 0x06, 0xE2, 0xC1, 0xA0, 0x00)
            + (0x20,) * 32,
            (0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x00)
            + (0x0A,) * 32,
        ),
        0x21: ((0x00,) + (0x20,) * 39, (0x00,) + (0x0A,) * 39),
        0x22: ((0x00,) + (0x20,) * 39, (0x00,) + (0x0A,) * 39),
        0x23: ((0x00,) + (0x20,) * 39, (0x00,) + (0x0A,) * 39),
        0x24: ((0x00,) + (0x20,) * 39, (0x00,) + (0x0A,) * 39),
        0x25: ((0x00,) + (0x20,) * 39, (0x00,) + (0x0A,) * 39),
    }
)


class MaskedPaneMacro(Enum):
    """Named macro slots that feed ``tempbott+40``/``var_4078``."""

    MAIN_MENU_HEADER = "main_menu.header"
    MAIN_MENU_PROMPT = "main_menu.prompt"
    MAIN_MENU_INVALID = "main_menu.invalid_selection"
    FILE_TRANSFERS_HEADER = "file_transfers.header"
    FILE_TRANSFERS_PROMPT = "file_transfers.prompt"
    FILE_TRANSFERS_INVALID = "file_transfers.invalid_selection"
    SYSOP_HEADER = "sysop.header"
    SYSOP_PROMPT = "sysop.prompt"
    SYSOP_SAYING_PREAMBLE = "sysop.saying_preamble"
    SYSOP_SAYING_OUTPUT = "sysop.saying_output"
    SYSOP_INVALID = "sysop.invalid_selection"
    SYSOP_ABORT = "sysop.abort"
    FLAG_MAIN_MENU_HEADER = "flag.main_menu.header"
    FLAG_MAIN_MENU_PROMPT = "flag.main_menu.prompt"
    FLAG_MAIN_MENU_INVALID = "flag.main_menu.invalid_selection"
    FLAG_SAYINGS_ENABLE = "flag.sayings.enable"
    FLAG_SAYINGS_DISABLE = "flag.sayings.disable"
    FLAG_SAYINGS_PROMPT_ENABLE = "flag.sayings.prompt_enable"
    FLAG_SAYINGS_PROMPT_DISABLE = "flag.sayings.prompt_disable"
    FLAG_PROMPT_ENABLE = "flag.prompt.enable"
    FLAG_PROMPT_DISABLE = "flag.prompt.disable"


_MACROS_BY_VALUE: Mapping[str, MaskedPaneMacro] = MappingProxyType(
    {macro.value: macro for macro in MaskedPaneMacro}
)


def _normalise_macro(macro: Any) -> MaskedPaneMacro:
    if isinstance(macro, MaskedPaneMacro):
        return macro
    name = getattr(macro, "name", None)
    if isinstance(name, str):
        try:
            return MaskedPaneMacro[name]
        except KeyError:
            pass
    value = getattr(macro, "value", None)
    if isinstance(value, str):
        resolved = _MACROS_BY_VALUE.get(value)
        if resolved is not None:
            return resolved
    if isinstance(macro, str):
        try:
            return MaskedPaneMacro[macro]
        except KeyError:
            resolved = _MACROS_BY_VALUE.get(macro)
            if resolved is not None:
                return resolved
    raise KeyError(f"unsupported masked pane macro: {macro!r}")


@dataclass(frozen=True)
class MaskedPaneMacroSpec:
    """Metadata describing a macro slot and its fallback payload."""

    macro: MaskedPaneMacro
    slot: int
    fallback_overlay: Optional[MaskOverlayPayload] = None


@dataclass(frozen=True)
class MaskedPaneStagingMap:
    """Immutable lookup that maps macros, flags, and ampersand helpers."""

    macros: Mapping[MaskedPaneMacro, MaskedPaneMacroSpec]
    macros_by_slot: Mapping[int, MaskedPaneMacroSpec]
    flag_slots: Mapping[int, MaskedPaneMacroSpec]
    ampersand_sequences: Mapping[str, Tuple[MaskedPaneMacroSpec, ...]]

    def spec(self, macro: Any) -> MaskedPaneMacroSpec:
        return self.macros[_normalise_macro(macro)]

    def spec_for_slot(self, slot: int) -> Optional[MaskedPaneMacroSpec]:
        return self.macros_by_slot.get(slot)

    def slot(self, macro: Any) -> int:
        return self.spec(macro).slot

    def fallback_overlay(self, macro: Any) -> Optional[MaskOverlayPayload]:
        return self.spec(macro).fallback_overlay

    def fallback_overlay_for_slot(self, slot: int) -> Optional[MaskOverlayPayload]:
        spec = self.spec_for_slot(slot)
        if spec is None:
            return None
        return spec.fallback_overlay

    def stage_macro(
        self,
        console: ConsoleService,
        macro: MaskedPaneMacro,
        *,
        fill_colour: Optional[int] = None,
    ) -> None:
        spec = self.spec(macro)
        run = console.stage_macro_slot(spec.slot, fill_colour=fill_colour)
        if run is None and spec.fallback_overlay is not None:
            glyphs, colours = spec.fallback_overlay
            console.stage_masked_pane_overlay(
                glyphs,
                colours,
                fill_colour=fill_colour,
                slot=spec.slot,
            )

    def stage_flag_index(
        self,
        console: ConsoleService,
        flag_index: int,
        *,
        fill_colour: Optional[int] = None,
    ) -> None:
        spec = self.flag_slots.get(flag_index)
        if spec is None:
            return
        self.stage_macro(console, spec.macro, fill_colour=fill_colour)

    def ampersand_sequence(self, key: str) -> Tuple[MaskedPaneMacroSpec, ...]:
        return self.ampersand_sequences.get(key, ())


_ITERATION_47_ALIAS_SLOTS: Mapping[MaskedPaneMacro, int] = MappingProxyType(
    {
        MaskedPaneMacro.MAIN_MENU_HEADER: 0x04,
        MaskedPaneMacro.MAIN_MENU_PROMPT: 0x09,
        MaskedPaneMacro.MAIN_MENU_INVALID: 0x0D,
        MaskedPaneMacro.FILE_TRANSFERS_HEADER: 0x28,
        MaskedPaneMacro.FILE_TRANSFERS_PROMPT: 0x29,
        MaskedPaneMacro.FILE_TRANSFERS_INVALID: 0x2A,
        MaskedPaneMacro.SYSOP_HEADER: 0x20,
        MaskedPaneMacro.SYSOP_PROMPT: 0x21,
        MaskedPaneMacro.SYSOP_SAYING_PREAMBLE: 0x22,
        MaskedPaneMacro.SYSOP_SAYING_OUTPUT: 0x23,
        MaskedPaneMacro.SYSOP_INVALID: 0x24,
        MaskedPaneMacro.SYSOP_ABORT: 0x25,
        MaskedPaneMacro.FLAG_MAIN_MENU_HEADER: 0x04,
        MaskedPaneMacro.FLAG_MAIN_MENU_PROMPT: 0x09,
        MaskedPaneMacro.FLAG_MAIN_MENU_INVALID: 0x0D,
        MaskedPaneMacro.FLAG_SAYINGS_ENABLE: 0x14,
        MaskedPaneMacro.FLAG_SAYINGS_DISABLE: 0x15,
        MaskedPaneMacro.FLAG_SAYINGS_PROMPT_ENABLE: 0x16,
        MaskedPaneMacro.FLAG_SAYINGS_PROMPT_DISABLE: 0x17,
        MaskedPaneMacro.FLAG_PROMPT_ENABLE: 0x18,
        MaskedPaneMacro.FLAG_PROMPT_DISABLE: 0x19,
    }
)


_ITERATION_47_FLAG_SEQUENCE_SLOTS: Tuple[int, ...] = (
    0x04,
    0x09,
    0x0D,
    0x14,
    0x15,
    0x16,
    0x17,
    0x18,
    0x19,
)


_FLAG_SEQUENCE_OPERATIONS: Mapping[int, Tuple[int, ...]] = MappingProxyType(
    {
        0x04: (3,),
        0x09: (3,),
        0x0D: (3,),
        0x14: (3, 2),
        0x15: (3,),
        0x16: (3,),
        0x17: (3,),
        0x18: (3,),
        0x19: (3,),
    }
)


def _build_alias_slot_map(console: ConsoleService) -> Mapping[MaskedPaneMacro, int]:
    macros_by_slot = console.defaults.macros_by_slot

    for macro, slot in _ITERATION_47_ALIAS_SLOTS.items():
        if slot in macros_by_slot:
            continue
        if slot in _SYSOP_FALLBACK_PAYLOADS:
            continue
        raise KeyError(f"console metadata missing macro slot 0x{slot:02x}")

    return _ITERATION_47_ALIAS_SLOTS


def build_masked_pane_staging_map(console: ConsoleService) -> MaskedPaneStagingMap:
    """Return the canonical staging plan recovered from overlay research."""

    alias_slots = _build_alias_slot_map(console)

    macros: dict[MaskedPaneMacro, MaskedPaneMacroSpec] = {}
    macros_by_slot: dict[int, MaskedPaneMacroSpec] = {}

    for macro, slot in alias_slots.items():
        fallback = _SYSOP_FALLBACK_PAYLOADS.get(slot)
        spec = MaskedPaneMacroSpec(macro=macro, slot=slot, fallback_overlay=fallback)
        macros[macro] = spec
        macros_by_slot.setdefault(slot, spec)

    flag_slots: dict[int, MaskedPaneMacroSpec] = {}
    for entry in console.device.flag_dispatch.entries:
        if entry.slot not in console._MASKED_OVERLAY_FLAG_SLOTS:
            continue
        spec = macros_by_slot.get(entry.slot)
        if spec is None:
            raise KeyError(
                f"masked-pane staging slot 0x{entry.slot:02x} missing macro spec"
            )
        flag_slots[entry.flag_index] = spec

    ampersand_sequences: dict[str, Tuple[MaskedPaneMacroSpec, ...]] = {
        "&,28": (
            macros[MaskedPaneMacro.FILE_TRANSFERS_HEADER],
            macros[MaskedPaneMacro.FILE_TRANSFERS_PROMPT],
        ),
        "&,28,invalid": (
            macros[MaskedPaneMacro.FILE_TRANSFERS_INVALID],
        ),
        "&,52": tuple(macros_by_slot[slot] for slot in _ITERATION_47_FLAG_SEQUENCE_SLOTS),
    }

    for flag_index, operations in _FLAG_SEQUENCE_OPERATIONS.items():
        spec = flag_slots.get(flag_index)
        if spec is None:
            continue
        for operation in operations:
            key = f"&,52,{flag_index},{operation}"
            ampersand_sequences[key] = (spec,)

    return MaskedPaneStagingMap(
        macros=MappingProxyType(macros),
        macros_by_slot=MappingProxyType(macros_by_slot),
        flag_slots=MappingProxyType(flag_slots),
        ampersand_sequences=MappingProxyType(ampersand_sequences),
    )


__all__ = [
    "MaskedPaneMacro",
    "MaskedPaneMacroSpec",
    "MaskedPaneStagingMap",
    "build_masked_pane_staging_map",
]

