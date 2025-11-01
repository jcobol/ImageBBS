from __future__ import annotations

import json
import types
from pathlib import Path

from imagebbs import (
    ml_extra_metadata_io,
    ml_extra_refresh_pipeline,
    ml_extra_snapshot_guard,
)
from imagebbs.ml_extra.sanity import core as sanity_core


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


def test_refresh_pipeline_if_changed_uses_conditional_write(monkeypatch, tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"value": 1}), encoding="utf-8")

    write_calls: list[dict[str, object]] = []

    def fake_run_checks(_overlay):
        return types.SimpleNamespace(metadata_snapshot={"value": 2})

    def fake_diff(baseline, snapshot):
        return sanity_core.MetadataDiff(
            matches=True,
            added=(),
            removed=(),
            changed=(),
            baseline_snapshot=baseline,
            current_snapshot=snapshot,
        )

    def fake_write(path: Path, payload, *, only_if_changed: bool, indent: int | None = 2):
        write_calls.append(
            {
                "path": path,
                "payload": payload,
                "only_if_changed": only_if_changed,
            }
        )
        return True

    monkeypatch.setattr(
        "imagebbs.ml_extra_refresh_pipeline.sanity_core.run_checks", fake_run_checks
    )
    monkeypatch.setattr(
        "imagebbs.ml_extra_refresh_pipeline.sanity_core.diff_metadata_snapshots",
        fake_diff,
    )
    monkeypatch.setattr(
        "imagebbs.ml_extra_refresh_pipeline.ml_extra_metadata_io.write_metadata_snapshot",
        fake_write,
    )

    exit_code = ml_extra_refresh_pipeline.main(
        ["--baseline", str(baseline), "--metadata-json", str(tmp_path / "out.json"), "--if-changed"]
    )

    assert exit_code == 0
    assert write_calls == [
        {
            "path": tmp_path / "out.json",
            "payload": {"value": 2},
            "only_if_changed": True,
        }
    ]


def test_snapshot_guard_update_baseline_uses_conditional_write(monkeypatch, tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"value": 1}), encoding="utf-8")

    write_calls: list[dict[str, object]] = []

    def fake_run_checks(_overlay):
        return types.SimpleNamespace(metadata_snapshot={"value": 2})

    def fake_diff(baseline, snapshot):
        return sanity_core.MetadataDiff(
            matches=True,
            added=(),
            removed=(),
            changed=(),
            baseline_snapshot=baseline,
            current_snapshot=snapshot,
        )

    def fake_write(path: Path, payload, *, only_if_changed: bool, indent: int | None = 2):
        write_calls.append(
            {
                "path": path,
                "payload": payload,
                "only_if_changed": only_if_changed,
            }
        )
        return True

    monkeypatch.setattr(
        "imagebbs.ml_extra_snapshot_guard.sanity_core.run_checks", fake_run_checks
    )
    monkeypatch.setattr(
        "imagebbs.ml_extra_snapshot_guard.sanity_core.diff_metadata_snapshots",
        fake_diff,
    )
    monkeypatch.setattr(
        "imagebbs.ml_extra_snapshot_guard.ml_extra_metadata_io.write_metadata_snapshot",
        fake_write,
    )

    exit_code = ml_extra_snapshot_guard.main(
        ["--baseline", str(baseline), "--update-baseline"]
    )

    assert exit_code == 0
    assert write_calls == [
        {
            "path": baseline,
            "payload": {"value": 2},
            "only_if_changed": True,
        }
    ]
