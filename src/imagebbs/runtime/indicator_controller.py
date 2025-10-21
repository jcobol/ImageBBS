"""Stateful controller that drives sysop indicators via ``ConsoleService``."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from ..device_context import ConsoleService

_SPACE_GLYPH = 0x20
_PAUSE_GLYPH = 0xD0
_ABORT_GLYPH = 0xC1
_SPINNER_DEFAULT_FRAMES: tuple[int, ...] = (0xB0, 0xAE, 0xAD, 0xAF)
_CARRIER_LEADING_GLYPH = 0xA0
_CARRIER_INDICATOR_GLYPH = 0xFA


@dataclass(slots=True)
class IndicatorController:
    """Cache indicator state and proxy updates into :class:`ConsoleService`."""

    console: ConsoleService
    pause_colour: int | None = 0x01
    abort_colour: int | None = 0x02
    spinner_colour: int | None = None
    carrier_leading_colour: int | None = None
    carrier_indicator_colour: int | None = None
    spinner_frames: Sequence[int] = field(
        default_factory=lambda: _SPINNER_DEFAULT_FRAMES
    )

    _pause_active: bool = field(init=False, default=False)
    _abort_active: bool = field(init=False, default=False)
    _carrier_active: bool = field(init=False, default=False)
    _spinner_enabled: bool = field(init=False, default=False)
    _spinner_index: int = field(init=False, default=0)

    def set_pause(self, active: bool) -> None:
        """Flip the pause indicator if ``active`` changed."""

        if active == self._pause_active:
            return
        self._pause_active = active
        glyph = _PAUSE_GLYPH if active else _SPACE_GLYPH
        self.console.set_pause_indicator(glyph, colour=self.pause_colour)

    def set_abort(self, active: bool) -> None:
        """Flip the abort indicator if ``active`` changed."""

        if active == self._abort_active:
            return
        self._abort_active = active
        glyph = _ABORT_GLYPH if active else _SPACE_GLYPH
        self.console.set_abort_indicator(glyph, colour=self.abort_colour)

    def set_carrier(self, active: bool) -> None:
        """Update carrier cells and synchronise spinner activation."""

        if active == self._carrier_active:
            return
        self._carrier_active = active
        if active:
            leading_glyph = _CARRIER_LEADING_GLYPH
            indicator_glyph = _CARRIER_INDICATOR_GLYPH
        else:
            leading_glyph = _SPACE_GLYPH
            indicator_glyph = _SPACE_GLYPH

        self.console.set_carrier_indicator(
            leading_cell=leading_glyph,
            indicator_cell=indicator_glyph,
            leading_colour=self.carrier_leading_colour,
            indicator_colour=self.carrier_indicator_colour,
        )
        self.set_spinner_enabled(active)

    def set_spinner_enabled(self, active: bool) -> None:
        """Enable or disable spinner animation."""

        if active == self._spinner_enabled:
            return
        self._spinner_enabled = active
        self._spinner_index = 0
        glyph = self._current_spinner_glyph() if active else _SPACE_GLYPH
        self.console.set_spinner_glyph(glyph, colour=self.spinner_colour)

    def on_idle_tick(self) -> None:
        """Advance the spinner when it is enabled."""

        if not self._spinner_enabled:
            return
        frames = tuple(int(code) & 0xFF for code in self.spinner_frames)
        if not frames:
            return
        self._spinner_index = (self._spinner_index + 1) % len(frames)
        self.console.set_spinner_glyph(
            frames[self._spinner_index], colour=self.spinner_colour
        )

    def _current_spinner_glyph(self) -> int:
        frames = tuple(int(code) & 0xFF for code in self.spinner_frames)
        if not frames:
            return _SPACE_GLYPH
        return frames[self._spinner_index % len(frames)]


__all__ = ["IndicatorController"]
