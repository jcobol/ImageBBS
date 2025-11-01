"""Runtime approximation of the ImageBBS file-transfer dispatcher."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar, Iterable, Mapping, Optional, Literal

from ..ampersand_dispatcher import AmpersandDispatcher
from ..ampersand_registry import AmpersandRegistry
from ..device_context import ConsoleService, ModemTransport
from ..session_kernel import SessionKernel, SessionState
from .file_library import FileLibraryModule
from .file_transfer_protocols import (
    FileTransferAborted,
    FileTransferError,
    FileTransferProtocolDriver,
    build_protocol_driver,
)
from .macro_rendering import render_macro_with_overlay_commit
from .masked_pane_staging import MaskedPaneMacro

class FileTransferMenuState(Enum):
    """Internal states exposed by :class:`FileTransfersModule`."""

    INTRO = auto()
    READY = auto()


class FileTransferEvent(Enum):
    """Events that drive menu rendering and command handling."""

    ENTER = auto()
    COMMAND = auto()


@dataclass(frozen=True)
class TransferCommandSpec:
    """Declarative metadata describing how each transfer command behaves."""

    direction: Literal["upload", "download"]
    default_protocol: str | None = None


@dataclass
class TransferSessionState:
    """Mutable bookkeeping staged between transfer operations."""

    upload_payloads: dict[str, bytes] = field(default_factory=dict)
    completed_uploads: dict[str, bytes] = field(default_factory=dict)
    completed_downloads: dict[str, bytes] = field(default_factory=dict)
    credits: int = 0
    abort_requested: bool = False
    progress_events: list[tuple[str, int, Optional[int]]] = field(
        default_factory=list
    )


@dataclass
class FileTransfersModule:
    """Finite-state approximation of the BASIC file-transfer dispatcher."""

    default_protocol: str = "Punter"
    registry: Optional[AmpersandRegistry] = None
    state: FileTransferMenuState = field(init=False, default=FileTransferMenuState.INTRO)
    rendered_slots: list[int] = field(init=False, default_factory=list)
    last_command: str = field(init=False, default="")
    active_drive_slot: int = field(init=False, default=1)
    _console: ConsoleService | None = field(init=False, default=None)
    _dispatcher: AmpersandDispatcher | None = field(init=False, default=None)
    library_module_factory: type[FileLibraryModule] = FileLibraryModule
    transfer_state_factory: type[TransferSessionState] = TransferSessionState
    _transfer_state: TransferSessionState | None = field(init=False, default=None)
    _active_protocol: str | None = field(init=False, default=None)

    MENU_HEADER_MACRO = MaskedPaneMacro.FILE_TRANSFERS_HEADER
    MENU_PROMPT_MACRO = MaskedPaneMacro.FILE_TRANSFERS_PROMPT
    INVALID_SELECTION_MACRO = MaskedPaneMacro.FILE_TRANSFERS_INVALID

    _DEFAULT_MACRO_SLOTS: ClassVar[dict[MaskedPaneMacro, int]] = {
        MENU_HEADER_MACRO: 0x28,
        MENU_PROMPT_MACRO: 0x29,
        INVALID_SELECTION_MACRO: 0x2A,
    }

    _BINARY_STREAM_COMMANDS: ClassVar[frozenset[str]] = frozenset(
        {"UD", "UL", "UX", "VB", "BB", "RF"}
    )
    _LIBRARY_COMMAND_CODES: ClassVar[dict[str, str]] = {
        "UD": "UD",
        "UL": "UD",
        "UX": "UX",
        "VB": "VB",
        "BB": "BB",
        "RF": "RF",
    }
    _TRANSFER_COMMAND_SPECS: ClassVar[dict[str, TransferCommandSpec]] = {
        "UL": TransferCommandSpec(direction="upload", default_protocol="Xmodem CRC"),
        "UD": TransferCommandSpec(direction="download", default_protocol="Xmodem CRC"),
        "UX": TransferCommandSpec(direction="upload", default_protocol="Xmodem 1K"),
        "VB": TransferCommandSpec(direction="download", default_protocol="Punter"),
        "BB": TransferCommandSpec(direction="download", default_protocol="Punter-C"),
        "RF": TransferCommandSpec(direction="download", default_protocol="Multi-Punter"),
    }

    @property
    def MENU_HEADER_SLOT(self) -> int:
        return self._macro_slot(self.MENU_HEADER_MACRO)

    @property
    def MENU_PROMPT_SLOT(self) -> int:
        return self._macro_slot(self.MENU_PROMPT_MACRO)

    @property
    def INVALID_SELECTION_SLOT(self) -> int:
        return self._macro_slot(self.INVALID_SELECTION_MACRO)

    @property
    # Why: expose transfer bookkeeping so tests and auxiliary modules can stage payloads.
    def transfer_state(self) -> TransferSessionState:
        state = self._transfer_state
        if state is None:
            state = self.transfer_state_factory()
            self._transfer_state = state
        return state

    # Command groups recovered from ``im.txt`` lines 1812-1889.  The dispatcher
    # reduces selections to their first two characters (``left$(an$,2)``) while
    # also branching on the leading character.  The modern port mirrors that
    # behaviour by normalising the input before categorising it.
    _KNOWN_COMMANDS: ClassVar[frozenset[str]] = frozenset(
        {
            "ED",
            "PC",
            "CP",
            "WF",
            "R",
            "O",
            "Q",
            "{F2}",
            "{F2:2}",
            "PF",
            "TF",
            "NF",
            "MF",
            "RF",
            "SB",
            "EM",
            "UD",
            "UL",
            "UX",
            "VB",
            "BB",
            "RD",
            "DC",
            "CA",
            "DR",
            "BF",
            "NL",
            "CD",
            "MM",
            "LD",
            "ST",
            "EX",
            "BA",
            "EP",
            "QM",
            "LG",
            "AT",
            "XP",
            "SY",
            "NU",
            "CF",
            "OR",
            "C",
            "T",
            "F",
            "PM",
            "ZZ",
        }
    )
    _EXIT_COMMANDS: ClassVar[frozenset[str]] = frozenset(
        {"Q", "EX", "LG", "AT", "BA", "EP", "QM"}
    )

    # Why: wire services, reset session state, and honour persisted protocol defaults.
    def start(self, kernel: SessionKernel) -> SessionState:
        """Bind runtime services and render the introductory macros."""

        self._dispatcher = kernel.dispatcher
        self.registry = kernel.dispatcher.registry
        console = kernel.services.get("console")
        if not isinstance(console, ConsoleService):
            raise TypeError("console service missing from session kernel")
        self._console = console
        self.rendered_slots.clear()
        self.last_command = ""
        self.state = FileTransferMenuState.INTRO
        self._set_binary_streaming(kernel, False)
        self.active_drive_slot = self._resolve_initial_drive_slot(kernel)
        self._transfer_state = self.transfer_state_factory()
        self._active_protocol = self._resolve_initial_protocol(kernel)
        self._render_intro()
        return SessionState.FILE_TRANSFERS

    # Why: translate masked-pane selections into state transitions and auxiliary module launches.
    def handle_event(
        self,
        kernel: SessionKernel,
        event: FileTransferEvent,
        selection: Optional[str] = None,
    ) -> SessionState:
        """Render macros and translate text commands to :class:`SessionState`."""

        if self._matches_event(event, FileTransferEvent.ENTER):
            self._render_intro()
            self.state = FileTransferMenuState.READY
            self._set_binary_streaming(kernel, False)
            return SessionState.FILE_TRANSFERS

        if self._matches_event(event, FileTransferEvent.COMMAND):
            if self.state is not FileTransferMenuState.READY:
                self._render_intro()
                self.state = FileTransferMenuState.READY
                self._set_binary_streaming(kernel, False)
                return SessionState.FILE_TRANSFERS

            normalised = self._normalise_command(selection)
            if not normalised:
                self._render_prompt()
                self._set_binary_streaming(kernel, False)
                return SessionState.FILE_TRANSFERS

            if normalised in self._EXIT_COMMANDS:
                self.last_command = normalised
                self._set_binary_streaming(kernel, False)
                return SessionState.MAIN_MENU

            if normalised in self._TRANSFER_COMMAND_SPECS:
                self.last_command = normalised
                spec = self._TRANSFER_COMMAND_SPECS[normalised]
                fallback_code = self._LIBRARY_COMMAND_CODES.get(normalised)
                self._set_binary_streaming(kernel, True)
                try:
                    self._execute_transfer_command(kernel, normalised, spec)
                except FileTransferError:
                    if fallback_code is not None:
                        self._set_binary_streaming(kernel, False)
                        self._register_library_module(
                            kernel, fallback_code, normalised
                        )
                        return SessionState.FILE_LIBRARY
                    raise
                finally:
                    self._set_binary_streaming(kernel, False)
                self._render_prompt()
                return SessionState.FILE_TRANSFERS

            library_code = self._LIBRARY_COMMAND_CODES.get(normalised)
            if library_code is not None:
                self.last_command = normalised
                self._set_binary_streaming(kernel, False)
                self._register_library_module(kernel, library_code, normalised)
                return SessionState.FILE_LIBRARY

            if normalised == "RD":
                self.last_command = normalised
                lines = self._read_active_drive_directory(kernel)
                self._stream_directory_lines(lines)
                self._render_prompt()
                self._set_binary_streaming(kernel, False)
                return SessionState.FILE_TRANSFERS

            if normalised == "DR":
                self.last_command = normalised
                parsed_ok, requested_slot = self._parse_drive_slot_selection(selection)
                available_slots = self._available_drive_slots(kernel)
                if not parsed_ok:
                    self._render_macro(self.INVALID_SELECTION_MACRO)
                    self._render_prompt()
                    self._set_binary_streaming(kernel, False)
                    return SessionState.FILE_TRANSFERS

                target_slot = (
                    requested_slot
                    if requested_slot is not None
                    else self._next_available_drive_slot(available_slots)
                )

                if target_slot in available_slots:
                    self.active_drive_slot = target_slot
                    self._render_prompt()
                    self._set_binary_streaming(kernel, False)
                    return SessionState.FILE_TRANSFERS

                self._render_macro(self.INVALID_SELECTION_MACRO)
                self._render_prompt()
                self._set_binary_streaming(kernel, False)
                return SessionState.FILE_TRANSFERS

            if normalised in self._KNOWN_COMMANDS:
                self.last_command = normalised
                self._render_prompt()
                self._set_binary_streaming(
                    kernel, normalised in self._BINARY_STREAM_COMMANDS
                )
                return SessionState.FILE_TRANSFERS

            self._render_macro(self.INVALID_SELECTION_MACRO)
            self._render_prompt()
            self._set_binary_streaming(kernel, False)
            return SessionState.FILE_TRANSFERS

        raise ValueError(f"unsupported file-transfer event: {event!r}")

    # Internal helpers -----------------------------------------------------

    def _render_intro(self) -> None:
        self._render_macro(self.MENU_HEADER_MACRO)
        self._render_prompt()

    def _render_prompt(self) -> None:
        self._render_macro(self.MENU_PROMPT_MACRO)

    def _render_macro(self, macro: MaskedPaneMacro) -> None:
        if self.registry is None:
            raise RuntimeError("ampersand registry has not been initialised")
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        staging_map = self._console.masked_pane_staging_map
        try:
            spec = staging_map.spec(macro)
        except KeyError:
            slot = self._DEFAULT_MACRO_SLOTS[macro]
            fallback_overlay = staging_map.fallback_overlay_for_slot(slot)
        else:
            slot = spec.slot
            fallback_overlay = spec.fallback_overlay

        render_macro_with_overlay_commit(
            console=self._console,
            dispatcher=self._dispatcher,
            slot=slot,
            fallback_overlay=fallback_overlay,
        )
        self.rendered_slots.append(slot)

    def _macro_slot(self, macro: MaskedPaneMacro) -> int:
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        staging_map = self._console.masked_pane_staging_map
        try:
            return staging_map.slot(macro)
        except KeyError:
            return self._DEFAULT_MACRO_SLOTS[macro]

    # Why: allow non-stream commands to enter the interactive library dispatcher.
    def _register_library_module(
        self, kernel: SessionKernel, code: str, command: str
    ) -> None:
        module = self.library_module_factory(
            library_code=code, invoked_command=command
        )
        kernel.register_module(SessionState.FILE_LIBRARY, module)

    # Why: drive UL/UD command families through the requested modem protocol.
    def _execute_transfer_command(
        self,
        kernel: SessionKernel,
        command: str,
        spec: TransferCommandSpec,
    ) -> None:
        state = self.transfer_state
        protocol = self._resolve_protocol_for_command(kernel, command, spec)
        driver = build_protocol_driver(protocol)
        transport = self._resolve_transport(kernel)
        label = driver.name or protocol
        self._show_transfer_banner(command, label, spec)
        progress_callback = lambda transferred, total: self._report_progress(
            command, transferred, total
        )
        try:
            if spec.direction == "upload":
                payload = self._upload_payload_for(state, command)
                driver.upload(
                    transport,
                    payload,
                    progress_callback=progress_callback,
                    abort_checker=self._should_abort,
                )
                state.completed_uploads[command] = payload
                self._adjust_credits(state, +1)
                self._write_line("Upload complete.")
            else:
                payload = driver.download(
                    transport,
                    progress_callback=progress_callback,
                    abort_checker=self._should_abort,
                )
                state.completed_downloads[command] = payload
                self._adjust_credits(state, -1)
                self._write_line("Download complete.")
        except FileTransferAborted:
            self._write_line("Transfer aborted.")
        finally:
            self._clear_transfer_prompts()
            self._persist_protocol_preference(kernel, label)

    # Why: retrieve the modem transport registered with the session kernel.
    def _resolve_transport(self, kernel: SessionKernel) -> ModemTransport:
        context = getattr(kernel, "context", None)
        if context is None:
            raise RuntimeError("device context is unavailable")
        modem = context.get_service("modem")
        transport = getattr(modem, "transport", None)
        if not isinstance(transport, ModemTransport):
            raise RuntimeError("modem transport is unavailable")
        return transport

    # Why: respect manual defaults, library metadata, and persisted choices when selecting drivers.
    def _resolve_protocol_for_command(
        self,
        kernel: SessionKernel,
        command: str,
        spec: TransferCommandSpec,
    ) -> str:
        if spec.default_protocol:
            protocol = spec.default_protocol
        else:
            protocol = self._select_library_protocol(kernel, command)
            if not protocol:
                protocol = self._active_protocol or self.default_protocol
        if not protocol:
            protocol = self.default_protocol
        self._active_protocol = protocol
        return protocol

    # Why: read setup descriptors so menu defaults mirror the configured libraries.
    def _select_library_protocol(
        self, kernel: SessionKernel, command: str
    ) -> str | None:
        defaults = getattr(kernel, "defaults", None)
        if defaults is None:
            return None
        code = self._LIBRARY_COMMAND_CODES.get(command)
        if not code:
            return None
        try:
            libraries = defaults.libraries_for_code(code)
        except AttributeError:
            return None
        for descriptor in libraries:
            candidate = getattr(descriptor, "protocol", None)
            if isinstance(candidate, str) and candidate.strip():
                return candidate
        return None

    # Why: seed new sessions from persisted defaults when available.
    def _resolve_initial_protocol(self, kernel: SessionKernel) -> str:
        defaults = getattr(kernel, "defaults", None)
        if defaults is not None:
            candidate = getattr(defaults, "last_file_transfer_protocol", None)
            if isinstance(candidate, str) and candidate.strip():
                return candidate
        return self.default_protocol

    # Why: remember the caller's protocol choice for subsequent transfers.
    def _persist_protocol_preference(self, kernel: SessionKernel, protocol: str) -> None:
        self._active_protocol = protocol
        defaults = getattr(kernel, "defaults", None)
        if defaults is not None:
            object.__setattr__(defaults, "last_file_transfer_protocol", protocol)

    # Why: load staged upload data without tying tests to disk image plumbing.
    def _upload_payload_for(
        self, state: TransferSessionState, command: str
    ) -> bytes:
        payload = state.upload_payloads.get(command)
        if payload is None:
            payload = state.upload_payloads.get("*", b"")
        return bytes(payload or b"")

    # Why: track progress for console feedback and unit tests.
    def _report_progress(
        self, command: str, transferred: int, total: Optional[int]
    ) -> None:
        state = self.transfer_state
        state.progress_events.append((command, int(transferred), total))
        if not isinstance(self._console, ConsoleService):
            return
        device = getattr(self._console, "device", None)
        writer = getattr(device, "write", None)
        if not callable(writer):
            return
        if total is None:
            writer(f"{command}: {transferred} bytes\r")
        else:
            writer(f"{command}: {transferred}/{total} bytes\r")

    # Why: allow protocol drivers to poll for aborts without new dependencies.
    def _should_abort(self) -> bool:
        return bool(self.transfer_state.abort_requested)

    # Why: emulate ImageBBS credit adjustments after each transfer cycle.
    def _adjust_credits(self, state: TransferSessionState, delta: int) -> None:
        if delta >= 0:
            state.credits += delta
        else:
            state.credits = max(0, state.credits + delta)

    # Why: toggle pause/abort indicators while a transfer is active.
    def _set_transfer_indicators(self, active: bool) -> None:
        if not isinstance(self._console, ConsoleService):
            return
        if active:
            self._console.set_pause_indicator(ord("P"), colour=2)
            self._console.set_abort_indicator(ord("A"), colour=2)
        else:
            self._console.set_pause_indicator(0x20)
            self._console.set_abort_indicator(0x20)

    # Why: announce the chosen protocol before bytes begin streaming.
    def _show_transfer_banner(
        self, command: str, protocol: str, spec: TransferCommandSpec
    ) -> None:
        self._set_transfer_indicators(True)
        self._write_line(f"{command} via {protocol} ({spec.direction})")

    # Why: clear indicators once transfers complete or abort.
    def _clear_transfer_prompts(self) -> None:
        self._set_transfer_indicators(False)

    # Why: centralise console writes so prompts remain consistent.
    def _write_line(self, text: str) -> None:
        if not isinstance(self._console, ConsoleService):
            return
        device = getattr(self._console, "device", None)
        writer = getattr(device, "write", None)
        if callable(writer):
            writer(f"{text}\r")

    @staticmethod
    def _normalise_command(selection: Optional[str]) -> str:
        if not selection:
            return ""
        text = selection.strip().upper()
        if not text:
            return ""
        if text.startswith("{") and "}" in text:
            closing = text.find("}") + 1
            token = text[:closing]
            remainder = text[closing:].strip()
            if remainder:
                prefix = remainder[:2]
                return prefix
            return token
        return text[:2]

    def _parse_drive_slot_selection(
        self, selection: Optional[str]
    ) -> tuple[bool, Optional[int]]:
        """Validate and extract the slot requested by a ``DR`` command."""

        if not selection:
            return True, None
        text = selection.strip().upper()
        if not text.startswith("DR"):
            return False, None
        suffix = text[2:].strip()
        if not suffix:
            return True, None
        try:
            return True, int(suffix)
        except ValueError:
            return False, None

    def _next_available_drive_slot(self, slots: tuple[int, ...]) -> int:
        """Return the next configured slot after :attr:`active_drive_slot`."""

        if not slots:
            return self.active_drive_slot
        try:
            index = slots.index(self.active_drive_slot)
        except ValueError:
            return slots[0]
        return slots[(index + 1) % len(slots)]

    def _set_binary_streaming(self, kernel: SessionKernel, enabled: bool) -> None:
        context = getattr(kernel, "context", None)
        services: Mapping[str, object] | None = getattr(context, "services", None)
        transport = None
        if isinstance(services, Mapping):
            modem = services.get("modem")
            transport = getattr(modem, "transport", None)
        setter = getattr(transport, "set_binary_mode", None)
        if callable(setter):
            setter(enabled)

    def _resolve_initial_drive_slot(self, kernel: SessionKernel) -> int:
        defaults = getattr(kernel, "defaults", None)
        default_slot = None
        if defaults is not None:
            candidate = getattr(defaults, "default_filesystem_drive_slot", None)
            if isinstance(candidate, int) and candidate > 0:
                default_slot = candidate

        available_slots = self._available_drive_slots(kernel)
        if default_slot in available_slots:
            return default_slot
        if available_slots:
            return min(available_slots)
        if isinstance(default_slot, int) and default_slot > 0:
            return default_slot
        return 1

    def _available_drive_slots(self, kernel: SessionKernel) -> tuple[int, ...]:
        context = getattr(kernel, "context", None)
        slots: set[int] = set()
        devices = getattr(context, "devices", None)
        if isinstance(devices, Mapping):
            for name in devices:
                if not isinstance(name, str):
                    continue
                if not name.startswith("drive"):
                    continue
                try:
                    slot = int(name[5:])
                except ValueError:
                    continue
                slots.add(slot)
        if slots:
            return tuple(sorted(slots))

        defaults = getattr(kernel, "defaults", None)
        drives = getattr(defaults, "drives", ())
        try:
            iterable = iter(drives)
        except TypeError:
            return tuple()
        else:
            for assignment in iterable:
                slot = getattr(assignment, "slot", None)
                locator = getattr(assignment, "locator", None)
                scheme = getattr(locator, "scheme", None)
                if isinstance(slot, int) and scheme == "fs":
                    slots.add(slot)
        if slots:
            return tuple(sorted(slots))
        return tuple()

    def _read_active_drive_directory(self, kernel: SessionKernel) -> Iterable[str]:
        context = getattr(kernel, "context", None)
        if context is None:
            raise RuntimeError("device context is unavailable")
        reader = getattr(context, "drive_directory_lines", None)
        if not callable(reader):
            raise RuntimeError("device context does not expose directory listings")
        return reader(self.active_drive_slot, refresh=True)

    def _stream_directory_lines(self, lines: Iterable[str]) -> None:
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        device = getattr(self._console, "device", None)
        writer = getattr(device, "write", None)
        if not callable(writer):
            raise RuntimeError("console device is unavailable")
        for line in lines:
            writer(f"{line}\r")

    @staticmethod
    def _matches_event(candidate: object, expected: FileTransferEvent) -> bool:
        if candidate is expected:
            return True
        if isinstance(candidate, FileTransferEvent):
            return candidate == expected
        name = getattr(candidate, "name", None)
        if not isinstance(name, str):
            return False
        return name == expected.name


__all__ = [
    "FileTransferEvent",
    "FileTransferMenuState",
    "FileTransfersModule",
]

