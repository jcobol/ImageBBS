"""Runtime configuration editor that mirrors the documented menu layout."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar, Mapping, Optional

from ..device_context import ConsoleService
from ..session_kernel import SessionKernel, SessionState


class ConfigurationEditorState(Enum):
    """High-level phases exposed by :class:`ConfigurationEditorModule`."""

    INTRO = auto()
    READY = auto()


class ConfigurationEditorEvent(Enum):
    """Events that drive rendering and command handling."""

    ENTER = auto()
    COMMAND = auto()


@dataclass
class ConfigurationEditorModule:
    """Finite-state controller that mirrors the V2.0 configuration editor layout."""

    state: ConfigurationEditorState = field(init=False, default=ConfigurationEditorState.INTRO)
    last_selection: str = field(init=False, default="")
    _console: ConsoleService | None = field(init=False, default=None)

    MENU_ENTRIES: ClassVar[tuple[tuple[str, str], ...]] = (
        ("A", "Macros Editor"),
        ("B", "Command Set"),
        ("C", "Payroll Editor"),
        ("D", "Logon Editor"),
        ("E", "Access Groups"),
        ("F", "File Lists"),
        ("G", "Function Keys"),
        ("H", "Lightbar/Alarm"),
        ("I", "Misc. Features"),
        ("J", "Modem Config"),
        ("K", "Set Time"),
        ("L", "System Drives"),
        ("M", "Netmail Config"),
        ("N", "Quit"),
    )

    _ENTRY_LOOKUP: ClassVar[Mapping[str, str]] = {code: name for code, name in MENU_ENTRIES}
    _PROMPT: ClassVar[str] = "CONFIG> "
    _COLUMN_WIDTH: ClassVar[int] = 24

    # Why: bind console access and draw the dual-column menu before accepting commands.
    def start(self, kernel: SessionKernel) -> SessionState:
        console = kernel.services.get("console")
        if not isinstance(console, ConsoleService):
            raise TypeError("console service missing from session kernel")
        self._console = console
        self.state = ConfigurationEditorState.INTRO
        self.last_selection = ""
        self._render_intro()
        self._render_prompt()
        return SessionState.CONFIGURATION_EDITOR

    # Why: translate session events into menu rendering and command dispatches.
    def handle_event(
        self,
        kernel: SessionKernel,
        event: ConfigurationEditorEvent,
        selection: Optional[str] = None,
    ) -> SessionState:
        if event is ConfigurationEditorEvent.ENTER:
            self._render_intro()
            self.state = ConfigurationEditorState.READY
            self._render_prompt()
            return SessionState.CONFIGURATION_EDITOR

        if event is ConfigurationEditorEvent.COMMAND:
            if self.state is not ConfigurationEditorState.READY:
                self._render_intro()
                self.state = ConfigurationEditorState.READY
                self._render_prompt()
                return SessionState.CONFIGURATION_EDITOR
            return self._handle_command(selection)

        raise ValueError(f"unsupported configuration-editor event: {event!r}")

    # Why: present the configuration editor heading and menu entries.
    def _render_intro(self) -> None:
        self._write_line("IMAGE BBS CONFIGURATION EDITOR")
        self._write_line("Select a module by its highlighted letter:")
        self._render_menu()

    # Why: render the dual-column menu layout described in the documentation.
    def _render_menu(self) -> None:
        left_entries = self.MENU_ENTRIES[:7]
        right_entries = self.MENU_ENTRIES[7:14]
        rows = max(len(left_entries), len(right_entries))
        for index in range(rows):
            left_text = ""
            right_text = ""
            if index < len(left_entries):
                code, name = left_entries[index]
                left_text = f"{code}. {name}".ljust(self._COLUMN_WIDTH)
            else:
                left_text = "".ljust(self._COLUMN_WIDTH)
            if index < len(right_entries):
                code, name = right_entries[index]
                right_text = f"{code}. {name}"
            self._write_line(f"{left_text}{right_text}".rstrip())

    # Why: display the interactive prompt between commands.
    def _render_prompt(self) -> None:
        self._write_line(self._PROMPT, end="")

    # Why: normalise selection text and trigger command side effects.
    def _handle_command(self, selection: Optional[str]) -> SessionState:
        command = self._normalise_command(selection)
        if not command:
            self._render_prompt()
            return SessionState.CONFIGURATION_EDITOR
        if command == "N":
            self.last_selection = command
            self._write_line("Leaving configuration editor...")
            return SessionState.MAIN_MENU
        name = self._ENTRY_LOOKUP.get(command)
        if name is not None:
            self.last_selection = command
            self._write_line(f"{name} module is not yet implemented.")
            self._render_prompt()
            return SessionState.CONFIGURATION_EDITOR
        self._write_line("?INVALID CONFIGURATION COMMAND")
        self._render_prompt()
        return SessionState.CONFIGURATION_EDITOR

    # Why: derive the canonical command token from arbitrary input text.
    def _normalise_command(self, selection: Optional[str]) -> str:
        if not selection:
            return ""
        text = selection.strip().upper()
        if not text:
            return ""
        return text[0]

    # Why: abstract console writes so tests can observe transcript output.
    def _write_line(self, text: str, *, end: str = "\r") -> None:
        if not isinstance(self._console, ConsoleService):
            raise RuntimeError("console service is unavailable")
        payload = text if end else text.rstrip("\r")
        self._console.device.write(f"{payload}{end}")


__all__ = [
    "ConfigurationEditorEvent",
    "ConfigurationEditorModule",
    "ConfigurationEditorState",
]
