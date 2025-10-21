"""Unit tests for the PETSCII decoding helpers used by ml.extra scripts."""

from __future__ import annotations

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
