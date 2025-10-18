import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.device_context import Console, ConsoleService


def _resolve_palette_colour(value: int, palette: tuple[int, ...], *, default_index: int = 0) -> int:
    resolved = int(value) & 0xFF
    if resolved in palette:
        return resolved
    if 0 <= resolved < len(palette):
        return palette[resolved]
    if not 0 <= default_index < len(palette):
        raise ValueError("default_index must reference a palette entry")
    return palette[default_index]


def test_masked_pane_blink_scheduler_cycles() -> None:
    console = Console()
    service = ConsoleService(console)

    countdowns: list[int] = []
    reverse_flags: list[bool] = []
    for _ in range(10):
        state = service.advance_masked_pane_blink()
        countdowns.append(state.countdown)
        reverse_flags.append(state.reverse)

    assert countdowns[:5] == [3, 2, 1, 0, 4]
    assert countdowns[5:] == [3, 2, 1, 0, 4]
    assert reverse_flags[:5] == [True, True, False, False, False]
    assert reverse_flags[5:] == [True, True, False, False, False]


def test_write_masked_pane_cell_applies_blink_and_preserves_transcript() -> None:
    console = Console()
    service = ConsoleService(console)

    reverse_pattern: list[bool] = []
    for _ in range(10):
        payload = service.write_masked_pane_cell(0, 0x41, 0x02)
        reverse_pattern.append(payload.reverse)

        expected_glyph = payload.glyph
        assert console.screen.peek_screen_address(0x0518) == expected_glyph

        palette = console.screen.palette
        expected_colour = _resolve_palette_colour(payload.colour, palette)
        assert console.screen.peek_colour_address(0xD918) == expected_colour

    assert reverse_pattern[:5] == [True, True, False, False, False]
    assert reverse_pattern[5:] == [True, True, False, False, False]
    assert console.transcript_bytes == b""
