from __future__ import annotations

from types import SimpleNamespace

from imagebbs.device.context import Console, ConsoleService, MaskedPaneBuffers
from imagebbs.runtime.session_instrumentation import (
    MaskedPaneColourStripAnimator,
    SessionInstrumentation,
)


def _resolve_palette_colour(
    value: int, palette: tuple[int, ...], *, default_index: int = 0
) -> int:
    resolved = int(value) & 0xFF
    if resolved in palette:
        return resolved
    if 0 <= resolved < len(palette):
        return palette[resolved]
    if not 0 <= default_index < len(palette):
        raise ValueError("default_index must reference a palette entry")
    return palette[default_index]


def _colour_strip_payload(service: ConsoleService) -> tuple[int, ...]:
    base = service._MASKED_PANE_COLOUR_STRIP_BASE
    length = service._MASKED_PANE_COLOUR_STRIP_LENGTH
    screen = service.screen
    return tuple(screen.peek_colour_address(base + offset) for offset in range(length))


def test_masked_pane_colour_strip_sequence_matches_overlay_palette() -> None:
    console = Console()
    service = ConsoleService(console)

    sequence = service.masked_pane_colour_strip_sequence()

    assert sequence == (0x0E, 0x03, 0x01, 0x03, 0x0E, 0x06)


def test_fill_masked_pane_colour_strip_writes_expected_colour() -> None:
    console = Console()
    service = ConsoleService(console)

    before = bytes(console._transcript)
    colour = service.fill_masked_pane_colour_strip(2)

    sequence = service.masked_pane_colour_strip_sequence()
    assert colour == sequence[2]
    palette = service.screen.palette
    resolved = _resolve_palette_colour(colour, palette)
    assert _colour_strip_payload(service) == (resolved,) * service._MASKED_PANE_COLOUR_STRIP_LENGTH
    assert bytes(console._transcript) == before


def test_colour_strip_animator_respects_split_screen_guard() -> None:
    console = Console()
    service = ConsoleService(console)
    animator = MaskedPaneColourStripAnimator(service)

    baseline = _colour_strip_payload(service)
    animator.tick()
    assert _colour_strip_payload(service) == baseline

    service.set_masked_pane_buffers(MaskedPaneBuffers())
    animator.tick()
    sequence = service.masked_pane_colour_strip_sequence()
    palette = service.screen.palette
    expected_first = _resolve_palette_colour(sequence[0], palette)
    assert _colour_strip_payload(service) == (expected_first,) * service._MASKED_PANE_COLOUR_STRIP_LENGTH

    animator.tick()
    expected_second = _resolve_palette_colour(sequence[1], palette)
    assert _colour_strip_payload(service) == (expected_second,) * service._MASKED_PANE_COLOUR_STRIP_LENGTH


def test_session_instrumentation_tick_advances_colour_strip() -> None:
    console = Console()
    service = ConsoleService(console)
    service.set_masked_pane_buffers(MaskedPaneBuffers())

    class _Runner:
        def __init__(self, console_service: ConsoleService) -> None:
            self.console = console_service
            self.defaults = SimpleNamespace(indicator=None)

    runner = _Runner(service)
    instrumentation = SessionInstrumentation(
        runner,
        indicator_controller_cls=None,
        idle_timer_scheduler_cls=None,
    )

    sequence = service.masked_pane_colour_strip_sequence()
    palette = service.screen.palette
    instrumentation.on_idle_cycle()
    expected_first = _resolve_palette_colour(sequence[0], palette)
    assert _colour_strip_payload(service) == (expected_first,) * service._MASKED_PANE_COLOUR_STRIP_LENGTH

    instrumentation.on_idle_cycle()
    expected_second = _resolve_palette_colour(sequence[1], palette)
    assert _colour_strip_payload(service) == (expected_second,) * service._MASKED_PANE_COLOUR_STRIP_LENGTH
