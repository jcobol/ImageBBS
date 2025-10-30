"""Host device/context abstractions for the ImageBBS runtime.

This module sketches a modern host-side equivalent of the Commodore device
multiplexer that ImageBBS exercises through `SETLFS` and `PRINT#` calls.  The
prototype is intentionally small; it focuses on the interactions we need to
validate while building the DOS command helper and overlay loader mentioned in
iteration 08's follow-ups.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict, deque
from importlib import import_module
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Deque,
    Dict,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

if TYPE_CHECKING:
    from ..ampersand_dispatcher import AmpersandDispatcher
    from ..ampersand_registry import AmpersandRegistry
    from ..runtime.masked_pane_staging import MaskedPaneStagingMap

from ..setup_defaults import DriveAssignment, FilesystemDriveLocator
from ..console_renderer import (
    FlagGlyphMapping,
    GlyphRun,
    OverlayGlyphLookup,
    PetsciiScreen,
    VicRegisterTimelineEntry,
    build_overlay_glyph_lookup,
)
from .. import ml_extra_defaults
from ..petscii import PetsciiStreamDecoder


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
        chars: Iterable[str] = (
            self._buffer.popleft() for _ in range(min(size, len(self._buffer)))
        )
        return "".join(chars)

    def dump(self) -> str:
        """Expose the buffered payload for inspection in tests."""

        return "".join(self._buffer)

    def close(self) -> None:  # pragma: no cover - default implementation has no effect
        """Close the underlying resource bound to the channel, if any."""


class SequentialFileChannel(LogicalChannel):
    """Channel backed by a sequential file on the host filesystem."""

    def __init__(self, descriptor: ChannelDescriptor, path: Path, mode: str) -> None:
        super().__init__(descriptor)
        self.path = path
        self._handle = path.open(mode)

    @staticmethod
    def _to_host_bytes(data: str | bytes) -> bytes:
        if isinstance(data, bytes):
            payload = data
        else:
            payload = data.encode("latin-1", errors="strict")
        payload = payload.replace(b"\r\n", b"\n")
        return payload.replace(b"\r", b"\n")

    @staticmethod
    def _to_petscii_text(data: bytes) -> str:
        payload = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r")
        return payload.decode("latin-1", errors="strict")

    def write(self, data: str | bytes) -> None:  # type: ignore[override]
        payload = self._to_host_bytes(data)
        self._handle.write(payload)
        self._handle.flush()

    def read(self, size: Optional[int] = None) -> str:  # type: ignore[override]
        if size is None:
            raw = self._handle.read()
        else:
            raw = self._handle.read(size)
        if not raw:
            return ""
        return self._to_petscii_text(raw)

    def close(self) -> None:
        try:
            self._handle.flush()
        finally:
            self._handle.close()


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
        root.mkdir(parents=True, exist_ok=True)
        self.root = root
        self._root = root.resolve()

    def open(self, descriptor: ChannelDescriptor) -> LogicalChannel:
        if descriptor.secondary_address != 15:
            raise DeviceError("disk: data channels require open_file")
        channel = LogicalChannel(descriptor)
        # Command channel; mirror Commodore behaviour by preloading the DOS prompt.
        channel.write("00,OK,00,00\r")
        return channel

    @staticmethod
    def _split_filename(specification: str) -> Tuple[str, Optional[str], Optional[str]]:
        parts = [segment.strip() for segment in specification.split(",")]
        if not parts or not parts[0]:
            raise DeviceError("disk: filename is required")
        name = parts[0]
        file_type = parts[1] if len(parts) > 1 and parts[1] else None
        mode = parts[2] if len(parts) > 2 and parts[2] else None
        return name, file_type, mode

    def _filename_to_path(self, name: str) -> Path:
        if ":" in name:
            _, name = name.split(":", 1)
        name = name.strip()
        if not name:
            raise DeviceError("disk: empty filename token")
        path = Path(name)
        if path.is_absolute():
            raise DeviceError("disk: absolute paths are not permitted")
        host_path = (self._root / path).resolve()
        try:
            host_path.relative_to(self._root)
        except ValueError as exc:
            raise DeviceError("disk: path escapes configured root") from exc
        return host_path

    def _parse_filename(self, specification: str) -> Tuple[Path, Optional[str], str]:
        name, file_type, mode = self._split_filename(specification)
        path = self._filename_to_path(name)
        type_normalised: Optional[str] = None
        if file_type:
            type_normalised = file_type.upper()
            if type_normalised not in {"S", "SEQ"}:
                raise DeviceError(f"disk: unsupported file type '{file_type}'")
        mode_token = (mode or "R").upper()
        if mode_token not in {"R", "W", "A"}:
            raise DeviceError(f"disk: unsupported file mode '{mode_token}'")
        return path, type_normalised, mode_token

    def open_file(self, descriptor: ChannelDescriptor, specification: str) -> SequentialFileChannel:
        path, file_type, mode_token = self._parse_filename(specification)
        if file_type is not None and file_type not in {"S", "SEQ"}:
            raise DeviceError("disk: only sequential files are supported")
        if mode_token == "R":
            if not path.exists() or not path.is_file():
                raise DeviceError(f"disk: '{path.name}' does not exist")
            file_mode = "rb"
        elif mode_token == "W":
            path.parent.mkdir(parents=True, exist_ok=True)
            file_mode = "wb"
        else:  # mode_token == "A"
            path.parent.mkdir(parents=True, exist_ok=True)
            file_mode = "ab"
        return SequentialFileChannel(descriptor, path, file_mode)

    def command(self, raw: str) -> str:
        command = raw.strip()
        if not command:
            raise DeviceError("disk: empty command")
        upper = command.upper()
        if upper == "I":
            return "00,OK,00,00"
        if upper == "$":
            # Simplistic directory listing for prototype purposes.
            entries = sorted(p.name for p in self.root.glob("**/*") if p.is_file())
            listing = "\r".join(entries)
            return f"00,{listing or '0 FILES'},00,00"
        if upper.startswith("S"):
            specification = command[1:]
            if specification.startswith(":"):
                specification = specification[1:]
            specification = specification.strip()
            if not specification:
                raise DeviceError("disk: scratch command requires a filename")
            path = self._filename_to_path(self._split_filename(specification)[0])
            if path.exists() and path.is_file():
                path.unlink()
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
        self._cli_decoder = PetsciiStreamDecoder()

    def open(self, descriptor: ChannelDescriptor) -> LogicalChannel:
        return ConsoleChannel(descriptor, self)

    @staticmethod
    def _payload_looks_ascii(text: str) -> bool:
        try:
            payload = text.encode("latin-1", errors="strict")
        except UnicodeEncodeError:
            return False
        allowed_control = {0x09, 0x0A, 0x0D}
        for byte in payload:
            if byte in allowed_control:
                continue
            if 0x20 <= byte <= 0x7E or 0xA0 <= byte <= 0xFF:
                continue
            return False
        return True

    def write(self, data: str | bytes) -> None:
        if isinstance(data, bytes):
            payload = data
            original_text: str | None = None
        else:
            payload = data.encode("latin-1", errors="replace")
            original_text = data
        text = self._cli_decoder.decode(payload)
        if original_text is not None and self._payload_looks_ascii(original_text):
            self.output.append(original_text)
        else:
            self.output.append(text)
        self._transcript.extend(payload)
        self._screen.write(payload)

    def poke_screen_byte(self, address: int, value: int) -> None:
        """Write ``value`` to the PETSCII screen byte stored at ``address``."""

        self._screen.poke_screen_address(address, value)

    def poke_colour_byte(self, address: int, value: int) -> None:
        """Write ``value`` to the colour RAM byte stored at ``address``."""

        self._screen.poke_colour_address(address, value)

    def fill_colour(self, address: int, value: int, length: int) -> None:
        """Write ``value`` across ``length`` bytes in colour RAM starting at ``address``."""

        if length < 0:
            raise ValueError("length must be non-negative")
        for offset in range(length):
            self._screen.poke_colour_address(address + offset, value)

    def poke_block(
        self,
        *,
        screen_address: int | None = None,
        screen_bytes: Sequence[int] | Iterable[int] | bytes | bytearray | None = None,
        screen_length: int | None = None,
        colour_address: int | None = None,
        colour_bytes: Sequence[int] | Iterable[int] | bytes | bytearray | None = None,
        colour_length: int | None = None,
    ) -> None:
        """Apply a block transfer against screen and/or colour RAM.

        The arguments mirror the overlay's expectations when streaming blocks into
        ``$0400`` and ``$d800``.  ``screen_bytes`` and ``colour_bytes`` accept any
        iterable returning integers in ``0-255`` or raw ``bytes``/``bytearray``
        payloads.  ``screen_length`` and ``colour_length`` limit the number of
        bytes written from each payload; the default writes the entire sequence.
        At least one of the payload arguments must be provided.
        """

        if screen_bytes is None and colour_bytes is None:
            raise ValueError("poke_block requires screen_bytes and/or colour_bytes")

        if screen_length is not None and screen_length < 0:
            raise ValueError("screen_length must be non-negative")
        if colour_length is not None and colour_length < 0:
            raise ValueError("colour_length must be non-negative")

        if screen_bytes is not None:
            if screen_address is None:
                raise ValueError("screen_address must be provided with screen_bytes")
            payload = bytes(screen_bytes)
            if screen_length is not None:
                payload = payload[:screen_length]
            for offset, byte in enumerate(payload):
                self._screen.poke_screen_address(screen_address + offset, byte)

        if colour_bytes is not None:
            if colour_address is None:
                raise ValueError("colour_address must be provided with colour_bytes")
            payload = bytes(colour_bytes)
            if colour_length is not None:
                payload = payload[:colour_length]
            for offset, byte in enumerate(payload):
                self._screen.poke_colour_address(colour_address + offset, byte)

    def peek_block(
        self,
        *,
        screen_address: int | None = None,
        screen_length: int | None = None,
        colour_address: int | None = None,
        colour_length: int | None = None,
    ) -> tuple[bytes | None, bytes | None]:
        """Return screen and/or colour RAM spans without mutating the console."""

        if screen_length is None and colour_length is None:
            raise ValueError("peek_block requires screen_length and/or colour_length")

        if screen_length is not None and screen_length < 0:
            raise ValueError("screen_length must be non-negative")
        if colour_length is not None and colour_length < 0:
            raise ValueError("colour_length must be non-negative")

        screen_payload: bytes | None = None
        colour_payload: bytes | None = None
        screen = self._screen

        if screen_length:
            if screen_address is None:
                raise ValueError(
                    "screen_address must be provided to peek a screen span"
                )
            screen_payload = bytes(
                screen.peek_screen_address(screen_address + offset)
                for offset in range(screen_length)
            )
        elif screen_length == 0:
            screen_payload = b""

        if colour_length:
            if colour_address is None:
                raise ValueError(
                    "colour_address must be provided to peek a colour span"
                )
            colour_payload = bytes(
                screen.peek_colour_address(colour_address + offset)
                for offset in range(colour_length)
            )
        elif colour_length == 0:
            colour_payload = b""

        return screen_payload, colour_payload

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
class ConsoleRegionBuffer:
    """Buffer that mirrors the overlay's screen/colour swap loops."""

    screen_length: int = 0
    colour_length: int = 0
    screen_bytes: bytearray = field(init=False)
    colour_bytes: bytearray = field(init=False)

    def __post_init__(self) -> None:
        if self.screen_length < 0:
            raise ValueError("screen_length must be non-negative")
        if self.colour_length < 0:
            raise ValueError("colour_length must be non-negative")
        self.screen_bytes = bytearray(self.screen_length)
        self.colour_bytes = bytearray(self.colour_length)

    def __bool__(self) -> bool:
        """Return ``True`` when the buffer carries screen or colour spans."""

        return bool(self.screen_length or self.colour_length)


