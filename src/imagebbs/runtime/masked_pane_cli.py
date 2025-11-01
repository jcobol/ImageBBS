"""CLI helper that emits masked-pane staging metadata as JSON."""
from __future__ import annotations

import json
from typing import Mapping, Sequence

from ..device_context import ConsoleService, DeviceContext, bootstrap_device_context
from .ampersand_overrides import BUILTIN_AMPERSAND_OVERRIDES
from .masked_pane_staging import MaskedPaneMacro, MaskedPaneStagingMap


# Why: normalise fallback tuples into JSON-friendly payloads for downstream tooling.
def _serialise_fallback(payload: tuple[tuple[int, ...], tuple[int, ...]] | None) -> Mapping[str, list[int]] | None:
    if payload is None:
        return None
    glyphs, colours = payload
    return {
        "glyphs": list(glyphs),
        "colours": list(colours),
    }


# Why: expose macro-level metadata so CLI consumers can align slots with fallbacks.
def _serialise_macros(staging: MaskedPaneStagingMap) -> tuple[dict[str, object], dict[int, list[str]]]:
    macros: dict[str, object] = {}
    slots: dict[int, list[str]] = {}
    for macro in sorted(MaskedPaneMacro, key=lambda value: value.value):
        spec = staging.spec(macro)
        macros[macro.value] = {
            "slot": spec.slot,
            "fallback": _serialise_fallback(spec.fallback_overlay),
        }
        slots.setdefault(spec.slot, []).append(macro.value)
    for slot_macros in slots.values():
        slot_macros.sort()
    return macros, slots


# Why: mirror flag dispatch metadata so ampersand tooling can target masked-pane slots.
def _serialise_flag_slots(staging: MaskedPaneStagingMap) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for flag_index, spec in sorted(staging.flag_slots.items()):
        records.append(
            {
                "flag_index": flag_index,
                "macro": spec.macro.value,
                "slot": spec.slot,
            }
        )
    return records


# Why: summarise ampersand expansion sequences to aid test fixtures and tooling scripts.
def _serialise_ampersand_sequences(staging: MaskedPaneStagingMap) -> dict[str, list[str]]:
    sequences: dict[str, list[str]] = {}
    for key in sorted(staging.ampersand_sequences):
        sequence = staging.ampersand_sequence(key)
        sequences[key] = [spec.macro.value for spec in sequence]
    return sequences


# Why: combine all staging metadata into a single JSON payload for CLI consumers.
def _collect_payload(console: ConsoleService) -> dict[str, object]:
    staging = console.masked_pane_staging_map
    macros, slots = _serialise_macros(staging)
    return {
        "macros": macros,
        "slots": {f"0x{slot:02x}": names for slot, names in sorted(slots.items())},
        "flag_slots": _serialise_flag_slots(staging),
        "ampersand_sequences": _serialise_ampersand_sequences(staging),
    }


# Why: build a default device context so the CLI can inspect runtime metadata.
def _bootstrap_console() -> ConsoleService:
    context: DeviceContext = bootstrap_device_context(
        assignments=(), ampersand_overrides=BUILTIN_AMPERSAND_OVERRIDES
    )
    console = context.get_service("console")
    if not isinstance(console, ConsoleService):  # pragma: no cover - defensive guard
        raise TypeError("console service unavailable")
    return console


# Why: entry point for ``python -m imagebbs.runtime.masked_pane_cli`` invocations.
def main(argv: Sequence[str] | None = None) -> int:
    console = _bootstrap_console()
    payload = _collect_payload(console)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via python -m
    raise SystemExit(main())
