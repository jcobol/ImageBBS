"""Tests for the ml_extra_refresh_pipeline CLI helpers."""

from __future__ import annotations

import types
import json
from pathlib import Path

import pytest

from imagebbs import ml_extra_refresh_pipeline
from imagebbs.ml_extra.baseline import BaselineWorkflowResult
from imagebbs.ml_extra.sanity import core as sanity_core


@pytest.fixture()
def snapshot_payload() -> dict[str, object]:
    return {"version": "1.2", "value": 42}


def test_main_if_changed_skips_write(tmp_path: Path, monkeypatch, capsys, snapshot_payload):
    metadata_path = tmp_path / "metadata.json"
    baseline_path = tmp_path / "baseline.json"

    recorded_call: dict[str, object] = {}

    diff = sanity_core.MetadataDiff(
        matches=True,
        added=(),
        removed=(),
        changed=(),
        baseline_snapshot=snapshot_payload,
        current_snapshot=snapshot_payload,
    )

    fake_result = BaselineWorkflowResult(
        report=types.SimpleNamespace(metadata_snapshot=snapshot_payload),
        metadata_snapshot=snapshot_payload,
        baseline_snapshot=snapshot_payload,
        diff=diff,
        metadata_path=metadata_path,
        metadata_updated=False,
        baseline_path=baseline_path,
        baseline_updated=None,
    )

    def fake_run_baseline_workflow(**kwargs):
        recorded_call.update(kwargs)
        return fake_result

    def fake_render(path: Path, diff: sanity_core.MetadataDiff) -> str:
        assert path == baseline_path
        assert diff is fake_result.diff
        return "rendered diff"

    monkeypatch.setattr(
        ml_extra_refresh_pipeline, "run_baseline_workflow", fake_run_baseline_workflow
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

    assert recorded_call == {
        "overlay_path": None,
        "baseline_path": baseline_path,
        "metadata_path": metadata_path,
        "metadata_only_if_changed": True,
        "update_baseline": False,
    }

    assert exit_code == 0


def test_main_if_changed_updates_file(tmp_path: Path, monkeypatch, capsys):
    metadata_path = tmp_path / "metadata.json"
    baseline_path = tmp_path / "baseline.json"

    diff = sanity_core.MetadataDiff(
        matches=False,
        added=(),
        removed=(),
        changed=(),
        baseline_snapshot={"version": "1.1", "value": 13},
        current_snapshot={"version": "1.2", "value": 99},
    )

    fake_result = BaselineWorkflowResult(
        report=types.SimpleNamespace(metadata_snapshot=diff.current_snapshot),
        metadata_snapshot=diff.current_snapshot,
        baseline_snapshot=diff.baseline_snapshot,
        diff=diff,
        metadata_path=metadata_path,
        metadata_updated=True,
        baseline_path=baseline_path,
        baseline_updated=None,
    )

    def fake_run_baseline_workflow(**kwargs):
        return fake_result

    def fake_render(path: Path, diff: sanity_core.MetadataDiff) -> str:
        assert path == baseline_path
        assert diff is fake_result.diff
        return "rendered diff"

    monkeypatch.setattr(
        ml_extra_refresh_pipeline, "run_baseline_workflow", fake_run_baseline_workflow
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


# Why: Verify the CLI can refresh metadata without requiring a baseline comparison.
def test_main_metadata_only_skips_diff(tmp_path: Path, monkeypatch, capsys):
    metadata_path = tmp_path / "metadata.json"

    recorded_call: dict[str, object] = {}

    fake_result = BaselineWorkflowResult(
        report=types.SimpleNamespace(metadata_snapshot={"version": "1.2"}),
        metadata_snapshot={"version": "1.2"},
        baseline_snapshot=None,
        diff=None,
        metadata_path=metadata_path,
        metadata_updated=True,
        baseline_path=None,
        baseline_updated=None,
    )

    def fake_run_baseline_workflow(**kwargs):
        recorded_call.update(kwargs)
        return fake_result

    def fail_render(*_args, **_kwargs):  # pragma: no cover - should not execute
        raise AssertionError("render_diff_summary should not be called in metadata-only mode")

    monkeypatch.setattr(
        ml_extra_refresh_pipeline, "run_baseline_workflow", fake_run_baseline_workflow
    )
    monkeypatch.setattr(
        ml_extra_refresh_pipeline.sanity_reporting, "render_diff_summary", fail_render
    )

    exit_code = ml_extra_refresh_pipeline.main(
        [
            "--metadata-json",
            str(metadata_path),
            "--metadata-only",
            "--if-changed",
        ]
    )

    out = capsys.readouterr().out.splitlines()
    assert out == [f"Metadata snapshot updated: {metadata_path}"]

    assert recorded_call == {
        "overlay_path": None,
        "baseline_path": None,
        "metadata_path": metadata_path,
        "metadata_only_if_changed": True,
        "update_baseline": False,
    }


def test_main_json_emits_diff_payload(tmp_path: Path, monkeypatch, capsys, snapshot_payload):
    baseline_path = tmp_path / "baseline.json"
    metadata_path = tmp_path / "metadata.json"

    diff_payload = {"matches": True, "added": [], "removed": [], "changed": []}

    class DummyDiff:
        def __init__(self, payload: dict[str, object]):
            self.matches = True
            self._payload = payload

        def to_dict(self) -> dict[str, object]:
            return self._payload

    diff = DummyDiff(diff_payload)

    fake_result = BaselineWorkflowResult(
        report=types.SimpleNamespace(metadata_snapshot=snapshot_payload),
        metadata_snapshot=snapshot_payload,
        baseline_snapshot=snapshot_payload,
        diff=diff,
        metadata_path=metadata_path,
        metadata_updated=None,
        baseline_path=baseline_path,
        baseline_updated=None,
    )

    recorded_call: dict[str, object] = {}

    def fake_run_baseline_workflow(**kwargs):
        recorded_call.update(kwargs)
        return fake_result

    def fail_render(*_args, **_kwargs):  # pragma: no cover - JSON mode bypasses renderer
        raise AssertionError("render_diff_summary should not be called when --json is set")

    monkeypatch.setattr(
        ml_extra_refresh_pipeline, "run_baseline_workflow", fake_run_baseline_workflow
    )
    monkeypatch.setattr(
        ml_extra_refresh_pipeline.sanity_reporting, "render_diff_summary", fail_render
    )

    exit_code = ml_extra_refresh_pipeline.main(
        [
            "--baseline",
            str(baseline_path),
            "--metadata-json",
            str(metadata_path),
            "--json",
        ]
    )

    captured = capsys.readouterr().out.splitlines()
    assert captured[0] == f"Metadata snapshot written to: {metadata_path}"
    payload = json.loads("\n".join(captured[1:]))
    assert payload == diff.to_dict()
    assert recorded_call == {
        "overlay_path": None,
        "baseline_path": baseline_path,
        "metadata_path": metadata_path,
        "metadata_only_if_changed": False,
        "update_baseline": False,
    }
    assert exit_code == 0


def test_main_update_baseline_messages(tmp_path: Path, monkeypatch, capsys, snapshot_payload):
    baseline_path = tmp_path / "baseline.json"
    metadata_path = tmp_path / "metadata.json"

    diff = sanity_core.MetadataDiff(
        matches=False,
        added=(),
        removed=(),
        changed=(),
        baseline_snapshot={"version": "1.1"},
        current_snapshot=snapshot_payload,
    )

    fake_result = BaselineWorkflowResult(
        report=types.SimpleNamespace(metadata_snapshot=snapshot_payload),
        metadata_snapshot=snapshot_payload,
        baseline_snapshot=diff.baseline_snapshot,
        diff=diff,
        metadata_path=metadata_path,
        metadata_updated=True,
        baseline_path=baseline_path,
        baseline_updated=True,
    )

    recorded_call: dict[str, object] = {}

    def fake_run_baseline_workflow(**kwargs):
        recorded_call.update(kwargs)
        return fake_result

    def fake_render(path: Path, diff_payload: sanity_core.MetadataDiff) -> str:
        assert path == baseline_path
        assert diff_payload is diff
        return "rendered diff"

    monkeypatch.setattr(
        ml_extra_refresh_pipeline, "run_baseline_workflow", fake_run_baseline_workflow
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
            "--update-baseline",
        ]
    )

    captured = capsys.readouterr().out.splitlines()
    assert captured[0] == f"Metadata snapshot written to: {metadata_path}"
    assert captured[1] == "rendered diff"
    assert captured[2] == f"Refreshed baseline snapshot at {baseline_path}"
    assert recorded_call == {
        "overlay_path": None,
        "baseline_path": baseline_path,
        "metadata_path": metadata_path,
        "metadata_only_if_changed": False,
        "update_baseline": True,
    }
    assert exit_code == 0

    assert exit_code == 0
