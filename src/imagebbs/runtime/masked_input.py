"""Helpers that mirror staged sysop keystrokes into the masked pane."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..device_context import ConsoleService, MaskedPaneGlyphPayload

__all__ = ["MaskedPaneKeystroke", "apply_masked_pane_keystrokes"]


@dataclass(frozen=True)
class MaskedPaneKeystroke:
    """Descriptor for a keystroke staged for the masked sysop pane."""

    offset: int
    glyph: int
    colour: int


def apply_masked_pane_keystrokes(
    console: ConsoleService,
    keystrokes: Iterable[MaskedPaneKeystroke],
) -> list[MaskedPaneGlyphPayload]:
    """Render ``keystrokes`` into the masked pane via the blink scheduler."""

    # Why: Mirror ``sub_ad62`` so host keystrokes traverse the same blink cadence
    # before ``&,50`` commits reuse the staged glyphs.
    payloads: list[MaskedPaneGlyphPayload] = []
    for keystroke in keystrokes:
        offset = int(keystroke.offset)
        glyph = int(keystroke.glyph) & 0xFF
        colour = int(keystroke.colour) & 0xFF
        payload = console.write_masked_pane_cell(offset, glyph, colour)
        payloads.append(payload)
    return payloads

