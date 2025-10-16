"""Sanity checks for the recovered ``ml.extra`` overlay data."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from scripts.prototypes import ml_extra_defaults  # type: ignore
else:  # pragma: no cover - exercised during package imports
    from . import ml_extra_defaults


@dataclass
class MacroComparison:
    """Diff result between stubbed and recovered macro tables."""

    slot: int
    address: int
    payload_length: int
    decoded_preview: str
    stub_fallback: str | None


def parse_stub_macro_directory(stub_path: Path) -> List[str]:
    """Return the placeholder macro names from ``ml_extra_stub.asm``."""

    macros: list[str] = []
    in_table = False
    for raw_line in stub_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split(";", 1)[0].strip()
        if not line:
            if in_table:
                break
            continue
        if line.startswith("macro_directory_stub:"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith(".byte"):
            break
        payload = line[len(".byte") :].strip()
        if payload == "4":
            # Count prefix, skip it.
            continue
        if not payload:
            continue
        if payload.startswith('"') and '"' in payload[1:]:
            text = payload.split('"', 2)[1]
            macros.append(text)
    return macros


def summarise_macros(defaults: ml_extra_defaults.MLExtraDefaults, stub_macros: List[str]) -> Iterable[MacroComparison]:
    """Yield :class:`MacroComparison` rows for the recovered macro slots."""

    fallbacks = iter(stub_macros)
    for entry in defaults.macros:
        try:
            stub = next(fallbacks)
        except StopIteration:
            stub = None
        yield MacroComparison(
            slot=entry.slot,
            address=entry.address,
            payload_length=len(entry.payload),
            decoded_preview=entry.decoded_text,
            stub_fallback=stub,
        )


def run_checks(overlay_path: Path | None = None) -> dict[str, object]:
    """Compute diff metadata for regression review."""

    defaults = ml_extra_defaults.MLExtraDefaults.from_overlay(overlay_path)
    stub_path = ml_extra_defaults._REPO_ROOT / "v1.2/source/ml_extra_stub.asm"
    stub_macros = parse_stub_macro_directory(stub_path)

    comparisons = list(summarise_macros(defaults, stub_macros))
    terminators = [entry.payload[-1] if entry.payload else None for entry in defaults.macros]
    return {
        "overlay_load_address": f"${defaults.load_address:04x}",
        "lightbar": defaults.lightbar.as_dict(),
        "palette": defaults.palette.as_dict(),
        "overlay_macro_count": len(defaults.macros),
        "stub_macro_count": len(stub_macros),
        "comparisons": [
            {
                "slot": row.slot,
                "address": f"${row.address:04x}",
                "payload_length": row.payload_length,
                "decoded_preview": row.decoded_preview,
                "stub_fallback": row.stub_fallback,
            }
            for row in comparisons
        ],
        "non_terminated_macros": [
            {
                "slot": entry.slot,
                "address": f"${entry.address:04x}",
            }
            for entry, terminator in zip(defaults.macros, terminators)
            if terminator != 0x00
        ],
    }


def format_report(report: dict[str, object]) -> str:
    lines = [
        "Recovered overlay summary:",
        f"  load address: {report['overlay_load_address']}",
        "  lightbar   : "
        + ", ".join(
            f"{name}={value}"
            for name, value in report["lightbar"].items()
        ),
        "  palette    : " + ", ".join(report["palette"]["colours"]),
        f"  macro slots : {report['overlay_macro_count']}",
        f"  stub macros : {report['stub_macro_count']}",
    ]

    comparisons: Iterable[dict[str, object]] = report["comparisons"]  # type: ignore[assignment]
    lines.append("")
    lines.append("Slot diff (recovered vs. stub placeholders):")
    for row in comparisons:
        stub = row["stub_fallback"] or "<none>"
        preview = row["decoded_preview"]
        if len(preview) > 48:
            preview = preview[:45] + "..."
        lines.append(
            f"  slot {row['slot']:>2} @ {row['address']}:"
            f" {row['payload_length']:>3} bytes | recovered='{preview}' | stub='{stub}'"
        )

    non_terminated: Iterable[dict[str, str]] = report["non_terminated_macros"]  # type: ignore[assignment]
    if non_terminated:
        lines.append("")
        lines.append("Warning: non-null-terminated macro payloads detected:")
        for row in non_terminated:
            lines.append(f"  slot {row['slot']} @ {row['address']}")

    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "overlay",
        type=Path,
        nargs="?",
        help="Override the default overlay binary path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text summary",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    report = run_checks(args.overlay)
    if args.json:
        import json

        print(json.dumps(report, indent=2))
    else:
        print(format_report(report))


if __name__ == "__main__":  # pragma: no cover
    main()
