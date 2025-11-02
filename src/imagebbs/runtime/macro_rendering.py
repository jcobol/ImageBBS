"""Shared helpers for staging and rendering menu macros."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Iterable, Optional

from ..ampersand_dispatcher import AmpersandDispatcher
from ..device_context import ConsoleService
from .masked_pane_staging import MaskedPaneMacro, MaskedPaneStagingMap
# Why: consolidate masked-pane staging so callers reuse consistent macro lookups.
def render_masked_macro(
    *,
    console: ConsoleService,
    dispatcher: Optional[AmpersandDispatcher],
    macro: MaskedPaneMacro,
    staging_map: Optional[MaskedPaneStagingMap] = None,
    default_slot: int | None = None,
) -> int:
    """Resolve ``macro`` staging metadata and render via ``render_macro_with_overlay_commit``."""

    if staging_map is None:
        staging_map = console.masked_pane_staging_map
    try:
        spec = staging_map.spec(macro)
    except KeyError:
        if default_slot is None:
            raise
        slot = default_slot
        fallback_overlay = staging_map.fallback_overlay_for_slot(slot)
    else:
        slot = spec.slot
        fallback_overlay = spec.fallback_overlay

    render_macro_with_overlay_commit(
        console=console,
        dispatcher=dispatcher,
        slot=slot,
        fallback_overlay=fallback_overlay,
    )
    return slot


def render_macro_with_overlay_commit(
    *,
    console: ConsoleService,
    dispatcher: Optional[AmpersandDispatcher],
    slot: int,
    fallback_overlay: Optional[
        tuple[Sequence[int] | Iterable[int], Sequence[int] | Iterable[int]]
    ] = None,
    fill_colour: int | None = None,
) -> None:
    """Stage, commit, restage, and push ``slot`` while mirroring ``&,50``."""

    def stage_once() -> None:
        staged = console.stage_macro_slot(slot, fill_colour=fill_colour)
        if staged is not None:
            return
        if fallback_overlay is None:
            raise RuntimeError(f"console failed to stage macro slot ${slot:02x}")
        glyphs, colours = fallback_overlay
        console.stage_masked_pane_overlay(
            glyphs,
            colours,
            fill_colour=fill_colour,
            slot=slot,
        )

    stage_once()
    if dispatcher is not None:
        dispatcher.dispatch("&,50")
    else:
        console.commit_masked_pane_staging()
    stage_once()
    console.push_macro_slot(slot)


__all__ = ["render_masked_macro", "render_macro_with_overlay_commit"]
