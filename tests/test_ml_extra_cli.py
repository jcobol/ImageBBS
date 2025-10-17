"""Integration coverage for the ml.extra CLI metadata paths."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import ml_extra_defaults
from scripts.prototypes import ml_extra_disasm
from scripts.prototypes import ml_extra_dump_macros
from scripts.prototypes import ml_extra_reporting


@pytest.fixture(scope="module")
def defaults() -> ml_extra_defaults.MLExtraDefaults:
    return ml_extra_defaults.MLExtraDefaults.from_overlay()


@pytest.fixture(scope="module")
def sample_slot(defaults: ml_extra_defaults.MLExtraDefaults) -> int:
    return defaults.macros[0].slot


@pytest.fixture(scope="module")
def metadata_snapshot(defaults: ml_extra_defaults.MLExtraDefaults) -> dict[str, object]:
    return ml_extra_reporting.collect_overlay_metadata(defaults)


def test_dump_macros_metadata_json(
    capsys: pytest.CaptureFixture[str],
    sample_slot: int,
    defaults: ml_extra_defaults.MLExtraDefaults,
    metadata_snapshot: dict[str, object],
) -> None:
    ml_extra_dump_macros.main(["--json", "--metadata", "--slot", str(sample_slot)])
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert "metadata" in payload
    metadata = payload["metadata"]
    assert metadata == metadata_snapshot
    assert "lightbar" in metadata and "palette" in metadata and "hardware" in metadata
    assert "flag_dispatch" in metadata
    assert "flag_directory_tail" in metadata
    assert metadata["flag_record_count"] == len(defaults.flag_records)
    assert metadata["macro_slots"] == [entry.slot for entry in defaults.macros]
    assert metadata["flag_directory_tail"]["text"] == defaults.flag_directory_text
    assert payload["macros"], "expected macro rows in JSON output"
    assert payload["macros"][0]["sha256"], "expected sha256 digest in JSON payload"


def test_dump_macros_metadata_text(capsys: pytest.CaptureFixture[str], sample_slot: int) -> None:
    ml_extra_dump_macros.main(["--metadata", "--slot", str(sample_slot)])
    output = capsys.readouterr().out
    assert "Overlay metadata:" in output
    assert "  lightbar" in output
    assert "flag dispatch:" in output
    assert "flag records:" in output
    assert "flag tail" in output
    assert "macro slots:" in output
    assert "sha256=" in output


def test_dump_macros_metadata_json_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    defaults: ml_extra_defaults.MLExtraDefaults,
    metadata_snapshot: dict[str, object],
) -> None:
    destination = tmp_path / "metadata.json"
    ml_extra_dump_macros.main(["--metadata-json", str(destination)])
    payload = json.loads(destination.read_text())
    assert payload == metadata_snapshot
    assert payload["flag_record_count"] == len(defaults.flag_records)
    assert payload["macro_slots"] == [entry.slot for entry in defaults.macros]
    output = capsys.readouterr().out
    assert "slot" in output, "expected macro dump output alongside file write"


def test_disasm_metadata_text(capsys: pytest.CaptureFixture[str], sample_slot: int) -> None:
    ml_extra_disasm.main(["--metadata", "--slot", str(sample_slot)])
    output = capsys.readouterr().out
    assert "Overlay metadata:" in output
    assert "flag dispatch:" in output
    assert f"Macro slot {sample_slot}" in output
    assert "Macro payload hashes:" in output


def _run_snapshot_guard(args: list[str]) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "-m",
        "scripts.prototypes.ml_extra_snapshot_guard",
        *args,
    ]
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )


def _baseline_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "porting"
        / "artifacts"
        / "ml-extra-overlay-metadata.json"
    )


def test_snapshot_guard_matches_baseline() -> None:
    result = _run_snapshot_guard(["--baseline", str(_baseline_path())])
    assert result.returncode == 0
    assert "Baseline snapshot matches" in result.stdout
    assert result.stderr == ""


def test_snapshot_guard_detects_drift(tmp_path: Path) -> None:
    baseline_data = json.loads(_baseline_path().read_text(encoding="utf-8"))
    baseline_data["flag_directory_tail"]["text"] = "Modified baseline text"
    altered = tmp_path / "baseline.json"
    altered.write_text(json.dumps(baseline_data, indent=2))

    result = _run_snapshot_guard(["--baseline", str(altered)])
    assert result.returncode == 1
    assert "Drift detected" in result.stdout
    assert "changed flag_directory_tail.text" in result.stdout