@dataclass(frozen=True)
class MaskedPaneBlinkState:
    """State snapshot produced each time the blink counter advances."""

    countdown: int
    reverse: bool


@dataclass(frozen=True)
class MaskedPaneGlyphPayload:
    """Character and colour bytes staged for the masked sysop pane."""

    glyph: int
    colour: int
    reverse: bool
    countdown: int


@dataclass
class MaskedPaneBuffers:
    """Host-side model of ``tempbott``/``$4050`` rotation buffers."""

    width: int = 40
    tempbott: bytearray = field(init=False, repr=False)
    tempbott_next: bytearray = field(init=False, repr=False)
    colour_4050: bytearray = field(init=False, repr=False)
    colour_var_4078: bytearray = field(init=False, repr=False)
    dirty: bool = field(default=False, init=False)
    staging_fill_glyph: int = field(init=False, repr=False)
    staging_fill_colour: int = field(init=False, repr=False)
    _pending_screen: bytes | None = field(default=None, init=False, repr=False)
    _pending_colour: bytes | None = field(default=None, init=False, repr=False)
    _suppress_cache_once: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError("width must be positive")
        self.tempbott = bytearray(self.width)
        self.tempbott_next = bytearray(self.width)
        self.colour_4050 = bytearray(self.width)
        self.colour_var_4078 = bytearray(self.width)
        self.clear_live()
        self.clear_staging()
        self.clear_pending_payload()

    @property
    def live_screen(self) -> bytearray:
        """Return the preserved overlay glyphs mirrored from ``tempbott``."""

        return self.tempbott

    @property
    def live_colour(self) -> bytearray:
        """Return the preserved overlay colours mirrored from ``$4050``."""

        return self.colour_4050

    @property
    def staged_screen(self) -> bytearray:
        """Return the next overlay glyphs staged in ``tempbott+40``."""

        return self.tempbott_next

    @property
    def staged_colour(self) -> bytearray:
        """Return the next overlay colours staged in ``var_4078``."""

        return self.colour_var_4078

    def clear_live(self, glyph: int = 0x20, colour: int = 0x00) -> None:
        """Reset ``tempbott``/``$4050`` to the provided ``glyph``/``colour``."""

        glyph_byte = int(glyph) & 0xFF
        colour_byte = int(colour) & 0xFF
        self.tempbott[:] = bytes((glyph_byte,) * self.width)
        self.colour_4050[:] = bytes((colour_byte,) * self.width)

    def clear_staging(self, glyph: int = 0x20, colour: int = 0x00) -> None:
        """Reset ``tempbott+40``/``var_4078`` to the provided ``glyph``/``colour``."""

        glyph_byte = int(glyph) & 0xFF
        colour_byte = int(colour) & 0xFF
        self.tempbott_next[:] = bytes((glyph_byte,) * self.width)
        self.colour_var_4078[:] = bytes((colour_byte,) * self.width)
        self.staging_fill_glyph = glyph_byte
        self.staging_fill_colour = colour_byte
        self.dirty = False

    def preview_staging_payload(
        self, screen_payload: Sequence[int], colour_payload: Sequence[int]
    ) -> None:
        """Update ``dirty`` to reflect the provided staging payload."""

        glyph_fill = getattr(self, "staging_fill_glyph", 0x20) & 0xFF
        colour_fill = getattr(self, "staging_fill_colour", 0x00) & 0xFF
        if any((int(byte) & 0xFF) != glyph_fill for byte in screen_payload):
            self.dirty = True
            return
        if any((int(byte) & 0xFF) != colour_fill for byte in colour_payload):
            self.dirty = True
            return
        self.dirty = False

    def recalculate_dirty(self) -> None:
        """Refresh ``dirty`` based on current staging buffer contents."""

        glyph_fill = getattr(self, "staging_fill_glyph", 0x20) & 0xFF
        colour_fill = getattr(self, "staging_fill_colour", 0x00) & 0xFF
        screen_dirty = any(byte != glyph_fill for byte in self.tempbott_next)
        colour_dirty = any(byte != colour_fill for byte in self.colour_var_4078)
        self.dirty = screen_dirty or colour_dirty

    def cache_pending_payload(
        self,
        screen_payload: Sequence[int] | bytes,
        colour_payload: Sequence[int] | bytes,
    ) -> None:
        """Persist the next staged overlay spans until consumed."""

        if self._suppress_cache_once:
            self._suppress_cache_once = False
            return

        screen_bytes = bytes(screen_payload)[: self.width]
        colour_bytes = bytes(colour_payload)[: self.width]
        self._pending_screen = screen_bytes
        self._pending_colour = colour_bytes

    def has_pending_payload(self) -> bool:
        """Return ``True`` if cached staging spans are waiting to be applied."""

        return self._pending_screen is not None and self._pending_colour is not None

    def peek_pending_payload(self) -> tuple[bytes, bytes] | None:
        """Return the cached staging spans without consuming them."""

        if not self.has_pending_payload():
            return None
        return (
            bytes(self._pending_screen or b""),
            bytes(self._pending_colour or b""),
        )

    def consume_pending_payload(self) -> tuple[bytes, bytes] | None:
        """Return and clear the cached staging spans once."""

        if not self.has_pending_payload():
            return None

        payload = (
            bytes(self._pending_screen or b""),
            bytes(self._pending_colour or b""),
        )
        self._pending_screen = None
        self._pending_colour = None
        self._suppress_cache_once = True
        return payload

    def clear_pending_payload(self) -> None:
        """Discard any cached staging spans and reset suppression state."""

        self._pending_screen = None
        self._pending_colour = None
        self._suppress_cache_once = False


