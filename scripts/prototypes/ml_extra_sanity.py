"""Sanity checks for the recovered ``ml.extra`` overlay data."""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from scripts.prototypes import ml_extra_defaults  # type: ignore
else:  # pragma: no cover - exercised during package imports
    from . import ml_extra_defaults


@dataclass
class StubMacroEntry:
    """Concrete macro payload recovered from ``ml_extra_stub.asm``."""

    slot: int
    address: int
    payload: Sequence[int]

    def decoded_text(self) -> str:
        """Return the PETSCII rendering of :attr:`payload`."""

        return ml_extra_defaults.ml_extra_extract.decode_petscii(self.payload)

    def byte_preview(self, limit: int = 8) -> str:
        """Return a short hex preview of the payload."""

        prefix = (f"${value:02x}" for value in self.payload[:limit])
        preview = ", ".join(prefix)
        if len(self.payload) > limit:
            preview += ", …"
        return preview


@dataclass
class MacroComparison:
    """Diff result between recovered and stub macro tables."""

    slot: int
    address: int
    recovered_length: int
    stub_length: int | None
    matches: bool
    recovered_preview: str
    stub_preview: str | None


@dataclass
class StubStaticData:
    """Structured view of fixed data copied into ``ml_extra_stub.asm``."""

    lightbar: Tuple[int, ...]
    underline: Tuple[int, ...]
    palette: Tuple[int, ...]
    flag_directory_block: Tuple[int, ...]
    flag_directory_tail: Tuple[int, ...]

    @property
    def flag_tail_text(self) -> str:
        return ml_extra_defaults.ml_extra_extract.decode_petscii(self.flag_directory_tail)


def _payload_hash(payload: Sequence[int]) -> str:
    """Return a stable checksum for the provided payload."""

    return hashlib.sha256(bytes(payload)).hexdigest()


def _parse_numeric_value(token: str) -> int:
    chunk = token.strip()
    if not chunk:
        raise ValueError("empty numeric token")
    if chunk.startswith("$"):
        return int(chunk[1:], 16)
    if chunk.lower().startswith("0x"):
        return int(chunk[2:], 16)
    if chunk.startswith("%"):
        return int(chunk[1:], 2)
    return int(chunk, 10)


def _parse_numeric_tokens(spec: str) -> List[int]:
    """Return integer values extracted from a ``.byte``/``.word`` line."""

    values: list[int] = []
    for token in spec.split(","):
        chunk = token.strip()
        if not chunk:
            continue
        values.append(_parse_numeric_value(chunk))
    return values


def _parse_stub_numeric_tokens(spec: str, symbols: Dict[str, int]) -> List[int]:
    values: list[int] = []
    for token in spec.split(","):
        chunk = token.strip()
        if not chunk:
            continue
        if chunk in symbols:
            values.append(symbols[chunk])
        else:
            values.append(_parse_numeric_value(chunk))
    return values


def _parse_label_tokens(spec: str) -> List[str]:
    """Return label names extracted from a ``.word`` directive."""

    labels: list[str] = []
    for token in spec.split(","):
        name = token.strip()
        if name:
            labels.append(name)
    return labels


