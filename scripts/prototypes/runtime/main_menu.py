"""Runtime main-menu dispatcher that mirrors the ImageBBS ``ON...GOTO`` flow."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar, Iterable, Mapping, Optional

from ..ampersand_dispatcher import AmpersandDispatcher
from ..ampersand_registry import AmpersandRegistry
from ..device_context import ConsoleService
from ..message_editor import MessageEditor
from .file_transfers import FileTransfersModule
from .sysop_options import SysopOptionsModule
from ..session_kernel import SessionKernel, SessionModule, SessionState
from .macro_rendering import render_macro_with_overlay_commit


class MenuState(Enum):
    """High-level phases exposed by :class:`MainMenuModule`."""

    INTRO = auto()
    READY = auto()


class MainMenuEvent(Enum):
    """Stimuli that drive menu rendering and command parsing."""

    ENTER = auto()
    SELECTION = auto()


class MenuCommand(Enum):
    """Semantic command groups translated from BASIC key handling."""

    NONE = auto()
    MESSAGE_BASE = auto()
    FILE_TRANSFERS = auto()
    SYSOP = auto()
    EXIT = auto()
    UNKNOWN = auto()


@dataclass
class MainMenuModule:
    """State-machine facade that reproduces the BASIC main-menu dispatcher."""

    registry: Optional[AmpersandRegistry] = None
    message_editor_factory: type[SessionModule] = MessageEditor
    file_transfers_factory: type[SessionModule] = FileTransfersModule
    sysop_options_factory: type[SessionModule] = SysopOptionsModule
    state: MenuState = field(init=False, default=MenuState.INTRO)
    rendered_slots: list[int] = field(init=False, default_factory=list)
    _console: ConsoleService | None = field(init=False, default=None)
    _dispatcher: AmpersandDispatcher | None = field(init=False, default=None)

    MENU_HEADER_SLOT = 0x04
    MENU_PROMPT_SLOT = 0x09
    INVALID_SELECTION_SLOT = 0x0D

    _COMMAND_TRANSITIONS: ClassVar[Mapping[MenuCommand, SessionState]] = {
        MenuCommand.MESSAGE_BASE: SessionState.MESSAGE_EDITOR,
        MenuCommand.FILE_TRANSFERS: SessionState.FILE_TRANSFERS,
        MenuCommand.SYSOP: SessionState.SYSOP_OPTIONS,
        MenuCommand.EXIT: SessionState.EXIT,
    }

    _MESSAGE_CODES: Iterable[str] = frozenset({
        "EM",
        "MF",
        "NF",
        "PF",
        "SB",
        "TF",
        "MB",
    })
    _TRANSFER_CODES: Iterable[str] = frozenset({
        "UD",
        "UL",
        "UX",
        "VB",
        "BB",
        "RF",
        "DR",
        "BF",
        "NL",
        "CD",
    })
    _SYSOP_CODES: Iterable[str] = frozenset({"SY"})
    _EXIT_CODES: Iterable[str] = frozenset({"EX", "LG", "AT", "Q"})

    def start(self, kernel: SessionKernel) -> SessionState:
        """Bind registry and register auxiliary modules with ``kernel``."""

        self._dispatcher = kernel.dispatcher
        self.registry = kernel.dispatcher.registry
        console = kernel.services.get("console")
        if not isinstance(console, ConsoleService):
            raise TypeError("console service missing from session kernel")
        self._console = console
        self.rendered_slots.clear()
        if self.message_editor_factory is not None:
            kernel.register_module(
                SessionState.MESSAGE_EDITOR, self.message_editor_factory()
            )
        if self.file_transfers_factory is not None:
            kernel.register_module(
                SessionState.FILE_TRANSFERS, self.file_transfers_factory()
            )
        if self.sysop_options_factory is not None:
            kernel.register_module(
                SessionState.SYSOP_OPTIONS, self.sysop_options_factory()
            )
        self.state = MenuState.INTRO
        self._render_intro()
        return SessionState.MAIN_MENU

    def handle_event(
        self,
        kernel: SessionKernel,
        event: MainMenuEvent,
        selection: Optional[str] = None,
    ) -> SessionState:
        """Render macros and translate selection text to :class:`SessionState`."""

        if event is MainMenuEvent.ENTER:
            self._render_intro()
            self.state = MenuState.READY
            return SessionState.MAIN_MENU

        if event is MainMenuEvent.SELECTION:
            if self.state is not MenuState.READY:
                self._render_intro()
                return SessionState.MAIN_MENU
            command = self._parse_selection(selection)
            if command is MenuCommand.UNKNOWN:
                self._render_macro(self.INVALID_SELECTION_SLOT)
                return SessionState.MAIN_MENU

            next_state = self._COMMAND_TRANSITIONS.get(command, SessionState.MAIN_MENU)
            if next_state is SessionState.EXIT:
                return SessionState.EXIT
            if next_state is not SessionState.MAIN_MENU:
                return next_state
            return SessionState.MAIN_MENU

        raise ValueError(f"unsupported main-menu event: {event!r}")

    # Internal helpers -----------------------------------------------------

    def _parse_selection(self, selection: Optional[str]) -> MenuCommand:
        if not selection:
            return MenuCommand.NONE
        text = selection.strip().upper()
        if not text:
            return MenuCommand.NONE
        prefix = text[:2]
        if prefix in self._EXIT_CODES or text in self._EXIT_CODES:
            return MenuCommand.EXIT
        if prefix in self._MESSAGE_CODES:
            return MenuCommand.MESSAGE_BASE
        if prefix in self._TRANSFER_CODES:
            return MenuCommand.FILE_TRANSFERS
        if prefix in self._SYSOP_CODES:
            return MenuCommand.SYSOP
        return MenuCommand.UNKNOWN

    def _render_macro(self, slot: int) -> None:
        if self.registry is None:
            raise RuntimeError("ampersand registry has not been initialised")
        defaults = self.registry.defaults
        if slot not in defaults.macros_by_slot:
            raise KeyError(f"macro slot ${slot:02x} missing from defaults")
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        render_macro_with_overlay_commit(
            console=self._console,
            dispatcher=self._dispatcher,
            slot=slot,
        )
        self.rendered_slots.append(slot)

    def _render_intro(self) -> None:
        self._render_macro(self.MENU_HEADER_SLOT)
        self._render_macro(self.MENU_PROMPT_SLOT)


__all__ = [
    "MainMenuEvent",
    "MainMenuModule",
    "MenuCommand",
    "MenuState",
]
