"""Prototype host device/context abstractions for the ImageBBS port.

This module sketches a modern host-side equivalent of the Commodore device
multiplexer that ImageBBS exercises through `SETLFS` and `PRINT#` calls.  The
prototype is intentionally small; it focuses on the interactions we need to
validate while building the DOS command helper and overlay loader mentioned in
iteration 08's follow-ups.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Dict, Iterable, Iterator, Optional, Tuple

from .setup_defaults import DriveAssignment, FilesystemDriveLocator
from .console_renderer import PetsciiScreen


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


class ConsoleChannel(LogicalChannel):
    """Logical channel that mirrors writes to the host console."""

    def __init__(self, descriptor: ChannelDescriptor, console: "Console") -> None:
        super().__init__(descriptor)
        self._console = console

    def write(self, data: str | bytes) -> None:
        if isinstance(data, bytes):
            text = data.decode("latin-1", errors="replace")
        else:
            text = data
        super().write(text)
        self._console.write(data)


class Console(Device):
    name = "console"

    def __init__(self, screen: PetsciiScreen | None = None) -> None:
        self.output: Deque[str] = deque()
        self._screen = screen or PetsciiScreen()
        self._transcript: bytearray = bytearray()

    def open(self, descriptor: ChannelDescriptor) -> LogicalChannel:
        return ConsoleChannel(descriptor, self)

    def write(self, data: str | bytes) -> None:
        if isinstance(data, bytes):
            payload = data
            text = data.decode("latin-1", errors="replace")
        else:
            payload = data.encode("latin-1", errors="replace")
            text = data
        self.output.append(text)
        self._transcript.extend(payload)
        self._screen.write(payload)

    @property
    def screen(self) -> PetsciiScreen:
        """Return the backing PETSCII screen buffer."""

        return self._screen

    @property
    def screen_colour(self) -> int:
        """Return the current foreground colour."""

        return self._screen.screen_colour

    @property
    def background_colour(self) -> int:
        """Return the current background colour."""

        return self._screen.background_colour

    @property
    def border_colour(self) -> int:
        """Return the current border colour."""

        return self._screen.border_colour

    @property
    def transcript(self) -> str:
        """Return the accumulated transcript as a decoded string."""

        return "".join(self.output)

    @property
    def transcript_bytes(self) -> bytes:
        """Return the accumulated transcript as raw bytes."""

        return bytes(self._transcript)


class ModemTransport(ABC):
    """Strategy object that hides the underlying modem transport."""

    def open(self) -> None:
        """Prepare the transport for use."""

        pass

    @abstractmethod
    def send(self, data: str) -> None:
        """Transmit data toward the remote peer."""

    @abstractmethod
    def receive(self, size: Optional[int] = None) -> str:
        """Return data provided by the remote peer."""

    def feed(self, data: str) -> None:
        """Inject inbound data for transports that emulate remote peers."""

        raise NotImplementedError("transport does not support manual inbound data")

    def collect_transmit(self) -> str:
        """Expose transmitted payloads for inspection in tests."""

        raise NotImplementedError("transport does not expose transmitted payloads")

    def close(self) -> None:
        """Release any transport resources."""

        pass


class LoopbackModemTransport(ModemTransport):
    """In-memory transport that mirrors the historical modem façade."""

    def __init__(self) -> None:
        self._inbound: Deque[str] = deque()
        self._outbound: Deque[str] = deque()

    def open(self) -> None:
        self._inbound.clear()
        self._outbound.clear()

    def send(self, data: str) -> None:
        self._outbound.extend(data)

    def receive(self, size: Optional[int] = None) -> str:
        if size is None:
            size = len(self._inbound)
        chars: Iterable[str] = (
            self._inbound.popleft() for _ in range(min(size, len(self._inbound)))
        )
        return "".join(chars)

    def feed(self, data: str) -> None:
        self._inbound.extend(data)

    def collect_transmit(self) -> str:
        payload = "".join(self._outbound)
        self._outbound.clear()
        return payload

    def close(self) -> None:
        self._inbound.clear()
        self._outbound.clear()


class ModemChannel(LogicalChannel):
    """Logical channel that proxies writes to a modem transport."""

    def __init__(self, descriptor: ChannelDescriptor, transport: ModemTransport) -> None:
        super().__init__(descriptor)
        self._transport = transport

    def write(self, data: str) -> None:
        super().write(data)
        self._transport.send(data)


class Modem(Device):
    name = "modem"

    def __init__(self, transport: Optional[ModemTransport] = None) -> None:
        self.transport = transport or LoopbackModemTransport()

    def open(self, descriptor: ChannelDescriptor) -> LogicalChannel:
        self.transport.open()
        return ModemChannel(descriptor, self.transport)

    def enqueue_receive(self, data: str) -> None:
        try:
            self.transport.feed(data)
        except NotImplementedError as exc:
            raise DeviceError("transport does not allow manual inbound data") from exc

    def read(self, size: Optional[int] = None) -> str:
        return self.transport.receive(size)

    def collect_transmit(self) -> str:
        try:
            return self.transport.collect_transmit()
        except NotImplementedError as exc:
            raise DeviceError("transport does not expose transmitted payloads") from exc

    def close(self) -> None:
        self.transport.close()


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


def bootstrap_device_context(assignments: Iterable[DriveAssignment]) -> DeviceContext:
    """Instantiate a device context with modern drive mappings."""

    context = DeviceContext()
    context.register("console", Console())
    context.register("modem", Modem())
    for assignment in assignments:
        locator = assignment.locator
        if isinstance(locator, FilesystemDriveLocator):
            context.register(f"drive{assignment.slot}", DiskDrive(locator.path))
    return context


__all__ = [
    "ChannelDescriptor",
    "Console",
    "DeviceContext",
    "DeviceError",
    "DiskDrive",
    "bootstrap_device_context",
    "LogicalChannel",
    "LoopbackModemTransport",
    "Modem",
    "ModemChannel",
    "ModemTransport",
]
