from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from imagebbs import ml_extra_metadata_io
from imagebbs.ml_extra import baseline as baseline_helper


def _read_raw(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_write_metadata_snapshot_creates_file(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    payload = {"value": 42}

    updated = ml_extra_metadata_io.write_metadata_snapshot(path, payload)

    assert updated is True
    assert json.loads(_read_raw(path)) == payload
    assert _read_raw(path).endswith("\n")


def test_write_metadata_snapshot_skips_when_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    payload = {"value": 42}

    ml_extra_metadata_io.write_metadata_snapshot(path, payload)
    original_contents = _read_raw(path)

    updated = ml_extra_metadata_io.write_metadata_snapshot(
        path, payload, only_if_changed=True
    )

    assert updated is False
    assert _read_raw(path) == original_contents


def test_write_metadata_snapshot_overwrites_when_forced(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    payload = {"value": 42}
    ml_extra_metadata_io.write_metadata_snapshot(path, payload)

    new_payload = {"value": 43}
    updated = ml_extra_metadata_io.write_metadata_snapshot(path, new_payload)

    assert updated is True
    assert json.loads(_read_raw(path)) == new_payload


def test_read_metadata_snapshot_returns_parsed_payload(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    payload = {"value": [1, 2, 3]}
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = ml_extra_metadata_io.read_metadata_snapshot(path)

    assert result == payload


def test_run_baseline_workflow_respects_metadata_only_if_changed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    baseline_path = tmp_path / "baseline.json"
    baseline_payload = {"value": 1}
    baseline_path.write_text(json.dumps(baseline_payload), encoding="utf-8")

    metadata_snapshot = {"value": 2}
    write_calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        baseline_helper.sanity_core,
        "run_checks",
        lambda _overlay: types.SimpleNamespace(metadata_snapshot=metadata_snapshot),
    )

    def fake_write(path: Path, payload, *, only_if_changed: bool, **kwargs):
        write_calls.append(
            {
                "path": path,
                "payload": payload,
                "only_if_changed": only_if_changed,
            }
        )
        return True

    monkeypatch.setattr(
        baseline_helper.ml_extra_metadata_io,
        "write_metadata_snapshot",
        fake_write,
    )

    result = baseline_helper.run_baseline_workflow(
        overlay_path=None,
        baseline_path=baseline_path,
        metadata_path=tmp_path / "out.json",
        metadata_only_if_changed=True,
    )

    assert write_calls == [
        {
            "path": tmp_path / "out.json",
            "payload": metadata_snapshot,
            "only_if_changed": True,
        }
    ]
    assert result.metadata_updated is True
    assert result.diff is not None and result.diff.matches is False


def test_run_baseline_workflow_updates_baseline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps({"value": 1}), encoding="utf-8")

    metadata_snapshot = {"value": 2}
    write_calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        baseline_helper.sanity_core,
        "run_checks",
        lambda _overlay: types.SimpleNamespace(metadata_snapshot=metadata_snapshot),
    )

    def fake_write(path: Path, payload, *, only_if_changed: bool, **kwargs):
        write_calls.append(
            {
                "path": path,
                "payload": payload,
                "only_if_changed": only_if_changed,
            }
        )
        return True

    monkeypatch.setattr(
        baseline_helper.ml_extra_metadata_io,
        "write_metadata_snapshot",
        fake_write,
    )

    result = baseline_helper.run_baseline_workflow(
        overlay_path=None,
        baseline_path=baseline_path,
        metadata_path=None,
        metadata_only_if_changed=False,
        update_baseline=True,
    )

    assert write_calls == [
        {
            "path": baseline_path,
            "payload": metadata_snapshot,
            "only_if_changed": True,
        }
    ]
    assert result.baseline_updated is True
