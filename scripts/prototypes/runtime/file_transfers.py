"""Runtime approximation of the ImageBBS file-transfer dispatcher."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from ..ampersand_dispatcher import AmpersandDispatcher
from ..ampersand_registry import AmpersandRegistry
from ..device_context import ConsoleService
from ..session_kernel import SessionKernel, SessionState


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
    _console: ConsoleService | None = field(init=False, default=None)
    _dispatcher: AmpersandDispatcher | None = field(init=False, default=None)

    # The BASIC source initialises the menu with ``&,28`` before prompting for a
    # command.  Slot ``$28`` mirrors that macro while ``$29`` and ``$2a`` track
    # the prompt loop and the ``?`` error shown for invalid selections.
    MENU_HEADER_SLOT = 0x28
    MENU_PROMPT_SLOT = 0x29
    INVALID_SELECTION_SLOT = 0x2A

    # Command groups recovered from ``im.txt`` lines 1812-1889.  The dispatcher
    # reduces selections to their first two characters (``left$(an$,2)``) while
    # also branching on the leading character.  The modern port mirrors that
    # behaviour by normalising the input before categorising it.
    _KNOWN_COMMANDS: frozenset[str] = frozenset(
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
    _EXIT_COMMANDS: frozenset[str] = frozenset({"Q", "EX", "LG", "AT", "BA", "EP", "QM"})

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
        self._render_intro()
        return SessionState.FILE_TRANSFERS

    def handle_event(
        self,
        kernel: SessionKernel,
        event: FileTransferEvent,
        selection: Optional[str] = None,
    ) -> SessionState:
        """Render macros and translate text commands to :class:`SessionState`."""

        if event is FileTransferEvent.ENTER:
            self._render_intro()
            self.state = FileTransferMenuState.READY
            return SessionState.FILE_TRANSFERS

        if event is FileTransferEvent.COMMAND:
            if self.state is not FileTransferMenuState.READY:
                self._render_intro()
                self.state = FileTransferMenuState.READY
                return SessionState.FILE_TRANSFERS

            normalised = self._normalise_command(selection)
            if not normalised:
                self._render_prompt()
                return SessionState.FILE_TRANSFERS

            if normalised in self._EXIT_COMMANDS:
                self.last_command = normalised
                return SessionState.MAIN_MENU

            if normalised in self._KNOWN_COMMANDS:
                self.last_command = normalised
                self._render_prompt()
                return SessionState.FILE_TRANSFERS

            self._render_macro(self.INVALID_SELECTION_SLOT)
            self._render_prompt()
            return SessionState.FILE_TRANSFERS

        raise ValueError(f"unsupported file-transfer event: {event!r}")

    # Internal helpers -----------------------------------------------------

    def _render_intro(self) -> None:
        self._render_macro(self.MENU_HEADER_SLOT)
        self._render_prompt()

    def _render_prompt(self) -> None:
        self._render_macro(self.MENU_PROMPT_SLOT)

    def _render_macro(self, slot: int) -> None:
        if self.registry is None:
            raise RuntimeError("ampersand registry has not been initialised")
        defaults = self.registry.defaults
        if slot not in defaults.macros_by_slot:
            raise KeyError(f"macro slot ${slot:02x} missing from defaults")
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        staged = self._console.stage_macro_slot(slot)
        if staged is None:
            raise RuntimeError(f"console failed to stage macro slot ${slot:02x}")
        if slot == self.MENU_PROMPT_SLOT:
            self._commit_masked_overlay()
            restaged = self._console.stage_macro_slot(slot)
            if restaged is None:  # pragma: no cover - defensive guard
                raise RuntimeError(
                    f"console failed to restage macro slot ${slot:02x}"
                )
        self._console.push_macro_slot(slot)
        self.rendered_slots.append(slot)

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

    def _commit_masked_overlay(self) -> None:
        dispatcher = self._dispatcher
        if dispatcher is not None:
            dispatcher.dispatch("&,50")
            return
        if isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            self._console.commit_masked_pane_staging()
            return
        raise RuntimeError("console service is unavailable")


__all__ = [
    "FileTransferEvent",
    "FileTransferMenuState",
    "FileTransfersModule",
]

