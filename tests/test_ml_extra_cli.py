"""Integration coverage for the ml.extra CLI metadata paths."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import ml_extra_defaults
from scripts.prototypes import ml_extra_disasm
from scripts.prototypes import ml_extra_dump_macros


@pytest.fixture(scope="module")
def defaults() -> ml_extra_defaults.MLExtraDefaults:
    return ml_extra_defaults.MLExtraDefaults.from_overlay()


@pytest.fixture(scope="module")
def sample_slot(defaults: ml_extra_defaults.MLExtraDefaults) -> int:
    return defaults.macros[0].slot


def test_dump_macros_metadata_json(
    capsys: pytest.CaptureFixture[str],
    sample_slot: int,
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> None:
    ml_extra_dump_macros.main(["--json", "--metadata", "--slot", str(sample_slot)])
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert "metadata" in payload
    metadata = payload["metadata"]
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


def test_disasm_metadata_text(capsys: pytest.CaptureFixture[str], sample_slot: int) -> None:
    ml_extra_disasm.main(["--metadata", "--slot", str(sample_slot)])
    output = capsys.readouterr().out
    assert "Overlay metadata:" in output
    assert "flag dispatch:" in output
    assert f"Macro slot {sample_slot}" in output
    assert "Macro payload hashes:" in output
