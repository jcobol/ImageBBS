"""Capture reference screen dumps for ``ml.extra`` macros and flag payloads."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from . import ml_extra_defaults
from .device_context import Console


def _format_bytes(values: Sequence[int]) -> List[str]:
    return [f"${value:02x}" for value in values]


def _capture_snapshot(
    payload: Iterable[int],
    *,
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> Dict[str, object]:
    """Render ``payload`` through :class:`Console` and return a snapshot."""

    console = Console(defaults=defaults)
    rendered = bytes(payload)
    if rendered:
        console.write(rendered)

    snapshot = console.snapshot()
    snapshot["transcript_bytes"] = _format_bytes(console.transcript_bytes)
    snapshot["transcript_text"] = console.transcript
    snapshot["palette"] = _format_bytes(console.screen.palette)
    return snapshot


def _collect_macro_screens(
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for entry in defaults.macros:
        snapshot = _capture_snapshot(entry.payload, defaults=defaults)
        rows.append(
            {
                "slot": entry.slot,
                "address": f"${entry.address:04x}",
                "byte_count": len(entry.payload),
                "bytes": _format_bytes(entry.payload),
                "text": entry.decoded_text,
                "snapshot": snapshot,
            }
        )
    return rows


def _collect_flag_payloads(
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> Dict[str, object]:
    records: List[Dict[str, object]] = []
    for index, record in enumerate(defaults.flag_records):
        data: Dict[str, object] = {
            "index": index,
            "header": f"${record.header:02x}",
            "mask_c0db": f"${record.mask_c0db:02x}",
            "mask_c0dc": f"${record.mask_c0dc:02x}",
            "long_form": record.long_form,
            "match_bytes": _format_bytes(record.match_sequence),
            "match_text": record.match_text,
            "pointer": f"${record.pointer:02x}",
        }
        if record.replacement is not None:
            data["replacement_bytes"] = _format_bytes(record.replacement)
            data["replacement_text"] = record.replacement_text
            data["replacement_snapshot"] = _capture_snapshot(
                record.replacement, defaults=defaults
            )
        if record.page1_payload is not None:
            data["page1_bytes"] = _format_bytes(record.page1_payload)
            data["page1_text"] = record.page1_text
            data["page1_snapshot"] = _capture_snapshot(
                record.page1_payload, defaults=defaults
            )
        if record.page2_payload is not None:
            data["page2_bytes"] = _format_bytes(record.page2_payload)
            data["page2_text"] = record.page2_text
            data["page2_snapshot"] = _capture_snapshot(
                record.page2_payload, defaults=defaults
            )
        records.append(data)

    tail_payload = defaults.flag_directory_tail
    tail = {
        "bytes": _format_bytes(tail_payload),
        "text": defaults.flag_directory_text,
        "snapshot": _capture_snapshot(tail_payload, defaults=defaults),
    }
    block_payload = defaults.flag_directory_block
    block = {
        "bytes": _format_bytes(block_payload),
        "snapshot": _capture_snapshot(block_payload, defaults=defaults),
    }
    return {
        "records": records,
        "directory_tail": tail,
        "directory_block": block,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "overlay",
        nargs="?",
        type=Path,
        help="Optional path to an ml.extra overlay to analyse",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/porting/artifacts"),
        help="Directory where the JSON dumps will be stored",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    defaults = ml_extra_defaults.MLExtraDefaults.from_overlay(args.overlay)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    macro_payload = _collect_macro_screens(defaults)
    flag_payload = _collect_flag_payloads(defaults)

    macro_path = output_dir / "ml-extra-macro-screens.json"
    flag_path = output_dir / "ml-extra-flag-screens.json"

    json_kwargs = {"separators": (",", ":")}

    if macro_payload:
        macro_body = ",\n".join(json.dumps(entry, **json_kwargs) for entry in macro_payload)
        macro_text = f"[\n{macro_body}\n]\n"
    else:
        macro_text = "[]\n"

    macro_path.write_text(macro_text, encoding="utf-8")
    flag_path.write_text(json.dumps(flag_payload, **json_kwargs) + "\n", encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
