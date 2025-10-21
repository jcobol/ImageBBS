"""Integration coverage for the ml.extra CLI metadata paths."""

from __future__ import annotations

import base64
import gzip
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from imagebbs import ml_extra_defaults
from imagebbs import ml_extra_disasm
from imagebbs import ml_extra_dump_macros
from imagebbs import ml_extra_reporting


@pytest.fixture(scope="module")
def defaults() -> ml_extra_defaults.MLExtraDefaults:
    return ml_extra_defaults.MLExtraDefaults.from_overlay()


@pytest.fixture(scope="module")
def sample_slot(defaults: ml_extra_defaults.MLExtraDefaults) -> int:
    return defaults.macros[0].slot


@pytest.fixture(scope="module")
def metadata_snapshot(defaults: ml_extra_defaults.MLExtraDefaults) -> dict[str, object]:
    return ml_extra_reporting.collect_overlay_metadata(defaults)


@pytest.fixture(scope="module")
def macro_screen_artifacts() -> dict[int, dict[str, object]]:
    root = Path(__file__).resolve().parents[1] / "docs/porting/artifacts"
    path = root / "ml-extra-macro-screens.json.gz.base64"
    raw_text = path.read_text(encoding="utf-8")
    payload = base64.b64decode("".join(raw_text.split()))
    archive = gzip.decompress(payload).decode("utf-8")
    records = json.loads(archive)
    return {int(entry["slot"]): entry for entry in records}


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
        "imagebbs.ml_extra_snapshot_guard",
        *args,
    ]
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=_python_env(),
    )


def _run_refresh_pipeline(args: list[str]) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "-m",
        "imagebbs.ml_extra_refresh_pipeline",
        *args,
    ]
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=_python_env(),
    )


def _python_env() -> dict[str, str]:
    env = os.environ.copy()
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    entries = [str(src_path), str(repo_root)]
    existing = env.get("PYTHONPATH")
    if existing:
        entries.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(entries)
    return env


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
    assert json.loads(altered.read_text()) == baseline_data


def test_snapshot_guard_json_output() -> None:
    result = _run_snapshot_guard(["--baseline", str(_baseline_path()), "--json"])
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["matches"] is True
    assert payload["baseline_lines"], "expected baseline text summary"
    assert payload["added"] == []
    assert result.stderr == ""


def test_snapshot_guard_update_baseline(tmp_path: Path) -> None:
    baseline_data = json.loads(_baseline_path().read_text(encoding="utf-8"))
    baseline_data["flag_directory_tail"]["text"] = "Modified baseline text"
    altered = tmp_path / "baseline.json"
    altered.write_text(json.dumps(baseline_data, indent=2) + "\n", encoding="utf-8")

    result = _run_snapshot_guard(
        ["--baseline", str(altered), "--update-baseline"]
    )

    assert result.returncode == 0
    assert "Drift detected" in result.stdout
    assert "Refreshed baseline snapshot" in result.stdout
    refreshed_payload = json.loads(altered.read_text(encoding="utf-8"))
    expected_payload = json.loads(
        _baseline_path().read_text(encoding="utf-8")
    )
    assert refreshed_payload == expected_payload


def test_dump_macros_file_transfer_slots(
    capsys: pytest.CaptureFixture[str],
    defaults: ml_extra_defaults.MLExtraDefaults,
    macro_screen_artifacts: dict[int, dict[str, object]],
) -> None:
    slots = [0x28, 0x29, 0x2A]
    slot_args = [item for slot in slots for item in ("--slot", f"${slot:02x}")]
    ml_extra_dump_macros.main(["--json", *slot_args])
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert len(payload) == len(slots)
    rows_by_slot = {row["slot"]: row for row in payload}
    assert set(rows_by_slot) == {40, 41, 42}
    header = rows_by_slot[40]
    prompt = rows_by_slot[41]
    error = rows_by_slot[42]
    assert header["sha256"] == "8e1d129eba5881d8546705478687e0fd2bd6b22e688ceda58cef0d11b3a44620"
    assert prompt["sha256"] == "ff429b988d00e0cadc5fadedb482816f4cee1805686aae0669a6e8a7630c8621"
    assert error["sha256"] == "748748598d02e1d8760e64d3c6f0d0e173d8adf4f64a2a28340d8dfc0ef04292"
    assert "FILE TRANSFER MENU" in header["text"]
    assert header["slot"] in defaults.macros_by_slot
    for slot in slots:
        assert slot in defaults.macros_by_slot
        entry = defaults.macros_by_slot[slot]
        assert entry.screen is not None
        assert entry.screen.width == 40
        assert entry.screen.height == 25
        assert len(entry.screen.glyph_bytes) == entry.screen.width * entry.screen.height
        assert len(entry.screen.colour_bytes) == entry.screen.width * entry.screen.height
        artifact = macro_screen_artifacts[slot]
        row = rows_by_slot[slot]
        assert row.keys() >= {"bytes", "text"}
        assert row["bytes"] == artifact["bytes"]
        assert row["text"] == artifact["text"]
        assert len(artifact["bytes"]) == artifact.get("byte_count", len(artifact["bytes"]))


def test_refresh_pipeline_matches_baseline(tmp_path: Path) -> None:
    baseline_copy = tmp_path / "baseline.json"
    baseline_copy.write_text(
        _baseline_path().read_text(encoding="utf-8"), encoding="utf-8"
    )
    metadata_path = tmp_path / "metadata.json"

    result = _run_refresh_pipeline(
        [
            "--baseline",
            str(baseline_copy),
            "--metadata-json",
            str(metadata_path),
        ]
    )

    assert result.returncode == 0
    assert "Baseline snapshot matches" in result.stdout
    assert result.stderr == ""

    baseline_payload = json.loads(baseline_copy.read_text(encoding="utf-8"))
    metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    expected_snapshot = json.loads(
        _baseline_path().read_text(encoding="utf-8")
    )
    assert baseline_payload == expected_snapshot
    assert metadata_payload == expected_snapshot


def test_refresh_pipeline_detects_drift(tmp_path: Path) -> None:
    baseline_data = json.loads(_baseline_path().read_text(encoding="utf-8"))
    baseline_data["flag_directory_tail"]["text"] = "Modified baseline text"
    altered = tmp_path / "baseline.json"
    altered.write_text(json.dumps(baseline_data, indent=2), encoding="utf-8")
    metadata_path = tmp_path / "metadata.json"

    result = _run_refresh_pipeline(
        [
            "--baseline",
            str(altered),
            "--metadata-json",
            str(metadata_path),
        ]
    )

    assert result.returncode == 1
    assert "Drift detected" in result.stdout
    assert result.stderr == ""

    metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    expected_snapshot = json.loads(
        _baseline_path().read_text(encoding="utf-8")
    )
    assert metadata_payload == expected_snapshot
