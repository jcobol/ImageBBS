"""Prototype sysop-options dispatcher that mirrors the ``SY`` command flow."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Sequence

from ..ampersand_dispatcher import AmpersandDispatcher
from ..ampersand_registry import AmpersandRegistry
from ..device_context import ConsoleService
from ..session_kernel import SessionKernel, SessionModule, SessionState
from .masked_pane_staging import MaskedPaneMacro, render_masked_macro


class SysopOptionsState(Enum):
    """Internal states exposed by :class:`SysopOptionsModule`."""

    INTRO = auto()
    READY = auto()


class SysopOptionsEvent(Enum):
    """Events that drive rendering and command handling."""

    ENTER = auto()
    COMMAND = auto()


_DEFAULT_SAYINGS: tuple[str, ...] = (
    "Remember to rotate your backup disks.",
    "Callers appreciate quick responses.",
    "Document configuration changes as you make them.",
)


@dataclass
class SysopOptionsModule:
    """Finite-state approximation of the BASIC ``SY`` dispatcher."""

    registry: Optional[AmpersandRegistry] = None
    sayings: Sequence[str] = _DEFAULT_SAYINGS
    state: SysopOptionsState = field(init=False, default=SysopOptionsState.INTRO)
    rendered_slots: list[int] = field(init=False, default_factory=list)
    last_command: str = field(init=False, default="")
    last_saying: str = field(init=False, default="")
    _console: ConsoleService | None = field(init=False, default=None)
    _dispatcher: AmpersandDispatcher | None = field(init=False, default=None)
    _saying_index: int = field(init=False, default=0)

    MENU_HEADER_MACRO = MaskedPaneMacro.SYSOP_HEADER
    MENU_PROMPT_MACRO = MaskedPaneMacro.SYSOP_PROMPT
    SAYING_PREAMBLE_MACRO = MaskedPaneMacro.SYSOP_SAYING_PREAMBLE
    SAYING_OUTPUT_MACRO = MaskedPaneMacro.SYSOP_SAYING_OUTPUT
    INVALID_SELECTION_MACRO = MaskedPaneMacro.SYSOP_INVALID
    ABORT_MACRO = MaskedPaneMacro.SYSOP_ABORT

    @property
    def MENU_HEADER_SLOT(self) -> int:
        return self._macro_slot(self.MENU_HEADER_MACRO)

    @property
    def MENU_PROMPT_SLOT(self) -> int:
        return self._macro_slot(self.MENU_PROMPT_MACRO)

    @property
    def SAYING_PREAMBLE_SLOT(self) -> int:
        return self._macro_slot(self.SAYING_PREAMBLE_MACRO)

    @property
    def SAYING_OUTPUT_SLOT(self) -> int:
        return self._macro_slot(self.SAYING_OUTPUT_MACRO)

    @property
    def INVALID_SELECTION_SLOT(self) -> int:
        return self._macro_slot(self.INVALID_SELECTION_MACRO)

    @property
    def ABORT_SLOT(self) -> int:
        return self._macro_slot(self.ABORT_MACRO)

    _SAYING_COMMANDS = frozenset({"SY", "S"})
    _MAIN_MENU_COMMANDS = frozenset({"Q"})
    _ABORT_COMMANDS = frozenset({"A"})
    _EXIT_COMMANDS = frozenset({"EX"})

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
        self.last_saying = ""
        self._saying_index = 0
        self.state = SysopOptionsState.INTRO
        self._render_intro()
        return SessionState.SYSOP_OPTIONS

    def handle_event(
        self,
        kernel: SessionKernel,
        event: SysopOptionsEvent,
        selection: Optional[str] = None,
    ) -> SessionState:
        """Render macros and translate text commands to :class:`SessionState`."""

        if event is SysopOptionsEvent.ENTER:
            self._render_intro()
            self.state = SysopOptionsState.READY
            return SessionState.SYSOP_OPTIONS

        if event is SysopOptionsEvent.COMMAND:
            if self.state is not SysopOptionsState.READY:
                self._render_intro()
                self.state = SysopOptionsState.READY
                return SessionState.SYSOP_OPTIONS

            command = self._normalise_command(selection)
            if not command:
                self._render_prompt()
                return SessionState.SYSOP_OPTIONS

            if command in self._SAYING_COMMANDS:
                self.last_command = command
                self._render_saying()
                return SessionState.SYSOP_OPTIONS

            if command in self._ABORT_COMMANDS:
                self.last_command = command
                self._render_macro(self.ABORT_MACRO)
                return SessionState.MAIN_MENU

            if command in self._MAIN_MENU_COMMANDS:
                self.last_command = command
                return SessionState.MAIN_MENU

            if command in self._EXIT_COMMANDS:
                self.last_command = command
                return SessionState.EXIT

            self.last_command = command
            self._render_macro(self.INVALID_SELECTION_MACRO)
            self._render_prompt()
            return SessionState.SYSOP_OPTIONS

        raise ValueError(f"unsupported sysop-options event: {event!r}")

    # Internal helpers -----------------------------------------------------

    def _render_intro(self) -> None:
        self._render_macro(self.MENU_HEADER_MACRO)
        self._render_prompt()

    def _render_prompt(self) -> None:
        self._render_macro(self.MENU_PROMPT_MACRO)

    def _render_saying(self) -> None:
        self._render_macro(self.SAYING_PREAMBLE_MACRO)
        saying = self._next_saying()
        self._write_saying(saying)
        self._render_macro(self.SAYING_OUTPUT_MACRO)
        self._render_prompt()

    def _render_macro(self, macro: MaskedPaneMacro) -> None:
        if self.registry is None:
            raise RuntimeError("ampersand registry has not been initialised")
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        staging = self._console.masked_pane_staging_map
        slot = staging.slot(macro)
        render_masked_macro(
            console=self._console,
            dispatcher=self._dispatcher,
            macro=macro,
        )
        self.rendered_slots.append(slot)

    def _macro_slot(self, macro: MaskedPaneMacro) -> int:
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        return self._console.masked_pane_staging_map.slot(macro)

    def _next_saying(self) -> str:
        if not self.sayings:
            saying = "No sysop sayings configured."
        else:
            saying = self.sayings[self._saying_index % len(self.sayings)]
            self._saying_index = (self._saying_index + 1) % len(self.sayings)
        self.last_saying = saying
        return saying

    def _write_saying(self, text: str) -> None:
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        self._console.device.write(f"{text}\r")

    @staticmethod
    def _normalise_command(selection: Optional[str]) -> str:
        if not selection:
            return ""
        text = selection.strip().upper()
        if not text:
            return ""
        if text.startswith("SY"):
            return "SY"
        if text.startswith("S"):
            return "S"
        if text.startswith("EX"):
            return "EX"
        if text.startswith("X"):
            return "EX"
        if text.startswith("Q"):
            return "Q"
        if text.startswith("A"):
            return "A"
        return text[:2]


__all__ = [
    "SysopOptionsEvent",
    "SysopOptionsModule",
    "SysopOptionsState",
]
