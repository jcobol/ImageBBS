"""Tests for the ml_extra_refresh_pipeline CLI helpers."""

from __future__ import annotations

import json
import time
import types
from pathlib import Path

import pytest

from imagebbs import ml_extra_refresh_pipeline
from imagebbs.ml_extra.sanity import core as sanity_core


@pytest.fixture()
def snapshot_payload() -> dict[str, object]:
    return {"version": "1.2", "value": 42}


def _dump(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2) + "\n"


def test_main_if_changed_skips_write(tmp_path: Path, monkeypatch, capsys, snapshot_payload):
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(_dump(snapshot_payload), encoding="utf-8")
    baseline_path = metadata_path

    captured_mtime = metadata_path.stat().st_mtime

    def fake_run_checks(overlay: Path | None):
        return types.SimpleNamespace(metadata_snapshot=snapshot_payload)

    def fake_diff(baseline: dict[str, object], current: dict[str, object]):
        assert baseline == snapshot_payload
        assert current == snapshot_payload
        return sanity_core.MetadataDiff(
            matches=True,
            added=(),
            removed=(),
            changed=(),
            baseline_snapshot=baseline,
            current_snapshot=current,
        )

    def fake_render(path: Path, diff: sanity_core.MetadataDiff) -> str:
        assert path == baseline_path
        assert diff.matches is True
        return "rendered diff"

    monkeypatch.setattr(
        ml_extra_refresh_pipeline.sanity_core, "run_checks", fake_run_checks
    )
    monkeypatch.setattr(
        ml_extra_refresh_pipeline.sanity_core,
        "diff_metadata_snapshots",
        fake_diff,
    )
    monkeypatch.setattr(
        ml_extra_refresh_pipeline.sanity_reporting,
        "render_diff_summary",
        fake_render,
    )

    exit_code = ml_extra_refresh_pipeline.main(
        [
            "--baseline",
            str(baseline_path),
            "--metadata-json",
            str(metadata_path),
            "--if-changed",
        ]
    )

    out = capsys.readouterr().out.splitlines()
    assert out[0] == f"Metadata snapshot already up to date: {metadata_path}"
    assert out[1] == "rendered diff"

    assert exit_code == 0
    assert metadata_path.read_text(encoding="utf-8") == _dump(snapshot_payload)
    assert metadata_path.stat().st_mtime == captured_mtime


def test_main_if_changed_updates_file(tmp_path: Path, monkeypatch, capsys):
    baseline_payload = {"version": "1.1", "value": 13}
    new_payload = {"version": "1.2", "value": 99}

    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(_dump(baseline_payload), encoding="utf-8")
    baseline_path = metadata_path

    original_mtime = metadata_path.stat().st_mtime

    # Ensure measurable mtime difference when running on fast filesystems.
    time.sleep(0.01)

    def fake_run_checks(overlay: Path | None):
        return types.SimpleNamespace(metadata_snapshot=new_payload)

    def fake_diff(baseline: dict[str, object], current: dict[str, object]):
        assert baseline == baseline_payload
        assert current == new_payload
        return sanity_core.MetadataDiff(
            matches=False,
            added=(),
            removed=(),
            changed=(),
            baseline_snapshot=baseline,
            current_snapshot=current,
        )

    def fake_render(path: Path, diff: sanity_core.MetadataDiff) -> str:
        assert path == baseline_path
        assert diff.matches is False
        return "rendered diff"

    monkeypatch.setattr(
        ml_extra_refresh_pipeline.sanity_core, "run_checks", fake_run_checks
    )
    monkeypatch.setattr(
        ml_extra_refresh_pipeline.sanity_core,
        "diff_metadata_snapshots",
        fake_diff,
    )
    monkeypatch.setattr(
        ml_extra_refresh_pipeline.sanity_reporting,
        "render_diff_summary",
        fake_render,
    )

    exit_code = ml_extra_refresh_pipeline.main(
        [
            "--baseline",
            str(baseline_path),
            "--metadata-json",
            str(metadata_path),
            "--if-changed",
        ]
    )

    out = capsys.readouterr().out.splitlines()
    assert out[0] == f"Metadata snapshot updated: {metadata_path}"
    assert out[1] == "rendered diff"

    assert exit_code == 1
    assert metadata_path.read_text(encoding="utf-8") == _dump(new_payload)
    assert metadata_path.stat().st_mtime > original_mtime
