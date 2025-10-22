"""Console rendering tests for the PETSCII host shim."""
from __future__ import annotations

import base64
import gzip
import io
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import pytest

from imagebbs import ml_extra_defaults, ml_extra_extract, petscii_glyphs
from imagebbs.console_renderer import (
    GlyphCell,
    GlyphRun,
    PetsciiScreen,
    VicRegisterTimelineEntry,
    render_petscii_payload,
)
from imagebbs.device_context import Console
from imagebbs.petscii import decode_petscii_for_cli


from scripts.prototypes.runtime import cli as runtime_cli


@pytest.fixture(scope="module")
def editor_defaults() -> ml_extra_defaults.MLExtraDefaults:
    return ml_extra_defaults.MLExtraDefaults.from_overlay()


def _artifact_root() -> Path:
    return Path(__file__).resolve().parents[1] / "docs/porting/artifacts"


def _load_artifact_json(name: str) -> Any:
    root = _artifact_root()
    candidates = [name, f"{name}.base64", f"{name}.b64"]
    if name.endswith(".gz"):
        gz_name = name
    else:
        gz_name = f"{name}.gz"
        candidates.extend([gz_name, f"{gz_name}.base64", f"{gz_name}.b64"])

    for candidate in candidates:
        path = root / candidate
        if not path.exists():
            continue
        is_base64 = candidate.endswith(".base64") or candidate.endswith(".b64")
        is_gzip = ".gz" in candidate
        if is_base64:
            raw_text = path.read_text(encoding="utf-8")
            payload = base64.b64decode("".join(raw_text.split()))
            if is_gzip:
                with gzip.GzipFile(fileobj=io.BytesIO(payload)) as gz_handle:
                    with io.TextIOWrapper(gz_handle, encoding="utf-8") as text_handle:
                        return json.load(text_handle)
            return json.loads(payload.decode("utf-8"))
        if is_gzip:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                return json.load(handle)
        with path.open("rt", encoding="utf-8") as handle:
            return json.load(handle)

    raise FileNotFoundError(f"Unable to locate artifact for {name!r} in {root}")


def _parse_hex_value(value: Any) -> Any:
    if isinstance(value, str):
        if value.startswith("$"):
            return int(value[1:], 16)
        if value.isdigit():
            return int(value, 10)
    return value


def _parse_hex_sequence(values: Iterable[Any]) -> tuple[int, ...]:
    return tuple(int(str(value)[1:], 16) if isinstance(value, str) and value.startswith("$") else int(value) for value in values)


def _normalise_snapshot_value(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_normalise_snapshot_value(item) for item in value)
    if isinstance(value, dict):
        return {key: _normalise_snapshot_value(item) for key, item in value.items()}
    return _parse_hex_value(value)


def _normalise_snapshot(snapshot: Mapping[str, Any]) -> Dict[str, Any]:
    normalised: Dict[str, Any] = {}
    for key, value in snapshot.items():
        if key == "hardware" and isinstance(value, Mapping):
            vic_registers: Dict[int, int | None] = {}
            raw_registers = value.get("vic_registers")
            if isinstance(raw_registers, Mapping):
                for register, register_value in raw_registers.items():
                    register_key = _parse_hex_value(register)
                    if not isinstance(register_key, int):
                        continue
                    if register_value is None:
                        vic_registers[register_key] = None
                    else:
                        vic_registers[register_key] = _parse_hex_value(register_value)
            hardware_data: Dict[str, Any] = {"vic_registers": vic_registers}
            raw_timeline = value.get("vic_register_timeline")
            if isinstance(raw_timeline, Iterable):
                timeline: list[Dict[str, int | None]] = []
                for entry in raw_timeline:
                    if not isinstance(entry, Mapping):
                        continue
                    store = _parse_hex_value(entry.get("store"))
                    address = _parse_hex_value(entry.get("address"))
                    value_field = _parse_hex_value(entry.get("value"))
                    if not isinstance(store, int) or not isinstance(address, int):
                        continue
                    timeline.append(
                        {
                            "store": store,
                            "address": address,
                            "value": value_field if isinstance(value_field, int) else None,
                        }
                    )
                hardware_data["vic_register_timeline"] = tuple(
                    sorted(timeline, key=lambda entry: entry["store"])
                )
            pointer_data = value.get("pointer")
            if isinstance(pointer_data, Mapping):
                initial = pointer_data.get("initial")
                if isinstance(initial, Mapping):
                    hardware_data["pointer"] = {
                        "initial": {
                            "low": _parse_hex_value(initial.get("low")),
                            "high": _parse_hex_value(initial.get("high")),
                        },
                        "scan_limit": _parse_hex_value(pointer_data.get("scan_limit")),
                        "reset_value": _parse_hex_value(pointer_data.get("reset_value")),
                    }
                else:
                    hardware_data["pointer"] = {
                        "initial": None,
                        "scan_limit": _parse_hex_value(pointer_data.get("scan_limit")),
                        "reset_value": _parse_hex_value(pointer_data.get("reset_value")),
                    }
            sid_volume = value.get("sid_volume")
            hardware_data["sid_volume"] = _parse_hex_value(sid_volume)
            normalised["hardware"] = hardware_data
            continue
        if key == "characters" and isinstance(value, list):
            normalised[key] = tuple(value)
            continue
        normalised[key] = _normalise_snapshot_value(value)
    return normalised


def _load_macro_screen_artifacts() -> list[Dict[str, Any]]:
    data = _load_artifact_json("ml-extra-macro-screens.json")
    records: list[Dict[str, Any]] = []
    for entry in data:
        record: Dict[str, Any] = {
            "slot": entry["slot"],
            "address": _parse_hex_value(entry.get("address")),
            "byte_count": entry.get("byte_count"),
            "payload": bytes(_parse_hex_sequence(entry.get("bytes", []))),
            "text": entry.get("text"),
        }
        snapshot_data = entry.get("snapshot")
        if isinstance(snapshot_data, Mapping):
            record["snapshot"] = _normalise_snapshot(snapshot_data)
        records.append(record)
    return records


