"""Core data collection for ``ml.extra`` sanity checks."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Sequence

from ... import ml_extra_defaults, ml_extra_reporting, ml_extra_stub_parser


@dataclass(frozen=True)
class SequenceSnapshot:
    """Represents a captured byte sequence and optional PETSCII text."""

    values: tuple[int, ...]
    text: str | None = None

    # Why: Provide a stable shape for JSON serialisation without leaking formatting helpers into callers.
    def to_dict(self) -> dict[str, object]:
        return {
            "bytes": [f"${value:02x}" for value in self.values],
            "length": len(self.values),
            "preview": _preview_bytes(self.values),
            **({"text": self.text} if self.text is not None else {}),
        }


@dataclass(frozen=True)
class SequenceDiff:
    """Comparison result between two byte sequences."""

    matches: bool
    expected: SequenceSnapshot
    actual: SequenceSnapshot

    # Why: Preserve the previous JSON structure so automation can diff against historical payloads without changes.
    def to_dict(self) -> dict[str, object]:
        return {
            "matches": self.matches,
            "expected": self.expected.to_dict(),
            "actual": self.actual.to_dict(),
        }


@dataclass(frozen=True)
class StubStaticDiff:
    """Aggregated verification results for stubbed static tables."""

    lightbar: SequenceDiff
    underline: SequenceDiff
    palette: SequenceDiff
    flag_directory_block: SequenceDiff
    flag_directory_tail: SequenceDiff

    # Why: Emit a serialisable representation consumed by JSON exports and downstream tooling.
    def to_dict(self) -> dict[str, object]:
        return {
            "lightbar": self.lightbar.to_dict(),
            "underline": self.underline.to_dict(),
            "palette": self.palette.to_dict(),
            "flag_directory_block": self.flag_directory_block.to_dict(),
            "flag_directory_tail": self.flag_directory_tail.to_dict(),
        }


@dataclass(frozen=True)
class MacroHashEntry:
    """SHA-256 digest for a recovered macro payload."""

    slot: int
    sha256: str

    # Why: Preserve the JSON payload structure exposed by ``--json`` outputs.
    def to_dict(self) -> dict[str, object]:
        return {"slot": self.slot, "sha256": self.sha256}


@dataclass(frozen=True)
class MacroDirectoryRow:
    """Structured snapshot of a recovered macro entry."""

    slot: int
    address: int
    length: int
    byte_preview: str
    text: str
    sha256: str

    # Why: Maintain compatibility with historical report serialisation while providing typed accessors.
    def to_dict(self) -> dict[str, object]:
        return {
            "slot": self.slot,
            "address": f"${self.address:04x}",
            "length": self.length,
            "byte_preview": self.byte_preview,
            "text": self.text,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class MacroComparison:
    """Diff result between recovered and stub macro tables."""

    slot: int
    address: int
    recovered_length: int
    stub_length: int | None
    matches: bool
    recovered_preview: str
    stub_preview: str | None
    recovered_sha256: str
    stub_sha256: str | None

    # Why: Allow callers to serialise comparison rows for JSON export without duplicating formatting logic.
    def to_dict(self) -> dict[str, object]:
        return {
            "slot": self.slot,
            "address": f"${self.address:04x}",
            "recovered_length": self.recovered_length,
            "stub_length": self.stub_length,
            "matches": self.matches,
            "recovered_preview": self.recovered_preview,
            "stub_preview": self.stub_preview,
            "recovered_sha256": self.recovered_sha256,
            "stub_sha256": self.stub_sha256,
        }


@dataclass(frozen=True)
class StubMacroSummary:
    """Macro exported by the stub that is absent from the recovered overlay."""

    slot: int
    address: int
    length: int
    byte_preview: str
    sha256: str

    # Why: Support JSON and text serialisation while keeping type information close to the data.
    def to_dict(self) -> dict[str, object]:
        return {
            "slot": self.slot,
            "address": f"${self.address:04x}",
            "length": self.length,
            "byte_preview": self.byte_preview,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class NonTerminatedMacro:
    """Macro slot whose payload is not null-terminated."""

    slot: int
    address: int

    # Why: Provide a consistent JSON representation for CLI output.
    def to_dict(self) -> dict[str, object]:
        return {"slot": self.slot, "address": f"${self.address:04x}"}


@dataclass(frozen=True)
class MetadataValue:
    """Represents an added or removed metadata value."""

    path: str
    value: object

    # Why: Allow downstream callers to reuse the legacy dictionary structure for compatibility.
    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "value": self.value}


@dataclass(frozen=True)
class MetadataChange:
    """Represents a changed value between baseline and recovered metadata."""

    path: str
    baseline: object
    current: object

    # Why: Preserve the JSON layout historically consumed by automation.
    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "baseline": self.baseline,
            "current": self.current,
        }


@dataclass(frozen=True)
class MetadataDiff:
    """Structured diff between overlay metadata snapshots."""

    matches: bool
    added: tuple[MetadataValue, ...]
    removed: tuple[MetadataValue, ...]
    changed: tuple[MetadataChange, ...]
    baseline_snapshot: dict[str, object]
    current_snapshot: dict[str, object]

    # Why: Produce a serialisable payload used by CLI consumers and integration tests.
    def to_dict(self) -> dict[str, object]:
        return {
            "matches": self.matches,
            "added": [entry.to_dict() for entry in self.added],
            "removed": [entry.to_dict() for entry in self.removed],
            "changed": [entry.to_dict() for entry in self.changed],
            "baseline_lines": ml_extra_reporting.format_overlay_metadata(
                self.baseline_snapshot
            ),
            "current_lines": ml_extra_reporting.format_overlay_metadata(
                self.current_snapshot
            ),
            "report_lines": metadata_diff_report_lines(self),
        }


@dataclass(frozen=True)
class SanityReport:
    """Aggregated output from ``run_checks``."""

    metadata_snapshot: dict[str, object]
    overlay_load_address: int
    lightbar: ml_extra_defaults.LightbarDefaults
    palette: ml_extra_defaults.EditorPalette
    hardware_defaults: ml_extra_defaults.HardwareDefaults
    flag_records: tuple[ml_extra_defaults.FlagRecord, ...]
    flag_dispatch: ml_extra_defaults.FlagDispatchTable
    flag_directory_tail: tuple[int, ...]
    flag_directory_block: tuple[int, ...]
    stub_static: StubStaticDiff
    overlay_macro_count: int
    stub_macro_count: int
    payload_hashes: tuple[MacroHashEntry, ...]
    macro_directory: tuple[MacroDirectoryRow, ...]
    comparisons: tuple[MacroComparison, ...]
    stub_only_macros: tuple[StubMacroSummary, ...]
    non_terminated_macros: tuple[NonTerminatedMacro, ...]

    # Why: Provide a backwards-compatible JSON structure used by existing callers and fixtures.
    def to_dict(self) -> dict[str, object]:
        return {
            "metadata_snapshot": self.metadata_snapshot,
            "overlay_load_address": f"${self.overlay_load_address:04x}",
            "lightbar": self.lightbar.as_dict(),
            "palette": self.palette.as_dict(),
            "hardware_defaults": self.hardware_defaults.as_dict(),
            "flag_records": [record.as_dict() for record in self.flag_records],
            "flag_dispatch": self.flag_dispatch.as_dict(),
            "flag_directory_tail": {
                "bytes": [f"${value:02x}" for value in self.flag_directory_tail],
                "text": ml_extra_defaults.ml_extra_extract.decode_petscii(
                    self.flag_directory_tail
                ),
            },
            "stub_static": self.stub_static.to_dict(),
            "overlay_macro_count": self.overlay_macro_count,
            "stub_macro_count": self.stub_macro_count,
            "payload_hashes": [entry.to_dict() for entry in self.payload_hashes],
            "macro_directory": [row.to_dict() for row in self.macro_directory],
            "comparisons": [row.to_dict() for row in self.comparisons],
            "stub_only_macros": [row.to_dict() for row in self.stub_only_macros],
            "non_terminated_macros": [row.to_dict() for row in self.non_terminated_macros],
        }


# Why: Produce deterministic SHA-256 digests for comparing stub and overlay payloads.
def _payload_hash(payload: Sequence[int]) -> str:
    return hashlib.sha256(bytes(payload)).hexdigest()


# Why: Capture a tuple of integers to simplify downstream comparisons.
def _normalise_sequence(values: Sequence[int]) -> tuple[int, ...]:
    return tuple(values)


# Why: Render a short preview of a byte sequence for JSON and text reports.
def _preview_bytes(values: Sequence[int], limit: int = 8) -> str:
    prefix = ", ".join(f"${value:02x}" for value in values[:limit])
    if len(values) > limit:
        return prefix + ", …"
    return prefix


# Why: Build the static-data diff payloads shared between JSON output and text reporting.
def _sequence_diff(
    expected: Sequence[int], actual: Sequence[int], *, include_text: bool = False
) -> SequenceDiff:
    expected_tuple = _normalise_sequence(expected)
    actual_tuple = _normalise_sequence(actual)
    expected_snapshot = SequenceSnapshot(
        values=expected_tuple,
        text=(
            ml_extra_defaults.ml_extra_extract.decode_petscii(expected_tuple)
            if include_text
            else None
        ),
    )
    actual_snapshot = SequenceSnapshot(
        values=actual_tuple,
        text=(
            ml_extra_defaults.ml_extra_extract.decode_petscii(actual_tuple)
            if include_text
            else None
        ),
    )
    return SequenceDiff(
        matches=expected_tuple == actual_tuple,
        expected=expected_snapshot,
        actual=actual_snapshot,
    )


# Why: Summarise overlay and stub macro payloads so downstream reporting can focus on presentation.
def summarise_macros(
    defaults: ml_extra_defaults.MLExtraDefaults,
    stub_macros: Sequence[ml_extra_stub_parser.StubMacroEntry],
) -> tuple[tuple[MacroComparison, ...], tuple[StubMacroSummary, ...]]:
    stub_map: Dict[int, ml_extra_stub_parser.StubMacroEntry] = {
        entry.slot: entry for entry in stub_macros
    }
    seen_slots: set[int] = set()
    comparisons: list[MacroComparison] = []

    overlay_hashes = {entry.slot: _payload_hash(entry.payload) for entry in defaults.macros}
    stub_hashes = {entry.slot: _payload_hash(entry.payload) for entry in stub_macros}

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
                    recovered_sha256=overlay_hashes[entry.slot],
                    stub_sha256=None,
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
                recovered_sha256=overlay_hashes[entry.slot],
                stub_sha256=stub_hashes[entry.slot],
            )
        )
        seen_slots.add(entry.slot)

    stub_only = tuple(
        StubMacroSummary(
            slot=entry.slot,
            address=entry.address,
            length=len(entry.payload),
            byte_preview=entry.byte_preview(),
            sha256=stub_hashes[entry.slot],
        )
        for entry in stub_macros
        if entry.slot not in seen_slots
    )

    return tuple(comparisons), stub_only


# Why: Collect overlay metadata, stub comparisons, and payload hashes for downstream reporting.
def run_checks(overlay_path: Path | None = None) -> SanityReport:
    defaults = ml_extra_defaults.MLExtraDefaults.from_overlay(overlay_path)
    stub_path = ml_extra_defaults._REPO_ROOT / "v1.2/source/ml_extra_stub.asm"
    stub_source = ml_extra_stub_parser.load_stub_source(stub_path)
    stub_macros = ml_extra_stub_parser.parse_stub_macro_directory(stub_source)
    stub_static = ml_extra_stub_parser.parse_stub_static_data(stub_source)
    metadata_snapshot = ml_extra_reporting.collect_overlay_metadata(defaults)

    comparisons, stub_only = summarise_macros(defaults, stub_macros)
    overlay_hashes = {entry.slot: _payload_hash(entry.payload) for entry in defaults.macros}

    stub_static_report = StubStaticDiff(
        lightbar=_sequence_diff(defaults.lightbar.bitmaps, stub_static.lightbar),
        underline=_sequence_diff(
            (defaults.lightbar.underline_char, defaults.lightbar.underline_color),
            stub_static.underline,
        ),
        palette=_sequence_diff(defaults.palette.colours, stub_static.palette),
        flag_directory_block=_sequence_diff(
            defaults.flag_directory_block, stub_static.flag_directory_block
        ),
        flag_directory_tail=_sequence_diff(
            defaults.flag_directory_tail,
            stub_static.flag_directory_tail,
            include_text=True,
        ),
    )

    payload_hashes = tuple(
        MacroHashEntry(slot=slot, sha256=overlay_hashes[slot])
        for slot in sorted(overlay_hashes)
    )
    macro_directory = tuple(
        MacroDirectoryRow(
            slot=entry.slot,
            address=entry.address,
            length=len(entry.payload),
            byte_preview=entry.byte_preview(),
            text=entry.decoded_text,
            sha256=overlay_hashes[entry.slot],
        )
        for entry in defaults.macros
    )
    non_terminated = tuple(
        NonTerminatedMacro(slot=entry.slot, address=entry.address)
        for entry in defaults.macros
        if entry.payload and entry.payload[-1] != 0x00
    )

    return SanityReport(
        metadata_snapshot=metadata_snapshot,
        overlay_load_address=defaults.load_address,
        lightbar=defaults.lightbar,
        palette=defaults.palette,
        hardware_defaults=defaults.hardware,
        flag_records=defaults.flag_records,
        flag_dispatch=defaults.flag_dispatch,
        flag_directory_tail=defaults.flag_directory_tail,
        flag_directory_block=defaults.flag_directory_block,
        stub_static=stub_static_report,
        overlay_macro_count=len(defaults.macros),
        stub_macro_count=len(stub_macros),
        payload_hashes=payload_hashes,
        macro_directory=macro_directory,
        comparisons=comparisons,
        stub_only_macros=stub_only,
        non_terminated_macros=non_terminated,
    )


# Why: Walk nested metadata payloads to identify added, removed, and changed entries.
def diff_metadata_snapshots(
    baseline: dict[str, object], current: dict[str, object]
) -> MetadataDiff:
    added: list[MetadataValue] = []
    removed: list[MetadataValue] = []
    changed: list[MetadataChange] = []

    def format_path(segments: list[str]) -> str:
        path = ""
        for segment in segments:
            if segment.startswith("["):
                path += segment
            elif path:
                path += f".{segment}"
            else:
                path = segment
        return path or "<root>"

    def walk(baseline_value: object, current_value: object, segments: list[str]) -> None:
        if isinstance(baseline_value, dict) and isinstance(current_value, dict):
            baseline_keys = set(baseline_value)
            current_keys = set(current_value)
            for key in sorted(baseline_keys - current_keys):
                segments.append(key)
                removed.append(
                    MetadataValue(path=format_path(segments), value=baseline_value[key])
                )
                segments.pop()
            for key in sorted(current_keys - baseline_keys):
                segments.append(key)
                added.append(
                    MetadataValue(path=format_path(segments), value=current_value[key])
                )
                segments.pop()
            for key in sorted(baseline_keys & current_keys):
                segments.append(key)
                walk(baseline_value[key], current_value[key], segments)
                segments.pop()
            return

        if isinstance(baseline_value, list) and isinstance(current_value, list):
            common_length = min(len(baseline_value), len(current_value))
            for index in range(common_length):
                segments.append(f"[{index}]")
                walk(baseline_value[index], current_value[index], segments)
                segments.pop()
            for index in range(common_length, len(baseline_value)):
                segments.append(f"[{index}]")
                removed.append(
                    MetadataValue(path=format_path(segments), value=baseline_value[index])
                )
                segments.pop()
            for index in range(common_length, len(current_value)):
                segments.append(f"[{index}]")
                added.append(
                    MetadataValue(path=format_path(segments), value=current_value[index])
                )
                segments.pop()
            return

        if baseline_value != current_value:
            changed.append(
                MetadataChange(
                    path=format_path(segments),
                    baseline=baseline_value,
                    current=current_value,
                )
            )

    walk(baseline, current, [])
    matches = not (added or removed or changed)

    return MetadataDiff(
        matches=matches,
        added=tuple(added),
        removed=tuple(removed),
        changed=tuple(changed),
        baseline_snapshot=baseline,
        current_snapshot=current,
    )


# Why: Provide textual diff summaries for legacy JSON outputs and CLI reporting.
def metadata_diff_report_lines(diff: MetadataDiff) -> list[str]:
    lines: list[str] = []
    if diff.matches:
        lines.append("Baseline metadata snapshot matches recovered overlay.")
        return lines

    lines.append("Differences detected between baseline and recovered overlay:")
    for entry in diff.changed:
        lines.append(
            "  changed {path}: baseline={baseline} current={current}".format(
                path=entry.path,
                baseline=entry.baseline,
                current=entry.current,
            )
        )
    for entry in diff.added:
        lines.append(f"  added {entry.path}: {entry.value}")
    for entry in diff.removed:
        lines.append(f"  removed {entry.path}: {entry.value}")
    return lines


__all__ = [
    "SequenceSnapshot",
    "SequenceDiff",
    "StubStaticDiff",
    "MacroHashEntry",
    "MacroDirectoryRow",
    "MacroComparison",
    "StubMacroSummary",
    "NonTerminatedMacro",
    "MetadataValue",
    "MetadataChange",
    "MetadataDiff",
    "SanityReport",
    "run_checks",
    "diff_metadata_snapshots",
    "summarise_macros",
    "metadata_diff_report_lines",
]
