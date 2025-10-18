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
from types import MappingProxyType
from typing import Deque, Dict, Iterable, Iterator, Mapping, Optional, Tuple

from .setup_defaults import DriveAssignment, FilesystemDriveLocator
from .console_renderer import (
    FlagGlyphMapping,
    GlyphRun,
    OverlayGlyphLookup,
    PetsciiScreen,
    VicRegisterTimelineEntry,
    build_overlay_glyph_lookup,
)
from . import ml_extra_defaults


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

    def __init__(
        self,
        screen: PetsciiScreen | None = None,
        defaults: ml_extra_defaults.MLExtraDefaults | None = None,
    ) -> None:
        self.output: Deque[str] = deque()
        if screen is not None:
            self._screen = screen
            self._defaults = defaults or screen.defaults
        else:
            self._screen = PetsciiScreen(defaults=defaults)
            self._defaults = self._screen.defaults
        self._transcript: bytearray = bytearray()
        self._sid_volume: int = self._defaults.hardware.sid_volume
        self._vic_registers: dict[int, int | None] = self._screen.vic_registers
        self._vic_register_timeline: tuple[VicRegisterTimelineEntry, ...] = (
            self._screen.vic_register_timeline
        )
        self._pointer_defaults = self._defaults.hardware.pointer
        self._glyph_lookup: OverlayGlyphLookup = build_overlay_glyph_lookup(
            self._defaults
        )

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
    def defaults(self) -> ml_extra_defaults.MLExtraDefaults:
        """Expose the cached overlay defaults backing the console."""

        return self._defaults

    @property
    def lightbar_defaults(self) -> ml_extra_defaults.LightbarDefaults:
        """Return the recovered lightbar underline and bitmap defaults."""

        return self._defaults.lightbar

    @property
    def flag_dispatch(self) -> ml_extra_defaults.FlagDispatchTable:
        """Return the recovered flag dispatch table."""

        return self._defaults.flag_dispatch

    @property
    def macros(self) -> Tuple[ml_extra_defaults.MacroDirectoryEntry, ...]:
        """Return the decoded macro directory entries."""

        return self._defaults.macros

    @property
    def overlay_glyph_lookup(self) -> OverlayGlyphLookup:
        """Expose rendered glyph metadata derived from the overlay text tables."""

        return self._glyph_lookup

    @property
    def macro_glyphs(self) -> Mapping[int, GlyphRun]:
        """Return rendered glyph runs for macros keyed by slot."""

        return self._glyph_lookup.macros_by_slot

    @property
    def macro_glyphs_by_text(self) -> Mapping[str, GlyphRun]:
        """Return rendered glyph runs for macros keyed by decoded text."""

        return self._glyph_lookup.macros_by_text

    @property
    def flag_glyph_records(self) -> tuple[FlagGlyphMapping, ...]:
        """Expose rendered glyph runs for each ampersand flag record."""

        return self._glyph_lookup.flag_records

    @property
    def flag_directory_glyphs(self) -> GlyphRun:
        """Return rendered glyph metadata for the flag directory tail text."""

        return self._glyph_lookup.flag_directory_tail

    @property
    def flag_directory_block_glyphs(self) -> GlyphRun:
        """Return rendered glyph metadata for the flag directory block payload."""

        return self._glyph_lookup.flag_directory_block

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
    def vic_registers(self) -> dict[int, int | None]:
        """Return the resolved VIC register defaults."""

        return dict(self._vic_registers)

    @property
    def vic_register_timeline(self) -> tuple[VicRegisterTimelineEntry, ...]:
        """Return the recovered VIC register write order."""

        return self._vic_register_timeline

    @property
    def sid_volume(self) -> int:
        """Return the recovered SID volume default."""

        return self._sid_volume

    @property
    def pointer_defaults(self) -> ml_extra_defaults.BufferPointerDefaults:
        """Return the recovered ``$42fe/$42ff`` pointer configuration."""

        return self._pointer_defaults

    @property
    def transcript(self) -> str:
        """Return the accumulated transcript as a decoded string."""

        return "".join(self.output)

    @property
    def transcript_bytes(self) -> bytes:
        """Return the accumulated transcript as raw bytes."""

        return bytes(self._transcript)

    def snapshot(self) -> Dict[str, object]:
        """Return a structured view of the console screen buffer."""

        screen = self._screen
        return {
            "characters": screen.characters,
            "colour_matrix": screen.colour_matrix,
            "code_matrix": screen.code_matrix,
            "glyph_indices": screen.glyph_index_matrix,
            "glyphs": screen.glyph_matrix,
            "reverse_matrix": screen.reverse_matrix,
            "resolved_colour_matrix": screen.resolved_colour_matrix,
            "underline_matrix": screen.underline_matrix,
            "palette": screen.palette,
            "resolved_palette": screen.resolved_palette_state,
            "lightbar_bitmaps": screen.lightbar_bitmaps,
            "underline_char": screen.underline_char,
            "underline_colour": screen.underline_colour,
            "screen_colour": self.screen_colour,
            "background_colour": self.background_colour,
            "border_colour": self.border_colour,
            "hardware": {
                "vic_registers": self.vic_registers,
                "vic_register_timeline": tuple(
                    entry.as_dict() for entry in self.vic_register_timeline
                ),
                "pointer": {
                    "initial": {
                        "low": self._pointer_defaults.initial[0],
                        "high": self._pointer_defaults.initial[1],
                    },
                    "scan_limit": self._pointer_defaults.scan_limit,
                    "reset_value": self._pointer_defaults.reset_value,
                },
                "sid_volume": self.sid_volume,
            },
        }


