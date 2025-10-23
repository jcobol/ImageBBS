"""Runtime approximation of the ImageBBS file-transfer dispatcher."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Optional

from ..ampersand_dispatcher import AmpersandDispatcher
from ..ampersand_registry import AmpersandRegistry
from ..device_context import ConsoleService
from ..session_kernel import SessionKernel, SessionState
from .macro_rendering import render_macro_with_overlay_commit
from .masked_pane_staging import MaskedPaneMacro
from scripts.prototypes.runtime.file_transfers import (
    FileTransferEvent as PrototypeFileTransferEvent,
    FileTransferMenuState as PrototypeFileTransferMenuState,
)

FileTransferEvent = PrototypeFileTransferEvent
FileTransferMenuState = PrototypeFileTransferMenuState


@dataclass
class FileTransfersModule:
    """Finite-state approximation of the BASIC file-transfer dispatcher."""

    registry: Optional[AmpersandRegistry] = None
    state: FileTransferMenuState = field(init=False, default=FileTransferMenuState.INTRO)
    rendered_slots: list[int] = field(init=False, default_factory=list)
    last_command: str = field(init=False, default="")
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
            return SessionState.FILE_TRANSFERS

        if self._matches_event(event, FileTransferEvent.COMMAND):
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

            self._render_macro(self.INVALID_SELECTION_MACRO)
            self._render_prompt()
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

    @staticmethod
    def _matches_event(
        candidate: object, expected: PrototypeFileTransferEvent
    ) -> bool:
        if candidate is expected:
            return True
        if isinstance(candidate, PrototypeFileTransferEvent):
            return candidate == expected
        name = getattr(candidate, "name", None)
        if name is None:
            return False
        try:
            return PrototypeFileTransferEvent[name] is expected
        except KeyError:  # pragma: no cover - defensive guard
            return False


__all__ = [
    "FileTransferEvent",
    "FileTransferMenuState",
    "FileTransfersModule",
]