class MaskedPaneBlinkScheduler:
    """Model the five-phase blink cadence driven by ``lbl_adca``."""

    def __init__(self, reset_value: int = 4) -> None:
        if reset_value < 0:
            raise ValueError("reset_value must be non-negative")
        self._reset_value = reset_value
        self._countdown = reset_value

    def advance(self) -> MaskedPaneBlinkState:
        """Decrement the countdown and return the active blink state."""

        next_value = self._countdown - 1
        if next_value < 0:
            next_value = self._reset_value
        self._countdown = next_value
        return MaskedPaneBlinkState(next_value, bool(next_value & 0x02))

    def peek(self) -> MaskedPaneBlinkState:
        """Return the current countdown without mutating it."""

        return MaskedPaneBlinkState(self._countdown, bool(self._countdown & 0x02))

    def reset(self) -> None:
        """Restore the countdown to its reset value."""

        self._countdown = self._reset_value


@dataclass
class ConsoleFramePayload:
    """Payload exported by :meth:`ConsoleService.export_frame_payload`."""

    screen_glyphs: bytes
    screen_colours: bytes
    masked_pane_chars: bytes
    masked_pane_colours: bytes
    masked_overlay_chars: bytes
    masked_overlay_colours: bytes
    pause_char: int
    abort_char: int
    carrier_char: int
    spinner_char: int
    pause_active: bool
    abort_active: bool
    carrier_active: bool
    idle_timer_digits: Tuple[int, int, int]


