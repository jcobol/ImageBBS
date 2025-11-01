"""Regression coverage for ``ml_extra_sanity`` helpers."""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import pytest

from imagebbs import ml_extra_defaults
from imagebbs import ml_extra_reporting
from imagebbs import ml_extra_sanity
from imagebbs.ml_extra.sanity import core as sanity_core


@pytest.fixture(scope="module")
def defaults() -> ml_extra_defaults.MLExtraDefaults:
    return ml_extra_defaults.MLExtraDefaults.from_overlay()


@pytest.fixture(scope="module")
def sanity_report() -> sanity_core.SanityReport:
    return ml_extra_sanity.run_checks()


@pytest.fixture(scope="module")
def metadata_snapshot(defaults: ml_extra_defaults.MLExtraDefaults) -> dict[str, object]:
    return ml_extra_reporting.collect_overlay_metadata(defaults)


def _load_metadata_artifact() -> dict[str, object]:
    path = (
        Path(__file__).resolve().parents[1]
        / "docs/porting/artifacts/ml-extra-overlay-metadata.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _load_macro_directory_artifact() -> list[dict[str, object]]:
    path = (
        Path(__file__).resolve().parents[1]
        / "docs/porting/artifacts/ml-extra-macro-screens.json.gz.base64"
    )
    raw = base64.b64decode(path.read_text(encoding="utf-8"))
    return json.loads(gzip.decompress(raw))


def test_run_checks_reports_payload_hashes(
    sanity_report: sanity_core.SanityReport,
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    hashes = sanity_report.payload_hashes
    assert hashes, "expected at least one payload hash entry"

    first = hashes[0]
    macro_entry = next(
        item for item in sanity_report.macro_directory if item.slot == first.slot
    )
    assert macro_entry.sha256 == first.sha256


def test_format_report_includes_hashes(
    sanity_report: sanity_core.SanityReport,
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    text = ml_extra_sanity.format_report(sanity_report)
    assert "Macro payload hashes" in text
    sample_slot = sanity_report.payload_hashes[0].slot
    sample_hash = sanity_report.payload_hashes[0].sha256
    assert f"slot {sample_slot:>2}" in text
    assert sample_hash in text


def test_stub_macros_match_overlay(
    sanity_report: sanity_core.SanityReport,
) -> None:
    mismatches = [row for row in sanity_report.comparisons if not row.matches]
    expected_missing = {0x28, 0x29, 0x2A}
    mismatch_slots = {row.slot for row in mismatches}
    assert mismatch_slots == expected_missing, mismatch_slots
    for row in mismatches:
        assert row.stub_length in (None, 0)
        assert row.stub_preview in (None, "")


def test_stub_static_tables_match(
    sanity_report: sanity_core.SanityReport,
) -> None:
    for diff in (
        sanity_report.stub_static.lightbar,
        sanity_report.stub_static.underline,
        sanity_report.stub_static.palette,
        sanity_report.stub_static.flag_directory_block,
        sanity_report.stub_static.flag_directory_tail,
    ):
        assert diff.matches, "expected stub static data to match overlay"


def test_stub_directory_counts(
    sanity_report: sanity_core.SanityReport,
) -> None:
    assert sanity_report.stub_only_macros == ()


def test_run_checks_metadata_snapshot_matches_helper(
    sanity_report: sanity_core.SanityReport,
    metadata_snapshot: dict[str, object],
) -> None:
    assert sanity_report.metadata_snapshot == metadata_snapshot


def test_collect_overlay_metadata_matches_artifact(
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    snapshot = ml_extra_reporting.collect_overlay_metadata(defaults)
    assert snapshot == _load_metadata_artifact()


def test_macro_directory_matches_artifact(
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    recovered = [
        {
            "slot": entry.slot,
            "address": entry.address,
            "bytes": list(entry.payload),
            "text": entry.decoded_text,
        }
        for entry in defaults.macros
        if entry.address or entry.payload
    ]

    expected = _load_macro_directory_artifact()
    overlay_slots = {item["slot"] for item in expected}
    filtered = [item for item in recovered if item["slot"] in overlay_slots]
    assert len(filtered) == len(expected)

    for current, reference in zip(filtered, expected, strict=True):
        assert current["slot"] == reference["slot"]
        assert current["address"] == int(reference["address"][1:], 16)
        assert [f"${value:02x}" for value in current["bytes"]] == reference["bytes"]
        assert current["text"] == reference["text"]


def test_extra_macro_payloads_present(
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    macros = defaults.macros_by_slot
    assert 0x28 in macros and 0x29 in macros and 0x2A in macros
    assert macros[0x29].decoded_text == "COMMAND (Q TO EXIT): "
    assert macros[0x2A].decoded_text == "?? UNKNOWN COMMAND"


def test_main_writes_metadata_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    metadata_snapshot: dict[str, object],
) -> None:
    destination = tmp_path / "overlay-metadata.json"
    ml_extra_sanity.main(["--metadata-json", str(destination)])
    capture = capsys.readouterr()
    assert destination.exists(), "expected metadata JSON to be written"

    snapshot_text = destination.read_text(encoding="utf-8")
    expected_encoding = json.dumps(metadata_snapshot, indent=2, sort_keys=True) + "\n"
    assert snapshot_text == expected_encoding

    written = json.loads(snapshot_text)
    assert written == metadata_snapshot

    # Ensure the text report is still rendered alongside the metadata export.
    assert "Macro directory (runtime order):" in capture.out
    assert "Macro payload hashes" in capture.out
    assert "Slot diff (recovered vs. stub data):" in capture.out


def test_main_json_output_includes_metadata(
    capsys: pytest.CaptureFixture[str],
    metadata_snapshot: dict[str, object],
) -> None:
    ml_extra_sanity.main(["--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["metadata_snapshot"] == metadata_snapshot
    assert payload["payload_hashes"], "expected payload hashes in JSON report"


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