@dataclass
class ConsoleService:
    """Service wrapper that exposes console metadata and helpers."""

    device: Console
    name: str = "console"

    @property
    def defaults(self) -> ml_extra_defaults.MLExtraDefaults:
        """Return the overlay defaults driving the console renderer."""

        return self.device.defaults

    @property
    def vic_registers(self) -> dict[int, int | None]:
        """Expose the recovered VIC register defaults."""

        return self.device.vic_registers

    @property
    def vic_register_timeline(self) -> tuple[VicRegisterTimelineEntry, ...]:
        """Expose the VIC register write order recovered from the overlay."""

        return self.device.vic_register_timeline

    @property
    def pointer_defaults(self) -> ml_extra_defaults.BufferPointerDefaults:
        """Expose the recovered ``$42fe/$42ff`` pointer configuration."""

        return self.device.pointer_defaults

    @property
    def sid_volume(self) -> int:
        """Expose the recovered SID volume default."""

        return self.device.sid_volume

    @property
    def screen(self) -> PetsciiScreen:
        """Expose the PETSCII-aware screen backing the console."""

        return self.device.screen

    @property
    def palette(self) -> tuple[int, int, int, int]:
        """Return the recovered VIC-II palette tuple."""

        return self.screen.palette

    @property
    def cursor_position(self) -> tuple[int, int]:
        """Return the current cursor position from the renderer."""

        return self.screen.cursor_position

    @property
    def flag_dispatch(self) -> ml_extra_defaults.FlagDispatchTable:
        """Expose the decoded ampersand flag dispatch table."""

        return self.device.flag_dispatch

    @property
    def glyph_lookup(self) -> OverlayGlyphLookup:
        """Expose the rendered glyph lookup derived from ``ml.extra``."""

        return self.device.overlay_glyph_lookup

    @property
    def macro_glyphs(self) -> Mapping[int, GlyphRun]:
        """Return rendered glyph metadata keyed by macro slot."""

        return self.device.macro_glyphs

    def home_cursor(self) -> None:
        """Home the renderer cursor without clearing the buffer."""

        self.screen.home_cursor()

    def set_cursor(self, x: int, y: int) -> None:
        """Move the renderer cursor, clamping to the visible area."""

        self.screen.set_cursor(x, y)

    def write(self, data: str | bytes) -> None:
        """Proxy writes through to the underlying console device."""

        self.device.write(data)

    def push_macro_slot(self, slot: int) -> GlyphRun | None:
        """Render a macro by slot identifier and mirror it to the console."""

        run = self.glyph_lookup.macros_by_slot.get(slot)
        if run is None:
            return None
        payload = bytes(run.payload)
        if payload:
            self.device.write(payload)
        return run

    def push_flag_macro(self, flag_index: int) -> GlyphRun | None:
        """Render the macro associated with ``flag_index`` via dispatch data."""

        for entry in self.device.flag_dispatch.entries:
            if entry.flag_index == flag_index:
                return self.push_macro_slot(entry.slot)
        return None


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
        self.services: Dict[str, object] = {}
        self._service_view: Mapping[str, object] = MappingProxyType(self.services)

    def register(self, name: str, device: Device) -> None:
        self.devices[name] = device

    def register_service(self, name: str, service: object) -> None:
        """Register a host service keyed by Commodore device name."""

        self.services[name] = service

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

    def get_service(self, name: str) -> object:
        """Return the registered service associated with ``name``."""

        try:
            return self.services[name]
        except KeyError as exc:
            raise DeviceError(f"no such service '{name}'") from exc

    @property
    def service_registry(self) -> Mapping[str, object]:
        """Expose a read-only view of the registered device services."""

        return self._service_view


def bootstrap_device_context(assignments: Iterable[DriveAssignment]) -> DeviceContext:
    """Instantiate a device context with modern drive mappings."""

    context = DeviceContext()
    console = Console()
    context.register("console", console)
    context.register_service("console", ConsoleService(console))
    context.register("modem", Modem())
    for assignment in assignments:
        locator = assignment.locator
        if isinstance(locator, FilesystemDriveLocator):
            context.register(f"drive{assignment.slot}", DiskDrive(locator.path))
    return context


__all__ = [
    "ChannelDescriptor",
    "Console",
    "ConsoleService",
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