@dataclass
class ConsoleService:
    """Service wrapper that exposes console metadata and helpers."""

    device: Console
    name: str = "console"

    # Masked-pane overlay macros mirrored from ``ml.extra`` metadata.
    _MASKED_OVERLAY_FLAG_SLOTS = frozenset(
        {0x04, 0x09, 0x0D, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19}
    )

    _SCREEN_BASE = 0x0400
    _COLOUR_BASE = 0xD800
    _PAUSE_SCREEN_ADDRESS = 0x041E
    _ABORT_SCREEN_ADDRESS = 0x041F
    _SPINNER_SCREEN_ADDRESS = 0x049C
    _CARRIER_LEADING_SCREEN_ADDRESS = 0x0400
    _CARRIER_INDICATOR_SCREEN_ADDRESS = 0x0427
    _MASKED_PANE_SCREEN_BASE = 0x0518
    _MASKED_PANE_COLOUR_BASE = 0xD918
    _MASKED_PANE_WIDTH = 40
    _MASKED_OVERLAY_SCREEN_BASE = 0x0770
    _MASKED_OVERLAY_COLOUR_BASE = 0xDB70
    _MASKED_OVERLAY_WIDTH = 40
    _MASKED_STAGING_SCREEN_BASE = 0x4028
    _MASKED_STAGING_COLOUR_BASE = 0x4078
    _IDLE_TIMER_SCREEN_ADDRESSES = (
        0x04DE,
        0x04E0,
        0x04E1,
    )

    def __post_init__(self) -> None:
        self._masked_pane_blink = MaskedPaneBlinkScheduler()
        self._masked_pane_buffers: MaskedPaneBuffers | None = None
        self._masked_pane_staging_map: "MaskedPaneStagingMap" | None = None

    @staticmethod
    def _normalise_linear_payload(
        payload: bytes | None, length: int, *, fill: int
    ) -> bytes:
        """Return ``payload`` truncated or padded to ``length`` using ``fill``."""

        if length <= 0:
            return b""
        fill_value = int(fill) & 0xFF
        if payload is None:
            return bytes((fill_value,) * length)
        data = bytes(payload)
        if len(data) < length:
            data += bytes((fill_value,) * (length - len(data)))
        elif len(data) > length:
            data = data[:length]
        return data

    def export_frame_payload(
        self, screen_width: int, screen_height: int
    ) -> ConsoleFramePayload:
        """Return glyph/colour spans and indicator metadata for the console."""

        width = max(0, int(screen_width))
        height = max(0, int(screen_height))
        total_cells = width * height

        screen_bytes, colour_bytes = self.peek_block(
            screen_address=self._SCREEN_BASE,
            screen_length=total_cells,
            colour_address=self._COLOUR_BASE,
            colour_length=total_cells,
        )

        screen_payload = self._normalise_linear_payload(
            screen_bytes, total_cells, fill=0x20
        )
        colour_payload = self._normalise_linear_payload(
            colour_bytes, total_cells, fill=0x00
        )

        def clamp_offset(address: int) -> int:
            offset = int(address) - self._SCREEN_BASE
            if total_cells <= 0:
                return 0
            max_offset = total_cells - 1
            if offset < 0:
                return 0
            if offset > max_offset:
                return max_offset
            return offset

        def read_screen(address: int, *, default: int) -> int:
            if total_cells <= 0 or not screen_payload:
                return int(default) & 0xFF
            offset = clamp_offset(address)
            return screen_payload[offset]

        def indicator_active(code: int) -> bool:
            value = int(code) & 0xFF
            return value not in (0x00, 0x20)

        pause_char = read_screen(self._PAUSE_SCREEN_ADDRESS, default=0x20)
        abort_char = read_screen(self._ABORT_SCREEN_ADDRESS, default=0x20)
        carrier_char = read_screen(
            self._CARRIER_INDICATOR_SCREEN_ADDRESS, default=0x20
        )
        spinner_char = read_screen(self._SPINNER_SCREEN_ADDRESS, default=0x20)

        idle_timer_digits = tuple(
            read_screen(address, default=0x30)
            for address in self._IDLE_TIMER_SCREEN_ADDRESSES
        )

        pane_length = self._MASKED_PANE_WIDTH
        pane_screen, pane_colour = self.peek_block(
            screen_address=self._MASKED_PANE_SCREEN_BASE,
            screen_length=pane_length,
            colour_address=self._MASKED_PANE_COLOUR_BASE,
            colour_length=pane_length,
        )
        pane_chars = self._normalise_linear_payload(
            pane_screen, pane_length, fill=0x20
        )
        pane_colours = self._normalise_linear_payload(
            pane_colour, pane_length, fill=0x00
        )

        overlay_length = self._MASKED_OVERLAY_WIDTH
        overlay_screen, overlay_colour = self.peek_block(
            screen_address=self._MASKED_OVERLAY_SCREEN_BASE,
            screen_length=overlay_length,
            colour_address=self._MASKED_OVERLAY_COLOUR_BASE,
            colour_length=overlay_length,
        )
        overlay_chars = self._normalise_linear_payload(
            overlay_screen, overlay_length, fill=0x20
        )
        overlay_colours = self._normalise_linear_payload(
            overlay_colour, overlay_length, fill=0x00
        )

        return ConsoleFramePayload(
            screen_glyphs=screen_payload,
            screen_colours=colour_payload,
            masked_pane_chars=pane_chars,
            masked_pane_colours=pane_colours,
            masked_overlay_chars=overlay_chars,
            masked_overlay_colours=overlay_colours,
            pause_char=pause_char,
            abort_char=abort_char,
            carrier_char=carrier_char,
            spinner_char=spinner_char,
            pause_active=indicator_active(pause_char),
            abort_active=indicator_active(abort_char),
            carrier_active=indicator_active(carrier_char),
            idle_timer_digits=tuple(int(digit) & 0xFF for digit in idle_timer_digits),
        )

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
    def screen_colour(self) -> int:
        """Return the active foreground colour from the renderer."""

        return self.device.screen_colour

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

    @property
    def masked_pane_staging_map(self) -> "MaskedPaneStagingMap":
        """Return the derived staging plan for masked-pane producers."""

        staging_map = self._masked_pane_staging_map
        if staging_map is None:
            from ..runtime.masked_pane_staging import build_masked_pane_staging_map

            staging_map = build_masked_pane_staging_map(self)
            self._masked_pane_staging_map = staging_map
        return staging_map

    def advance_masked_pane_blink(self) -> MaskedPaneBlinkState:
        """Simulate ``lbl_adca`` and return the active blink state."""

        return self._masked_pane_blink.advance()

    def reset_masked_pane_blink(self) -> None:
        """Restore the blink countdown to its reset value."""

        self._masked_pane_blink.reset()

    def masked_pane_next_payload(
        self, glyph: int, colour: int
    ) -> MaskedPaneGlyphPayload:
        """Return glyph/colour bytes with blink modulation applied."""

        state = self.advance_masked_pane_blink()
        glyph_byte = int(glyph) & 0xFF
        if state.reverse:
            glyph_byte ^= 0x80
        colour_byte = int(colour) & 0xFF
        return MaskedPaneGlyphPayload(
            glyph=glyph_byte,
            colour=colour_byte,
            reverse=state.reverse,
            countdown=state.countdown,
        )

    def write_masked_pane_cell(
        self, offset: int, glyph: int, colour: int
    ) -> MaskedPaneGlyphPayload:
        """Commit a glyph to ``$0518/$D918`` using the blink scheduler."""

        if not 0 <= offset < self._MASKED_PANE_WIDTH:
            raise ValueError("offset must reference a masked pane cell")

        payload = self.masked_pane_next_payload(glyph, colour)
        screen_address = self._MASKED_PANE_SCREEN_BASE + offset
        colour_address = self._MASKED_PANE_COLOUR_BASE + offset
        self.poke_screen_byte(screen_address, payload.glyph)
        self.poke_colour_byte(colour_address, payload.colour)
        return payload

    def capture_masked_pane_buffers(self, buffers: MaskedPaneBuffers) -> None:
        """Copy the live bottom overlay into ``buffers.live_*`` spans."""

        if buffers.width != self._MASKED_OVERLAY_WIDTH:
            raise ValueError("masked pane buffers must span 40 bytes")

        screen_bytes, colour_bytes = self.peek_block(
            screen_address=self._MASKED_OVERLAY_SCREEN_BASE,
            screen_length=buffers.width,
            colour_address=self._MASKED_OVERLAY_COLOUR_BASE,
            colour_length=buffers.width,
        )

        if screen_bytes is None or colour_bytes is None:
            raise ValueError("masked pane capture requires screen and colour spans")

        buffers.live_screen[:] = screen_bytes
        buffers.live_colour[:] = colour_bytes

    def clear_masked_pane_staging(
        self, buffers: MaskedPaneBuffers, *, glyph: int = 0x20, colour: int | None = None
    ) -> None:
        """Reset staged overlay spans mirroring ``var_4078`` and ``tempbott+40``."""

        colour_value = self.screen_colour if colour is None else int(colour) & 0xFF
        buffers.clear_staging(glyph=glyph, colour=colour_value)

    def stage_masked_pane_overlay(
        self,
        screen_bytes: Sequence[int] | Iterable[int] | bytes | bytearray,
        colour_bytes: Sequence[int] | Iterable[int] | bytes | bytearray | None = None,
        *,
        fill_colour: int | None = None,
    ) -> None:
        """Normalise ``screen_bytes``/``colour_bytes`` and stage them for commit."""

        width = self._MASKED_OVERLAY_WIDTH

        glyph_payload = bytes(screen_bytes)
        glyph_slice = glyph_payload[:width]
        if len(glyph_slice) < width:
            glyph_slice = glyph_slice + bytes((0x20,) * (width - len(glyph_slice)))

        default_colour = self.screen_colour if fill_colour is None else int(fill_colour)
        default_colour &= 0xFF

        if colour_bytes is None:
            colour_slice = bytes((default_colour,) * width)
        else:
            colour_payload = bytes(colour_bytes)
            colour_slice = colour_payload[:width]
            if len(colour_slice) < width:
                colour_slice = colour_slice + bytes(
                    (default_colour,) * (width - len(colour_slice))
                )

        buffers = self._masked_pane_buffers
        if buffers is not None:
            buffers.cache_pending_payload(glyph_slice, colour_slice)
            buffers.preview_staging_payload(glyph_slice, colour_slice)

        self.poke_block(
            screen_address=self._MASKED_STAGING_SCREEN_BASE,
            screen_bytes=glyph_slice,
            colour_address=self._MASKED_STAGING_COLOUR_BASE,
            colour_bytes=colour_slice,
        )

    @staticmethod
    def _pad_linear_span(payload: bytes, width: int, fill: int) -> bytes:
        """Return ``payload`` truncated/padded to ``width`` using ``fill``."""

        fill_byte = int(fill) & 0xFF
        if width <= 0:
            return b""

        slice_ = bytes(payload[:width])
        if len(slice_) >= width:
            return slice_

        return slice_ + bytes((fill_byte,) * (width - len(slice_)))

    def _macro_slot_overlay_spans(
        self,
        slot: int,
        run: GlyphRun,
        *,
        fill_colour: int | None,
    ) -> tuple[bytes, bytes]:
        """Return 40-byte glyph/colour spans representing ``slot``."""

        width = self._MASKED_OVERLAY_WIDTH
        glyph_fill = 0x20
        colour_fill = self.screen_colour if fill_colour is None else int(fill_colour)
        colour_fill &= 0xFF

        entry = self.defaults.macros_by_slot.get(slot)
        glyph_bytes: bytes
        colour_bytes: bytes | None

        if entry is not None and entry.screen is not None:
            glyph_bytes = bytes(entry.screen.glyph_bytes[:width])
            colour_bytes = bytes(entry.screen.colour_bytes[:width])
        else:
            glyph_bytes = bytes(run.rendered[:width])
            colour_bytes = None

        glyph_slice = self._pad_linear_span(glyph_bytes, width, glyph_fill)
        if colour_bytes is None:
            colour_slice = bytes((colour_fill,) * width)
        else:
            colour_slice = self._pad_linear_span(colour_bytes, width, colour_fill)

        return glyph_slice, colour_slice

    def rotate_masked_pane_buffers(
        self,
        buffers: MaskedPaneBuffers,
        *,
        fill_glyph: int = 0x20,
        fill_colour: int | None = None,
    ) -> None:
        """Simulate ``loopb94e`` and rotate masked-pane staging buffers."""

        if buffers.width != self._MASKED_OVERLAY_WIDTH:
            raise ValueError("masked pane buffers must span 40 bytes")

        self.poke_block(
            screen_address=self._MASKED_OVERLAY_SCREEN_BASE,
            screen_bytes=buffers.live_screen,
            screen_length=buffers.width,
            colour_address=self._MASKED_OVERLAY_COLOUR_BASE,
            colour_bytes=buffers.live_colour,
            colour_length=buffers.width,
        )
        buffers.dirty = False

        next_screen = bytes(buffers.staged_screen)
        next_colour = bytes(buffers.staged_colour)
        buffers.live_screen[:] = next_screen
        buffers.live_colour[:] = next_colour

        self.clear_masked_pane_staging(buffers, glyph=fill_glyph, colour=fill_colour)

    def commit_masked_pane_staging(
        self,
        *,
        fill_glyph: int = 0x20,
        fill_colour: int | None = None,
    ) -> None:
        """Flush staged overlay bytes to ``$0770/$DB70`` using bound buffers."""

        buffers = self._masked_pane_buffers
        if buffers is None:
            raise DeviceError("masked pane buffers have not been bound")
        if not buffers.dirty:
            return

        self.rotate_masked_pane_buffers(
            buffers,
            fill_glyph=fill_glyph,
            fill_colour=fill_colour,
        )
        buffers.clear_pending_payload()

        self.poke_block(
            screen_address=self._MASKED_OVERLAY_SCREEN_BASE,
            screen_bytes=buffers.live_screen,
            screen_length=buffers.width,
            colour_address=self._MASKED_OVERLAY_COLOUR_BASE,
            colour_bytes=buffers.live_colour,
            colour_length=buffers.width,
        )

    def capture_region(
        self,
        buffer: "ConsoleRegionBuffer",
        *,
        screen_address: int | None = None,
        colour_address: int | None = None,
    ) -> None:
        """Copy live screen/colour bytes into ``buffer`` without mutating RAM."""

        screen_bytes, colour_bytes = self.peek_block(
            screen_address=screen_address if buffer.screen_length else None,
            screen_length=buffer.screen_length if buffer.screen_length else 0,
            colour_address=colour_address if buffer.colour_length else None,
            colour_length=buffer.colour_length if buffer.colour_length else 0,
        )

        if buffer.screen_length:
            if screen_bytes is None:
                raise ValueError(
                    "screen_address must be provided to capture a screen span"
                )
            buffer.screen_bytes[:] = screen_bytes
        if buffer.colour_length:
            if colour_bytes is None:
                raise ValueError(
                    "colour_address must be provided to capture a colour span"
                )
            buffer.colour_bytes[:] = colour_bytes

    def restore_region(
        self,
        buffer: "ConsoleRegionBuffer",
        *,
        screen_address: int | None = None,
        colour_address: int | None = None,
    ) -> None:
        """Replay ``buffer`` contents back into screen and/or colour RAM.

        The ``ConsoleRegionBuffer`` span lengths determine how many screen and
        colour bytes are written back to the renderer.
        """

        if not buffer:
            raise ValueError("buffer does not contain screen or colour spans")

        self.poke_block(
            screen_address=screen_address if buffer.screen_length else None,
            screen_bytes=buffer.screen_bytes if buffer.screen_length else None,
            screen_length=buffer.screen_length if buffer.screen_length else None,
            colour_address=colour_address if buffer.colour_length else None,
            colour_bytes=buffer.colour_bytes if buffer.colour_length else None,
            colour_length=buffer.colour_length if buffer.colour_length else None,
        )

    def swap_region(
        self,
        buffer: "ConsoleRegionBuffer",
        *,
        screen_address: int | None = None,
        colour_address: int | None = None,
    ) -> None:
        """Swap ``buffer`` payloads with screen/colour RAM spans atomically.

        The exchanged spans honour ``buffer.screen_length`` and
        ``buffer.colour_length`` when writing into screen and colour RAM.
        """

        if not buffer:
            raise ValueError("buffer does not contain screen or colour spans")

        screen_snapshot, colour_snapshot = self.peek_block(
            screen_address=screen_address if buffer.screen_length else None,
            screen_length=buffer.screen_length if buffer.screen_length else 0,
            colour_address=colour_address if buffer.colour_length else None,
            colour_length=buffer.colour_length if buffer.colour_length else 0,
        )

        if buffer.screen_length and screen_snapshot is None:
            raise ValueError(
                "screen_address must be provided to swap a screen span"
            )
        if buffer.colour_length and colour_snapshot is None:
            raise ValueError(
                "colour_address must be provided to swap a colour span"
            )

        self.poke_block(
            screen_address=screen_address if buffer.screen_length else None,
            screen_bytes=buffer.screen_bytes if buffer.screen_length else None,
            screen_length=buffer.screen_length if buffer.screen_length else None,
            colour_address=colour_address if buffer.colour_length else None,
            colour_bytes=buffer.colour_bytes if buffer.colour_length else None,
            colour_length=buffer.colour_length if buffer.colour_length else None,
        )

        if screen_snapshot is not None:
            buffer.screen_bytes[:] = screen_snapshot
        if colour_snapshot is not None:
            buffer.colour_bytes[:] = colour_snapshot

    def home_cursor(self) -> None:
        """Home the renderer cursor without clearing the buffer."""

        self.screen.home_cursor()

    def set_cursor(self, x: int, y: int) -> None:
        """Move the renderer cursor, clamping to the visible area."""

        self.screen.set_cursor(x, y)

    def write(self, data: str | bytes) -> None:
        """Proxy writes through to the underlying console device."""

        self.device.write(data)

    def poke_screen_byte(self, address: int, value: int) -> None:
        """Write a raw PETSCII code to ``address`` in screen RAM."""

        if self._capture_masked_pane_screen(address, value):
            return
        self.device.poke_screen_byte(address, value)

    def poke_colour_byte(self, address: int, value: int) -> None:
        """Write a colour attribute to ``address`` in colour RAM."""

        if self._capture_masked_pane_colour(address, value):
            return
        self.device.poke_colour_byte(address, value)

    def fill_colour(self, address: int, value: int, length: int) -> None:
        """Write ``value`` across ``length`` bytes in colour RAM starting at ``address``."""

        if length < 0:
            raise ValueError("length must be non-negative")

        for offset in range(length):
            self.poke_colour_byte(address + offset, value)

    def poke_block(
        self,
        *,
        screen_address: int | None = None,
        screen_bytes: Sequence[int] | Iterable[int] | bytes | bytearray | None = None,
        screen_length: int | None = None,
        colour_address: int | None = None,
        colour_bytes: Sequence[int] | Iterable[int] | bytes | bytearray | None = None,
        colour_length: int | None = None,
    ) -> None:
        """Apply a block transfer to screen and/or colour RAM.

        ``screen_length`` and ``colour_length`` limit how many bytes from each
        payload are written; passing ``None`` mirrors the full-span behaviour
        expected by existing overlay helpers.
        """

        if screen_bytes is None and colour_bytes is None:
            raise ValueError("poke_block requires screen_bytes and/or colour_bytes")

        if screen_length is not None and screen_length < 0:
            raise ValueError("screen_length must be non-negative")
        if colour_length is not None and colour_length < 0:
            raise ValueError("colour_length must be non-negative")

        if screen_bytes is not None:
            if screen_address is None:
                raise ValueError("screen_address must be provided with screen_bytes")
            payload = bytes(screen_bytes)
            if screen_length is not None:
                payload = payload[:screen_length]
            for offset, byte in enumerate(payload):
                self.poke_screen_byte(screen_address + offset, byte)

        if colour_bytes is not None:
            if colour_address is None:
                raise ValueError("colour_address must be provided with colour_bytes")
            payload = bytes(colour_bytes)
            if colour_length is not None:
                payload = payload[:colour_length]
            for offset, byte in enumerate(payload):
                self.poke_colour_byte(colour_address + offset, byte)

    def peek_block(
        self,
        *,
        screen_address: int | None = None,
        screen_length: int | None = None,
        colour_address: int | None = None,
        colour_length: int | None = None,
    ) -> tuple[bytes | None, bytes | None]:
        """Return screen and/or colour RAM spans without mutating the renderer."""

        return self.device.peek_block(
            screen_address=screen_address,
            screen_length=screen_length,
            colour_address=colour_address,
            colour_length=colour_length,
        )

    @staticmethod
    def _colour_address_for(screen_address: int) -> int:
        """Return the colour RAM address corresponding to ``screen_address``."""

        offset = screen_address - ConsoleService._SCREEN_BASE
        if offset < 0:
            raise ValueError(
                f"screen address ${screen_address:04x} precedes screen base"
            )
        return ConsoleService._COLOUR_BASE + offset

    def set_masked_pane_buffers(self, buffers: MaskedPaneBuffers) -> None:
        """Register ``buffers`` to capture masked-pane staging writes."""

        self._masked_pane_buffers = buffers

    def clear_masked_pane_buffers(self) -> None:
        """Disable masked-pane staging interception."""

        self._masked_pane_buffers = None

    def _capture_masked_pane_screen(self, address: int, value: int) -> bool:
        buffers = self._masked_pane_buffers
        if buffers is None:
            return False

        offset = address - self._MASKED_STAGING_SCREEN_BASE
        if not 0 <= offset < buffers.width:
            return False

        buffers.staged_screen[offset] = int(value) & 0xFF
        buffers.recalculate_dirty()
        return True

    def _capture_masked_pane_colour(self, address: int, value: int) -> bool:
        buffers = self._masked_pane_buffers
        if buffers is None:
            return False

        offset = address - self._MASKED_STAGING_COLOUR_BASE
        if not 0 <= offset < buffers.width:
            return False

        buffers.staged_colour[offset] = int(value) & 0xFF
        buffers.recalculate_dirty()
        return True

    def set_pause_indicator(self, value: int, *, colour: int | None = None) -> None:
        """Update the sysop pause indicator cell at ``$041e``."""

        self.poke_screen_byte(self._PAUSE_SCREEN_ADDRESS, value)
        if colour is not None:
            self.poke_colour_byte(
                self._colour_address_for(self._PAUSE_SCREEN_ADDRESS), colour
            )

    def set_abort_indicator(self, value: int, *, colour: int | None = None) -> None:
        """Update the sysop abort indicator cell at ``$041f``."""

        self.poke_screen_byte(self._ABORT_SCREEN_ADDRESS, value)
        if colour is not None:
            self.poke_colour_byte(
                self._colour_address_for(self._ABORT_SCREEN_ADDRESS), colour
            )

    def update_idle_timer_digits(
        self,
        digits: Sequence[int],
        *,
        colours: Sequence[int] | None = None,
    ) -> None:
        """Write idle timer digits into ``$04de/$04e0/$04e1`` in order."""

        addresses = self._IDLE_TIMER_SCREEN_ADDRESSES
        if len(digits) != len(addresses):
            raise ValueError(
                "idle timer requires three digits for minutes/seconds"
            )
        if colours is not None and len(colours) != len(addresses):
            raise ValueError("colours span must match idle timer digit count")

        for address, value in zip(addresses, digits):
            self.poke_screen_byte(address, value)

        if colours is not None:
            for address, colour in zip(addresses, colours):
                self.poke_colour_byte(self._colour_address_for(address), colour)

    def set_spinner_glyph(self, value: int, *, colour: int | None = None) -> None:
        """Update the activity spinner glyph at ``$049c``."""

        self.poke_screen_byte(self._SPINNER_SCREEN_ADDRESS, value)
        if colour is not None:
            self.poke_colour_byte(
                self._colour_address_for(self._SPINNER_SCREEN_ADDRESS), colour
            )

    def set_carrier_indicator(
        self,
        *,
        leading_cell: int | None = None,
        indicator_cell: int | None = None,
        leading_colour: int | None = None,
        indicator_colour: int | None = None,
    ) -> None:
        """Update the carrier status cells at ``$0400`` and ``$0427``."""

        if leading_cell is not None:
            self.poke_screen_byte(self._CARRIER_LEADING_SCREEN_ADDRESS, leading_cell)
        if indicator_cell is not None:
            self.poke_screen_byte(
                self._CARRIER_INDICATOR_SCREEN_ADDRESS, indicator_cell
            )

        if leading_colour is not None:
            self.poke_colour_byte(
                self._colour_address_for(self._CARRIER_LEADING_SCREEN_ADDRESS),
                leading_colour,
            )

        if indicator_colour is not None:
            self.poke_colour_byte(
                self._colour_address_for(self._CARRIER_INDICATOR_SCREEN_ADDRESS),
                indicator_colour,
            )

    def push_macro_slot(self, slot: int) -> GlyphRun | None:
        """Render a macro by slot identifier and mirror it to the console."""

        run = self.glyph_lookup.macros_by_slot.get(slot)
        if run is None:
            return None
        payload = bytes(run.payload)
        if payload:
            self.device.write(payload)
        return run

    def stage_macro_slot(
        self,
        slot: int,
        *,
        fill_colour: int | None = None,
    ) -> GlyphRun | None:
        """Stage macro ``slot`` into ``tempbott+40``/``var_4078`` buffers."""

        run = self.glyph_lookup.macros_by_slot.get(slot)
        if run is None:
            return None

        glyph_slice, colour_slice = self._macro_slot_overlay_spans(
            slot,
            run,
            fill_colour=fill_colour,
        )

        self.stage_masked_pane_overlay(
            glyph_slice,
            colour_slice,
            fill_colour=fill_colour,
        )

        return run

    def push_flag_macro(self, flag_index: int) -> GlyphRun | None:
        """Render the macro associated with ``flag_index`` via dispatch data."""

        for entry in self.device.flag_dispatch.entries:
            if entry.flag_index == flag_index:
                slot = entry.slot
                if slot in self._MASKED_OVERLAY_FLAG_SLOTS:
                    run = self.stage_macro_slot(slot)
                    if run is None:
                        fallback_overlay = self.masked_pane_staging_map.fallback_overlay_for_slot(slot)
                        if fallback_overlay is not None:
                            glyphs, colours = fallback_overlay
                            self.stage_masked_pane_overlay(glyphs, colours)
                        else:
                            fallback = self.glyph_lookup.macros_by_slot.get(slot)
                            if fallback is not None:
                                glyph_slice, colour_slice = self._macro_slot_overlay_spans(
                                    slot,
                                    fallback,
                                    fill_colour=None,
                                )
                                self.stage_masked_pane_overlay(glyph_slice, colour_slice)
                return self.push_macro_slot(slot)
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

    def register_console_device(self, console: Console | None = None) -> ConsoleService:
        """Register a console device and expose the service wrapper."""

        device = console or Console()
        self.register(device.name, device)
        service = ConsoleService(device)
        self.register_service(service.name, service)
        return service

    def register_modem_device(
        self,
        modem: Modem | None = None,
        *,
        transport: ModemTransport | None = None,
    ) -> Modem:
        """Register a modem device and expose it as a service."""

        if modem is not None and transport is not None:
            raise ValueError("provide either modem or transport, not both")

        device = modem
        if device is None:
            device = Modem(transport=transport) if transport is not None else Modem()
        elif transport is not None:
            device.transport = transport

        previous = self.devices.get(device.name)
        if isinstance(previous, Modem) and previous is not device:
            previous.close()

        self.register(device.name, device)
        self.register_service(device.name, device)
        return device

    def register_ampersand_dispatcher(
        self,
        *,
        registry: "AmpersandRegistry" | None = None,
        override_imports: Mapping[int, str] | None = None,
    ) -> "AmpersandDispatcher":
        """Wire an :class:`AmpersandDispatcher` into the service map."""

        if registry is None:
            from ..ampersand_registry import AmpersandRegistry

            registry = AmpersandRegistry(
                services=self.services, override_imports=override_imports
            )
        from ..ampersand_dispatcher import AmpersandDispatcher

        dispatcher = AmpersandDispatcher(registry=registry)
        self.register_service(dispatcher.name, dispatcher)
        return dispatcher

    def open(self, device_name: str, logical_number: int, secondary_address: int) -> LogicalChannel:
        if device_name not in self.devices:
            raise DeviceError(f"no such device '{device_name}'")
        descriptor = ChannelDescriptor(device=device_name, logical_number=logical_number, secondary_address=secondary_address)
        device = self.devices[device_name]
        channel = device.open(descriptor)
        self.close(logical_number, secondary_address)
        self.channels[(logical_number, secondary_address)] = channel
        if secondary_address == 15:
            self.command_channels[logical_number] = channel
        return channel

    def open_file(
        self,
        slot: int,
        logical_number: int,
        filename: str,
        secondary_address: int,
    ) -> LogicalChannel:
        device_name = self.drive_device_name(slot)
        try:
            device = self.devices[device_name]
        except KeyError as exc:
            raise DeviceError(f"drive slot {slot}: no disk drive registered") from exc
        if not isinstance(device, DiskDrive):
            raise DeviceError(f"{device_name}: device does not support file channels")
        descriptor = ChannelDescriptor(
            device=device_name,
            logical_number=logical_number,
            secondary_address=secondary_address,
        )
        channel = device.open_file(descriptor, filename)
        self.close(logical_number, secondary_address)
        self.channels[(logical_number, secondary_address)] = channel
        return channel

    def close(self, logical_number: int, secondary_address: int) -> None:
        channel = self.channels.pop((logical_number, secondary_address), None)
        if secondary_address == 15:
            self.command_channels.pop(logical_number, None)
        if channel is not None:
            channel.close()

    def issue_command(self, logical_number: int, command: str) -> str:
        channel = self.command_channels.get(logical_number)
        if channel is None:
            raise DeviceError(f"logical {logical_number}: no command channel open")
        device = self.devices[channel.descriptor.device]
        response = device.command(command)
        channel.write(response + "\r")
        return response

    @staticmethod
    def drive_device_name(slot: int) -> str:
        return f"drive{slot}"

    def drive_directory_lines(self, slot: int, *, refresh: bool = False) -> Tuple[str, ...]:
        device_name = self.drive_device_name(slot)
        if device_name not in self.devices:
            raise DeviceError(f"drive slot {slot}: no disk drive registered")
        if refresh or not self.directory_cache[device_name]:
            response = self.issue_command(slot, "$")
            parts = response.split(",", maxsplit=3)
            listing: Tuple[str, ...]
            if len(parts) > 1 and parts[1]:
                listing = tuple(parts[1].split("\r"))
            else:
                listing = tuple()
            self.directory_cache[device_name] = listing
        return self.directory_cache[device_name]

    def read_directory(self, device_name: str, refresh: bool = False) -> Tuple[str, ...]:
        if not device_name.startswith("drive"):
            raise DeviceError(
                "read_directory expects a Commodore-style drive name; use drive_directory_lines for slots"
            )
        try:
            slot = int(device_name[5:])
        except ValueError as exc:
            raise DeviceError(f"{device_name!r} is not a numeric drive slot") from exc
        return self.drive_directory_lines(slot, refresh=refresh)

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