def _load_flag_screen_artifacts() -> Dict[str, Any]:
    data = _load_artifact_json("ml-extra-flag-screens.json")
    records: list[Dict[str, Any]] = []
    for entry in data.get("records", []):
        record: Dict[str, Any] = {
            "index": entry.get("index"),
            "header": _parse_hex_value(entry.get("header")),
            "mask_c0db": _parse_hex_value(entry.get("mask_c0db")),
            "mask_c0dc": _parse_hex_value(entry.get("mask_c0dc")),
            "long_form": entry.get("long_form"),
            "match_bytes": bytes(_parse_hex_sequence(entry.get("match_bytes", []))),
            "match_text": entry.get("match_text"),
            "pointer": _parse_hex_value(entry.get("pointer")),
        }
        if "replacement_bytes" in entry:
            record["replacement_bytes"] = bytes(
                _parse_hex_sequence(entry.get("replacement_bytes", []))
            )
            record["replacement_text"] = entry.get("replacement_text")
        if "replacement_snapshot" in entry:
            replacement_snapshot = entry.get("replacement_snapshot")
            if isinstance(replacement_snapshot, Mapping):
                record["replacement_snapshot"] = _normalise_snapshot(
                    replacement_snapshot
                )
        if "page1_bytes" in entry:
            record["page1_bytes"] = bytes(
                _parse_hex_sequence(entry.get("page1_bytes", []))
            )
            record["page1_text"] = entry.get("page1_text")
        if "page1_snapshot" in entry:
            page1_snapshot = entry.get("page1_snapshot")
            if isinstance(page1_snapshot, Mapping):
                record["page1_snapshot"] = _normalise_snapshot(page1_snapshot)
        if "page2_bytes" in entry:
            record["page2_bytes"] = bytes(
                _parse_hex_sequence(entry.get("page2_bytes", []))
            )
            record["page2_text"] = entry.get("page2_text")
        if "page2_snapshot" in entry:
            page2_snapshot = entry.get("page2_snapshot")
            if isinstance(page2_snapshot, Mapping):
                record["page2_snapshot"] = _normalise_snapshot(page2_snapshot)
        snapshot_data = entry.get("snapshot")
        if isinstance(snapshot_data, Mapping):
            record["snapshot"] = _normalise_snapshot(snapshot_data)
        records.append(record)

    def _load_directory(name: str) -> Dict[str, Any]:
        directory_entry = data.get(name, {})
        record: Dict[str, Any] = {
            "bytes": bytes(_parse_hex_sequence(directory_entry.get("bytes", []))),
        }
        if "text" in directory_entry:
            record["text"] = directory_entry["text"]
        snapshot_data = directory_entry.get("snapshot") if isinstance(directory_entry, Mapping) else None
        if isinstance(snapshot_data, Mapping):
            record["snapshot"] = _normalise_snapshot(snapshot_data)
        return record

    return {
        "records": records,
        "directory_tail": _load_directory("directory_tail"),
        "directory_block": _load_directory("directory_block"),
    }


_MACRO_SCREEN_ARTIFACTS = _load_macro_screen_artifacts()
_FLAG_SCREEN_ARTIFACTS = _load_flag_screen_artifacts()

_FLAG_REPLACEMENT_RECORDS = [
    record
    for record in _FLAG_SCREEN_ARTIFACTS["records"]
    if "replacement_bytes" in record and "replacement_snapshot" in record
]

_FLAG_PAGE_PAYLOADS: list[tuple[Dict[str, Any], str]] = [
    (record, field)
    for record in _FLAG_SCREEN_ARTIFACTS["records"]
    for field in ("page1", "page2")
    if f"{field}_bytes" in record and f"{field}_snapshot" in record
]


@pytest.fixture(scope="module")
def macro_screen_captures() -> list[Dict[str, Any]]:
    return _MACRO_SCREEN_ARTIFACTS


@pytest.fixture(scope="module")
def flag_screen_captures() -> Dict[str, Any]:
    return _FLAG_SCREEN_ARTIFACTS


_SNAPSHOT_MATRIX_KEYS = (
    "characters",
    "colour_matrix",
    "glyph_indices",
    "glyphs",
    "reverse_matrix",
    "resolved_colour_matrix",
)


def _assert_snapshot_structure(snapshot: Mapping[str, Any]) -> None:
    characters = snapshot.get("characters")
    if characters is not None:
        assert isinstance(characters, tuple)
        assert all(isinstance(row, str) for row in characters)

    for key in _SNAPSHOT_MATRIX_KEYS[1:]:
        rows = snapshot.get(key)
        if rows is None:
            continue
        assert isinstance(rows, tuple)
        for row in rows:
            assert isinstance(row, tuple)
            if key == "reverse_matrix":
                assert all(isinstance(cell, bool) for cell in row)
            elif key == "glyphs":
                for glyph in row:
                    assert isinstance(glyph, tuple)
                    for glyph_row in glyph:
                        assert isinstance(glyph_row, tuple)
                        assert all(isinstance(pixel, int) for pixel in glyph_row)
            elif key == "resolved_colour_matrix":
                for cell in row:
                    assert isinstance(cell, tuple)
                    assert len(cell) == 2
                    assert all(isinstance(component, int) for component in cell)
            else:
                assert all(isinstance(cell, int) for cell in row)


