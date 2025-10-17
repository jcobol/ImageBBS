"""Tests for loading modern drive configuration overlays."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import (  # noqa: E402
    SetupDefaults,
    bootstrap_device_context,
    derive_drive_inventory,
    load_drive_config,
)
from scripts.prototypes.setup_defaults import (  # noqa: E402
    CommodoreDeviceDrive,
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
    assignments = load_drive_config(sample_config)
    lookup = {assignment.slot: assignment for assignment in assignments}

    defaults = SetupDefaults.stub()
    assert len(assignments) >= len(defaults.drives)

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


def test_bootstrap_device_context_registers_filesystem_drives(sample_config: Path) -> None:
    assignments = load_drive_config(sample_config)
    context = bootstrap_device_context(assignments)

    drive5 = context.devices.get("drive5")
    drive6 = context.devices.get("drive6")
    assert isinstance(drive5, DiskDrive)
    assert isinstance(drive6, DiskDrive)

    lookup = {assignment.slot: assignment for assignment in assignments}
    assert drive5.root == lookup[5].locator.path
    assert drive6.root == lookup[6].locator.path

    # Commodore-backed slots are intentionally not mounted as host paths.
    assert "drive1" not in context.devices
