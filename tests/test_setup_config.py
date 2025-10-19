"""Tests for loading modern drive configuration overlays."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import (  # noqa: E402
    SetupDefaults,
    SetupConfig,
    bootstrap_device_context,
    derive_drive_inventory,
    load_drive_config,
)
from scripts.prototypes.setup_defaults import (  # noqa: E402
    CommodoreDeviceDrive,
    DEFAULT_MODEM_BAUD_LIMIT,
    FilesystemDriveLocator,
)
from scripts.prototypes.device_context import DiskDrive  # noqa: E402


@pytest.fixture()
def sample_config(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "relative_drive").mkdir()
    absolute_drive = tmp_path / "absolute_drive"
    absolute_drive.mkdir()

    config_path = config_dir / "storage.toml"
    config_path.write_text(
        "[slots]\n"
        "5 = \"relative_drive\"\n"
        f"6 = \"{absolute_drive}\"\n",
        encoding="utf-8",
    )
    return config_path


def test_load_drive_config_merges_stub_defaults(sample_config: Path) -> None:
    config = load_drive_config(sample_config)
    assert isinstance(config, SetupConfig)

    assignments = config.drives
    lookup = {assignment.slot: assignment for assignment in assignments}

    defaults = SetupDefaults.stub()
    assert len(assignments) >= len(defaults.drives)
    assert defaults.modem.baud_limit == DEFAULT_MODEM_BAUD_LIMIT

    for slot in (1, 2, 3, 4):
        locator = lookup[slot].locator
        assert isinstance(locator, CommodoreDeviceDrive)

    fs_five = lookup[5].locator
    fs_six = lookup[6].locator
    assert isinstance(fs_five, FilesystemDriveLocator)
    assert isinstance(fs_six, FilesystemDriveLocator)
    assert fs_five.path == (sample_config.parent / "relative_drive").resolve()
    assert fs_six.path == (sample_config.parent.parent / "absolute_drive").resolve()

    inventory = derive_drive_inventory(assignments)
    assert inventory == defaults.drive_inventory
    assert config.modem_baud_limit is None


def test_bootstrap_device_context_registers_filesystem_drives(sample_config: Path) -> None:
    config = load_drive_config(sample_config)
    context = bootstrap_device_context(config.drives)

    drive5 = context.devices.get("drive5")
    drive6 = context.devices.get("drive6")
    assert isinstance(drive5, DiskDrive)
    assert isinstance(drive6, DiskDrive)

    lookup = {assignment.slot: assignment for assignment in config.drives}
    assert drive5.root == lookup[5].locator.path
    assert drive6.root == lookup[6].locator.path

    # Commodore-backed slots are intentionally not mounted as host paths.
    assert "drive1" not in context.devices


def test_load_drive_config_accepts_string_slot_keys(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "string_drive").mkdir()

    config_path = config_dir / "storage.toml"
    config_path.write_text(
        "[slots]\n" '"7" = "string_drive"\n',
        encoding="utf-8",
    )

    assignments = load_drive_config(config_path).drives
    lookup = {assignment.slot: assignment for assignment in assignments}

    fs_seven = lookup[7].locator
    assert isinstance(fs_seven, FilesystemDriveLocator)
    assert fs_seven.path == (config_dir / "string_drive").resolve()


def test_load_drive_config_rejects_non_positive_slot(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "storage.toml"
    config_path.write_text(
        "[slots]\n" "0 = 'invalid'\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="drive slot numbers must be positive"):
        load_drive_config(config_path)


def test_load_drive_config_parses_ampersand_overrides(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "drive").mkdir()

    config_path = config_dir / "storage.toml"
    config_path.write_text(
        "[slots]\n"
        "8 = \"drive\"\n\n"
        "[ampersand_overrides]\n"
        "0 = \"package.module:callable\"\n"
        '"0x21" = "pkg.mod.attr"\n',
        encoding="utf-8",
    )

    config = load_drive_config(config_path)
    assert config.ampersand_overrides == {0: "package.module:callable", 0x21: "pkg.mod.attr"}
    assert config.modem_baud_limit is None


def test_load_drive_config_parses_modem_baud_limit(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "drive").mkdir()

    config_path = config_dir / "storage.toml"
    config_path.write_text(
        "[slots]\n"
        "8 = \"drive\"\n\n"
        "[modem]\n"
        "baud_limit = 2400\n",
        encoding="utf-8",
    )

    config = load_drive_config(config_path)
    assert config.modem_baud_limit == 2400
