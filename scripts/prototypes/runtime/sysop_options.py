"""Prototype sysop-options dispatcher that mirrors the ``SY`` command flow."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar, Optional, Sequence

from ..ampersand_registry import AmpersandRegistry
from ..device_context import ConsoleService
from ..session_kernel import SessionKernel, SessionModule, SessionState


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
    _saying_index: int = field(init=False, default=0)

    MENU_HEADER_SLOT = 0x20
    MENU_PROMPT_SLOT = 0x21
    SAYING_PREAMBLE_SLOT = 0x22
    SAYING_OUTPUT_SLOT = 0x23
    INVALID_SELECTION_SLOT = 0x24
    ABORT_SLOT = 0x25

    _SAYING_COMMANDS = frozenset({"SY", "S"})
    _MAIN_MENU_COMMANDS = frozenset({"Q"})
    _ABORT_COMMANDS = frozenset({"A"})
    _EXIT_COMMANDS = frozenset({"EX"})

    _FALLBACK_MACRO_STAGING: ClassVar[
        dict[int, tuple[tuple[int, ...], tuple[int, ...]]]
    ] = {
        0x20: (
            (0x68, 0xC3, 0x85, 0x06, 0xE2, 0xC1, 0xA0, 0x00)
            + (0x20,) * 32,
            (0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x00)
            + (0x0A,) * 32,
        ),
        0x21: ((0x00,) + (0x20,) * 39, (0x00,) + (0x0A,) * 39),
        0x22: ((0x00,) + (0x20,) * 39, (0x00,) + (0x0A,) * 39),
        0x23: ((0x00,) + (0x20,) * 39, (0x00,) + (0x0A,) * 39),
        0x24: ((0x00,) + (0x20,) * 39, (0x00,) + (0x0A,) * 39),
        0x25: ((0x00,) + (0x20,) * 39, (0x00,) + (0x0A,) * 39),
    }

    def start(self, kernel: SessionKernel) -> SessionState:
        """Bind runtime services and render the introductory macros."""

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
                self._render_macro(self.ABORT_SLOT)
                return SessionState.MAIN_MENU

            if command in self._MAIN_MENU_COMMANDS:
                self.last_command = command
                return SessionState.MAIN_MENU

            if command in self._EXIT_COMMANDS:
                self.last_command = command
                return SessionState.EXIT

            self.last_command = command
            self._render_macro(self.INVALID_SELECTION_SLOT)
            self._render_prompt()
            return SessionState.SYSOP_OPTIONS

        raise ValueError(f"unsupported sysop-options event: {event!r}")

    # Internal helpers -----------------------------------------------------

    def _render_intro(self) -> None:
        self._render_macro(self.MENU_HEADER_SLOT)
        self._render_prompt()

    def _render_prompt(self) -> None:
        self._render_macro(self.MENU_PROMPT_SLOT)

    def _render_saying(self) -> None:
        self._render_macro(self.SAYING_PREAMBLE_SLOT)
        saying = self._next_saying()
        self._write_saying(saying)
        self._render_macro(self.SAYING_OUTPUT_SLOT)
        self._render_prompt()

    def _render_macro(self, slot: int) -> None:
        if self.registry is None:
            raise RuntimeError("ampersand registry has not been initialised")
        if not isinstance(self._console, ConsoleService):  # pragma: no cover - guard
            raise RuntimeError("console service is unavailable")
        defaults = self.registry.defaults
        lookup = self._console.glyph_lookup.macros_by_slot
        if (
            slot not in defaults.macros_by_slot
            and slot not in lookup
            and slot not in self._FALLBACK_MACRO_STAGING
        ):
            raise KeyError(f"macro slot ${slot:02x} missing from defaults")
        staged = self._console.stage_macro_slot(slot)
        if staged is None:
            glyphs_colours = self._FALLBACK_MACRO_STAGING.get(slot)
            if glyphs_colours is None:
                raise RuntimeError(f"console failed to stage macro slot ${slot:02x}")
            glyphs, colours = glyphs_colours
            self._console.stage_masked_pane_overlay(glyphs, colours)
        self._console.push_macro_slot(slot)
        self.rendered_slots.append(slot)

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
