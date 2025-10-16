"""Dump `ml.extra` macro payloads as PETSCII byte strings."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from . import ml_extra_defaults
from . import ml_extra_extract


@dataclass(frozen=True)
class MacroDump:
    """Recovered macro directory entry with PETSCII rendering."""

    slot: int
    address: int
    payload: Sequence[int]

    @property
    def text(self) -> str:
        """Return the PETSCII decode for :attr:`payload`."""

        return ml_extra_extract.decode_petscii(self.payload)

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation of the dump."""

        return {
            "slot": self.slot,
            "address": f"${self.address:04x}",
            "bytes": [f"${byte:02x}" for byte in self.payload],
            "text": self.text,
        }


def iter_macro_dumps(
    defaults: ml_extra_defaults.MLExtraDefaults,
    *,
    slots: Sequence[int] | None = None,
) -> Iterable[MacroDump]:
    """Yield :class:`MacroDump` rows for the requested slots."""

    allowed = set(slots) if slots else None
    for entry in defaults.macros:
        if allowed is not None and entry.slot not in allowed:
            continue
        yield MacroDump(slot=entry.slot, address=entry.address, payload=entry.payload)


def parse_slots(raw: Sequence[str] | None) -> List[int]:
    """Normalise ``--slot`` arguments into integers."""

    if not raw:
        return []
    slots: List[int] = []
    for value in raw:
        text = value.lower()
        if text.startswith("$"):
            cleaned = value[1:]
            slots.append(int(cleaned, base=16))
            continue
        if text.startswith("0x"):
            slots.append(int(value, base=16))
            continue
        slots.append(int(value, base=10))
    return slots


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "overlay",
        type=Path,
        nargs="?",
        help="Override the default ml.extra binary path",
    )
    parser.add_argument(
        "--slot",
        action="append",
        help="Limit output to the specified macro slot (decimal or $hex)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report",
    )
    return parser.parse_args(argv)


def format_report(rows: Iterable[MacroDump]) -> str:
    lines: List[str] = []
    for row in rows:
        text = row.text.replace("\n", "\\n") or "<no text>"
        byte_repr = " ".join(f"${byte:02x}" for byte in row.payload)
        lines.append(
            f"slot {row.slot:02x} @ ${row.address:04x}: {len(row.payload):3d} bytes | {byte_repr} | {text}"
        )
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)
    defaults = ml_extra_defaults.MLExtraDefaults.from_overlay(args.overlay)
    slots = parse_slots(args.slot)
    rows = list(iter_macro_dumps(defaults, slots=slots))
    if args.json:
        import json

        payload = [row.as_dict() for row in rows]
        print(json.dumps(payload, indent=2))
    else:
        print(format_report(rows))


if __name__ == "__main__":  # pragma: no cover
    main()
