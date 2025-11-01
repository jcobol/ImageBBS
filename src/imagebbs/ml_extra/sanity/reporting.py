"""Presentation utilities for ``ml.extra`` sanity checks."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ... import ml_extra_defaults, ml_extra_reporting
from .core import (
    MetadataDiff,
    SanityReport,
    SequenceDiff,
    metadata_diff_report_lines,
)


# Why: Render byte values using the conventional ``$`` prefix used across reports.
def _hex_bytes(values: Sequence[int]) -> list[str]:
    return [f"${value:02x}" for value in values]


# Why: Summarise long byte sequences when rendering human-readable reports.
def _preview_bytes(values: Sequence[int], limit: int = 8) -> str:
    prefix = ", ".join(_hex_bytes(values)[:limit])
    if len(values) > limit:
        prefix += ", …"
    return prefix


# Why: Produce lines describing metadata drift so CLI entry points can print summaries consistently.
def format_metadata_diff(diff: MetadataDiff) -> list[str]:
    return metadata_diff_report_lines(diff)


# Why: Format a stub static-data diff row mirroring the legacy text report.
def _format_stub_static(label: str, diff: SequenceDiff) -> str:
    status = "match" if diff.matches else "DIFF"
    expected = _preview_bytes(diff.expected.values)
    actual = _preview_bytes(diff.actual.values)
    lengths = f"exp={len(diff.expected.values)} act={len(diff.actual.values)}"
    return f"  {label:<22}: {status} | expected={expected} | actual={actual} | {lengths}"


# Why: Render the flag directory tail comparison including decoded PETSCII text.
def _format_tail_diff(diff: SequenceDiff) -> list[str]:
    lines = [
        "  flag directory tail   : {status} | expected={expected} | actual={actual}".format(
            status="match" if diff.matches else "DIFF",
            expected=_preview_bytes(diff.expected.values),
            actual=_preview_bytes(diff.actual.values),
        )
    ]
    expected_text = diff.expected.text or ""
    actual_text = diff.actual.text or ""
    if expected_text == actual_text:
        lines.append(f"    text='{actual_text}'")
    else:
        lines.append(f"    expected text='{expected_text}'")
        lines.append(f"    actual text  ='{actual_text}'")
    return lines


# Why: Assemble the human-readable sanity report using the structured dataclasses from ``core``.
def format_report(report: SanityReport, baseline_diff: MetadataDiff | None = None) -> str:
    lines: list[str] = []
    if report.metadata_snapshot:
        lines.extend(ml_extra_reporting.format_overlay_metadata(report.metadata_snapshot))
        lines.append("")

    if baseline_diff is not None:
        diff_lines = format_metadata_diff(baseline_diff)
        if diff_lines:
            lines.append("Baseline comparison:")
            lines.extend(f"  {entry}" for entry in diff_lines)
            lines.append("")

    lines.extend(
        [
            "Recovered overlay summary:",
            f"  load address: ${report.overlay_load_address:04x}",
            "  lightbar   : "
            + ", ".join(
                f"{name}={value}"
                for name, value in report.lightbar.as_dict().items()
            ),
            "  palette    : " + ", ".join(report.palette.as_dict()["colours"]),
            "  sid volume : " + report.hardware_defaults.as_dict()["sid_volume"],
            f"  flag records: {len(report.flag_records)}",
            f"  macro slots : {report.overlay_macro_count}",
            f"  stub macros : {report.stub_macro_count}",
        ]
    )

    hardware = report.hardware_defaults.as_dict()
    lines.append("")
    lines.append("Hardware defaults:")
    pointer = hardware["pointer"]
    initial = pointer["initial"]
    lines.append(
        "  pointer initial: " f"low={initial['low']} high={initial['high']}"
    )
    lines.append(f"  pointer scan limit: {pointer['scan_limit']}")
    lines.append(f"  pointer reset: {pointer['reset_value']}")
    lines.append("  VIC writes:")
    for entry in hardware["vic_registers"]:
        lines.append(f"    {entry['address']}:")
        for write in entry["writes"]:
            value = write.get("value")
            if value is None:
                lines.append(f"      store @ {write['store']} (dynamic)")
            else:
                lines.append(
                    f"      store @ {write['store']} value={value}"
                )

    lines.append("")
    lines.append("Flag table:")
    for entry in report.flag_records:
        data = entry.as_dict()
        kind = "long" if data["long_form"] else "short"
        masks = f"mask=({data['mask_c0db']},{data['mask_c0dc']})"
        match = data["match_text"]
        lines.append(
            f"  {kind:<5} header={data['header']} {masks} match='{match}' pointer={data['pointer']}"
        )
        if data.get("page1_text"):
            lines.append(f"    page1='{data['page1_text']}'")
        if data.get("page2_text"):
            lines.append(f"    page2='{data['page2_text']}'")
        if data.get("replacement_text"):
            lines.append(f"    replacement='{data['replacement_text']}'")

    dispatch = report.flag_dispatch.as_dict()
    lines.append("")
    lines.append("Flag dispatch directory:")
    lines.append(f"  leading marker : {dispatch['leading_marker']}")
    lines.append(f"  trailing marker: {dispatch['trailing_marker']}")
    for entry in dispatch["entries"]:
        lines.append(
            f"  flag {entry['flag_index']} -> slot {entry['slot']} handler={entry['handler']}"
        )

    tail_bytes = [f"${value:02x}" for value in report.flag_directory_tail]
    tail_text = ml_extra_defaults.ml_extra_extract.decode_petscii(
        report.flag_directory_tail
    )
    lines.append("")
    lines.append("Flag directory tail:")
    lines.append(f"  bytes: {', '.join(tail_bytes)}")
    lines.append(f"  text : {tail_text}")

    lines.append("")
    lines.append("Stub static-data verification:")
    static_labels = [
        ("lightbar", "lightbar defaults"),
        ("underline", "underline defaults"),
        ("palette", "editor palette"),
        ("flag_directory_block", "flag directory block"),
    ]
    for attr, label in static_labels:
        diff = getattr(report.stub_static, attr)
        lines.append(_format_stub_static(label, diff))

    lines.extend(_format_tail_diff(report.stub_static.flag_directory_tail))

    lines.append("")
    lines.append("Macro directory (runtime order):")
    for entry in report.macro_directory:
        text = entry.text or "<no text>"
        if len(text) > 48:
            text = text[:45] + "..."
        lines.append(
            f"  slot {entry.slot:>2} @ ${entry.address:04x}:"
            f" {entry.length:>3} bytes | bytes={entry.byte_preview} | text='{text}'"
        )

    lines.append("")
    lines.append("Macro payload hashes:")
    for entry in report.payload_hashes:
        lines.append(f"  slot {entry.slot:>2}: {entry.sha256}")

    lines.append("")
    lines.append("Slot diff (recovered vs. stub data):")
    for row in report.comparisons:
        status = "match" if row.matches else "DIFF"
        recovered_preview = row.recovered_preview
        if len(recovered_preview) > 48:
            recovered_preview = recovered_preview[:45] + "..."
        stub_preview = row.stub_preview or "<missing>"
        if len(stub_preview) > 48:
            stub_preview = stub_preview[:45] + "..."
        stub_length = row.stub_length
        stub_length_text = f"{stub_length:>3}" if stub_length is not None else "  –"
        stub_hash = (
            ""
            if row.stub_sha256 is None
            else f" | stub_sha256={row.stub_sha256}"
        )
        lines.append(
            f"  slot {row.slot:>2} @ ${row.address:04x}:"
            f" rec={row.recovered_length:>3}b stub={stub_length_text}b"
            f" | status={status}"
            f" | recovered={recovered_preview}"
            f" | recovered_sha256={row.recovered_sha256}"
            f" | stub={stub_preview}"
            + stub_hash
        )

    if report.stub_only_macros:
        lines.append("")
        lines.append("Warning: stub exports macros not present in the recovered overlay:")
        for row in report.stub_only_macros:
            lines.append(
                f"  slot {row.slot:>2} @ ${row.address:04x}:"
                f" {row.length:>3} bytes | bytes={row.byte_preview} | sha256={row.sha256}"
            )

    if report.non_terminated_macros:
        lines.append("")
        lines.append("Warning: non-null-terminated macro payloads detected:")
        for row in report.non_terminated_macros:
            lines.append(f"  slot {row.slot} @ ${row.address:04x}")

    return "\n".join(lines)


# Why: Provide a convenience wrapper for snapshot guard messaging without reimplementing formatting logic.
def render_diff_summary(baseline: Path, diff: MetadataDiff) -> str:
    lines: list[str] = []
    if diff.matches:
        lines.append(f"Baseline snapshot matches {baseline}")
        return "\n".join(lines)

    lines.append(f"Drift detected relative to {baseline}:")
    diff_lines = format_metadata_diff(diff)
    lines.extend(f"  {entry}" for entry in diff_lines)
    return "\n".join(lines)


__all__ = ["format_metadata_diff", "format_report", "render_diff_summary"]