def _assert_console_snapshot_state(
    console: Console,
    expected_snapshot: Mapping[str, Any],
    *,
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    actual_snapshot = console.snapshot()

    for key in (
        "characters",
        "code_matrix",
        "colour_matrix",
        "glyph_indices",
        "glyphs",
        "reverse_matrix",
        "resolved_colour_matrix",
        "underline_matrix",
        "lightbar_bitmaps",
    ):
        if key in expected_snapshot:
            assert actual_snapshot[key] == expected_snapshot[key]

    assert actual_snapshot["screen_colour"] == expected_snapshot["screen_colour"]
    assert actual_snapshot["background_colour"] == expected_snapshot["background_colour"]
    assert actual_snapshot["border_colour"] == expected_snapshot["border_colour"]

    screen = console.screen
    assert actual_snapshot["palette"] == screen.palette
    expected_palette = tuple(expected_snapshot.get("palette", ()))
    if expected_palette:
        assert expected_palette == editor_defaults.palette.colours
        assert actual_snapshot["palette"] == expected_palette

    expected_resolved_palette = {
        "entries": screen.palette,
        "screen": console.screen_colour,
        "background": console.background_colour,
        "border": console.border_colour,
        "underline": screen.underline_colour,
        "reverse": {
            "foreground": console.background_colour,
            "background": console.screen_colour,
        },
    }
    assert actual_snapshot["resolved_palette"] == expected_resolved_palette
    if "resolved_palette" in expected_snapshot:
        assert expected_snapshot["resolved_palette"] == expected_resolved_palette

    registers, timeline = _resolve_vic_register_state(editor_defaults)
    expected_timeline = tuple(entry.as_dict() for entry in timeline)
    pointer_defaults = editor_defaults.hardware.pointer
    expected_pointer = {
        "initial": {
            "low": pointer_defaults.initial[0],
            "high": pointer_defaults.initial[1],
        },
        "scan_limit": pointer_defaults.scan_limit,
        "reset_value": pointer_defaults.reset_value,
    }

    actual_hardware = actual_snapshot["hardware"]
    assert actual_hardware["vic_registers"] == registers
    assert actual_hardware["vic_register_timeline"] == expected_timeline
    assert actual_hardware["pointer"] == expected_pointer
    assert actual_hardware["sid_volume"] == editor_defaults.hardware.sid_volume

    hardware = expected_snapshot.get("hardware")
    if isinstance(hardware, Mapping):
        if "vic_registers" in hardware:
            assert hardware["vic_registers"] == registers
        if "vic_register_timeline" in hardware:
            assert hardware["vic_register_timeline"] == expected_timeline
        if "pointer" in hardware:
            assert hardware["pointer"] == expected_pointer
        if "sid_volume" in hardware:
            assert hardware["sid_volume"] == editor_defaults.hardware.sid_volume

    glyph_bank = getattr(screen, "_glyph_bank")
    for y, (codes_row, index_row, glyph_row) in enumerate(
        zip(
            expected_snapshot["code_matrix"],
            expected_snapshot["glyph_indices"],
            expected_snapshot["glyphs"],
            strict=True,
        )
    ):
        for x, (code, glyph_index, glyph_bitmap) in enumerate(
            zip(codes_row, index_row, glyph_row, strict=True)
        ):
            lowercase = bool(glyph_bank[y][x])
            expected_index = petscii_glyphs.get_glyph_index(
                code,
                lowercase=lowercase,
            )
            expected_glyph = petscii_glyphs.get_glyph(
                code,
                lowercase=lowercase,
            )
            assert glyph_index == expected_index
            assert glyph_bitmap == expected_glyph


def _assert_payload_snapshot(
    payload: bytes,
    snapshot: Mapping[str, Any],
    *,
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
    expected_text: str | None = None,
) -> None:
    console = Console()
    if payload:
        console.write(payload)

    _assert_console_snapshot_state(console, snapshot, editor_defaults=editor_defaults)

    expected_bytes = snapshot.get("transcript_bytes")
    transcript_bytes = tuple(console.transcript_bytes)
    if expected_bytes is not None:
        assert transcript_bytes == tuple(expected_bytes)
    else:
        assert transcript_bytes == tuple(payload)

    raw_transcript = console.transcript
    expected_raw = decode_petscii_for_cli(payload)
    assert raw_transcript == expected_raw

    transcript_text = snapshot.get("transcript_text")
    if transcript_text is not None:
        encoded_text = transcript_text.encode("latin-1", errors="strict")
        assert decode_petscii_for_cli(encoded_text) == expected_raw

    if expected_text is not None:
        decoded = ml_extra_extract.decode_petscii(console.transcript_bytes)
        assert decoded == expected_text


def _assert_lookup_run_matches_snapshot(
    run: GlyphRun, snapshot: Mapping[str, Any]
) -> None:
    transcript_bytes = snapshot.get("transcript_bytes")
    if transcript_bytes is not None:
        assert tuple(run.payload) == tuple(transcript_bytes)

    glyph_indices = snapshot.get("glyph_indices")
    glyphs = snapshot.get("glyphs")
    reverse_matrix = snapshot.get("reverse_matrix")

    latest_cells: dict[tuple[int, int], GlyphCell] = {}
    for cell in run.glyphs:
        latest_cells[cell.position] = cell

    for (x, y), cell in latest_cells.items():
        if glyph_indices is not None:
            assert glyph_indices[y][x] == cell.glyph_index
        if glyphs is not None:
            assert tuple(glyphs[y][x]) == tuple(cell.glyph)
        if reverse_matrix is not None:
            assert reverse_matrix[y][x] == cell.reverse


@pytest.mark.parametrize(
    "record",
    [
        pytest.param(
            record,
            id=f"slot-{record['slot']}" if "slot" in record else None,
        )
        for record in _MACRO_SCREEN_ARTIFACTS
    ],
)
def test_console_macro_screens_match_artifacts(
    record: Dict[str, Any],
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    snapshot = record.get("snapshot")
    if not isinstance(snapshot, Mapping):
        pytest.skip("macro capture lacks snapshot data")

    console = Console()
    payload = bytes(record["payload"])
    console.write(payload)

    actual_snapshot = console.snapshot()
    for key in (
        "characters",
        "code_matrix",
        "colour_matrix",
        "glyph_indices",
        "glyphs",
        "reverse_matrix",
        "resolved_colour_matrix",
    ):
        assert actual_snapshot[key] == snapshot[key]

    assert console.transcript_bytes == payload
    expected_text = record.get("text") or ""
    assert console.transcript == decode_petscii_for_cli(payload)
    assert (
        ml_extra_extract.decode_petscii(console.transcript_bytes) == expected_text
    )

    palette = editor_defaults.palette.colours
    assert snapshot["palette"] == palette
    assert snapshot["screen_colour"] in palette
    assert snapshot["background_colour"] == palette[2]
    assert snapshot["border_colour"] == palette[3]

    screen = console.screen
    glyph_bank = getattr(screen, "_glyph_bank")
    for y, (codes_row, index_row, glyph_row) in enumerate(
        zip(
            snapshot["code_matrix"],
            snapshot["glyph_indices"],
            snapshot["glyphs"],
            strict=True,
        )
    ):
        for x, (code, glyph_index, glyph_bitmap) in enumerate(
            zip(codes_row, index_row, glyph_row, strict=True)
        ):
            lowercase = bool(glyph_bank[y][x])
            expected_index = petscii_glyphs.get_glyph_index(
                code,
                lowercase=lowercase,
            )
            expected_glyph = petscii_glyphs.get_glyph(
                code,
                lowercase=lowercase,
            )
            assert glyph_index == expected_index
            assert glyph_bitmap == expected_glyph
            if lowercase:
                assert glyph_index == petscii_glyphs.get_glyph_index(
                    code, lowercase=True
                )
                assert glyph_bitmap == petscii_glyphs.get_glyph(
                    code, lowercase=True
                )
            else:
                assert glyph_index == petscii_glyphs.get_glyph_index(
                    code, lowercase=False
                )
                assert glyph_bitmap == petscii_glyphs.get_glyph(
                    code, lowercase=False
                )


def test_console_cli_decoder_tracks_cursor_state() -> None:
    console = Console()
    console.write(b"HELLO")
    console.write(b"\x9D")
    console.write(b"X")

    assert console.transcript == "HELLO\rHELLX"
    assert console.transcript_bytes == b"HELLO\x9dX"


def test_decode_petscii_for_cli_emits_readable_macro_text() -> None:
    console = Console()
    payload = bytes(console.macro_glyphs[0x28].payload)

    decoded = decode_petscii_for_cli(payload)
    assert "FILE TRANSFER MENU" in decoded
    assert "{CBM-" not in decoded
    assert all(ch.isprintable() or ch in "\n\r" for ch in decoded)

    console.write(payload)
    assert "FILE TRANSFER MENU" in console.transcript
    assert "{CBM-" not in console.transcript


def test_macro_screen_artifacts_are_normalised(
    macro_screen_captures: list[Dict[str, Any]],
) -> None:
    assert macro_screen_captures, "expected macro captures from artifact payload"
    for capture in macro_screen_captures:
        payload = capture["payload"]
        assert isinstance(payload, bytes)
        byte_count = capture.get("byte_count")
        if isinstance(byte_count, int):
            assert len(payload) == byte_count
        snapshot = capture.get("snapshot")
        if isinstance(snapshot, Mapping):
            _assert_snapshot_structure(snapshot)


def test_flag_screen_artifacts_are_normalised(
    flag_screen_captures: Dict[str, Any],
) -> None:
    records = flag_screen_captures["records"]
    assert records, "expected flag capture records"
    for record in records:
        assert isinstance(record["match_bytes"], bytes)
        assert isinstance(record.get("header"), int | type(None))
        assert isinstance(record.get("mask_c0db"), int | type(None))
        assert isinstance(record.get("mask_c0dc"), int | type(None))
        assert isinstance(record.get("pointer"), int | type(None))
        for field in ("replacement_bytes", "page1_bytes", "page2_bytes"):
            payload = record.get(field)
            if payload is not None:
                assert isinstance(payload, bytes)
        snapshot = record.get("snapshot")
        if isinstance(snapshot, Mapping):
            _assert_snapshot_structure(snapshot)

    tail = flag_screen_captures["directory_tail"]
    assert isinstance(tail["bytes"], bytes)
    if isinstance(tail.get("snapshot"), Mapping):
        _assert_snapshot_structure(tail["snapshot"])

    block = flag_screen_captures["directory_block"]
    assert isinstance(block["bytes"], bytes)
    if isinstance(block.get("snapshot"), Mapping):
        _assert_snapshot_structure(block["snapshot"])


@pytest.mark.parametrize(
    "record",
    [
        pytest.param(
            record,
            id=f"flag-{record['index']}",
        )
        for record in _FLAG_REPLACEMENT_RECORDS
    ],
)
def test_console_flag_replacement_snapshots_match_artifacts(
    record: Dict[str, Any],
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    snapshot = record.get("replacement_snapshot")
    if not isinstance(snapshot, Mapping):
        pytest.skip("flag replacement capture lacks snapshot data")

    payload = record["replacement_bytes"]
    expected_text = record.get("replacement_text")
    _assert_payload_snapshot(
        payload,
        snapshot,
        editor_defaults=editor_defaults,
        expected_text=expected_text,
    )


@pytest.mark.parametrize(
    ("record", "page_field"),
    [
        pytest.param(
            record,
            field,
            id=f"flag-{record['index']}-{field}",
        )
        for record, field in _FLAG_PAGE_PAYLOADS
    ],
)
def test_console_flag_page_snapshots_match_artifacts(
    record: Dict[str, Any],
    page_field: str,
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    key_bytes = f"{page_field}_bytes"
    key_snapshot = f"{page_field}_snapshot"
    snapshot = record.get(key_snapshot)
    if not isinstance(snapshot, Mapping):
        pytest.skip(f"flag {page_field} capture lacks snapshot data")

    payload = record[key_bytes]
    expected_text = record.get(f"{page_field}_text")
    _assert_payload_snapshot(
        payload,
        snapshot,
        editor_defaults=editor_defaults,
        expected_text=expected_text,
    )


def test_console_flag_directory_tail_snapshot_matches_artifact(
    flag_screen_captures: Dict[str, Any],
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    tail = flag_screen_captures["directory_tail"]
    snapshot = tail.get("snapshot")
    if not isinstance(snapshot, Mapping):
        pytest.skip("flag directory tail lacks snapshot data")

    payload = tail["bytes"]
    expected_text = tail.get("text")
    _assert_payload_snapshot(
        payload,
        snapshot,
        editor_defaults=editor_defaults,
        expected_text=expected_text,
    )


def test_console_flag_directory_block_snapshot_matches_artifact(
    flag_screen_captures: Dict[str, Any],
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    block = flag_screen_captures["directory_block"]
    snapshot = block.get("snapshot")
    if not isinstance(snapshot, Mapping):
        pytest.skip("flag directory block lacks snapshot data")

    payload = block["bytes"]
    _assert_payload_snapshot(
        payload,
        snapshot,
        editor_defaults=editor_defaults,
    )


def test_overlay_macro_lookup_aligns_with_macro_artifacts(
    macro_screen_captures: list[Dict[str, Any]]
) -> None:
    console = Console()
    lookup = console.overlay_glyph_lookup

    assert len(lookup.macros) == len(macro_screen_captures)
    assert len(lookup.macros_by_slot) == len(macro_screen_captures)

    for record in macro_screen_captures:
        snapshot = record.get("snapshot")
        if not isinstance(snapshot, Mapping):
            continue
        slot = record["slot"]
        run = lookup.macros_by_slot[slot]
        assert run in lookup.macros
        _assert_lookup_run_matches_snapshot(run, snapshot)
        assert tuple(run.payload) == tuple(snapshot["transcript_bytes"])
        assert tuple(run.payload) == tuple(record["payload"])
        expected_text = record.get("text") or ""
        assert run.text == expected_text


def test_overlay_flag_lookup_aligns_with_flag_artifacts(
    flag_screen_captures: Dict[str, Any]
) -> None:
    console = Console()
    lookup = console.overlay_glyph_lookup

    records = flag_screen_captures["records"]
    assert len(lookup.flag_records) == len(records)

    for mapping, record in zip(lookup.flag_records, records):
        assert tuple(mapping.record.match_sequence) == tuple(record["match_bytes"])
        expected_match_text = record.get("match_text") or ""
        assert mapping.record.match_text == expected_match_text

        replacement_bytes = record.get("replacement_bytes")
        if mapping.replacement is None:
            assert replacement_bytes in (None, b"")
        else:
            assert isinstance(replacement_bytes, bytes)
            assert bytes(mapping.replacement.payload) == replacement_bytes
            snapshot = record.get("replacement_snapshot")
            if isinstance(snapshot, Mapping):
                _assert_lookup_run_matches_snapshot(mapping.replacement, snapshot)
                assert tuple(mapping.replacement.payload) == tuple(
                    snapshot["transcript_bytes"]
                )
            expected_text = record.get("replacement_text") or ""
            assert mapping.replacement.text == expected_text

        for page_field in ("page1", "page2"):
            run = getattr(mapping, page_field)
            payload_key = f"{page_field}_bytes"
            snapshot_key = f"{page_field}_snapshot"
            payload_bytes = record.get(payload_key)
            snapshot = record.get(snapshot_key)
            if run is None:
                assert payload_bytes in (None, b"")
                continue
            assert isinstance(payload_bytes, bytes)
            assert bytes(run.payload) == payload_bytes
            if isinstance(snapshot, Mapping):
                _assert_lookup_run_matches_snapshot(run, snapshot)
                assert tuple(run.payload) == tuple(snapshot["transcript_bytes"])
            expected_text = record.get(f"{page_field}_text") or ""
            assert run.text == expected_text


def test_overlay_flag_directory_lookup_aligns_with_artifacts(
    flag_screen_captures: Dict[str, Any]
) -> None:
    console = Console()
    lookup = console.overlay_glyph_lookup

    tail = flag_screen_captures["directory_tail"]
    tail_snapshot = tail.get("snapshot")
    assert tuple(lookup.flag_directory_tail.payload) == tuple(tail["bytes"])
    expected_tail_text = tail.get("text") or ""
    assert lookup.flag_directory_tail.text == expected_tail_text
    if isinstance(tail_snapshot, Mapping):
        _assert_lookup_run_matches_snapshot(lookup.flag_directory_tail, tail_snapshot)
        assert tuple(lookup.flag_directory_tail.payload) == tuple(
            tail_snapshot["transcript_bytes"]
        )

    block = flag_screen_captures["directory_block"]
    block_snapshot = block.get("snapshot")
    assert tuple(lookup.flag_directory_block.payload) == tuple(block["bytes"])
    if isinstance(block_snapshot, Mapping):
        _assert_lookup_run_matches_snapshot(lookup.flag_directory_block, block_snapshot)
        assert tuple(lookup.flag_directory_block.payload) == tuple(
            block_snapshot["transcript_bytes"]
        )


def _resolve_vic_register_state(
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> tuple[dict[int, int | None], tuple[VicRegisterTimelineEntry, ...]]:
    registers: dict[int, int | None] = {}
    timeline: list[VicRegisterTimelineEntry] = []
    for entry in defaults.hardware.vic_registers:
        last_value: int | None = None
        for store, value in entry.writes:
            timeline.append(
                VicRegisterTimelineEntry(store=store, address=entry.address, value=value)
            )
            if value is not None:
                last_value = value
        registers[entry.address] = last_value
    ordered_timeline = tuple(sorted(timeline, key=lambda record: record.store))
    return dict(sorted(registers.items())), ordered_timeline


def test_screen_seeds_overlay_palette(editor_defaults: ml_extra_defaults.MLExtraDefaults) -> None:
    screen = PetsciiScreen()
    assert screen.palette == editor_defaults.palette.colours
    assert screen.screen_colour == editor_defaults.palette.colours[0]
    assert screen.background_colour == editor_defaults.palette.colours[2]
    assert screen.border_colour == editor_defaults.palette.colours[3]


def test_screen_replays_hardware_colour_defaults(
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    screen = PetsciiScreen()
    registers, timeline = _resolve_vic_register_state(editor_defaults)

    assert screen.vic_registers == registers
    assert screen.vic_register_timeline == timeline

    screen_register = registers.get(0xD405)
    if screen_register is not None:
        assert screen.screen_colour == screen_register

    background_register = registers.get(0xD403)
    if background_register is not None:
        assert screen.background_colour == background_register

    border_register = registers.get(0xD404)
    if border_register is not None:
        assert screen.border_colour == border_register


def test_console_renders_startup_banner(editor_defaults: ml_extra_defaults.MLExtraDefaults) -> None:
    console = Console()
    banner_sequence = bytes([0x93])  # {clear}
    banner_sequence += bytes([0x11] * 11)  # move cursor down
    banner_sequence += bytes([0x1D] * 15)  # move cursor right
    banner_sequence += bytes([0x05, 0x0E])  # set white, lowercase
    banner_sequence += bytes([0xC9, 0x6D, 0x61, 0x67, 0x65, 0x20, 0x31, 0x2E, 0x32])

    console.write(banner_sequence)

    screen = console.screen
    snapshot = console.snapshot()
    rows = snapshot["characters"]
    assert rows == screen.characters
    assert len(rows) == screen.height

    expected_row = rows[11]
    assert expected_row[15:24] == "Image 1.2"
    assert expected_row[:15] == " " * 15

    colours = snapshot["colour_matrix"][11]
    assert colours == screen.colour_matrix[11]
    for index in range(15, 24):
        assert colours[index] == console.screen_colour

    codes = snapshot["code_matrix"][11]
    assert codes == screen.code_matrix[11]
    expected_codes = (0xC9, 0x6D, 0x61, 0x67, 0x65, 0x20, 0x31, 0x2E, 0x32)
    assert tuple(codes[15:24]) == expected_codes

    glyph_indices = snapshot["glyph_indices"][11]
    assert glyph_indices == screen.glyph_index_matrix[11]
    expected_indices = tuple(
        petscii_glyphs.get_glyph_index(code, lowercase=True)
        for code in expected_codes
    )
    assert tuple(glyph_indices[15:24]) == expected_indices

    glyphs = snapshot["glyphs"][11]
    assert glyphs == screen.glyph_matrix[11]
    expected_glyphs = tuple(
        petscii_glyphs.get_glyph(code, lowercase=True)
        for code in expected_codes
    )
    assert tuple(glyphs[15:24]) == expected_glyphs

    reverse_flags = snapshot["reverse_matrix"][11]
    assert reverse_flags == screen.reverse_matrix[11]
    assert all(flag is False for flag in reverse_flags)

    resolved_colours = snapshot["resolved_colour_matrix"][11]
    assert resolved_colours == screen.resolved_colour_matrix[11]
    for index in range(15, 24):
        foreground, background = resolved_colours[index]
        assert foreground == colours[index]
        assert background == console.background_colour

    assert console.screen_colour == console.screen.palette[1]
    assert snapshot["screen_colour"] == console.screen_colour
    assert console.background_colour == editor_defaults.palette.colours[2]
    assert snapshot["background_colour"] == console.background_colour
    assert console.border_colour == editor_defaults.palette.colours[3]
    assert snapshot["border_colour"] == console.border_colour
    assert snapshot["palette"] == screen.palette
    resolved_palette = snapshot["resolved_palette"]
    assert resolved_palette["entries"] == screen.palette
    assert resolved_palette["screen"] == console.screen_colour
    assert resolved_palette["background"] == console.background_colour
    assert resolved_palette["border"] == console.border_colour
    assert resolved_palette["underline"] == screen.underline_colour
    assert resolved_palette["reverse"] == {
        "foreground": console.background_colour,
        "background": console.screen_colour,
    }
    hardware = snapshot["hardware"]
    registers, timeline = _resolve_vic_register_state(editor_defaults)
    expected_timeline = tuple(entry.as_dict() for entry in timeline)
    pointer_defaults = editor_defaults.hardware.pointer
    expected_pointer = {
        "initial": {
            "low": pointer_defaults.initial[0],
            "high": pointer_defaults.initial[1],
        },
        "scan_limit": pointer_defaults.scan_limit,
        "reset_value": pointer_defaults.reset_value,
    }
    assert hardware["vic_registers"] == registers
    assert hardware["vic_register_timeline"] == expected_timeline
    assert hardware["pointer"] == expected_pointer
    assert hardware["sid_volume"] == editor_defaults.hardware.sid_volume

    assert console.transcript_bytes == banner_sequence
    assert console.transcript == decode_petscii_for_cli(banner_sequence)


def _load_overlay_metadata() -> dict[str, object]:
    path = (
        Path(__file__).resolve().parents[1]
        / "docs/porting/artifacts/ml-extra-overlay-metadata.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_console_exposes_overlay_defaults(
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    console = Console()

    assert console.defaults == editor_defaults
    assert console.lightbar_defaults == editor_defaults.lightbar
    assert console.flag_dispatch == editor_defaults.flag_dispatch
    assert console.macros == editor_defaults.macros


def test_screen_lightbar_defaults_match_metadata(
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    screen = PetsciiScreen(defaults=editor_defaults)
    metadata = _load_overlay_metadata()
    lightbar_metadata = metadata["lightbar"]  # type: ignore[index]
    expected_bitmaps = tuple(
        int(lightbar_metadata[key][1:], 16)
        for key in (
            "page1_left",
            "page1_right",
            "page2_left",
            "page2_right",
        )
    )
    assert screen.lightbar_bitmaps == expected_bitmaps
    assert screen.underline_char == int(lightbar_metadata["underline_char"][1:], 16)
    expected_colour = int(lightbar_metadata["underline_color"][1:], 16)
    palette = screen.palette
    if expected_colour in palette:
        expected_mapped = expected_colour
    elif 0 <= expected_colour < len(palette):
        expected_mapped = palette[expected_colour]
    else:
        expected_mapped = palette[0]
    assert screen.underline_colour == expected_mapped


def test_lightbar_underline_colour_applied() -> None:
    screen = PetsciiScreen()
    screen.set_underline(char=0x2D, colour=1)
    screen.write(bytes([0x2D]))
    assert screen.underline_matrix[0][0] is True
    assert screen.colour_matrix[0][0] == screen.underline_colour
    resolved = screen.resolved_colour_matrix[0][0]
    assert resolved[0] == screen.underline_colour
    assert resolved[1] == screen.background_colour


def test_reverse_video_respects_palette_mapping() -> None:
    screen = PetsciiScreen()
    screen.write(bytes([0x05]))  # map to palette index 1
    screen.write("A")
    normal_pair = screen.resolved_colour_matrix[0][0]
    assert normal_pair == (screen.screen_colour, screen.background_colour)

    screen.write(bytes([0x12]))  # reverse on
    screen.write("B")
    reverse_pair = screen.resolved_colour_matrix[0][1]
    assert reverse_pair == (screen.background_colour, screen.screen_colour)


def test_palette_updates_apply_to_reverse_and_underline_cells() -> None:
    screen = PetsciiScreen()
    palette = screen.palette
    initial_screen_colour = screen.screen_colour
    underline_code = screen.underline_char
    screen.write(
        bytes([
            0x12,
            ord("A"),
            0x92,
            ord("B"),
            underline_code,
        ])
    )

    colour_row = screen.colour_matrix[0]
    assert colour_row[0] == initial_screen_colour
    assert colour_row[1] == initial_screen_colour
    assert colour_row[2] == screen.underline_colour
    reverse_row = screen.reverse_matrix[0]
    assert reverse_row[:3] == (True, False, False)
    underline_row = screen.underline_matrix[0]
    assert underline_row[2] is True

    screen.apply_vic_register_write(0xD405, palette[0])
    screen.apply_vic_register_write(0xD403, palette[3])

    updated_screen_colour = screen.screen_colour
    updated_background_colour = screen.background_colour

    screen.write(bytes([0x12, ord("C"), 0x92, ord("D")]))

    colour_row = screen.colour_matrix[0]
    assert colour_row[0] == initial_screen_colour
    assert colour_row[1] == initial_screen_colour
    assert colour_row[2] == screen.underline_colour
    assert colour_row[3] == updated_screen_colour
    assert colour_row[4] == updated_screen_colour

    reverse_row = screen.reverse_matrix[0]
    assert reverse_row[:5] == (True, False, False, True, False)
    underline_row = screen.underline_matrix[0]
    assert underline_row[2] is True
    assert underline_row[3] is False
    assert underline_row[4] is False

    resolved_row = screen.resolved_colour_matrix[0]
    assert resolved_row[0] == (updated_background_colour, colour_row[0])
    assert resolved_row[1] == (colour_row[1], updated_background_colour)
    assert resolved_row[2] == (screen.underline_colour, updated_background_colour)
    assert resolved_row[3] == (updated_background_colour, colour_row[3])
    assert resolved_row[4] == (colour_row[4], updated_background_colour)

    assert updated_screen_colour == screen.screen_colour
    assert updated_background_colour == screen.background_colour
    assert screen.resolved_palette_state["reverse"] == {
        "foreground": updated_background_colour,
        "background": updated_screen_colour,
    }


def test_console_exposes_overlay_glyph_lookup() -> None:
    console = Console()

    lookup = console.overlay_glyph_lookup
    assert console.macro_glyphs is lookup.macros_by_slot
    assert console.macro_glyphs_by_text is lookup.macros_by_text
    assert console.flag_glyph_records == lookup.flag_records
    assert console.flag_directory_glyphs == lookup.flag_directory_tail
    assert console.flag_directory_block_glyphs == lookup.flag_directory_block
    assert len(console.macro_glyphs) == len(console.macros)
    assert len(lookup.macros) == len(console.macros)


def test_console_exposes_hardware_defaults(
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    console = Console()
    registers, timeline = _resolve_vic_register_state(editor_defaults)

    assert console.vic_registers == registers
    assert console.vic_register_timeline == timeline
    assert console.sid_volume == editor_defaults.hardware.sid_volume
    assert console.pointer_defaults == editor_defaults.hardware.pointer

    background = registers.get(0xD403)
    if background is not None:
        assert console.background_colour == background

    border = registers.get(0xD404)
    if border is not None:
        assert console.border_colour == border

def test_screen_tracks_glyph_banks() -> None:
    screen = PetsciiScreen()
    screen.write(bytes([0x41, 0x0E, 0x61]))

    assert screen.characters[0][:2] == "Aa"

    codes = screen.code_matrix[0]
    assert codes[0] == 0x41
    assert codes[1] == 0x61

    glyph_indices = screen.glyph_index_matrix[0]
    assert glyph_indices[0] == petscii_glyphs.get_glyph_index(0x41)
    assert glyph_indices[1] == petscii_glyphs.get_glyph_index(0x61, lowercase=True)

    glyphs = screen.glyph_matrix[0]
    assert glyphs[0] == petscii_glyphs.get_glyph(0x41)
    assert glyphs[1] == petscii_glyphs.get_glyph(0x61, lowercase=True)


def test_macro_glyph_lookup_matches_renderer(
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    console = Console()
    slot = 20
    macro_entry = console.defaults.macros_by_slot[slot]
    macro_run = console.macro_glyphs[slot]

    # The rendered payload omits the zero terminator stored in the directory.
    expected_rendered_list: list[int] = []
    for value in macro_entry.payload:
        byte = value & 0xFF
        if byte == 0x00:
            break
        expected_rendered_list.append(byte)
    expected_rendered = tuple(expected_rendered_list)
    assert macro_run.rendered == expected_rendered
    assert macro_run.text == macro_entry.decoded_text

    screen = PetsciiScreen(defaults=editor_defaults)
    screen.write(bytes(macro_run.rendered))

    for cell in macro_run.glyphs:
        x, y = cell.position
        assert screen.code_matrix[y][x] == cell.code
        assert screen.glyph_index_matrix[y][x] == cell.glyph_index
        assert screen.glyph_matrix[y][x] == cell.glyph
        assert petscii_glyphs.get_glyph_index(
            cell.code, lowercase=cell.lowercase
        ) == cell.glyph_index
        assert petscii_glyphs.get_glyph(cell.code, lowercase=cell.lowercase) == cell.glyph


def test_render_petscii_payload_handles_lowercase_bank() -> None:
    run = render_petscii_payload([0x0E, 0x61, 0x62, 0x8E, 0x41])

    assert [cell.lowercase for cell in run.glyphs] == [True, True, False]
    expected_codes = [0x61, 0x62, 0x41]
    assert [cell.code for cell in run.glyphs] == expected_codes
    for code, cell in zip(expected_codes, run.glyphs, strict=True):
        assert cell.glyph_index == petscii_glyphs.get_glyph_index(
            code, lowercase=cell.lowercase
        )
        assert cell.glyph == petscii_glyphs.get_glyph(
            code, lowercase=cell.lowercase
        )


def test_reverse_mode_swaps_render_colours(editor_defaults: ml_extra_defaults.MLExtraDefaults) -> None:
    console = Console()
    console.write(bytes([0x93]))  # clear
    console.write(bytes([0x05]))  # white foreground
    initial_background = console.background_colour

    console.write(bytes([0x12]))  # reverse on
    console.write(b"A")
    console.write(bytes([0x92]))  # reverse off
    console.write(b"B")

    snapshot = console.snapshot()
    characters = snapshot["characters"][0]
    assert characters[:2] == "AB"

    colour_row = snapshot["colour_matrix"][0]
    assert colour_row[0] == colour_row[1] == console.screen_colour

    reverse_row = snapshot["reverse_matrix"][0]
    assert reverse_row[0] is True
    assert reverse_row[1] is False

    resolved_row = snapshot["resolved_colour_matrix"][0]
    assert resolved_row[0] == (initial_background, colour_row[0])
    assert resolved_row[1] == (colour_row[1], initial_background)

    assert snapshot["background_colour"] == initial_background == editor_defaults.palette.colours[2]


def _resolve_expected_colour(screen: PetsciiScreen, value: int, *, default_index: int = 0) -> int:
    resolved = int(value) & 0xFF
    palette = screen.palette
    if resolved in palette:
        return resolved
    if 0 <= resolved < len(palette):
        return palette[resolved]
    return palette[default_index]


def test_console_poke_block_updates_chat_region_with_reverse_and_underline_state() -> None:
    console = Console()
    screen = console.screen

    screen_address = 0x0428
    colour_address = 0xD828
    underline_code = screen.underline_char

    screen_bytes = [0x41, 0xC2, underline_code, 0x20, 0xD0]
    colour_bytes = [
        screen.palette[1],
        0x02,
        0xFF,
        screen.palette[2],
        0x01,
    ]

    console.poke_block(
        screen_address=screen_address,
        screen_bytes=screen_bytes,
        colour_address=colour_address,
        colour_bytes=colour_bytes,
    )

    offset = screen_address - 0x0400
    row, column = divmod(offset, screen.width)
    slice_end = column + len(screen_bytes)

    assert screen.characters[row][column:slice_end] == "AB  P"

    expected_codes = tuple(screen_bytes)
    for index, expected in enumerate(expected_codes):
        cell = column + index
        assert screen.code_matrix[row][cell] == expected

    expected_colours = (
        _resolve_expected_colour(screen, screen.palette[1]),
        _resolve_expected_colour(screen, 0x02),
        screen.underline_colour,
        _resolve_expected_colour(screen, screen.palette[2]),
        _resolve_expected_colour(screen, 0x01),
    )
    colour_row = screen.colour_matrix[row][column:slice_end]
    assert tuple(colour_row) == expected_colours

    reverse_row = screen.reverse_matrix[row][column:slice_end]
    assert reverse_row == (False, True, False, False, True)

    underline_row = screen.underline_matrix[row][column:slice_end]
    assert underline_row == (False, False, True, False, False)

    resolved_row = screen.resolved_colour_matrix[row][column:slice_end]
    background = screen.background_colour
    assert resolved_row[0] == (expected_colours[0], background)
    assert resolved_row[1] == (background, expected_colours[1])
    assert resolved_row[2] == (screen.underline_colour, background)
    assert resolved_row[3] == (expected_colours[3], background)
    assert resolved_row[4] == (background, expected_colours[4])


def test_spinner_direct_pokes_preserve_reverse_behaviour() -> None:
    screen = PetsciiScreen()

    screen.set_lightbar_bitmaps([0x11, 0x22, 0x33, 0x44])
    assert screen.lightbar_bitmaps == (0x11, 0x22, 0x33, 0x44)

    spinner_screen_address = 0x049C
    spinner_colour_address = 0xD89C
    offset = spinner_screen_address - 0x0400
    row, column = divmod(offset, screen.width)

    screen.poke_colour_address(spinner_colour_address, 0x0F)
    clamped_colour = _resolve_expected_colour(screen, 0x0F)
    assert screen.colour_matrix[row][column] == clamped_colour

    screen.poke_screen_address(spinner_screen_address, screen.underline_char)
    assert screen.code_matrix[row][column] == screen.underline_char
    assert screen.underline_matrix[row][column] is True
    assert screen.colour_matrix[row][column] == screen.underline_colour
    assert screen.reverse_matrix[row][column] is False

    screen.poke_screen_address(spinner_screen_address, 0xC1)
    assert screen.code_matrix[row][column] == 0xC1
    assert screen.characters[row][column] == "A"
    assert screen.underline_matrix[row][column] is False
    assert screen.reverse_matrix[row][column] is True
    assert screen.colour_matrix[row][column] == screen.underline_colour

    screen.poke_colour_address(spinner_colour_address, 0x01)
    updated_colour = _resolve_expected_colour(screen, 0x01)
    assert screen.colour_matrix[row][column] == updated_colour
    assert screen.reverse_matrix[row][column] is True
    assert screen.underline_matrix[row][column] is False

    resolved = screen.resolved_colour_matrix[row][column]
    assert resolved == (screen.background_colour, updated_colour)


def test_session_runner_cli_boot_banner_uses_ascii() -> None:
    args = runtime_cli.parse_args([])
    runner = runtime_cli.create_runner(args)
    _ = runner.read_output()
    runner.console.push_macro_slot(0x28)
    output = runner.read_output()
    assert "FILE TRANSFER MENU" in output
    assert "UPLOAD FILES" in output
    assert "{CBM-" not in output

