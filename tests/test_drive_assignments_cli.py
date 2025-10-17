"""Integration coverage for the drive assignments CLI helper."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import SetupDefaults  # noqa: E402
from scripts.prototypes import drive_assignments_cli  # noqa: E402


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


def test_cli_reports_filesystem_slots(capsys: pytest.CaptureFixture[str], sample_config: Path) -> None:
    defaults = SetupDefaults.stub()

    exit_code = drive_assignments_cli.main([str(sample_config)])
    assert exit_code == 0

    output = capsys.readouterr().out.splitlines()
    assert output[0] == "Configured drive slots:"

    # Commodore-backed slots should still be listed for context.
    expected_legacy = {
        f"slot {assignment.slot}: cbm device {assignment.device} drive {assignment.drive}"
        for assignment in defaults.drives
        if assignment.locator is not None and assignment.locator.scheme == "cbm"
    }
    assert expected_legacy <= set(output)

    # Filesystem slots should include their resolved host paths and drive labels.
    expected_relative = (sample_config.parent / "relative_drive").resolve()
    expected_absolute = (sample_config.parent.parent / "absolute_drive").resolve()
    assert (
        f"slot 5 (drive5): filesystem -> {expected_relative}" in output
    ), output
    assert (
        f"slot 6 (drive6): filesystem -> {expected_absolute}" in output
    ), output


def test_cli_rejects_missing_config(tmp_path: Path) -> None:
    missing = tmp_path / "missing.toml"
    with pytest.raises(SystemExit, match="configuration file not found"):
        drive_assignments_cli.main([str(missing)])
