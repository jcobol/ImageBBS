"""Regression tests for the TOML setup configuration loader."""
from __future__ import annotations

from pathlib import Path

import pytest

from imagebbs.setup_config import load_drive_config
from imagebbs.setup_defaults import (
    DriveAssignment,
    FilesystemDriveLocator,
    SetupConfig,
    SetupDefaults,
)


def test_load_drive_config_applies_overrides(tmp_path: Path) -> None:
    defaults = SetupDefaults.stub()

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    relative_drive = config_dir / "relative"
    relative_drive.mkdir()
    absolute_drive = tmp_path / "absolute"
    absolute_drive.mkdir()

    config_path = config_dir / "storage.toml"
    config_path.write_text(
        "[slots]\n"
        "1 = \"relative\"\n"
        f"9 = \"{absolute_drive}\"\n\n"
        "[ampersand_overrides]\n"
        "0 = \"package.module:callable\"\n"
        '"0x20" = "pkg.mod.attr"\n\n'
        "[modem]\n"
        "baud_limit = \"2400\"\n",
        encoding="utf-8",
    )

    config = load_drive_config(config_path)
    assert isinstance(config, SetupConfig)

    expected_drives = list(defaults.drives)
    expected_drives[0] = DriveAssignment(
        slot=1,
        locator=FilesystemDriveLocator(path=relative_drive.resolve()),
    )
    expected_drives.append(
        DriveAssignment(
            slot=9,
            locator=FilesystemDriveLocator(path=absolute_drive.resolve()),
        )
    )

    assert config.drives == tuple(expected_drives)
    assert config.ampersand_overrides == {0: "package.module:callable", 0x20: "pkg.mod.attr"}
    assert config.modem_baud_limit == 2400


def test_load_drive_config_accepts_table_slots(tmp_path: Path) -> None:
    defaults = SetupDefaults.stub()

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "relative").mkdir()
    read_only_dir = tmp_path / "read-only"
    read_only_dir.mkdir()
    extra_dir = config_dir / "extra"
    extra_dir.mkdir()

    config_path = config_dir / "storage.toml"
    config_path.write_text(
        "[slots]\n"
        "1 = \"relative\"\n"
        f"2 = {{ path = \"{read_only_dir}\", read_only = true }}\n"
        "9 = { path = \"extra\" }\n",
        encoding="utf-8",
    )

    config = load_drive_config(config_path)

    expected_drives = {assignment.slot: assignment for assignment in defaults.drives}
    expected_drives[1] = DriveAssignment(
        slot=1,
        locator=FilesystemDriveLocator(path=(config_dir / "relative").resolve()),
    )
    expected_drives[2] = DriveAssignment(
        slot=2,
        locator=FilesystemDriveLocator(path=read_only_dir.resolve(), read_only=True),
    )
    expected_drives[9] = DriveAssignment(
        slot=9,
        locator=FilesystemDriveLocator(path=extra_dir.resolve()),
    )

    assignments = {assignment.slot: assignment for assignment in config.drives}

    assert assignments.keys() == expected_drives.keys()
    for slot, expected in expected_drives.items():
        assert assignments[slot] == expected

    assert assignments[2].read_only is True
    assert assignments[1].read_only is False


@pytest.mark.parametrize(
    "config_text",
    [
        "slots = \"not-a-table\"\n",
        "[slots]\n1 = []\n",
    ],
)
def test_load_drive_config_rejects_invalid_slots(tmp_path: Path, config_text: str) -> None:
    config_path = tmp_path / "storage.toml"
    config_path.write_text(config_text, encoding="utf-8")

    with pytest.raises((TypeError, ValueError)):
        load_drive_config(config_path)


@pytest.mark.parametrize(
    "overrides, expected_exception",
    [
        ("ampersand_overrides = []\n", ValueError),
        ("[ampersand_overrides]\n0 = 1\n", TypeError),
        ("[ampersand_overrides]\n-1 = \"callable\"\n", ValueError),
    ],
)
def test_load_drive_config_validates_ampersand_overrides(
    tmp_path: Path, overrides: str, expected_exception: type[Exception]
) -> None:
    (tmp_path / "drive").mkdir()
    config_path = tmp_path / "storage.toml"
    config_path.write_text(
        overrides + "\n[slots]\n1 = \"drive\"\n",
        encoding="utf-8",
    )

    with pytest.raises(expected_exception):
        load_drive_config(config_path)
