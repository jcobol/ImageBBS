"""Console rendering tests for the PETSCII host shim."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import ml_extra_defaults, petscii_glyphs
from scripts.prototypes.console_renderer import (
    PetsciiScreen,
    render_petscii_payload,
)
from scripts.prototypes.device_context import Console


@pytest.fixture(scope="module")
def editor_defaults() -> ml_extra_defaults.MLExtraDefaults:
    return ml_extra_defaults.MLExtraDefaults.from_overlay()


def _artifact_root() -> Path:
    return Path(__file__).resolve().parents[1] / "docs/porting/artifacts"


def _load_artifact_json(name: str) -> Any:
    path = _artifact_root() / name
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_hex_value(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("$"):
        return int(value[1:], 16)
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
            sid_volume = value.get("sid_volume")
            normalised["hardware"] = {
                "vic_registers": vic_registers,
                "sid_volume": _parse_hex_value(sid_volume),
            }
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
        if "page1_bytes" in entry:
            record["page1_bytes"] = bytes(
                _parse_hex_sequence(entry.get("page1_bytes", []))
            )
            record["page1_text"] = entry.get("page1_text")
        if "page2_bytes" in entry:
            record["page2_bytes"] = bytes(
                _parse_hex_sequence(entry.get("page2_bytes", []))
            )
            record["page2_text"] = entry.get("page2_text")
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


@pytest.fixture(scope="module")
def macro_screen_captures() -> list[Dict[str, Any]]:
    return _load_macro_screen_artifacts()


@pytest.fixture(scope="module")
def flag_screen_captures() -> Dict[str, Any]:
    return _load_flag_screen_artifacts()


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


def _resolve_vic_registers(
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> dict[int, int | None]:
    registers: dict[int, int | None] = {}
    for entry in defaults.hardware.vic_registers:
        last_value: int | None = None
        for _, value in entry.writes:
            if value is not None:
                last_value = value
        registers[entry.address] = last_value
    return registers


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
    registers = _resolve_vic_registers(editor_defaults)

    assert screen.vic_registers == registers

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
    hardware = snapshot["hardware"]
    registers = _resolve_vic_registers(editor_defaults)
    assert hardware["vic_registers"] == registers
    assert hardware["sid_volume"] == editor_defaults.hardware.sid_volume

    assert console.transcript_bytes == banner_sequence
    assert console.transcript == banner_sequence.decode("latin-1")


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


def test_console_exposes_overlay_glyph_lookup() -> None:
    console = Console()

    lookup = console.overlay_glyph_lookup
    assert console.macro_glyphs is lookup.macros_by_slot
    assert console.macro_glyphs_by_text is lookup.macros_by_text
    assert console.flag_glyph_records == lookup.flag_records
    assert console.flag_directory_glyphs == lookup.flag_directory
    assert len(console.macro_glyphs) >= len(console.macros)


def test_console_exposes_hardware_defaults(
    editor_defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    console = Console()
    registers = _resolve_vic_registers(editor_defaults)

    assert console.vic_registers == registers
    assert console.sid_volume == editor_defaults.hardware.sid_volume

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
    assert snapshot["screen_colour"] == console.screen_colour
