"""PETSCII translation helpers shared across runtime components."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Iterable

from . import petscii_glyphs


_BLOCK_CHAR_BY_MASK: Final[dict[int, str]] = {
    0b0000: " ",
    0b0001: "▘",
    0b0010: "▝",
    0b0011: "▀",
    0b0100: "▖",
    0b0101: "▌",
    0b0110: "▞",
    0b0111: "▛",
    0b1000: "▗",
    0b1001: "▚",
    0b1010: "▐",
    0b1011: "▜",
    0b1100: "▄",
    0b1101: "▙",
    0b1110: "▟",
    0b1111: "█",
}


def _glyph_rows_to_ints(glyph: petscii_glyphs.GlyphMatrix) -> list[int]:
    return [int("".join("1" if bit else "0" for bit in row), 2) for row in glyph]


def _glyph_bounds(glyph: petscii_glyphs.GlyphMatrix) -> tuple[int, int, int, int] | None:
    coords = [
        (x, y) for y, row in enumerate(glyph) for x, bit in enumerate(row) if bit
    ]
    if not coords:
        return None
    xs = [x for x, _ in coords]
    ys = [y for _, y in coords]
    return min(xs), max(xs), min(ys), max(ys)


def _quadrant_mask(glyph: petscii_glyphs.GlyphMatrix) -> int:
    mask = 0
    for index, (y0, y1, x0, x1) in enumerate(((0, 4, 0, 4), (0, 4, 4, 8), (4, 8, 0, 4), (4, 8, 4, 8))):
        filled = sum(
            glyph[y][x] for y in range(y0, y1) for x in range(x0, x1)
        )
        if filled >= 8:
            mask |= 1 << index
    return mask


def _looks_like_checkerboard(rows: list[int]) -> bool:
    seen = {value for value in rows if value}
    return seen == {0xCC, 0x33}


def _looks_like_left_triangle(rows: list[int]) -> bool:
    return all(row == ((0xFF << index) & 0xFF) for index, row in enumerate(rows))


def _approximate_graphics_glyph(code: int) -> str:
    glyph = petscii_glyphs.get_glyph(code)
    rows = _glyph_rows_to_ints(glyph)
    if not any(rows):
        return " "
    if _looks_like_checkerboard(rows):
        return "▒"
    if _looks_like_left_triangle(rows):
        return "◤"
    mask = _quadrant_mask(glyph)
    bounds = _glyph_bounds(glyph)
    width = bounds[1] - bounds[0] + 1 if bounds else 0
    height = bounds[3] - bounds[2] + 1 if bounds else 0

    if mask in (0b0101, 0b1010):
        if width <= 2:
            return "▎" if mask == 0b0101 else "▕"
        if width == 3:
            return "▍" if mask == 0b0101 else "▐"
        return _BLOCK_CHAR_BY_MASK[mask]
    if mask in (0b0011, 0b1100):
        if height == 1:
            return "▔" if mask == 0b0011 else "▁"
        if height == 2:
            return "▀" if mask == 0b0011 else "▂"
        if height == 3:
            return "▀" if mask == 0b0011 else "▃"
        return _BLOCK_CHAR_BY_MASK[mask]
    if mask:
        return _BLOCK_CHAR_BY_MASK[mask]

    if rows[0] and not any(rows[1:]):
        return "▔"
    if rows[-1] and not any(rows[:-1]):
        return "▁"
    if rows == [24, 24, 24, 31, 31, 24, 24, 24]:
        return "├"
    if rows == [24, 24, 24, 31, 31, 0, 0, 0]:
        return "┐"
    if rows == [0, 0, 0, 248, 248, 24, 24, 24]:
        return "└"
    if rows == [0, 0, 0, 31, 31, 24, 24, 24]:
        return "┘"
    if rows == [24, 24, 24, 255, 255, 0, 0, 0]:
        return "┴"
    if rows == [0, 0, 0, 255, 255, 24, 24, 24]:
        return "┬"
    if rows == [24, 24, 24, 248, 248, 24, 24, 24]:
        return "┼"
    if rows == [24, 24, 24, 248, 248, 0, 0, 0]:
        return "┌"

    return "█"


def _build_base_glyphs() -> tuple[str, ...]:
    table = [" "] * 0x80
    table[0x00] = "@"
    for offset in range(26):
        table[0x01 + offset] = chr(ord("A") + offset)
    table[0x1B] = "["
    table[0x1C] = "£"
    table[0x1D] = "]"
    table[0x1E] = "↑"
    table[0x1F] = "←"
    for code in range(0x20, 0x40):
        table[code] = chr(code)
    for code in range(0x40, 0x5B):
        table[code] = chr(code)
    table[0x5B] = "["
    table[0x5C] = "\\"
    table[0x5D] = "]"
    table[0x5E] = "^"
    table[0x5F] = "_"
    for code in range(0x60, 0x80):
        table[code] = _approximate_graphics_glyph(code)
    return tuple(table)


def _decode_glyph(raw: int) -> str:
    base = raw & 0x7F
    glyph = _PETSCII_BASE_GLYPHS[base]
    if 0xE0 <= raw <= 0xFA and 0x61 <= base <= 0x7A:
        return chr(base - 0x20)
    return glyph


def _resolve_reverse(code: int) -> bool:
    raw = int(code) & 0xFF
    if raw == 0xA0:
        return False
    return bool(raw & 0x80)


_PETSCII_BASE_GLYPHS: Final[tuple[str, ...]] = _build_base_glyphs()

_PETSCII_TRANSLATION_TABLE: Final[tuple[tuple[str, bool], ...]] = tuple(
    (_decode_glyph(index), _resolve_reverse(index)) for index in range(256)
)


def translate_petscii(code: int) -> tuple[str, bool]:
    """Return the glyph and reverse flag for a PETSCII ``code``."""

    return _PETSCII_TRANSLATION_TABLE[int(code) & 0xFF]


_PRINTABLE_ASCII: Final[set[int]] = set(range(0x20, 0x7F))
_PRINTABLE_EXTRA: Final[dict[int, str]] = {0x0D: "\n", 0x8D: "\n"}


_IGNORED_EDITOR_CONTROL_BYTES: Final[frozenset[int]] = frozenset({0x03, 0x04, 0x05, 0x06, 0x07})


@dataclass
class PetsciiStreamDecoder:
    """Incrementally decode PETSCII payloads into ASCII text."""

    width: int = 40
    _cursor_x: int = 0
    _cursor_y: int = 0
    _lowercase_mode: bool = False
    _reverse_mode: bool = False
    _current_line: list[str] = field(default_factory=list)
    _line_emitted_length: int = 0
    _pending: list[str] = field(default_factory=list)

    def decode(self, payload: Iterable[int]) -> str:
        for raw in payload:
            byte = int(raw) & 0xFF
            if self._handle_control(byte):
                continue
            self._write_character(byte)
        output = "".join(self._pending)
        self._pending.clear()
        return output

    def _handle_control(self, byte: int) -> bool:
        if byte == 0x93:  # clear
            self._line_break(reset_x=True, force=True)
            self._cursor_y = 0
            return True
        if byte == 0x13:  # home
            self._line_break(reset_x=True, force=True)
            self._cursor_y = 0
            return True
        if byte == 0x0D:  # carriage return
            self._line_break(reset_x=True, force=True)
            return True
        if byte == 0x0A:  # line feed
            self._line_break(reset_x=False, force=True)
            return True
        if byte == 0x11:  # cursor down
            self._line_break(reset_x=False, force=True)
            return True
        if byte == 0x91:  # cursor up
            if self._cursor_y > 0:
                self._cursor_y -= 1
            return True
        if byte == 0x1D:  # cursor right
            if self._cursor_x < self.width - 1:
                self._cursor_x += 1
            else:
                self._cursor_x = 0
                self._line_break(reset_x=True, force=True)
            return True
        if byte == 0x9D:  # cursor left
            if self._cursor_x > 0:
                self._cursor_x -= 1
            return True
        if byte == 0x14:  # delete/backspace
            if self._cursor_x > 0:
                self._cursor_x -= 1
            self._write_at_cursor(" ")
            return True
        if byte == 0x12:  # reverse on
            self._reverse_mode = True
            return True
        if byte == 0x92:  # reverse off
            self._reverse_mode = False
            return True
        if byte == 0x0E:  # lowercase on
            self._lowercase_mode = True
            return True
        if byte == 0x8E:  # lowercase off
            self._lowercase_mode = False
            return True
        if byte in _IGNORED_EDITOR_CONTROL_BYTES:
            return True
        if 0x90 <= byte <= 0x9F:
            return True
        return False

    def _line_break(self, *, reset_x: bool, force: bool) -> None:
        if not force and self._line_emitted_length == 0 and not self._current_line:
            return
        if self._line_emitted_length < len(self._current_line):
            tail = "".join(self._current_line[self._line_emitted_length :])
            if tail:
                self._pending.append(tail)
            self._line_emitted_length = len(self._current_line)
        self._pending.append("\n")
        self._current_line = []
        self._line_emitted_length = 0
        if reset_x:
            self._cursor_x = 0
        self._cursor_y += 1

    def _write_character(self, byte: int) -> None:
        char = self._translate_character(byte)
        if char is None:
            return
        self._write_at_cursor(char)
        self._cursor_x += 1
        if self._cursor_x >= self.width:
            self._cursor_x = 0
            self._line_break(reset_x=True, force=True)

    def _write_at_cursor(self, char: str) -> None:
        if self._cursor_x > len(self._current_line):
            self._current_line.extend(
                " " for _ in range(self._cursor_x - len(self._current_line))
            )
        if self._cursor_x == len(self._current_line):
            self._current_line.append(char)
        else:
            self._current_line[self._cursor_x] = char

        current_length = len(self._current_line)
        if self._cursor_x < self._line_emitted_length:
            self._pending.append("\r")
            self._pending.append("".join(self._current_line[: self._line_emitted_length]))
        else:
            gap = self._cursor_x - self._line_emitted_length
            if gap > 0:
                self._pending.append(" " * gap)
                self._line_emitted_length += gap
            self._pending.append(char)
            self._line_emitted_length += 1

        if self._line_emitted_length < current_length:
            self._line_emitted_length = current_length

    def _translate_character(self, byte: int) -> str | None:
        raw = int(byte) & 0xFF
        if raw == 0x00:
            return None
        if raw == 0xA0:
            char = " "
        elif 0x20 <= raw <= 0x7E:
            char = chr(raw)
        elif 0xA0 <= raw <= 0xBF:
            char = chr(raw - 0x20)
        elif 0xC0 <= raw <= 0xDA:
            char = chr(raw - 0x80)
        elif 0xE0 <= raw <= 0xFA:
            base = chr(raw - 0xA0)
            char = base if self._lowercase_mode else base.upper()
        else:
            glyph = petscii_to_cli_glyph(raw)
            if glyph.startswith("{CBM-") and glyph.endswith("}"):
                return None
            return glyph if glyph else None
        if not char.isascii():
            glyph = petscii_to_cli_glyph(raw)
            if glyph.startswith("{CBM-") and glyph.endswith("}"):
                return None
            return glyph if glyph else None
        return char


def decode_petscii_stream(payload: Iterable[int], *, width: int = 40) -> str:
    """Decode ``payload`` into ASCII text using PETSCII screen semantics."""

    decoder = PetsciiStreamDecoder(width=width)
    return decoder.decode(payload)


def petscii_to_cli_glyph(byte: int) -> str:
    """Map ``byte`` to a printable glyph suitable for CLI output."""

    raw = int(byte) & 0xFF
    if raw in _PRINTABLE_EXTRA:
        return _PRINTABLE_EXTRA[raw]
    if raw in _PRINTABLE_ASCII:
        return chr(raw)
    candidate = raw & 0x7F
    if candidate in _PRINTABLE_ASCII:
        return chr(candidate)
    if candidate in _PRINTABLE_EXTRA:
        return _PRINTABLE_EXTRA[candidate]
    return f"{{CBM-${raw:02X}}}"


def decode_petscii_for_cli(payload: Iterable[int]) -> str:
    """Translate ``payload`` into the CLI's printable text representation."""

    return decode_petscii_stream(payload)


__all__ = [
    "translate_petscii",
    "petscii_to_cli_glyph",
    "PetsciiStreamDecoder",
    "decode_petscii_stream",
    "decode_petscii_for_cli",
]