def bootstrap_device_context(
    assignments: Iterable[DriveAssignment],
    *,
    ampersand_overrides: Mapping[int, str] | None = None,
) -> DeviceContext:
    """Instantiate a device context with modern drive mappings."""

    context = DeviceContext()
    console_service = context.register_console_device()
    context.register_modem_device()
    context.register_ampersand_dispatcher(override_imports=ampersand_overrides)
    context.register_service("device_context", context)
    masked_pane_buffers = MaskedPaneBuffers()
    console_service.capture_masked_pane_buffers(masked_pane_buffers)
    console_service.set_masked_pane_buffers(masked_pane_buffers)
    context.register_service("masked_pane_buffers", masked_pane_buffers)
    for assignment in assignments:
        locator = assignment.locator
        if isinstance(locator, FilesystemDriveLocator):
            device_name = context.drive_device_name(assignment.slot)
            context.register(device_name, DiskDrive(locator.path))
            context.open(device_name, assignment.slot, 15)
    return context


__all__ = [
    "ChannelDescriptor",
    "Console",
    "ConsoleService",
    "ConsoleFramePayload",
    "ConsoleRegionBuffer",
    "DeviceContext",
    "DeviceError",
    "DiskDrive",
    "bootstrap_device_context",
    "LogicalChannel",
    "LoopbackModemTransport",
    "MaskedPaneBlinkState",
    "MaskedPaneBuffers",
    "MaskedPaneGlyphPayload",
    "Modem",
    "ModemChannel",
    "ModemTransport",
    "SequentialFileChannel",
]


