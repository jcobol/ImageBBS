"""Unit coverage for ml.extra slot parsing helpers."""

from __future__ import annotations

import pytest

from imagebbs.ml_extra_dump_macros import parse_slots


@pytest.mark.parametrize(
    "raw, expected",
    [
        (["0", "5", "42"], [0, 5, 42]),
        (["$0a", "$ff", "$10"], [0x0A, 0xFF, 0x10]),
        ([], []),
        (None, []),
    ],
)
def test_parse_slots_normalises_decimal_and_dollar_hex_inputs(
    raw: list[str] | None, expected: list[int]
) -> None:
    # Why: Guarantee decimal and $-prefixed slot arguments decode for CLI ergonomics.
    assert parse_slots(raw) == expected


def test_parse_slots_accepts_0x_prefixed_hex_inputs() -> None:
    # Why: Exercise the 0x-prefixed parsing branch so regressions surface immediately.
    values = parse_slots(["0x1a", "0X2B"])
    assert values == [0x1A, 0x2B]
