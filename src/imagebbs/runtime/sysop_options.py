"""Runtime approximation of the ImageBBS ``SY`` dispatcher."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar, Optional, Sequence

from ..ampersand_dispatcher import AmpersandDispatcher
from ..ampersand_registry import AmpersandRegistry
from ..device_context import ConsoleService
from ..session_kernel import SessionKernel, SessionModule, SessionState
from .macro_rendering import render_macro_with_overlay_commit
from .masked_pane_staging import MaskedPaneMacro
from scripts.prototypes.runtime.sysop_options import (
    SysopOptionsEvent as PrototypeSysopOptionsEvent,
)


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

    _DEFAULT_MACRO_SLOTS: ClassVar[dict[MaskedPaneMacro, int]] = {
        MENU_HEADER_MACRO: 0x20,
        MENU_PROMPT_MACRO: 0x21,
        SAYING_PREAMBLE_MACRO: 0x22,
        SAYING_OUTPUT_MACRO: 0x23,
        INVALID_SELECTION_MACRO: 0x24,
        ABORT_MACRO: 0x25,
    }

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

    _SAYING_COMMANDS: ClassVar[frozenset[str]] = frozenset({"SY", "S"})
    _MAIN_MENU_COMMANDS: ClassVar[frozenset[str]] = frozenset({"Q"})
    _ABORT_COMMANDS: ClassVar[frozenset[str]] = frozenset({"A"})
    _EXIT_COMMANDS: ClassVar[frozenset[str]] = frozenset({"EX"})

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

        if self._matches_event(event, SysopOptionsEvent.ENTER):
            self._render_intro()
            self.state = SysopOptionsState.READY
            return SessionState.SYSOP_OPTIONS

        if self._matches_event(event, SysopOptionsEvent.COMMAND):
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

    @staticmethod
    def _matches_event(
        candidate: object, expected: SysopOptionsEvent
    ) -> bool:
        if candidate is expected:
            return True
        if isinstance(candidate, SysopOptionsEvent):
            return candidate == expected
        if isinstance(candidate, PrototypeSysopOptionsEvent):
            return candidate.name == expected.name
        name = getattr(candidate, "name", None)
        if name is None:
            return False
        try:
            return PrototypeSysopOptionsEvent[name].name == expected.name
        except KeyError:  # pragma: no cover - defensive guard
            try:
                return SysopOptionsEvent[name] is expected
            except KeyError:
                return False


__all__ = [
    "SysopOptionsEvent",
    "SysopOptionsModule",
    "SysopOptionsState",
]