def parse_stub_macro_directory(stub_path: Path) -> List[StubMacroEntry]:
    """Return concrete macro payloads recovered from the stub module."""

    slot_ids: list[int] = []
    runtime_targets: list[int] = []
    directory_labels: list[str] = []
    payloads: Dict[str, List[int]] = {}

    current_label: str | None = None
    for raw_line in stub_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split(";", 1)[0].rstrip()
        if not line:
            continue
        if line.endswith(":"):
            current_label = line[:-1]
            continue
        if current_label is None:
            continue
        stripped = line.strip()
        if current_label == "macro_slot_ids" and stripped.startswith(".byte"):
            slot_ids.extend(_parse_numeric_tokens(stripped[len(".byte") :]))
        elif current_label == "macro_runtime_targets" and stripped.startswith(".word"):
            runtime_targets.extend(_parse_numeric_tokens(stripped[len(".word") :]))
        elif current_label == "macro_payload_directory" and stripped.startswith(".word"):
            directory_labels.extend(_parse_label_tokens(stripped[len(".word") :]))
        elif current_label.startswith("macro_payload_") and stripped.startswith(".byte"):
            payloads.setdefault(current_label, []).extend(
                _parse_numeric_tokens(stripped[len(".byte") :])
            )

    if not slot_ids or not directory_labels or not runtime_targets:
        raise ValueError("failed to parse macro directory from stub")
    if not (
        len(slot_ids) == len(directory_labels) == len(runtime_targets)
    ):
        raise ValueError("stub macro directory has mismatched counts")

    entries: list[StubMacroEntry] = []
    for slot, label, address in zip(slot_ids, directory_labels, runtime_targets):
        if label not in payloads:
            raise ValueError(f"macro payload {label} missing from stub")
        payload = tuple(payloads[label])
        entries.append(StubMacroEntry(slot=slot, address=address, payload=payload))
    return entries


def parse_stub_static_data(stub_path: Path) -> StubStaticData:
    """Recover fixed data tables stored in ``ml_extra_stub.asm``."""

    targets = {
        "lightbar_default_bitmaps": [],
        "underline_default": [],
        "editor_palette_default": [],
        "flag_directory_block": [],
        "flag_directory_tail_decoded": [],
    }

    current_label: str | None = None
    symbols: Dict[str, int] = {}
    for raw_line in stub_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split(";", 1)[0].rstrip()
        if not line:
            continue
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith(".") and ":" not in stripped:
            name, value = (part.strip() for part in stripped.split("=", 1))
            if name and value:
                try:
                    symbols[name] = _parse_numeric_value(value)
                except ValueError:
                    pass
        if line.endswith(":"):
            current_label = line[:-1]
            continue
        if current_label not in targets:
            continue
        if stripped.startswith(".byte"):
            targets[current_label].extend(
                _parse_stub_numeric_tokens(stripped[len(".byte") :], symbols)
            )

    missing = [label for label, values in targets.items() if not values]
    if missing:
        raise ValueError(
            "failed to recover stub tables: " + ", ".join(sorted(missing))
        )

    return StubStaticData(
        lightbar=tuple(targets["lightbar_default_bitmaps"]),
        underline=tuple(targets["underline_default"]),
        palette=tuple(targets["editor_palette_default"]),
        flag_directory_block=tuple(targets["flag_directory_block"]),
        flag_directory_tail=tuple(targets["flag_directory_tail_decoded"]),
    )


def summarise_macros(
    defaults: ml_extra_defaults.MLExtraDefaults,
    stub_macros: Sequence[StubMacroEntry],
) -> tuple[List[MacroComparison], List[StubMacroEntry]]:
    """Return comparison rows and stub-only entries for reporting."""

    stub_map: Dict[int, StubMacroEntry] = {entry.slot: entry for entry in stub_macros}
    seen_slots: set[int] = set()
    comparisons: list[MacroComparison] = []

    for entry in defaults.macros:
        stub_entry = stub_map.get(entry.slot)
        if stub_entry is None:
            comparisons.append(
                MacroComparison(
                    slot=entry.slot,
                    address=entry.address,
                    recovered_length=len(entry.payload),
                    stub_length=None,
                    matches=False,
                    recovered_preview=entry.byte_preview(),
                    stub_preview=None,
                )
            )
            continue

        recovered_payload = tuple(entry.payload)
        stub_payload = tuple(stub_entry.payload)
        matches = recovered_payload == stub_payload and entry.address == stub_entry.address
        comparisons.append(
            MacroComparison(
                slot=entry.slot,
                address=entry.address,
                recovered_length=len(recovered_payload),
                stub_length=len(stub_payload),
                matches=matches,
                recovered_preview=entry.byte_preview(),
                stub_preview=stub_entry.byte_preview(),
            )
        )
        seen_slots.add(entry.slot)

    stub_only = [entry for entry in stub_macros if entry.slot not in seen_slots]
    return comparisons, stub_only


