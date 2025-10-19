"""Regression coverage for ``ml_extra_sanity`` helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import ml_extra_defaults
from scripts.prototypes import ml_extra_reporting
from scripts.prototypes import ml_extra_sanity


@pytest.fixture(scope="module")
def defaults() -> ml_extra_defaults.MLExtraDefaults:
    return ml_extra_defaults.MLExtraDefaults.from_overlay()


@pytest.fixture(scope="module")
def sanity_report() -> dict[str, object]:
    return ml_extra_sanity.run_checks()


@pytest.fixture(scope="module")
def metadata_snapshot(defaults: ml_extra_defaults.MLExtraDefaults) -> dict[str, object]:
    return ml_extra_reporting.collect_overlay_metadata(defaults)


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
    expected_missing = {0x28, 0x29, 0x2A}
    mismatch_slots = {row["slot"] for row in mismatches}
    assert mismatch_slots == expected_missing, mismatch_slots
    for row in mismatches:
        assert row["stub_length"] in (None, 0)
        assert row["stub_preview"] in (None, "")


def test_stub_static_tables_match(sanity_report: dict[str, object]) -> None:
    stub_static = sanity_report["stub_static"]
    for key in ("lightbar", "underline", "palette", "flag_directory_block", "flag_directory_tail"):
        assert stub_static[key]["matches"], f"stub field {key} did not match overlay"


def test_stub_directory_counts(sanity_report: dict[str, object]) -> None:
    assert sanity_report["stub_only_macros"] == []


def test_run_checks_metadata_snapshot_matches_helper(
    sanity_report: dict[str, object],
    metadata_snapshot: dict[str, object],
) -> None:
    assert "metadata_snapshot" in sanity_report
    assert sanity_report["metadata_snapshot"] == metadata_snapshot


def test_main_writes_metadata_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    metadata_snapshot: dict[str, object],
) -> None:
    destination = tmp_path / "overlay-metadata.json"
    ml_extra_sanity.main(["--metadata-json", str(destination)])
    capture = capsys.readouterr()
    assert destination.exists(), "expected metadata JSON to be written"

    written = json.loads(destination.read_text())
    assert written == metadata_snapshot

    # Ensure the text report is still rendered alongside the metadata export.
    assert "Macro directory (runtime order):" in capture.out
    assert "Macro payload hashes" in capture.out
    assert "Slot diff (recovered vs. stub data):" in capture.out


def test_main_with_matching_baseline(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    metadata_snapshot: dict[str, object],
) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps(metadata_snapshot, indent=2, sort_keys=True))

    ml_extra_sanity.main(["--baseline-metadata", str(baseline)])

    capture = capsys.readouterr()
    assert "Baseline metadata snapshot matches recovered overlay." in capture.out


def test_main_with_tampered_baseline(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    metadata_snapshot: dict[str, object],
) -> None:
    baseline_data = json.loads(json.dumps(metadata_snapshot))
    baseline_data["load_address"] = "$c100"

    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps(baseline_data, indent=2, sort_keys=True))

    with pytest.raises(SystemExit) as excinfo:
        ml_extra_sanity.main(["--baseline-metadata", str(baseline), "--json"])

    assert excinfo.value.code == 1

    capture = capsys.readouterr()
    payload = json.loads(capture.out)
    assert payload["baseline_diff"]["matches"] is False
    changed_paths = {entry["path"] for entry in payload["baseline_diff"]["changed"]}
    assert "load_address" in changed_paths
