"""Runtime approximation of the ImageBBS file-transfer dispatcher."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar, Iterable, Mapping, Optional

from ..ampersand_dispatcher import AmpersandDispatcher
from ..ampersand_registry import AmpersandRegistry
from ..device_context import ConsoleService
from ..session_kernel import SessionKernel, SessionState
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


@dataclass
class FileTransfersModule:
    """Finite-state approximation of the BASIC file-transfer dispatcher."""

    registry: Optional[AmpersandRegistry] = None
    state: FileTransferMenuState = field(init=False, default=FileTransferMenuState.INTRO)
    rendered_slots: list[int] = field(init=False, default_factory=list)
    last_command: str = field(init=False, default="")
    active_drive_slot: int = field(init=False, default=1)
    _console: ConsoleService | None = field(init=False, default=None)
    _dispatcher: AmpersandDispatcher | None = field(init=False, default=None)

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

    @property
    def MENU_HEADER_SLOT(self) -> int:
        return self._macro_slot(self.MENU_HEADER_MACRO)

    @property
    def MENU_PROMPT_SLOT(self) -> int:
        return self._macro_slot(self.MENU_PROMPT_MACRO)

    @property
    def INVALID_SELECTION_SLOT(self) -> int:
        return self._macro_slot(self.INVALID_SELECTION_MACRO)

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
        self._render_intro()
        return SessionState.FILE_TRANSFERS

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

