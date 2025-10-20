"""Shared helpers for staging and rendering menu macros."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Iterable, Optional

from ..ampersand_dispatcher import AmpersandDispatcher
from ..device_context import ConsoleService


def _commit_masked_overlay(
    console: ConsoleService, dispatcher: Optional[AmpersandDispatcher]
) -> None:
    """Flush staged masked-pane bytes using ``&,50`` semantics."""

    if dispatcher is not None:
        dispatcher.dispatch("&,50")
        return
    console.commit_masked_pane_staging()


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
        )

    stage_once()
    _commit_masked_overlay(console, dispatcher)
    stage_once()
    console.push_macro_slot(slot)


__all__ = ["render_macro_with_overlay_commit"]
