from __future__ import annotations

import json

import pytest

from imagebbs.device_context import ConsoleService, bootstrap_device_context
from imagebbs.runtime.ampersand_overrides import BUILTIN_AMPERSAND_OVERRIDES
from imagebbs.runtime import masked_pane_cli
from imagebbs.runtime.masked_pane_staging import MaskedPaneMacro


# Why: assemble the expected JSON payload so CLI output can be verified deterministically.
def _build_expected_payload(console: ConsoleService) -> dict[str, object]:
    staging = console.masked_pane_staging_map
    macros: dict[str, object] = {}
    slots: dict[str, list[str]] = {}
    for macro in MaskedPaneMacro:
        spec = staging.spec(macro)
        fallback = staging.fallback_overlay(macro)
        macros[macro.value] = {
            "slot": spec.slot,
            "fallback": (
                {
                    "glyphs": list(fallback[0]),
                    "colours": list(fallback[1]),
                }
                if fallback is not None
                else None
            ),
        }
        slots.setdefault(f"0x{spec.slot:02x}", []).append(macro.value)
    for entries in slots.values():
        entries.sort()
    flag_slots = [
        {
            "flag_index": flag_index,
            "macro": spec.macro.value,
            "slot": spec.slot,
        }
        for flag_index, spec in sorted(staging.flag_slots.items())
    ]
    ampersand_sequences = {
        key: [spec.macro.value for spec in staging.ampersand_sequence(key)]
        for key in sorted(staging.ampersand_sequences)
    }
    return {
        "macros": macros,
        "slots": {key: entries for key, entries in sorted(slots.items())},
        "flag_slots": flag_slots,
        "ampersand_sequences": ampersand_sequences,
    }


# Why: ensure developers can trust the CLI snapshot when mirroring integration expectations.
def test_masked_pane_cli_matches_staging_map(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = masked_pane_cli.main([])
    assert exit_code == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    context = bootstrap_device_context(
        assignments=(), ampersand_overrides=BUILTIN_AMPERSAND_OVERRIDES
    )
    console = context.get_service("console")
    assert isinstance(console, ConsoleService)

    expected = _build_expected_payload(console)
    assert payload == expected
