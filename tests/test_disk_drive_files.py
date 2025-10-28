from __future__ import annotations

from pathlib import Path

from imagebbs.device_context import (
    DeviceContext,
    DiskDrive,
    LoopbackModemTransport,
    Modem,
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


def test_disk_drive_command_responses(tmp_path: Path) -> None:
    context = _bootstrap_context(tmp_path)
    slot = 8

    command_channel = context.command_channels[slot]
    assert command_channel.dump().endswith("00,OK,00,00\r")

    initialise_response = context.issue_command(slot, "I")
    assert initialise_response == "00,OK,00,00"
    assert command_channel.dump().endswith("00,OK,00,00\r")

    host_file = tmp_path / "DOSFILE"
    host_file.write_text("PAYLOAD", encoding="latin-1")

    directory_response = context.issue_command(slot, "$")
    assert directory_response.startswith("00,")
    assert "DOSFILE" in directory_response

    scratch_response = context.issue_command(slot, "S:DOSFILE")
    assert scratch_response == "00,OK,00,00"
    assert not host_file.exists()


def test_loopback_modem_transport_roundtrip() -> None:
    context = DeviceContext()
    modem = context.register_modem_device()
    assert isinstance(modem, Modem)
    assert isinstance(modem.transport, LoopbackModemTransport)

    channel = context.open(modem.name, 2, 0)
    channel.write("HELLO")
    assert modem.collect_transmit() == "HELLO"

    modem.enqueue_receive("WORLD")
    assert modem.read() == "WORLD"

    context.close(2, 0)
