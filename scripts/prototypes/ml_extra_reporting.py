"""Shared helpers for presenting recovered ``ml.extra`` metadata."""

from __future__ import annotations

from typing import Dict, Iterable, List

from . import ml_extra_defaults


def collect_overlay_metadata(
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> Dict[str, object]:
    """Return a JSON-friendly snapshot of high-level overlay tables."""

    return {
        "load_address": f"${defaults.load_address:04x}",
        "lightbar": defaults.lightbar.as_dict(),
        "palette": defaults.palette.as_dict(),
        "hardware": defaults.hardware.as_dict(),
        "flag_dispatch": defaults.flag_dispatch.as_dict(),
        "flag_directory_tail": {
            "bytes": [f"${value:02x}" for value in defaults.flag_directory_tail],
            "text": defaults.flag_directory_text,
        },
        "flag_record_count": len(defaults.flag_records),
        "macro_slots": [entry.slot for entry in defaults.macros],
    }


def format_overlay_metadata(metadata: Dict[str, object]) -> List[str]:
    """Return human-readable lines for ``collect_overlay_metadata`` output."""

    lines = [
        "Overlay metadata:",
        f"  load address: {metadata['load_address']}",
    ]

    lightbar: Dict[str, str] = metadata["lightbar"]  # type: ignore[assignment]
    lines.append(
        "  lightbar   : "
        + ", ".join(f"{key}={value}" for key, value in lightbar.items())
    )

    palette: Dict[str, Iterable[str]] = metadata["palette"]  # type: ignore[assignment]
    colours = list(palette.get("colours", ()))
    lines.append("  palette    : " + ", ".join(colours))

    hardware: Dict[str, object] = metadata["hardware"]  # type: ignore[assignment]
    pointer = hardware.get("pointer", {})  # type: ignore[assignment]
    if pointer:
        initial = pointer.get("initial", {})  # type: ignore[assignment]
        lines.append(
            "  pointer    : "
            + f"low={initial.get('low', '?')} high={initial.get('high', '?')}"
            + f" scan_limit={pointer.get('scan_limit', '?')}"
            + f" reset={pointer.get('reset_value', '?')}"
        )

    sid_volume = hardware.get("sid_volume")  # type: ignore[assignment]
    if sid_volume:
        lines.append(f"  sid volume : {sid_volume}")

    vic_registers: Iterable[Dict[str, object]] = hardware.get(
        "vic_registers", []
    )  # type: ignore[assignment]
    if vic_registers:
        lines.append("  VIC writes:")
        for entry in vic_registers:
            address = entry.get("address", "?")  # type: ignore[assignment]
            lines.append(f"    {address}:")
            for write in entry.get("writes", ()):  # type: ignore[assignment]
                store = write.get("store", "?")  # type: ignore[assignment]
                value = write.get("value")  # type: ignore[assignment]
                if value is None:
                    lines.append(f"      store @ {store} (dynamic)")
                else:
                    lines.append(f"      store @ {store} value={value}")

    dispatch: Dict[str, object] | None = metadata.get("flag_dispatch")  # type: ignore[assignment]
    if dispatch:
        entries: List[Dict[str, object]] = list(  # type: ignore[assignment]
            dispatch.get("entries", [])
        )
        entry_count = len(entries)
        lines.append(
            "  flag dispatch: "
            + f"lead={dispatch.get('leading_marker', '?')}"
            + f" trail={dispatch.get('trailing_marker', '?')}"
            + f" entries={entry_count}"
        )

    record_count = metadata.get("flag_record_count")
    if record_count is not None:
        lines.append(f"  flag records: {record_count}")

    tail: Dict[str, object] | None = metadata.get("flag_directory_tail")  # type: ignore[assignment]
    if tail:
        bytes_preview = list(tail.get("bytes", []))  # type: ignore[assignment]
        preview = ", ".join(bytes_preview[:4])
        if preview:
            suffix = " …" if len(bytes_preview) > 4 else ""
            preview = f" ({preview}{suffix})"
        lines.append(
            "  flag tail  : "
            + tail.get("text", "")  # type: ignore[assignment]
            + preview
        )

    slots_raw: Iterable[int] | None = metadata.get("macro_slots")  # type: ignore[assignment]
    if slots_raw:
        slots = list(slots_raw)
        hex_slots = [f"${slot:02x}" for slot in slots]
        lines.append("  macro slots: " + ", ".join(hex_slots))

    return lines
