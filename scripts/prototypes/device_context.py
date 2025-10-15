"""Prototype host device/context abstractions for the ImageBBS port.

This module sketches a modern host-side equivalent of the Commodore device
multiplexer that ImageBBS exercises through `SETLFS` and `PRINT#` calls.  The
prototype is intentionally small; it focuses on the interactions we need to
validate while building the DOS command helper and overlay loader mentioned in
iteration 08's follow-ups.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Dict, Iterable, Iterator, Optional, Tuple


class DeviceError(RuntimeError):
    """Raised when a device or channel is misused."""


@dataclass
class ChannelDescriptor:
    """Describes an open logical file on a Commodore-style device."""

    device: str
    logical_number: int
    secondary_address: int


class LogicalChannel:
    """Represents the data stream ImageBBS would associate with a logical file."""

    def __init__(self, descriptor: ChannelDescriptor) -> None:
        self.descriptor = descriptor
        self._buffer: Deque[str] = deque()

    def write(self, data: str) -> None:
        self._buffer.extend(data)

    def read(self, size: Optional[int] = None) -> str:
        if size is None:
            size = len(self._buffer)
        chars: Iterable[str] = (self._buffer.popleft() for _ in range(min(size, len(self._buffer))))
        return "".join(chars)

    def dump(self) -> str:
        """Expose the buffered payload for inspection in tests."""

        return "".join(self._buffer)


class Device:
    """Base class for host devices."""

    name: str = "device"

    def open(self, descriptor: ChannelDescriptor) -> LogicalChannel:
        raise NotImplementedError

    def command(self, raw: str) -> str:
        """Handle a raw DOS command sent to the device."""

        raise DeviceError(f"{self.name}: command channel not supported")


class DiskDrive(Device):
    name = "disk"

    def __init__(self, root: Path) -> None:
        self.root = root

    def open(self, descriptor: ChannelDescriptor) -> LogicalChannel:
        channel = LogicalChannel(descriptor)
        if descriptor.secondary_address == 15:
            # Command channel; mirror Commodore behaviour by preloading the DOS prompt.
            channel.write("00,OK,00,00\r")
        return channel

    def command(self, raw: str) -> str:
        verb, *args = raw.strip().split()
        verb = verb.upper()
        if verb == "I":
            return "00,OK,00,00"
        if verb == "$":
            # Simplistic directory listing for prototype purposes.
            entries = sorted(p.name for p in self.root.glob("**/*") if p.is_file())
            listing = "\r".join(entries)
            return f"00,{listing or '0 FILES'},00,00"
        if verb == "S" and args:
            # Scratch/delete command.
            (target,) = args
            for match in self.root.glob(target):
                if match.is_file():
                    match.unlink()
            return "00,OK,00,00"
        raise DeviceError(f"disk: unsupported command '{raw}'")


class Console(Device):
    name = "console"

    def __init__(self) -> None:
        self.output: Deque[str] = deque()

    def open(self, descriptor: ChannelDescriptor) -> LogicalChannel:
        return LogicalChannel(descriptor)

    def write(self, data: str) -> None:
        self.output.append(data)


class Modem(Device):
    name = "modem"

    def __init__(self) -> None:
        self.buffer: Deque[str] = deque()

    def open(self, descriptor: ChannelDescriptor) -> LogicalChannel:
        return LogicalChannel(descriptor)

    def enqueue_receive(self, data: str) -> None:
        self.buffer.extend(data)

    def read(self, size: Optional[int] = None) -> str:
        if size is None:
            size = len(self.buffer)
        chars: Iterable[str] = (self.buffer.popleft() for _ in range(min(size, len(self.buffer))))
        return "".join(chars)


class DeviceContext:
    """Dispatcher that mirrors the Commodore `SETLFS` triple."""

    def __init__(self) -> None:
        self.devices: Dict[str, Device] = {}
        self.channels: Dict[Tuple[int, int], LogicalChannel] = {}
        self.command_channels: Dict[int, LogicalChannel] = {}
        self.directory_cache: Dict[str, Tuple[str, ...]] = defaultdict(tuple)

    def register(self, name: str, device: Device) -> None:
        self.devices[name] = device

    def open(self, device_name: str, logical_number: int, secondary_address: int) -> LogicalChannel:
        if device_name not in self.devices:
            raise DeviceError(f"no such device '{device_name}'")
        descriptor = ChannelDescriptor(device=device_name, logical_number=logical_number, secondary_address=secondary_address)
        device = self.devices[device_name]
        channel = device.open(descriptor)
        self.channels[(logical_number, secondary_address)] = channel
        if secondary_address == 15:
            self.command_channels[logical_number] = channel
        return channel

    def close(self, logical_number: int, secondary_address: int) -> None:
        self.channels.pop((logical_number, secondary_address), None)
        if secondary_address == 15:
            self.command_channels.pop(logical_number, None)

    def issue_command(self, logical_number: int, command: str) -> str:
        channel = self.command_channels.get(logical_number)
        if channel is None:
            raise DeviceError(f"logical {logical_number}: no command channel open")
        device = self.devices[channel.descriptor.device]
        response = device.command(command)
        channel.write(response + "\r")
        return response

    def read_directory(self, device_name: str, refresh: bool = False) -> Tuple[str, ...]:
        if refresh or not self.directory_cache[device_name]:
            response = self.issue_command(15, "$")
            # Response is "status, listing"; we only care about listing portion.
            parts = response.split(",", maxsplit=3)
            listing = tuple(parts[1].split("\r")) if len(parts) > 1 else tuple()
            self.directory_cache[device_name] = listing
        return self.directory_cache[device_name]

    def iter_open_channels(self) -> Iterator[ChannelDescriptor]:
        for channel in self.channels.values():
            yield channel.descriptor


__all__ = [
    "ChannelDescriptor",
    "Console",
    "DeviceContext",
    "DeviceError",
    "DiskDrive",
    "LogicalChannel",
    "Modem",
]