def _hex_bytes(values: Sequence[int]) -> List[str]:
    return [f"${value:02x}" for value in values]


def _preview_bytes(values: Sequence[int], limit: int = 8) -> str:
    prefix = ", ".join(_hex_bytes(values)[:limit])
    if len(values) > limit:
        prefix += ", …"
    return prefix


def _sequence_report(
    expected: Sequence[int], actual: Sequence[int]
) -> Dict[str, object]:
    expected_tuple = tuple(expected)
    actual_tuple = tuple(actual)
    return {
        "matches": expected_tuple == actual_tuple,
        "expected": {
            "bytes": _hex_bytes(expected_tuple),
            "length": len(expected_tuple),
            "preview": _preview_bytes(expected_tuple),
        },
        "actual": {
            "bytes": _hex_bytes(actual_tuple),
            "length": len(actual_tuple),
            "preview": _preview_bytes(actual_tuple),
        },
    }


def _tail_report(
    expected: Sequence[int], actual: Sequence[int]
) -> Dict[str, object]:
    report = _sequence_report(expected, actual)
    report["expected"]["text"] = ml_extra_defaults.ml_extra_extract.decode_petscii(
        expected
    )
    report["actual"]["text"] = ml_extra_defaults.ml_extra_extract.decode_petscii(
        actual
    )
    return report


