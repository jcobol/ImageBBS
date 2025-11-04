"""Runtime main-menu dispatcher that mirrors the ImageBBS ``ON...GOTO`` flow."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar, Iterable, Mapping, Optional

from ..ampersand_dispatcher import AmpersandDispatcher
from ..ampersand_registry import AmpersandRegistry
from ..device_context import ConsoleService
from ..message_editor import MessageEditor
from ..session_kernel import SessionKernel, SessionModule, SessionState
from .configuration_editor import ConfigurationEditorModule
from .file_transfers import FileTransfersModule
from .macro_rendering import render_masked_macro
from .masked_pane_staging import MaskedPaneMacro
from .sysop_options import SysopOptionsModule


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
    CONFIGURATION_EDITOR = auto()
    EXIT = auto()
    CHAT = auto()
    TIME = auto()
    UNKNOWN = auto()


@dataclass
class MainMenuModule:
    """State-machine facade that reproduces the BASIC main-menu dispatcher."""

    registry: Optional[AmpersandRegistry] = None
    message_editor_factory: type[SessionModule] = MessageEditor
    file_transfers_factory: type[SessionModule] = FileTransfersModule
    sysop_options_factory: type[SessionModule] = SysopOptionsModule
    configuration_editor_factory: type[SessionModule] = ConfigurationEditorModule
    state: MenuState = field(init=False, default=MenuState.INTRO)
    rendered_slots: list[int] = field(init=False, default_factory=list)
    _console: ConsoleService | None = field(init=False, default=None)
    _dispatcher: AmpersandDispatcher | None = field(init=False, default=None)

    MENU_HEADER_MACRO = MaskedPaneMacro.MAIN_MENU_HEADER
    MENU_PROMPT_MACRO = MaskedPaneMacro.MAIN_MENU_PROMPT
    INVALID_SELECTION_MACRO = MaskedPaneMacro.MAIN_MENU_INVALID

    _DEFAULT_MACRO_SLOTS: ClassVar[Mapping[MaskedPaneMacro, int]] = {
        MENU_HEADER_MACRO: 0x04,
        MENU_PROMPT_MACRO: 0x09,
        INVALID_SELECTION_MACRO: 0x0D,
        MaskedPaneMacro.FILE_TRANSFERS_HEADER: 0x28,
        MaskedPaneMacro.FILE_TRANSFERS_PROMPT: 0x29,
        MaskedPaneMacro.FILE_TRANSFERS_INVALID: 0x2A,
        MaskedPaneMacro.SYSOP_HEADER: 0x20,
        MaskedPaneMacro.SYSOP_PROMPT: 0x21,
        MaskedPaneMacro.SYSOP_SAYING_PREAMBLE: 0x22,
        MaskedPaneMacro.SYSOP_SAYING_OUTPUT: 0x23,
        MaskedPaneMacro.SYSOP_INVALID: 0x24,
        MaskedPaneMacro.SYSOP_ABORT: 0x25,
        MaskedPaneMacro.FLAG_MAIN_MENU_HEADER: 0x04,
        MaskedPaneMacro.FLAG_MAIN_MENU_PROMPT: 0x09,
        MaskedPaneMacro.FLAG_MAIN_MENU_INVALID: 0x0D,
        MaskedPaneMacro.FLAG_SAYINGS_ENABLE: 0x14,
        MaskedPaneMacro.FLAG_SAYINGS_DISABLE: 0x15,
        MaskedPaneMacro.FLAG_SAYINGS_PROMPT_ENABLE: 0x16,
        MaskedPaneMacro.FLAG_SAYINGS_PROMPT_DISABLE: 0x17,
        MaskedPaneMacro.FLAG_PROMPT_ENABLE: 0x18,
        MaskedPaneMacro.FLAG_PROMPT_DISABLE: 0x19,
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

    _COMMAND_TRANSITIONS: ClassVar[Mapping[MenuCommand, SessionState]] = {
        MenuCommand.MESSAGE_BASE: SessionState.MESSAGE_EDITOR,
        MenuCommand.FILE_TRANSFERS: SessionState.FILE_TRANSFERS,
        MenuCommand.SYSOP: SessionState.SYSOP_OPTIONS,
        MenuCommand.CONFIGURATION_EDITOR: SessionState.CONFIGURATION_EDITOR,
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
    _CONFIGURATION_CODES: Iterable[str] = frozenset({"CF"})
    _EXIT_CODES: Iterable[str] = frozenset({"EX", "LG", "AT", "Q"})
    _CHAT_CODES: Iterable[str] = frozenset({"C", "CHAT"})
    _TIME_CODES: Iterable[str] = frozenset({"T", "TIME"})

    # Why: attach supporting modules so menu selections transition to their handlers.
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
        if self.configuration_editor_factory is not None:
            kernel.register_module(
                SessionState.CONFIGURATION_EDITOR,
                self.configuration_editor_factory(),
            )
        self.state = MenuState.INTRO
        self._render_intro()
        return SessionState.MAIN_MENU

    # Why: translate menu events into macro renders and cross-module transitions.
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
                self._render_macro(self.INVALID_SELECTION_MACRO)
                return SessionState.MAIN_MENU
            if command is MenuCommand.CHAT:
                self._handle_chat_request(kernel, selection)
                return SessionState.MAIN_MENU
            if command is MenuCommand.TIME:
                self._handle_time_request(kernel)
                return SessionState.MAIN_MENU

            next_state = self._COMMAND_TRANSITIONS.get(command, SessionState.MAIN_MENU)
            if next_state is SessionState.EXIT:
                return SessionState.EXIT
            if next_state is not SessionState.MAIN_MENU:
                return next_state
            return SessionState.MAIN_MENU

        raise ValueError(f"unsupported main-menu event: {event!r}")

    # Internal helpers -----------------------------------------------------

    # Why: map textual selections to high-level command groups.
    def _parse_selection(self, selection: Optional[str]) -> MenuCommand:
        if not selection:
            return MenuCommand.NONE
        text = selection.strip().upper()
        if not text:
            return MenuCommand.NONE
        uppercase = text.upper()
        token = uppercase
        for delimiter in (" ", ":"):
            if delimiter in token:
                token = token.split(delimiter, 1)[0]
        if token in self._CHAT_CODES:
            return MenuCommand.CHAT
        if token in self._TIME_CODES:
            return MenuCommand.TIME
        prefix = uppercase[:2]
        if prefix in self._EXIT_CODES or uppercase in self._EXIT_CODES:
            return MenuCommand.EXIT
        if prefix in self._MESSAGE_CODES:
            return MenuCommand.MESSAGE_BASE
        if prefix in self._TRANSFER_CODES:
            return MenuCommand.FILE_TRANSFERS
        if prefix in self._SYSOP_CODES:
            return MenuCommand.SYSOP
        if prefix in self._CONFIGURATION_CODES:
            return MenuCommand.CONFIGURATION_EDITOR
        return MenuCommand.UNKNOWN

    # Why: handle chat dispatch so console prompts mirror the BASIC runtime guard behaviour.
    def _handle_chat_request(
        self,
        kernel: SessionKernel,
        selection: Optional[str],
    ) -> None:
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        tracker = kernel.services.get("chat")
        if tracker is None:
            tracker = kernel.service_map.get("chat")
        is_page_active_attr = getattr(tracker, "is_page_active", None)
        if callable(is_page_active_attr):
            page_active = bool(is_page_active_attr())
        elif is_page_active_attr is not None:
            page_active = bool(is_page_active_attr)
        else:
            page_active = False
        device = self._console.device
        if page_active:
            device.write("Page is On.\r")
            self._restage_prompt_overlay()
            return

        raw_selection = (selection or "").strip()
        reason = ""
        if raw_selection:
            upper_selection = raw_selection.upper()
            resolved_alias = ""
            for candidate in sorted(self._CHAT_CODES, key=len, reverse=True):
                if upper_selection.startswith(candidate):
                    resolved_alias = candidate
                    break
            if resolved_alias:
                reason = raw_selection[len(resolved_alias) :].lstrip(" :")
            else:
                reason = raw_selection
        device.write(f"C: {reason}\r" if reason else "C: \r")
        request_chat = getattr(tracker, "request_chat", None)
        if callable(request_chat):
            request_chat(reason)
        self._restage_prompt_overlay()

    # Why: keep the menu prompt macro in sync after console chat interactions.
    def _restage_prompt_overlay(self) -> None:
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        staging_map = self._console.masked_pane_staging_map
        slot = render_masked_macro(
            console=self._console,
            dispatcher=self._dispatcher,
            macro=self.MENU_PROMPT_MACRO,
            staging_map=staging_map,
            default_slot=self._DEFAULT_MACRO_SLOTS[self.MENU_PROMPT_MACRO],
        )
        self.rendered_slots.append(slot)
        staging_map.stage_flag_index(self._console, 0)

    # Why: surface session timing details so the BASIC T command has a modern analogue.
    def _handle_time_request(self, kernel: SessionKernel) -> None:
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")

        service_lookup = kernel.services.get("session_runner")
        if service_lookup is None:
            service_lookup = kernel.service_map.get("session_runner")

        logon_text = "Unavailable"
        current_text = "Unavailable"
        remaining_text = "Infinite"

        if service_lookup is not None:
            logon_fn = getattr(service_lookup, "formatted_logon_time", None)
            current_fn = getattr(service_lookup, "formatted_current_time", None)
            remaining_fn = getattr(service_lookup, "formatted_minutes_remaining", None)

            if callable(logon_fn):
                logon_text = str(logon_fn())
            if callable(current_fn):
                current_text = str(current_fn())
            if callable(remaining_fn):
                remaining_text = str(remaining_fn())

        device = self._console.device
        device.write(f"Logon Time: {logon_text}\r")
        device.write(f"Current Time: {current_text}\r")
        device.write(f"Minutes Left: {remaining_text}\r")
        self._restage_prompt_overlay()

    # Why: centralise masked-pane rendering so intro and errors reuse shared staging.
    def _render_macro(self, macro: MaskedPaneMacro) -> None:
        if self.registry is None:
            raise RuntimeError("ampersand registry has not been initialised")
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        staging_map = self._console.masked_pane_staging_map
        slot = render_masked_macro(
            console=self._console,
            dispatcher=self._dispatcher,
            macro=macro,
            staging_map=staging_map,
            default_slot=self._DEFAULT_MACRO_SLOTS[macro],
        )
        self.rendered_slots.append(slot)

    def _render_intro(self) -> None:
        self._render_macro(self.MENU_HEADER_MACRO)
        self._render_macro(self.MENU_PROMPT_MACRO)

    def _macro_slot(self, macro: MaskedPaneMacro) -> int:
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        staging_map = self._console.masked_pane_staging_map
        try:
            return staging_map.slot(macro)
        except KeyError:
            return self._DEFAULT_MACRO_SLOTS[macro]


__all__ = [
    "MainMenuEvent",
    "MainMenuModule",
    "MenuCommand",
    "MenuState",
]
