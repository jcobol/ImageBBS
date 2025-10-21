from __future__ import annotations

from pathlib import Path

from imagebbs.device_context import (
    DeviceContext,
    DiskDrive,
    SequentialFileChannel,
)


def _bootstrap_context(root: Path, slot: int = 8) -> DeviceContext:
    context = DeviceContext()
    device_name = context.drive_device_name(slot)
    drive = DiskDrive(root)
    context.register(device_name, drive)
    context.open(device_name, slot, 15)
    return context


def test_sequential_file_roundtrip(tmp_path: Path) -> None:
    context = _bootstrap_context(tmp_path)
    slot = 8

    write_channel = context.open_file(slot, 1, "GREETING,S,W", 1)
    assert isinstance(write_channel, SequentialFileChannel)
    host_path = tmp_path / "GREETING"

    write_channel.write("HELLO\rWORLD\r")
    context.close(1, 1)

    assert host_path.exists()
    assert host_path.read_bytes() == b"HELLO\nWORLD\n"

    read_channel = context.open_file(slot, 2, "GREETING,S,R", 2)
    contents = read_channel.read()
    context.close(2, 2)

    assert contents == "HELLO\rWORLD\r"

    response = context.issue_command(slot, "S:GREETING")
    assert response == "00,OK,00,00"
    assert not host_path.exists()
