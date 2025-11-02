"""Tests for macro rendering helpers."""
from __future__ import annotations

from typing import Any, Iterable, Sequence

import pytest

from imagebbs.runtime.macro_rendering import (
    render_macro_with_overlay_commit,
    render_masked_macro,
)
from imagebbs.runtime.masked_pane_staging import MaskedPaneMacro, MaskedPaneMacroSpec


class FakeConsoleService:
    """Minimal console stub capturing interactions for assertions."""

    def __init__(self, stage_macro_slot_results: Iterable[Any]) -> None:
        self._stage_macro_slot_results = list(stage_macro_slot_results)
        self.stage_macro_slot_calls: list[dict[str, Any]] = []
        self.stage_masked_pane_overlay_calls: list[dict[str, Any]] = []
        self.commit_masked_pane_staging_calls = 0
        self.push_macro_slot_calls: list[int] = []
        self.event_log: list[tuple[Any, ...]] = []

    def stage_macro_slot(self, slot: int, *, fill_colour: int | None = None) -> Any:
        self.stage_macro_slot_calls.append({"slot": slot, "fill_colour": fill_colour})
        self.event_log.append(("stage_macro_slot", slot, fill_colour))
        if self._stage_macro_slot_results:
            return self._stage_macro_slot_results.pop(0)
        return None

    def stage_masked_pane_overlay(
        self,
        glyphs: Sequence[int] | Iterable[int],
        colours: Sequence[int] | Iterable[int],
        *,
        fill_colour: int | None = None,
        slot: int | None = None,
    ) -> None:
        self.stage_masked_pane_overlay_calls.append(
            {
                "glyphs": glyphs,
                "colours": colours,
                "fill_colour": fill_colour,
                "slot": slot,
            }
        )
        self.event_log.append(
            (
                "stage_masked_pane_overlay",
                glyphs,
                colours,
                fill_colour,
                slot,
            )
        )

    def commit_masked_pane_staging(self) -> None:
        self.commit_masked_pane_staging_calls += 1
        self.event_log.append(("commit_masked_pane_staging",))

    def push_macro_slot(self, slot: int) -> None:
        self.push_macro_slot_calls.append(slot)
        self.event_log.append(("push_macro_slot", slot))


class FakeAmpersandDispatcher:
    """Dispatcher stub that records every command it receives."""

    def __init__(self) -> None:
        self.commands: list[str] = []

    def dispatch(self, command: str) -> None:
        self.commands.append(command)


class FakeStagingMap:
    """Minimal staging map stub exposing spec and fallback lookups."""

    def __init__(
        self,
        *,
        specs: dict[MaskedPaneMacro, MaskedPaneMacroSpec] | None = None,
        fallbacks: dict[int, tuple[Sequence[int], Sequence[int]]] | None = None,
    ) -> None:
        # Why: capture stub configuration for predictable staging behaviour.
        self._specs = specs or {}
        self._fallbacks = fallbacks or {}
        self.spec_calls: list[MaskedPaneMacro] = []
        self.fallback_calls: list[int] = []

    def spec(self, macro: MaskedPaneMacro) -> MaskedPaneMacroSpec:
        # Why: emulate staging-map resolution so helpers receive slot metadata.
        self.spec_calls.append(macro)
        if macro not in self._specs:
            raise KeyError(macro)
        return self._specs[macro]

    def fallback_overlay_for_slot(
        self, slot: int
    ) -> tuple[Sequence[int], Sequence[int]] | None:
        # Why: provide overlay data when staging falls back to a direct slot.
        self.fallback_calls.append(slot)
        return self._fallbacks.get(slot)


@pytest.mark.parametrize("use_dispatcher", [False, True])
def test_render_macro_with_overlay_commit_stages_commits_and_pushes(use_dispatcher: bool) -> None:
    """The helper stages twice, commits once, and pushes regardless of commit strategy."""

    staged_object = object()
    console = FakeConsoleService(stage_macro_slot_results=[staged_object, staged_object])
    dispatcher = FakeAmpersandDispatcher() if use_dispatcher else None

    render_macro_with_overlay_commit(
        console=console,
        dispatcher=dispatcher,
        slot=0x10,
    )

    assert len(console.stage_macro_slot_calls) == 2
    assert all(call["slot"] == 0x10 for call in console.stage_macro_slot_calls)
    assert [entry[0] for entry in console.event_log].count("stage_macro_slot") == 2
    assert console.stage_masked_pane_overlay_calls == []

    if use_dispatcher:
        assert dispatcher is not None
        assert dispatcher.commands == ["&,50"]
        assert console.commit_masked_pane_staging_calls == 0
    else:
        assert console.commit_masked_pane_staging_calls == 1

    assert console.push_macro_slot_calls == [0x10]
    assert console.event_log[-1] == ("push_macro_slot", 0x10)


