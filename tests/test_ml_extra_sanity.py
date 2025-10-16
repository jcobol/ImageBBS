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


def test_run_checks_reports_payload_hashes(defaults: ml_extra_defaults.MLExtraDefaults) -> None:
    report = ml_extra_sanity.run_checks()
    hashes = report["payload_hashes"]
    assert isinstance(hashes, list)
    assert hashes, "expected at least one payload hash entry"

    first = hashes[0]
    assert "slot" in first and "sha256" in first

    macro_entry = next(item for item in report["macro_directory"] if item["slot"] == first["slot"])
    assert macro_entry["sha256"] == first["sha256"]


def test_format_report_includes_hashes(defaults: ml_extra_defaults.MLExtraDefaults) -> None:
    report = ml_extra_sanity.run_checks()
    text = ml_extra_sanity.format_report(report)
    assert "Macro payload hashes" in text
    sample_slot = report["payload_hashes"][0]["slot"]
    sample_hash = report["payload_hashes"][0]["sha256"]
    assert f"slot {sample_slot:>2}" in text
    assert sample_hash in text