def _mirror_prototype_module() -> None:
    try:
        import scripts.prototypes.device_context as _prototype_device_context  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - prototype mirrors optional at runtime
        return

    for _name in __all__:
        setattr(_prototype_device_context, _name, globals()[_name])

    try:
        import scripts.prototypes.ampersand_registry as _prototype_ampersand_registry  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - prototype mirrors optional at runtime
        pass
    else:
        _prototype_ampersand_registry.ConsoleService = ConsoleService

    try:
        import scripts.prototypes.runtime.ampersand_overrides as _prototype_ampersand_overrides  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - prototype mirrors optional at runtime
        _prototype_ampersand_overrides = None
    else:
        _prototype_ampersand_overrides.ConsoleService = ConsoleService
        _prototype_ampersand_overrides.MaskedPaneBuffers = MaskedPaneBuffers
        _prototype_ampersand_overrides.DeviceContext = DeviceContext
        _prototype_ampersand_overrides.DeviceError = DeviceError

    for _module_name in (
        "scripts.prototypes.runtime.main_menu",
        "scripts.prototypes.runtime.file_transfers",
        "scripts.prototypes.runtime.sysop_options",
        "scripts.prototypes.runtime.session_runner",
        "scripts.prototypes.runtime.cli",
    ):
        try:
            _module = import_module(_module_name)  # type: ignore[import-not-found]
        except ModuleNotFoundError:  # pragma: no cover - prototype mirrors optional at runtime
            continue
        if hasattr(_module, "ConsoleService"):
            setattr(_module, "ConsoleService", ConsoleService)
        if hasattr(_module, "MaskedPaneBuffers"):
            setattr(_module, "MaskedPaneBuffers", MaskedPaneBuffers)
        if hasattr(_module, "DeviceContext"):
            setattr(_module, "DeviceContext", DeviceContext)
        if hasattr(_module, "DeviceError"):
            setattr(_module, "DeviceError", DeviceError)


_mirror_prototype_module()
