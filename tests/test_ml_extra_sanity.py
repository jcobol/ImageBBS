"""Regression coverage for ``ml_extra_sanity`` helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import ml_extra_defaults
from scripts.prototypes import ml_extra_sanity


@pytest.fixture(scope="module")
def defaults() -> ml_extra_defaults.MLExtraDefaults:
    return ml_extra_defaults.MLExtraDefaults.from_overlay()


@pytest.fixture(scope="module")
def sanity_report() -> dict[str, object]:
    return ml_extra_sanity.run_checks()


def test_run_checks_reports_payload_hashes(
    sanity_report: dict[str, object],
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    hashes = sanity_report["payload_hashes"]
    assert isinstance(hashes, list)
    assert hashes, "expected at least one payload hash entry"

    first = hashes[0]
    assert "slot" in first and "sha256" in first

    macro_entry = next(
        item for item in sanity_report["macro_directory"] if item["slot"] == first["slot"]
    )
    assert macro_entry["sha256"] == first["sha256"]


def test_format_report_includes_hashes(
    sanity_report: dict[str, object],
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    text = ml_extra_sanity.format_report(sanity_report)
    assert "Macro payload hashes" in text
    sample_slot = sanity_report["payload_hashes"][0]["slot"]
    sample_hash = sanity_report["payload_hashes"][0]["sha256"]
    assert f"slot {sample_slot:>2}" in text
    assert sample_hash in text


def test_stub_macros_match_overlay(sanity_report: dict[str, object]) -> None:
    comparisons = sanity_report["comparisons"]
    mismatches = [row for row in comparisons if not row["matches"]]
    assert not mismatches, f"expected all macro slots to match, found {mismatches}"


def test_stub_static_tables_match(sanity_report: dict[str, object]) -> None:
    stub_static = sanity_report["stub_static"]
    for key in ("lightbar", "underline", "palette", "flag_directory_block", "flag_directory_tail"):
        assert stub_static[key]["matches"], f"stub field {key} did not match overlay"


def test_stub_directory_counts(sanity_report: dict[str, object]) -> None:
    assert sanity_report["stub_only_macros"] == []
