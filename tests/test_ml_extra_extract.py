"""Unit tests for the PETSCII decoding helpers used by ml.extra scripts."""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

from imagebbs import ml_extra_defaults
from imagebbs import ml_extra_extract


def test_decode_petscii_stops_at_terminator() -> None:
    payload = [0x41, 0x00, 0x42]
    assert ml_extra_extract.decode_petscii(payload) == "A"


def test_decode_petscii_handles_printable_braces() -> None:
    payload = [0x7B, 0x7D, 0x00]
    assert ml_extra_extract.decode_petscii(payload) == "{}"


def test_decode_petscii_formats_control_codes() -> None:
    payload = [0x03, 0x9D, 0x00]
    assert ml_extra_extract.decode_petscii(payload) == "{CBM-$03}{CBM-$9d}"


def test_decode_petscii_strips_high_bit_for_ascii() -> None:
    payload = [0xC1, 0xD2, 0x00]
    assert ml_extra_extract.decode_petscii(payload) == "AR"


def _trim_payload(payload: list[int]) -> list[int]:
    trimmed: list[int] = []
    for value in payload:
        if value == 0:
            break
        trimmed.append(value)
    return trimmed


def _load_pointer_directory_snapshot() -> list[dict[str, object]]:
    path = (
        Path(__file__).resolve().parents[1]
        / "docs/porting/artifacts/ml-extra-macro-screens.json.gz.base64"
    )
    raw = base64.b64decode(path.read_text(encoding="utf-8"))
    data = gzip.decompress(raw)
    return json.loads(data)


def test_iter_pointer_directory_matches_artifact() -> None:
    overlay_path = ml_extra_defaults.default_overlay_path()
    load_addr, memory = ml_extra_extract.load_prg(overlay_path)
    directory = list(
        ml_extra_extract.iter_pointer_directory(memory, load_addr=load_addr)
    )

    snapshot = [
        entry for entry in _load_pointer_directory_snapshot() if entry["address"] != "$0000"
    ]
    assert len(directory) == len(snapshot)

    directory.sort(key=lambda entry: entry.slot)
    snapshot.sort(key=lambda entry: entry["slot"])

    for entry, expected in zip(directory, snapshot, strict=True):
        assert entry.slot == expected["slot"]
        assert entry.address == int(expected["address"][1:], 16)

        expected_bytes = [int(value[1:], 16) for value in expected["bytes"]]
        assert _trim_payload(entry.data) == _trim_payload(expected_bytes)
        assert entry.text == expected["text"]
