"""Tests for the metadata snapshot JSON helpers."""

import json

from imagebbs.ml_extra_metadata_io import (
    PRETTY_PRINT_THRESHOLD_BYTES,
    write_metadata_snapshot,
)


def test_write_metadata_snapshot_pretty_branch_with_newline(tmp_path):
    path = tmp_path / "snapshot.json"
    payload = {"alpha": 1, "beta": {"gamma": 2}}

    wrote = write_metadata_snapshot(path, payload, only_if_changed=True)
    assert wrote is True

    expected = json.dumps(payload, indent=2) + "\n"
    assert path.read_text(encoding="utf-8") == expected

    wrote_again = write_metadata_snapshot(path, payload, only_if_changed=True)
    assert wrote_again is False


def test_write_metadata_snapshot_compact_branch_respects_threshold(tmp_path):
    path = tmp_path / "snapshot.json"
    payload = {"payload": ["x" * 32 for _ in range(32)]}

    wrote = write_metadata_snapshot(path, payload, pretty_threshold_bytes=64)
    assert wrote is True

    expected = json.dumps(payload, indent=None) + "\n"
    assert path.read_text(encoding="utf-8") == expected

    wrote_again = write_metadata_snapshot(
        path,
        payload,
        only_if_changed=True,
        pretty_threshold_bytes=64,
    )
    assert wrote_again is False


def test_write_metadata_snapshot_allows_threshold_override(tmp_path):
    path = tmp_path / "snapshot.json"
    payload = {"payload": ["x" * 32 for _ in range(32)]}

    wrote = write_metadata_snapshot(
        path,
        payload,
        indent=4,
        pretty_threshold_bytes=None,
    )
    assert wrote is True

    expected = json.dumps(payload, indent=4) + "\n"
    assert path.read_text(encoding="utf-8") == expected

    assert PRETTY_PRINT_THRESHOLD_BYTES == 131_072