def run_checks(overlay_path: Path | None = None) -> dict[str, object]:
    """Compute diff metadata for regression review."""

    defaults = ml_extra_defaults.MLExtraDefaults.from_overlay(overlay_path)
    stub_path = ml_extra_defaults._REPO_ROOT / "v1.2/source/ml_extra_stub.asm"
    stub_macros = parse_stub_macro_directory(stub_path)
    stub_static = parse_stub_static_data(stub_path)

    comparisons, stub_only = summarise_macros(defaults, stub_macros)
    overlay_hashes = {
        entry.slot: _payload_hash(entry.payload) for entry in defaults.macros
    }
    stub_hashes = {entry.slot: _payload_hash(entry.payload) for entry in stub_macros}
    terminators = [entry.payload[-1] if entry.payload else None for entry in defaults.macros]
    lightbar_expected = defaults.lightbar.bitmaps
    underline_expected = (
        defaults.lightbar.underline_char,
        defaults.lightbar.underline_color,
    )
    stub_static_report = {
        "lightbar": _sequence_report(lightbar_expected, stub_static.lightbar),
        "underline": _sequence_report(underline_expected, stub_static.underline),
        "palette": _sequence_report(defaults.palette.colours, stub_static.palette),
        "flag_directory_block": _sequence_report(
            defaults.flag_directory_block, stub_static.flag_directory_block
        ),
        "flag_directory_tail": _tail_report(
            defaults.flag_directory_tail, stub_static.flag_directory_tail
        ),
    }
    return {
        "overlay_load_address": f"${defaults.load_address:04x}",
        "lightbar": defaults.lightbar.as_dict(),
        "palette": defaults.palette.as_dict(),
        "hardware_defaults": defaults.hardware.as_dict(),
        "flag_records": [record.as_dict() for record in defaults.flag_records],
        "flag_dispatch": defaults.flag_dispatch.as_dict(),
        "flag_directory_tail": {
            "bytes": [f"${value:02x}" for value in defaults.flag_directory_tail],
            "text": defaults.flag_directory_text,
        },
        "stub_static": stub_static_report,
        "overlay_macro_count": len(defaults.macros),
        "stub_macro_count": len(stub_macros),
        "payload_hashes": [
            {"slot": slot, "sha256": overlay_hashes[slot]} for slot in sorted(overlay_hashes)
        ],
        "macro_directory": [
            {
                "slot": entry.slot,
                "address": f"${entry.address:04x}",
                "length": len(entry.payload),
                "byte_preview": entry.byte_preview(),
                "text": entry.decoded_text,
                "sha256": overlay_hashes[entry.slot],
            }
            for entry in defaults.macros
        ],
        "comparisons": [
            {
                "slot": row.slot,
                "address": f"${row.address:04x}",
                "recovered_length": row.recovered_length,
                "stub_length": row.stub_length,
                "matches": row.matches,
                "recovered_preview": row.recovered_preview,
                "stub_preview": row.stub_preview,
                "recovered_sha256": overlay_hashes[row.slot],
                "stub_sha256": stub_hashes.get(row.slot),
            }
            for row in comparisons
        ],
        "stub_only_macros": [
            {
                "slot": entry.slot,
                "address": f"${entry.address:04x}",
                "length": len(entry.payload),
                "byte_preview": entry.byte_preview(),
                "sha256": stub_hashes[entry.slot],
            }
            for entry in stub_only
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
        "  sid volume : " + report["hardware_defaults"]["sid_volume"],
        f"  flag records: {len(report['flag_records'])}",
        f"  macro slots : {report['overlay_macro_count']}",
        f"  stub macros : {report['stub_macro_count']}",
    ]

    hardware: dict[str, object] = report["hardware_defaults"]  # type: ignore[assignment]
    lines.append("")
    lines.append("Hardware defaults:")
    pointer = hardware["pointer"]  # type: ignore[assignment]
    initial = pointer["initial"]  # type: ignore[assignment]
    lines.append(
        "  pointer initial: "
        f"low={initial['low']} high={initial['high']}"  # type: ignore[index]
    )
    lines.append(
        f"  pointer scan limit: {pointer['scan_limit']}"  # type: ignore[index]
    )
    lines.append(
        f"  pointer reset: {pointer['reset_value']}"  # type: ignore[index]
    )
    lines.append("  VIC writes:")
    for entry in hardware["vic_registers"]:  # type: ignore[assignment]
        lines.append(f"    {entry['address']}:")  # type: ignore[index]
        for write in entry["writes"]:  # type: ignore[index]
            value = write.get("value")
            if value is None:
                lines.append(f"      store @ {write['store']} (dynamic)")  # type: ignore[index]
            else:
                lines.append(
                    f"      store @ {write['store']} value={value}"  # type: ignore[index]
                )

    flag_records: Iterable[dict[str, object]] = report["flag_records"]  # type: ignore[assignment]
    lines.append("")
    lines.append("Flag table:")
    for entry in flag_records:
        kind = "long" if entry["long_form"] else "short"
        masks = f"mask=({entry['mask_c0db']},{entry['mask_c0dc']})"
        match = entry["match_text"]
        lines.append(
            f"  {kind:<5} header={entry['header']} {masks} match='{match}' pointer={entry['pointer']}"
        )
        if entry.get("page1_text"):
            lines.append(f"    page1='{entry['page1_text']}'")
        if entry.get("page2_text"):
            lines.append(f"    page2='{entry['page2_text']}'")
        if entry.get("replacement_text"):
            lines.append(f"    replacement='{entry['replacement_text']}'")

    dispatch: dict[str, object] = report["flag_dispatch"]  # type: ignore[assignment]
    lines.append("")
    lines.append("Flag dispatch directory:")
    lines.append(
        f"  leading marker : {dispatch['leading_marker']}"  # type: ignore[index]
    )
    lines.append(
        f"  trailing marker: {dispatch['trailing_marker']}"  # type: ignore[index]
    )
    entries: Iterable[dict[str, object]] = dispatch["entries"]  # type: ignore[assignment]
    for entry in entries:
        lines.append(
            f"  flag {entry['flag_index']} -> slot {entry['slot']} handler={entry['handler']}"
        )

    tail: dict[str, object] = report["flag_directory_tail"]  # type: ignore[assignment]
    lines.append("")
    lines.append("Flag directory tail:")
    lines.append(f"  bytes: {', '.join(tail['bytes'])}")
    lines.append(f"  text : {tail['text']}")

    stub_static: Dict[str, Dict[str, object]] = report["stub_static"]  # type: ignore[assignment]
    lines.append("")
    lines.append("Stub static-data verification:")
    for key, label in [
        ("lightbar", "lightbar defaults"),
        ("underline", "underline defaults"),
        ("palette", "editor palette"),
        ("flag_directory_block", "flag directory block"),
    ]:
        entry: Dict[str, object] = stub_static[key]  # type: ignore[index]
        status = "match" if entry["matches"] else "DIFF"  # type: ignore[index]
        expected = entry["expected"]["preview"]  # type: ignore[index]
        actual = entry["actual"]["preview"]  # type: ignore[index]
        lengths = (
            f"exp={entry['expected']['length']}"  # type: ignore[index]
            f" act={entry['actual']['length']}"  # type: ignore[index]
        )
        lines.append(
            f"  {label:<22}: {status} | expected={expected} | actual={actual} | {lengths}"
        )

    tail_check: Dict[str, object] = stub_static["flag_directory_tail"]  # type: ignore[index]
    tail_status = "match" if tail_check["matches"] else "DIFF"  # type: ignore[index]
    expected_text = tail_check["expected"]["text"]  # type: ignore[index]
    actual_text = tail_check["actual"]["text"]  # type: ignore[index]
    tail_expected_preview = tail_check["expected"]["preview"]  # type: ignore[index]
    tail_actual_preview = tail_check["actual"]["preview"]  # type: ignore[index]
    lines.append(
        f"  flag directory tail   : {tail_status} | expected={tail_expected_preview}"
        f" | actual={tail_actual_preview}"
    )
    if actual_text != expected_text:
        lines.append(f"    expected text='{expected_text}'")
        lines.append(f"    actual text  ='{actual_text}'")
    else:
        lines.append(f"    text='{actual_text}'")

    directory: Iterable[dict[str, object]] = report["macro_directory"]  # type: ignore[assignment]
    comparisons: Iterable[dict[str, object]] = report["comparisons"]  # type: ignore[assignment]
    lines.append("")
    lines.append("Macro directory (runtime order):")
    for entry in directory:
        text = entry["text"] or "<no text>"
        if len(text) > 48:
            text = text[:45] + "..."
        lines.append(
            f"  slot {entry['slot']:>2} @ {entry['address']}:"
            f" {entry['length']:>3} bytes | bytes={entry['byte_preview']} | text='{text}'"
        )

    hashes: Iterable[dict[str, object]] = report["payload_hashes"]  # type: ignore[assignment]
    lines.append("")
    lines.append("Macro payload hashes:")
    for entry in hashes:
        lines.append(f"  slot {entry['slot']:>2}: {entry['sha256']}")

    lines.append("")
    lines.append("Slot diff (recovered vs. stub data):")
    for row in comparisons:
        status = "match" if row["matches"] else "DIFF"
        recovered_preview = row["recovered_preview"]
        if len(recovered_preview) > 48:
            recovered_preview = recovered_preview[:45] + "..."
        stub_preview = row["stub_preview"] or "<missing>"
        if len(stub_preview) > 48:
            stub_preview = stub_preview[:45] + "..."
        stub_length = row["stub_length"]
        stub_length_text = f"{stub_length:>3}" if stub_length is not None else "  –"
        lines.append(
            f"  slot {row['slot']:>2} @ {row['address']}:"
            f" rec={row['recovered_length']:>3}b stub={stub_length_text}b"
            f" | status={status}"
            f" | recovered={recovered_preview}"
            f" | recovered_sha256={row['recovered_sha256']}"
            f" | stub={stub_preview}"
            + (
                ""
                if row["stub_sha256"] is None
                else f" | stub_sha256={row['stub_sha256']}"
            )
        )

    stub_only: Iterable[dict[str, object]] = report["stub_only_macros"]  # type: ignore[assignment]
    if stub_only:
        lines.append("")
        lines.append("Warning: stub exports macros not present in the recovered overlay:")
        for row in stub_only:
            lines.append(
                f"  slot {row['slot']:>2} @ {row['address']}:"
                f" {row['length']:>3} bytes | bytes={row['byte_preview']} | sha256={row['sha256']}"
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
