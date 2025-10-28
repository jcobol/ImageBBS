from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from imagebbs.storage_config import (
    StorageConfigError,
    load_storage_config,
    validate_filename,
)


def write_config(tmp_path: Path, body: str) -> Path:
    config_path = tmp_path / "storage.toml"
    config_path.write_text(textwrap.dedent(body), encoding="utf-8")
    return config_path


def test_load_storage_config_infers_default_drive_for_single_entry(tmp_path: Path) -> None:
    drive_root = tmp_path / "drive8"
    drive_root.mkdir()
    config_path = write_config(
        tmp_path,
        """
        [storage]
        [[storage.drives]]
        drive = 8
        path = "drive8"
        """,
    )

    storage = load_storage_config(config_path)

    assert storage.default_drive == 8
    mapping = storage.require_drive(8)
    assert mapping.root == drive_root.resolve()
    assert not mapping.read_only
    assert storage.resolve("FILE", drive=8) == drive_root / "FILE"


def test_resolve_requires_drive_when_no_default(tmp_path: Path) -> None:
    (tmp_path / "drive8").mkdir()
    (tmp_path / "drive9").mkdir()
    config_path = write_config(
        tmp_path,
        """
        [storage]
        [[storage.drives]]
        drive = 8
        path = "drive8"
        [[storage.drives]]
        drive = 9
        path = "drive9"
        """,
    )

    storage = load_storage_config(config_path)

    with pytest.raises(StorageConfigError, match="no drive specified"):
        storage.resolve("FILE")

    resolved = storage.resolve("FILE", drive=9)
    assert resolved == (tmp_path / "drive9" / "FILE")


def test_validate_save_target_blocks_read_only(tmp_path: Path) -> None:
    writable = tmp_path / "write"
    readonly = tmp_path / "readonly"
    writable.mkdir()
    readonly.mkdir()
    config_path = write_config(
        tmp_path,
        """
        [storage]
        default_drive = "9"

        [[storage.drives]]
        drive = 8
        path = "write"

        [[storage.drives]]
        drive = 9
        path = "readonly"
        read_only = true
        """,
    )

    storage = load_storage_config(config_path)

    assert storage.default_drive == 9
    assert storage.require_drive(9).read_only is True

    with pytest.raises(StorageConfigError, match="read-only"):
        storage.validate_save_target("FILE")

    target = storage.validate_save_target("FILE", drive=8)
    assert target == writable / "FILE"


def test_invalid_drive_entry_reports_missing_directory(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        """
        [storage]
        [[storage.drives]]
        drive = 8
        path = "missing"
        """,
    )

    with pytest.raises(StorageConfigError, match="does not exist"):
        load_storage_config(config_path)


def test_invalid_default_drive_reference(tmp_path: Path) -> None:
    (tmp_path / "drive8").mkdir()
    config_path = write_config(
        tmp_path,
        """
        [storage]
        default_drive = 9

        [[storage.drives]]
        drive = 8
        path = "drive8"
        """,
    )

    with pytest.raises(StorageConfigError, match="does not match a configured drive"):
        load_storage_config(config_path)


@pytest.mark.parametrize(
    "candidate, message",
    [
        ("bad/name", "forbidden path characters"),
        (" bad", "trimming would alter"),
        ("", "must not be empty"),
    ],
)
def test_validate_filename_errors(candidate: str, message: str) -> None:
    with pytest.raises(StorageConfigError, match=message):
        validate_filename(candidate)
