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
    pause_colour: int | None = None
    abort_colour: int | None = None
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
    _pause_colour_cache: int | None = field(init=False, default=None)
    _abort_colour_cache: int | None = field(init=False, default=None)
    _carrier_leading_colour_cache: int | None = field(init=False, default=None)
    _carrier_indicator_colour_cache: int | None = field(
        init=False, default=None
    )

    def __post_init__(self) -> None:
        # Refresh cached colours immediately so overlay defaults are honoured before we touch the screen.
        self._refresh_indicator_colour_cache()

    def sync_from_console(
        self,
        *,
        pause_active: bool | None = None,
        abort_active: bool | None = None,
        spinner_enabled: bool | None = None,
        spinner_glyph: int | None = None,
        carrier_active: bool | None = None,
    ) -> None:
        """Refresh cached indicator state from the console without mutating it."""

        # Keep the colour cache aligned with console RAM so later writes reuse the operator's palette.
        self._refresh_indicator_colour_cache()

        if pause_active is None:
            pause_value = self._peek_screen_byte(self.console._PAUSE_SCREEN_ADDRESS)
            if pause_value is not None:
                pause_active = bool(pause_value == _PAUSE_GLYPH)
        if pause_active is not None:
            self._pause_active = pause_active

        if abort_active is None:
            abort_value = self._peek_screen_byte(self.console._ABORT_SCREEN_ADDRESS)
            if abort_value is not None:
                abort_active = bool(abort_value == _ABORT_GLYPH)
        if abort_active is not None:
            self._abort_active = abort_active

        if spinner_glyph is None:
            spinner_value = self._peek_screen_byte(
                self.console._SPINNER_SCREEN_ADDRESS
            )
        else:
            spinner_value = int(spinner_glyph) & 0xFF
        if spinner_enabled is None:
            spinner_enabled = bool(
                spinner_value is not None and spinner_value != _SPACE_GLYPH
            )
        if spinner_enabled is not None:
            self._spinner_enabled = spinner_enabled
            frames = tuple(int(code) & 0xFF for code in self.spinner_frames)
            if not spinner_enabled:
                self._spinner_index = 0
            else:
                if spinner_value is None or spinner_value == _SPACE_GLYPH:
                    self._spinner_index = 0
                elif frames:
                    try:
                        self._spinner_index = next(
                            index for index, glyph in enumerate(frames)
                            if glyph == spinner_value
                        )
                    except StopIteration:
                        self._spinner_index = 0
                else:
                    self._spinner_index = 0

        if carrier_active is None:
            leading_value = self._peek_screen_byte(
                self.console._CARRIER_LEADING_SCREEN_ADDRESS
            )
            indicator_value = self._peek_screen_byte(
                self.console._CARRIER_INDICATOR_SCREEN_ADDRESS
            )
            carrier_active = bool(
                (leading_value is not None and leading_value != _SPACE_GLYPH)
                or (indicator_value is not None and indicator_value != _SPACE_GLYPH)
            )
        if carrier_active is not None:
            self._carrier_active = carrier_active

    def set_pause(self, active: bool) -> None:
        """Flip the pause indicator if ``active`` changed."""

        if active == self._pause_active:
            return
        self._pause_active = active
        glyph = _PAUSE_GLYPH if active else _SPACE_GLYPH
        colour = self.pause_colour
        if colour is None:
            colour = self._pause_colour_cache
        self.console.set_pause_indicator(glyph, colour=colour)

    def set_abort(self, active: bool) -> None:
        """Flip the abort indicator if ``active`` changed."""

        if active == self._abort_active:
            return
        self._abort_active = active
        glyph = _ABORT_GLYPH if active else _SPACE_GLYPH
        colour = self.abort_colour
        if colour is None:
            colour = self._abort_colour_cache
        self.console.set_abort_indicator(glyph, colour=colour)

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
            leading_colour=(
                self.carrier_leading_colour
                if self.carrier_leading_colour is not None
                else self._carrier_leading_colour_cache
            ),
            indicator_colour=(
                self.carrier_indicator_colour
                if self.carrier_indicator_colour is not None
                else self._carrier_indicator_colour_cache
            ),
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

    def _peek_screen_byte(self, address: int) -> int | None:
        screen, _ = self.console.peek_block(screen_address=address, screen_length=1)
        if not screen:
            return None
        return screen[0]

    def _refresh_indicator_colour_cache(self) -> None:
        # Capture indicator colour RAM so writes reuse overlay defaults when overrides are absent.
        self._pause_colour_cache = self._resolve_indicator_colour(
            self.pause_colour, self.console._PAUSE_SCREEN_ADDRESS
        )
        self._abort_colour_cache = self._resolve_indicator_colour(
            self.abort_colour, self.console._ABORT_SCREEN_ADDRESS
        )
        self._carrier_leading_colour_cache = self._resolve_indicator_colour(
            self.carrier_leading_colour,
            self.console._CARRIER_LEADING_SCREEN_ADDRESS,
        )
        self._carrier_indicator_colour_cache = self._resolve_indicator_colour(
            self.carrier_indicator_colour,
            self.console._CARRIER_INDICATOR_SCREEN_ADDRESS,
        )

    def _resolve_indicator_colour(
        self, override: int | None, screen_address: int
    ) -> int | None:
        # Delegate colour lookups through peek_block so controller writes mirror the console state exactly.
        if override is not None:
            return int(override) & 0xFF
        colour_address = self.console._COLOUR_BASE + (
            int(screen_address) - self.console._SCREEN_BASE
        )
        _, colours = self.console.peek_block(
            colour_address=colour_address, colour_length=1
        )
        if not colours:
            return None
        return colours[0]


__all__ = ["IndicatorController"]
