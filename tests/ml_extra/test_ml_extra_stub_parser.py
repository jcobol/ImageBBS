"""Regression coverage for ``ml_extra_stub_parser`` helpers."""

from __future__ import annotations

import pytest

from imagebbs import ml_extra_defaults
from imagebbs import ml_extra_stub_parser


@pytest.fixture(scope="module")
def stub_source() -> tuple[str, ...]:
    stub_path = ml_extra_defaults._REPO_ROOT / "v1.2/source/ml_extra_stub.asm"
    return ml_extra_stub_parser.load_stub_source(stub_path)


@pytest.fixture(scope="module")
def defaults() -> ml_extra_defaults.MLExtraDefaults:
    return ml_extra_defaults.MLExtraDefaults.from_overlay()


def test_macro_directory_components_round_trip(stub_source: tuple[str, ...]) -> None:
    entries = ml_extra_stub_parser.parse_stub_macro_directory(stub_source)
    slot_ids = ml_extra_stub_parser.read_macro_slot_ids(stub_source)
    runtime_targets = ml_extra_stub_parser.read_macro_runtime_targets(stub_source)
    directory_labels = ml_extra_stub_parser.read_macro_payload_directory(stub_source)
    payloads = ml_extra_stub_parser.read_macro_payloads(stub_source)

    assert len(entries) == len(slot_ids) == len(runtime_targets) == len(directory_labels)
    assert payloads, "expected payload mapping to be populated"

    for entry, slot, address, label in zip(
        entries, slot_ids, runtime_targets, directory_labels, strict=True
    ):
        assert entry.slot == slot
        assert entry.address == address
        assert label in payloads
        assert tuple(entry.payload) == payloads[label]


def test_parse_stub_static_data_matches_overlay(
    stub_source: tuple[str, ...],
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    stub_static = ml_extra_stub_parser.parse_stub_static_data(stub_source)

    assert stub_static.lightbar == defaults.lightbar.bitmaps
    assert stub_static.underline == (
        defaults.lightbar.underline_char,
        defaults.lightbar.underline_color,
    )
    assert stub_static.palette == defaults.palette.colours
    assert stub_static.flag_directory_block == defaults.flag_directory_block
    assert stub_static.flag_directory_tail == defaults.flag_directory_tail


def test_stub_macro_entry_helpers_share_decoder(
    stub_source: tuple[str, ...],
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    entries = ml_extra_stub_parser.parse_stub_macro_directory(stub_source)
    directory = {entry.slot: entry for entry in entries}

    for macro in defaults.macros:
        stub_entry = directory.get(macro.slot)
        if stub_entry is None:
            continue
        assert stub_entry.byte_preview() == macro.byte_preview()
        assert stub_entry.decoded_text() == macro.decoded_text
