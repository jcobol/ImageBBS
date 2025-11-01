"""Integration coverage for the ml.extra CLI metadata paths."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from datetime import datetime

import pytest

from imagebbs import ml_extra_cli
from imagebbs import ml_extra_defaults
from imagebbs import ml_extra_disasm
from imagebbs import ml_extra_dump_flag_strings
from imagebbs import ml_extra_dump_macros
from imagebbs import ml_extra_reporting
from imagebbs import ml_extra_screen_dumps


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
def macro_screen_records() -> list[dict[str, object]]:
    root = Path(__file__).resolve().parents[1] / "docs/porting/artifacts"
    path = root / "ml-extra-macro-screens.json.gz.base64"
    raw_text = path.read_text(encoding="utf-8")
    payload = base64.b64decode("".join(raw_text.split()))
    archive = gzip.decompress(payload).decode("utf-8")
    return json.loads(archive)


@pytest.fixture(scope="module")
def macro_screen_artifacts(
    macro_screen_records: list[dict[str, object]]
) -> dict[int, dict[str, object]]:
    return {int(entry["slot"]): entry for entry in macro_screen_records}


@pytest.fixture(scope="module")
def flag_screen_artifact() -> dict[str, object]:
    path = (
        Path(__file__).resolve().parents[1]
        / "docs/porting/artifacts/ml-extra-flag-screens.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


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


def test_dump_macros_hashes_json(
    tmp_path: Path, defaults: ml_extra_defaults.MLExtraDefaults
) -> None:
    # Why: Ensure the CLI snapshot exports stable slot hashes for overlay regression tracking.
    destination = tmp_path / "hashes.json"
    ml_extra_dump_macros.main(["--hashes-json", str(destination)])
    payload = json.loads(destination.read_text())
    assert "timestamp" in payload
    parsed_timestamp = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
    assert parsed_timestamp.tzinfo is not None
    overlay_path = Path(payload["overlay"]).resolve()
    assert overlay_path == ml_extra_defaults.default_overlay_path().resolve()
    expected_hashes = {
        f"{entry.slot:02x}": hashlib.sha256(bytes(entry.payload)).hexdigest()
        for entry in defaults.macros
    }
    assert payload["hashes"] == expected_hashes
    assert list(payload["hashes"].keys()) == sorted(payload["hashes"].keys())


def test_dump_flag_strings_cli_output(
    capsys: pytest.CaptureFixture[str], defaults: ml_extra_defaults.MLExtraDefaults
) -> None:
    ml_extra_dump_flag_strings.main([])
    output = capsys.readouterr().out
    assert f"overlay: {ml_extra_defaults.default_overlay_path()}" in output
    assert "flag data start: $d9c3" in output
    decoded_line = next(
        line for line in output.splitlines() if line.startswith("decoded bytes")
    )
    raw_line = next(line for line in output.splitlines() if line.startswith("raw bytes"))
    raw_values = raw_line.partition(": ")[2].split()
    assert raw_values == [f"${value:02x}" for value in defaults.flag_directory_block]
    decoded_values = decoded_line.partition(": ")[2].split()
    expected = [f"${(value ^ 0xFF):02x}" for value in defaults.flag_directory_block]
    assert decoded_values == expected
    assert defaults.flag_directory_text in output


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


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-m", "imagebbs.ml_extra_cli", *args]
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=_python_env(),
    )


def test_cli_lists_commands(capsys: pytest.CaptureFixture[str]) -> None:
    ml_extra_cli.main(["--help"])
    output = capsys.readouterr().out
    for name in sorted(ml_extra_cli.COMMANDS):
        assert name in output


def test_cli_dispatches_dump_macros(
    sample_slot: int, defaults: ml_extra_defaults.MLExtraDefaults
) -> None:
    result = _run_cli(["dump-macros", "--json", "--slot", str(sample_slot)])
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    rows = list(
        ml_extra_dump_macros.iter_macro_dumps(defaults, slots=[sample_slot])
    )
    assert payload == [row.as_dict() for row in rows]


def test_cli_unknown_command() -> None:
    result = _run_cli(["unknown-command"])
    assert result.returncode == 1
    assert "Unknown command" in result.stdout


def test_cli_help_from_subprocess() -> None:
    result = _run_cli(["--help"])
    assert result.returncode == 0
    assert "Available commands" in result.stdout


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


def test_screen_dumps_matches_artifacts(
    tmp_path: Path,
    macro_screen_records: list[dict[str, object]],
    flag_screen_artifact: dict[str, object],
) -> None:
    output_dir = tmp_path / "dumps"
    ml_extra_screen_dumps.main(["--output-dir", str(output_dir)])

    macro_path = output_dir / "ml-extra-macro-screens.json"
    flag_path = output_dir / "ml-extra-flag-screens.json"

    generated_macros = json.loads(macro_path.read_text(encoding="utf-8"))
    generated_flags = json.loads(flag_path.read_text(encoding="utf-8"))

    assert generated_macros == macro_screen_records
    assert generated_flags == flag_screen_artifact


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