def test_render_macro_with_overlay_commit_uses_fallback_overlay_when_stage_fails() -> None:
    """When staging fails the console overlay fallback receives the provided iterables."""

    console = FakeConsoleService(stage_macro_slot_results=[])
    glyphs = [1, 2, 3]
    colours = [4, 5, 6]

    render_macro_with_overlay_commit(
        console=console,
        dispatcher=None,
        slot=0x42,
        fallback_overlay=(glyphs, colours),
        fill_colour=7,
    )

    assert len(console.stage_macro_slot_calls) == 2
    assert all(call["slot"] == 0x42 for call in console.stage_macro_slot_calls)
    assert all(call["fill_colour"] == 7 for call in console.stage_macro_slot_calls)

    assert len(console.stage_masked_pane_overlay_calls) == 2
    for call in console.stage_masked_pane_overlay_calls:
        assert call["glyphs"] is glyphs
        assert call["colours"] is colours
        assert call["fill_colour"] == 7
        assert call["slot"] == 0x42

    assert console.commit_masked_pane_staging_calls == 1
    assert console.push_macro_slot_calls == [0x42]
    assert console.event_log == [
        ("stage_macro_slot", 0x42, 7),
        ("stage_masked_pane_overlay", glyphs, colours, 7, 0x42),
        ("commit_masked_pane_staging",),
        ("stage_macro_slot", 0x42, 7),
        ("stage_masked_pane_overlay", glyphs, colours, 7, 0x42),
        ("push_macro_slot", 0x42),
    ]


def test_render_masked_macro_uses_spec_slot_when_available() -> None:
    # Why: ensure macros registered in the staging map reuse their mapped slot.
    """The helper routes through the staging-map spec when the macro is mapped."""

    spec = MaskedPaneMacroSpec(
        macro=MaskedPaneMacro.MAIN_MENU_HEADER,
        slot=0x11,
        fallback_overlay=((1, 2), (3, 4)),
    )
    staging_map = FakeStagingMap(specs={MaskedPaneMacro.MAIN_MENU_HEADER: spec})
    console = FakeConsoleService(stage_macro_slot_results=[object(), object()])
    console.masked_pane_staging_map = staging_map

    slot = render_masked_macro(
        console=console,
        dispatcher=None,
        macro=MaskedPaneMacro.MAIN_MENU_HEADER,
    )

    assert slot == 0x11
    assert staging_map.spec_calls == [MaskedPaneMacro.MAIN_MENU_HEADER]
    assert staging_map.fallback_calls == []
    assert [call["slot"] for call in console.stage_macro_slot_calls] == [0x11, 0x11]


def test_render_masked_macro_falls_back_to_default_slot() -> None:
    # Why: confirm macros outside the staging map render with the default slot fallback.
    """Macros missing from the staging map use the provided default slot and fallback."""

    fallback_overlay = ([5, 6], [7, 8])
    staging_map = FakeStagingMap(fallbacks={0x22: fallback_overlay})
    console = FakeConsoleService(stage_macro_slot_results=[])
    console.masked_pane_staging_map = staging_map

    slot = render_masked_macro(
        console=console,
        dispatcher=None,
        macro=MaskedPaneMacro.MAIN_MENU_PROMPT,
        default_slot=0x22,
    )

    assert slot == 0x22
    assert staging_map.spec_calls == [MaskedPaneMacro.MAIN_MENU_PROMPT]
    assert staging_map.fallback_calls == [0x22]
    assert console.stage_masked_pane_overlay_calls[0]["glyphs"] == fallback_overlay[0]
    assert console.stage_masked_pane_overlay_calls[0]["colours"] == fallback_overlay[1]
