from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from imagebbs import drive_assignments_cli
from imagebbs.drive_assignments_cli import DiskDrive, main, render_assignments
from imagebbs.setup_defaults import (
    CommodoreDeviceDrive,
    DriveAssignment,
    FilesystemDriveLocator,
)


@dataclass(frozen=True)
class CustomLocator:
    scheme: str = "custom"

    def describe(self) -> str:
        return "custom description"


def test_render_assignments_formats_all_locators(monkeypatch: pytest.MonkeyPatch) -> None:
    assignments = [
        DriveAssignment(slot=1, locator=FilesystemDriveLocator(path=Path("/configured/path"))),
        DriveAssignment(slot=2, locator=CommodoreDeviceDrive(device=8, drive=1)),
        DriveAssignment(slot=3, locator=None),
        DriveAssignment(slot=4, locator=CustomLocator()),
    ]
    overrides = {0x10: "ampersand.module:flag", 0x02: "math:sin"}

    class FakeDiskDrive(DiskDrive):  # type: ignore[misc]
        def __init__(self, root: Path) -> None:
            self.root = root

    class FakeContext:
        def __init__(self) -> None:
            self.devices = {"drive1": FakeDiskDrive(Path("/mounted/path"))}

    def fake_bootstrap(assignments_iter, *, ampersand_overrides):
        assert list(assignments_iter) == assignments
        assert ampersand_overrides is overrides
        return FakeContext()

    monkeypatch.setattr(drive_assignments_cli, "bootstrap_device_context", fake_bootstrap)

    lines = render_assignments(assignments, ampersand_overrides=overrides)

    assert lines == [
        "Configured drive slots:",
        "slot 1 (drive1): filesystem -> /configured/path (mounted at /mounted/path)",
        "slot 2: cbm device 8 drive 1",
        "slot 3: <unassigned>",
        "slot 4: custom -> custom description",
        "",
        "Ampersand overrides:",
        "flag 0x02 -> math:sin",
        "flag 0x10 -> ampersand.module:flag",
    ]


def create_sample_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "config.toml"
    slot1 = tmp_path / "drive1"
    slot4 = tmp_path / "drive4"
    config_path.write_text(
        "[slots]\n"
        f"1 = \"{slot1}\"\n"
        f"4 = \"{slot4}\"\n"
        "\n"
        "[ampersand_overrides]\n"
        "0x10 = \"math:cos\"\n",
        encoding="utf-8",
    )
    return config_path


def test_main_reports_assignments_and_overrides(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = create_sample_config(tmp_path)
    slot1 = tmp_path / "drive1"
    slot4 = tmp_path / "drive4"

    exit_code = main([str(config_path)])
    assert exit_code == 0

    output_lines = capsys.readouterr().out.strip().splitlines()
    assert output_lines[0] == "Configured drive slots:"

    resolved_slot1 = slot1.resolve()
    resolved_slot4 = slot4.resolve()
    assert (
        f"slot 1 (drive1): filesystem -> {resolved_slot1}" in output_lines
    ), output_lines
    assert (
        f"slot 4 (drive4): filesystem -> {resolved_slot4}" in output_lines
    ), output_lines

    assert "Ampersand overrides:" in output_lines
    section = output_lines.index("Ampersand overrides:")
    assert output_lines[section + 1] == "flag 0x10 -> math:cos"


def test_main_can_emit_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config_path = create_sample_config(tmp_path)

    exit_code = main(["--json", str(config_path)])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert set(payload.keys()) == {"slots", "ampersand_overrides"}

    slots = payload["slots"]
    assert isinstance(slots, list)
    slot_records = {slot["slot"]: slot for slot in slots}
    assert {1, 4} <= set(slot_records)

    slot1_record = slot_records[1]
    assert slot1_record["scheme"] == "fs"
    assert slot1_record["configured_path"].endswith("drive1")
    assert slot1_record.get("resolved_host_path")

    slot4_record = slot_records[4]
    assert slot4_record["scheme"] == "fs"
    assert slot4_record["configured_path"].endswith("drive4")

    overrides = payload["ampersand_overrides"]
    assert overrides == [{"flag": 0x10, "module": "math:cos"}]
