"""In-memory PETSCII renderer approximating the C64 text screen."""
from __future__ import annotations

from functools import lru_cache
from typing import Sequence

from . import ml_extra_defaults

_WIDTH = 40
_HEIGHT = 25


@lru_cache()
def _load_default_palette() -> tuple[int, int, int, int]:
    """Return the editor palette recovered from ``ml.extra``."""

    defaults = ml_extra_defaults.MLExtraDefaults.from_overlay()
    return defaults.palette.colours


_COLOR_CODES: dict[int, int] = {
    0x90: 0,  # black
    0x05: 1,  # white
    0x1C: 2,  # red
    0x9F: 3,  # cyan
    0x9C: 4,  # purple
    0x1E: 5,  # green
    0x1F: 6,  # blue
    0x9E: 7,  # yellow
    0x81: 8,  # orange
    0x95: 9,  # brown
    0x96: 10,  # light red
    0x97: 11,  # dark grey
    0x98: 12,  # medium grey
    0x99: 13,  # light green
    0x9A: 14,  # light blue
    0x9B: 15,  # light grey
}


class PetsciiScreen:
    """Simplified representation of the 40×25 ImageBBS console."""

    width: int = _WIDTH
    height: int = _HEIGHT

    def __init__(self, palette: Sequence[int] | None = None) -> None:
        palette_values = tuple(palette) if palette is not None else _load_default_palette()
        if len(palette_values) != 4:
            raise ValueError("palette must contain four VIC-II colour entries")
        self._palette: list[int] = list(palette_values)
        self._screen_colour: int = self._palette[0]
        self._background_colour: int = self._palette[2]
        self._border_colour: int = self._palette[3]
        self._cursor_x: int = 0
        self._cursor_y: int = 0
        self._lowercase_mode = False
        self._chars: list[list[str]] = [[" " for _ in range(self.width)] for _ in range(self.height)]
        self._colours: list[list[int]] = [
            [self._screen_colour for _ in range(self.width)] for _ in range(self.height)
        ]

    @property
    def palette(self) -> tuple[int, int, int, int]:
        """Return the VIC-II palette entries staged by the overlay."""

        return tuple(self._palette)

    @property
    def screen_colour(self) -> int:
        """Return the current text colour."""

        return self._screen_colour

    @property
    def background_colour(self) -> int:
        """Return the background colour."""

        return self._background_colour

    @property
    def border_colour(self) -> int:
        """Return the border colour."""

        return self._border_colour

    @property
    def characters(self) -> tuple[str, ...]:
        """Return the rendered screen as rows of PETSCII text."""

        return tuple("".join(row) for row in self._chars)

    @property
    def colour_matrix(self) -> tuple[tuple[int, ...], ...]:
        """Expose the per-cell colour buffer."""

        return tuple(tuple(row) for row in self._colours)

    def clear(self) -> None:
        """Clear the screen and home the cursor."""

        for y in range(self.height):
            for x in range(self.width):
                self._chars[y][x] = " "
                self._colours[y][x] = self._screen_colour
        self._cursor_x = 0
        self._cursor_y = 0

    def write(self, payload: bytes | bytearray | memoryview | str) -> None:
        """Render the supplied PETSCII payload to the buffer."""

        if isinstance(payload, str):
            data = payload.encode("latin-1", errors="replace")
        else:
            data = bytes(payload)
        for byte in data:
            if self._handle_control(byte):
                continue
            if self._handle_colour(byte):
                continue
            self._draw_character(byte)

    def _handle_control(self, byte: int) -> bool:
        if byte == 0x93:  # clear
            self.clear()
            return True
        if byte == 0x13:  # home
            self._cursor_x = 0
            self._cursor_y = 0
            return True
        if byte == 0x0D:  # carriage return
            self._cursor_x = 0
            self._cursor_y += 1
            self._clamp_cursor()
            return True
        if byte == 0x0A:  # line feed
            self._cursor_y += 1
            self._clamp_cursor()
            return True
        if byte == 0x11:  # cursor down
            self._cursor_y += 1
            self._clamp_cursor()
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
                self._cursor_y += 1
                self._clamp_cursor()
            return True
        if byte == 0x9D:  # cursor left
            if self._cursor_x > 0:
                self._cursor_x -= 1
            return True
        if byte == 0x14:  # delete/backspace
            if self._cursor_x > 0:
                self._cursor_x -= 1
            self._put_character(" ")
            return True
        if byte == 0x12:  # reverse on
            return True
        if byte == 0x92:  # reverse off
            return True
        if byte == 0x0E:  # switch to lowercase/uppercase
            self._lowercase_mode = True
            return True
        if byte == 0x8E:  # switch to uppercase/graphics
            self._lowercase_mode = False
            return True
        return False

    def _handle_colour(self, byte: int) -> bool:
        colour = _COLOR_CODES.get(byte)
        if colour is None:
            return False
        self._screen_colour = colour
        return True

    def _draw_character(self, byte: int) -> None:
        char = self._translate_character(byte)
        self._put_character(char)
        self._cursor_x += 1
        if self._cursor_x >= self.width:
            self._cursor_x = 0
            self._cursor_y += 1
            self._clamp_cursor()

    def _put_character(self, char: str) -> None:
        if 0 <= self._cursor_y < self.height and 0 <= self._cursor_x < self.width:
            self._chars[self._cursor_y][self._cursor_x] = char
            self._colours[self._cursor_y][self._cursor_x] = self._screen_colour

    def _clamp_cursor(self) -> None:
        if self._cursor_y < self.height:
            return
        self._scroll()

    def _scroll(self) -> None:
        self._chars.pop(0)
        self._colours.pop(0)
        self._chars.append([" " for _ in range(self.width)])
        self._colours.append([self._screen_colour for _ in range(self.width)])
        self._cursor_y = self.height - 1

    def _translate_character(self, byte: int) -> str:
        if byte == 0xA0:
            return " "
        if 0x20 <= byte <= 0x7E:
            return chr(byte)
        if 0xA0 <= byte <= 0xBF:
            return chr(byte - 0x20)
        if 0xC0 <= byte <= 0xDA:
            return chr(byte - 0x80)
        if 0xE0 <= byte <= 0xFA:
            base = byte - 0xA0
            char = chr(base)
            if not self._lowercase_mode:
                return char.upper()
            return char
        return " "
