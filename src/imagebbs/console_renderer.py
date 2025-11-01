"""In-memory PETSCII renderer approximating the C64 text screen."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence

from . import ml_extra_defaults
from . import ml_extra_extract
from . import petscii_glyphs

_WIDTH = 40
_HEIGHT = 25

_VIC_REGISTER_BACKGROUND = 0xD403
_VIC_REGISTER_BORDER = 0xD404
_VIC_REGISTER_SCREEN = 0xD405


@lru_cache()
def _load_editor_defaults() -> ml_extra_defaults.MLExtraDefaults:
    """Return the cached ``ml.extra`` defaults for the console renderer."""

    return ml_extra_defaults.MLExtraDefaults.from_overlay()


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


@dataclass
class _CursorState:
    """Track the cursor position and mode flags for a PETSCII screen."""

    width: int
    height: int
    x: int = 0
    y: int = 0
    lowercase_mode: bool = False
    reverse_mode: bool = False

    def home(self) -> None:
        """Return the cursor to the top-left corner of the screen."""

        self.x = 0
        self.y = 0

    def set_position(self, x: int, y: int) -> None:
        """Clamp ``(x, y)`` to the visible screen bounds and update state."""

        self.x, self.y = _clamp_screen_coordinates(
            x, y, width=self.width, height=self.height
        )

    def move_left(self) -> None:
        """Move the cursor one column to the left without wrapping."""

        if self.x > 0:
            self.x -= 1

    def move_right(self) -> bool:
        """Advance the cursor to the right, wrapping at the end of the row."""

        if self.x < self.width - 1:
            self.x += 1
            return False
        self.x = 0
        self.y += 1
        return self.requires_scroll()

    def move_up(self) -> None:
        """Move the cursor up one row, clamping to the top edge."""

        if self.y > 0:
            self.y -= 1

    def move_down(self) -> bool:
        """Move the cursor down one row and report if scrolling is required."""

        self.y += 1
        return self.requires_scroll()

    def carriage_return(self) -> bool:
        """Return the cursor to column zero and advance to the next row."""

        self.x = 0
        self.y += 1
        return self.requires_scroll()

    def line_feed(self) -> bool:
        """Advance the cursor to the next row without altering the column."""

        self.y += 1
        return self.requires_scroll()

    def backspace(self) -> None:
        """Move the cursor left when processing ``{delete}`` control codes."""

        if self.x > 0:
            self.x -= 1

    def requires_scroll(self) -> bool:
        """Return ``True`` when the cursor moved beyond the bottom row."""

        return self.y >= self.height

    def apply_scroll(self) -> None:
        """Adjust the cursor after the backing buffer scrolls."""

        if self.height:
            self.y = self.height - 1
        else:
            self.y = 0


def _clamp_screen_coordinates(
    x: int, y: int, *, width: int, height: int
) -> tuple[int, int]:
    """Clamp ``(x, y)`` to the 40×25 text plane exposed by the VIC-II."""

    clamped_x = max(0, min(int(x), width - 1))
    clamped_y = max(0, min(int(y), height - 1))
    return clamped_x, clamped_y


def _vic_address_to_coordinates(
    address: int,
    *,
    base: int,
    end: int,
    width: int,
    height: int,
) -> tuple[int, int]:
    """Translate a VIC-II RAM address into zero-based screen coordinates.

    Image BBS mirrors the Commodore 64 layout where screen RAM resides at
    ``$0400-$07E7`` and colour RAM at ``$D800-$DBFF``.  The helper clamps the
    incoming address to that range before translating it into the 40×25
    character grid used by the overlay.
    """

    clamped = max(base, min(int(address), end)) - base
    cells = width * height
    if clamped >= cells:
        clamped = cells - 1
    x = clamped % width
    y = clamped // width
    return x, y


def _resolve_palette_colour(
    value: int, palette: Sequence[int], *, default_index: int
) -> int:
    """Return a palette-safe VIC-II colour derived from the overlay defaults.

    The overlay seeds exactly four VIC-II entries (foreground, unused, background,
    border).  Rendering may supply either a direct colour index or a palette slot
    reference; this helper normalises both forms and falls back to
    ``default_index`` when the value lies outside the configured table.
    """

    resolved = int(value) & 0xFF
    if resolved in palette:
        return resolved
    if 0 <= resolved < len(palette):
        return palette[resolved]
    if not 0 <= default_index < len(palette):
        raise ValueError("default_index must reference a palette entry")
    return palette[default_index]


@dataclass(frozen=True)
class VicRegisterTimelineEntry:
    """Concrete register write emitted during the overlay bootstrap."""

    store: int
    address: int
    value: int | None

    def as_dict(self) -> dict[str, int | None]:
        """Return a JSON-serialisable representation of the timeline entry."""

        return {
            "store": self.store,
            "address": self.address,
            "value": self.value,
        }


def _resolve_vic_register_state(
    entries: Sequence[ml_extra_defaults.HardwareRegisterWrite],
) -> tuple[dict[int, int | None], tuple[VicRegisterTimelineEntry, ...]]:
    """Return the resolved VIC register defaults and write timeline."""

    resolved: dict[int, int | None] = {}
    timeline: list[VicRegisterTimelineEntry] = []
    for entry in entries:
        last_value: int | None = None
        for store, value in entry.writes:
            timeline.append(
                VicRegisterTimelineEntry(store=int(store), address=entry.address, value=value)
            )
            if value is not None:
                last_value = value
        resolved[entry.address] = last_value
    sorted_timeline = tuple(sorted(timeline, key=lambda item: item.store))
    return dict(sorted(resolved.items())), sorted_timeline


class PetsciiScreen:
    """Simplified representation of the 40×25 ImageBBS console."""

    width: int = _WIDTH
    height: int = _HEIGHT

    _SCREEN_BASE = 0x0400
    _SCREEN_END = 0x07E7
    _COLOUR_BASE = 0xD800
    _COLOUR_END = 0xDBFF

    def __init__(
        self,
        palette: Sequence[int] | None = None,
        defaults: ml_extra_defaults.MLExtraDefaults | None = None,
    ) -> None:
        self._defaults = defaults or _load_editor_defaults()
        palette_values = (
            tuple(palette) if palette is not None else self._defaults.palette.colours
        )
        if len(palette_values) != 4:
            raise ValueError("palette must contain four VIC-II colour entries")
        self._palette: list[int] = list(palette_values)
        hardware = self._defaults.hardware
        (
            self._vic_registers,
            self._vic_register_timeline,
        ) = _resolve_vic_register_state(hardware.vic_registers)

        lightbar = self._defaults.lightbar
        self._lightbar_bitmaps: list[int] = [
            lightbar.page1_left,
            lightbar.page1_right,
            lightbar.page2_left,
            lightbar.page2_right,
        ]
        self._underline_char: int = lightbar.underline_char & 0xFF
        self._underline_colour: int = _resolve_palette_colour(
            lightbar.underline_color, self._palette, default_index=0
        )

        self._screen_colour: int = _resolve_palette_colour(
            self._palette[0], self._palette, default_index=0
        )
        self._background_colour: int = _resolve_palette_colour(
            self._palette[2], self._palette, default_index=2
        )
        self._border_colour: int = _resolve_palette_colour(
            self._palette[3], self._palette, default_index=3
        )

        for entry in self._vic_register_timeline:
            self._apply_vic_register_default(entry.address, entry.value)
        self._cursor = _CursorState(width=self.width, height=self.height)
        self._chars: list[list[str]] = [[" " for _ in range(self.width)] for _ in range(self.height)]
        self._colours: list[list[int]] = [
            [self._screen_colour for _ in range(self.width)] for _ in range(self.height)
        ]
        self._codes: list[list[int]] = [[0x20 for _ in range(self.width)] for _ in range(self.height)]
        self._glyph_bank: list[list[int]] = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self._reverse_flags: list[list[bool]] = [
            [False for _ in range(self.width)] for _ in range(self.height)
        ]
        self._underline_flags: list[list[bool]] = [
            [False for _ in range(self.width)] for _ in range(self.height)
        ]

    def _address_to_coordinates(
        self, address: int, *, colour_ram: bool = False
    ) -> tuple[int, int]:
        base = self._COLOUR_BASE if colour_ram else self._SCREEN_BASE
        end = self._COLOUR_END if colour_ram else self._SCREEN_END
        return _vic_address_to_coordinates(
            address,
            base=base,
            end=end,
            width=self.width,
            height=self.height,
        )

    @property
    def defaults(self) -> ml_extra_defaults.MLExtraDefaults:
        """Expose the cached overlay defaults backing the renderer."""

        return self._defaults

    @property
    def lightbar_bitmaps(self) -> tuple[int, int, int, int]:
        """Return the cached lightbar bitmap bytes in overlay order."""

        return tuple(self._lightbar_bitmaps)

    @property
    def underline_char(self) -> int:
        """Return the PETSCII code the overlay uses for lightbar underlines."""

        return self._underline_char

    @property
    def underline_colour(self) -> int:
        """Return the VIC-II colour used when drawing lightbar underlines."""

        return self._underline_colour

    @property
    def palette(self) -> tuple[int, int, int, int]:
        """Return the VIC-II palette entries staged by the overlay."""

        return tuple(self._palette)

    @property
    def resolved_palette_state(self) -> dict[str, object]:
        """Return the active palette state with resolved hardware colours."""

        reverse_state = {
            "foreground": self._background_colour,
            "background": self._screen_colour,
        }
        return {
            "entries": self.palette,
            "screen": self._screen_colour,
            "background": self._background_colour,
            "border": self._border_colour,
            "underline": self._underline_colour,
            "reverse": reverse_state,
        }

    @property
    def cursor_position(self) -> tuple[int, int]:
        """Return the current cursor position as ``(x, y)`` coordinates."""

        return self._cursor.x, self._cursor.y

    def home_cursor(self) -> None:
        """Home the cursor without clearing the backing character matrix."""

        self._cursor.home()

    def set_cursor(self, x: int, y: int) -> None:
        """Position the cursor, clamping to the renderer's visible bounds."""

        self._cursor.set_position(int(x), int(y))

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

    def set_screen_colour(self, value: int) -> None:
        """Update the current screen colour using palette-aware clamping."""

        self._screen_colour = _resolve_palette_colour(
            value, self._palette, default_index=0
        )

    def set_background_colour(self, value: int) -> None:
        """Update the current background colour using palette-aware clamping."""

        self._background_colour = _resolve_palette_colour(
            value, self._palette, default_index=2
        )

    def set_border_colour(self, value: int) -> None:
        """Update the current border colour using palette-aware clamping."""

        self._border_colour = _resolve_palette_colour(
            value, self._palette, default_index=3
        )

    def peek_screen(self, x: int, y: int) -> int:
        """Return the PETSCII code stored at ``(x, y)``."""

        clamped_x, clamped_y = _clamp_screen_coordinates(
            x, y, width=self.width, height=self.height
        )
        return self._codes[clamped_y][clamped_x]

    def poke_screen(self, x: int, y: int, value: int) -> None:
        """Stage ``value`` at ``(x, y)`` without moving the cursor."""

        clamped_x, clamped_y = _clamp_screen_coordinates(
            x, y, width=self.width, height=self.height
        )
        raw_code = int(value) & 0xFF
        char = self._translate_character(raw_code)
        glyph_bank = self._resolve_glyph_bank(None)
        underline_flag = raw_code == self._underline_char
        previous_reverse = self._reverse_flags[clamped_y][clamped_x]
        if raw_code >= 0xC0:
            reverse_flag = True
        elif raw_code < 0x80 or raw_code == 0xA0:
            reverse_flag = False
        else:
            reverse_flag = previous_reverse
        active_colour = (
            self._underline_colour
            if underline_flag
            else self._colours[clamped_y][clamped_x]
        )
        self._write_cell(
            clamped_x,
            clamped_y,
            code=raw_code,
            char=char,
            glyph_bank=glyph_bank,
            colour=active_colour,
            reverse=reverse_flag,
            underline=underline_flag,
        )

    def peek_colour(self, x: int, y: int) -> int:
        """Return the VIC-II colour index stored at ``(x, y)``."""

        clamped_x, clamped_y = _clamp_screen_coordinates(
            x, y, width=self.width, height=self.height
        )
        return self._colours[clamped_y][clamped_x]

    def poke_colour(self, x: int, y: int, value: int) -> None:
        """Update the colour RAM entry at ``(x, y)``."""

        clamped_x, clamped_y = _clamp_screen_coordinates(
            x, y, width=self.width, height=self.height
        )
        resolved_colour = _resolve_palette_colour(
            value, self._palette, default_index=0
        )
        underline_flag = self._underline_flags[clamped_y][clamped_x]
        active_colour = self._underline_colour if underline_flag else resolved_colour
        self._write_cell(
            clamped_x,
            clamped_y,
            code=self._codes[clamped_y][clamped_x],
            char=self._chars[clamped_y][clamped_x],
            glyph_bank=self._glyph_bank[clamped_y][clamped_x],
            colour=active_colour,
            reverse=self._reverse_flags[clamped_y][clamped_x],
            underline=underline_flag,
        )

    def peek_screen_address(self, address: int) -> int:
        """Return the PETSCII code stored at ``address`` in screen RAM."""

        x, y = self._address_to_coordinates(address, colour_ram=False)
        return self.peek_screen(x, y)

    def poke_screen_address(self, address: int, value: int) -> None:
        """Write ``value`` to ``address`` in screen RAM."""

        x, y = self._address_to_coordinates(address, colour_ram=False)
        self.poke_screen(x, y, value)

    def peek_colour_address(self, address: int) -> int:
        """Return the colour RAM value stored at ``address``."""

        x, y = self._address_to_coordinates(address, colour_ram=True)
        return self.peek_colour(x, y)

    def poke_colour_address(self, address: int, value: int) -> None:
        """Write ``value`` to ``address`` in colour RAM."""

        x, y = self._address_to_coordinates(address, colour_ram=True)
        self.poke_colour(x, y, value)

    def apply_vic_register_write(self, address: int, value: int | None) -> None:
        """Apply a VIC register update to the palette state."""

        if value is None:
            return
        if address == _VIC_REGISTER_SCREEN:
            self.set_screen_colour(value)
        elif address == _VIC_REGISTER_BACKGROUND:
            self.set_background_colour(value)
        elif address == _VIC_REGISTER_BORDER:
            self.set_border_colour(value)

    @property
    def characters(self) -> tuple[str, ...]:
        """Return the rendered screen as rows of PETSCII text."""

        return tuple("".join(row) for row in self._chars)

    @property
    def colour_matrix(self) -> tuple[tuple[int, ...], ...]:
        """Expose the per-cell colour buffer."""

        return tuple(tuple(row) for row in self._colours)

    @property
    def code_matrix(self) -> tuple[tuple[int, ...], ...]:
        """Expose the PETSCII character code staged in each screen cell."""

        return tuple(tuple(row) for row in self._codes)

    @property
    def glyph_index_matrix(self) -> tuple[tuple[int, ...], ...]:
        """Return glyph ROM indices corresponding to each screen cell."""

        return tuple(
            tuple(
                petscii_glyphs.get_glyph_index(code, lowercase=bool(self._glyph_bank[y][x]))
                for x, code in enumerate(row)
            )
            for y, row in enumerate(self._codes)
        )

    @property
    def glyph_matrix(self) -> tuple[tuple[petscii_glyphs.GlyphMatrix, ...], ...]:
        """Return the rendered glyph bitmaps for each screen cell."""

        return tuple(
            tuple(
                petscii_glyphs.get_glyph(code, lowercase=bool(self._glyph_bank[y][x]))
                for x, code in enumerate(row)
            )
            for y, row in enumerate(self._codes)
        )

    @property
    def reverse_matrix(self) -> tuple[tuple[bool, ...], ...]:
        """Expose the per-cell reverse attribute state."""

        return tuple(tuple(row) for row in self._reverse_flags)

    @property
    def underline_matrix(self) -> tuple[tuple[bool, ...], ...]:
        """Expose the per-cell underline state derived from the lightbar defaults."""

        return tuple(tuple(row) for row in self._underline_flags)

    @property
    def vic_registers(self) -> dict[int, int | None]:
        """Return the resolved VIC register defaults."""

        return dict(self._vic_registers)

    @property
    def vic_register_timeline(self) -> tuple[VicRegisterTimelineEntry, ...]:
        """Return the timeline of VIC register writes recovered from the overlay."""

        return self._vic_register_timeline

    @property
    def resolved_colour_matrix(self) -> tuple[tuple[tuple[int, int], ...], ...]:
        """Return the foreground/background colour pairs for each cell."""

        background = _resolve_palette_colour(
            self._background_colour, self._palette, default_index=2
        )
        return tuple(
            tuple(
                (
                    background
                    if reverse
                    else _resolve_palette_colour(
                        colour, self._palette, default_index=0
                    ),
                    _resolve_palette_colour(
                        colour, self._palette, default_index=0
                    )
                    if reverse
                    else background,
                )
                for colour, reverse in zip(colour_row, reverse_row)
            )
            for colour_row, reverse_row in zip(self._colours, self._reverse_flags)
        )

    def set_lightbar_bitmaps(self, bitmaps: Sequence[int]) -> None:
        """Override the cached lightbar bitmaps using overlay ordering."""

        if len(bitmaps) != 4:
            raise ValueError("lightbar bitmap sequence must contain four entries")
        self._lightbar_bitmaps = [int(value) & 0xFF for value in bitmaps]

    def set_underline(
        self,
        *,
        char: int | None = None,
        colour: int | None = None,
    ) -> None:
        """Update the underline PETSCII code or colour using palette-safe values."""

        if char is not None:
            self._underline_char = int(char) & 0xFF
        if colour is not None:
            self._underline_colour = _resolve_palette_colour(
                int(colour), self._palette, default_index=0
            )

    def clear(self) -> None:
        """Clear the screen and home the cursor."""

        for y in range(self.height):
            for x in range(self.width):
                self._write_cell(
                    x,
                    y,
                    code=0x20,
                    char=" ",
                    glyph_bank=0,
                    colour=self._screen_colour,
                    reverse=False,
                    underline=False,
                )
        self._cursor.home()

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
            self._cursor.home()
            return True
        if byte == 0x0D:  # carriage return
            self._ensure_scroll(self._cursor.carriage_return())
            return True
        if byte == 0x0A:  # line feed
            self._ensure_scroll(self._cursor.line_feed())
            return True
        if byte == 0x11:  # cursor down
            self._ensure_scroll(self._cursor.move_down())
            return True
        if byte == 0x91:  # cursor up
            self._cursor.move_up()
            return True
        if byte == 0x1D:  # cursor right
            self._ensure_scroll(self._cursor.move_right())
            return True
        if byte == 0x9D:  # cursor left
            self._cursor.move_left()
            return True
        if byte == 0x14:  # delete/backspace
            self._cursor.backspace()
            self._put_character(0x20, " ", glyph_bank=0, reverse=False)
            return True
        if byte == 0x12:  # reverse on
            self._cursor.reverse_mode = True
            return True
        if byte == 0x92:  # reverse off
            self._cursor.reverse_mode = False
            return True
        if byte == 0x0E:  # switch to lowercase/uppercase
            self._cursor.lowercase_mode = True
            return True
        if byte == 0x8E:  # switch to uppercase/graphics
            self._cursor.lowercase_mode = False
            return True
        return False

    def _handle_colour(self, byte: int) -> bool:
        colour = _COLOR_CODES.get(byte)
        if colour is None:
            return False
        self._screen_colour = _resolve_palette_colour(
            colour, self._palette, default_index=0
        )
        return True

    def _ensure_scroll(self, needs_scroll: bool) -> None:
        if needs_scroll:
            self._scroll()

    def _draw_character(self, byte: int) -> None:
        char = self._translate_character(byte)
        self._put_character(byte, char)
        self._ensure_scroll(self._cursor.move_right())

    def _put_character(
        self,
        byte: int,
        char: str,
        *,
        glyph_bank: int | None = None,
        reverse: bool | None = None,
        underline: bool | None = None,
    ) -> None:
        x, y = self._cursor.x, self._cursor.y
        if 0 <= y < self.height and 0 <= x < self.width:
            bank = self._resolve_glyph_bank(glyph_bank)
            reverse_flag = (
                self._cursor.reverse_mode if reverse is None else reverse
            )
            raw_code = byte & 0xFF
            underline_flag = (
                bool(underline)
                if underline is not None
                else raw_code == self._underline_char
            )
            active_colour = (
                self._underline_colour if underline_flag else self._screen_colour
            )
            self._write_cell(
                x,
                y,
                code=raw_code,
                char=char,
                glyph_bank=bank,
                colour=active_colour,
                reverse=reverse_flag,
                underline=underline_flag,
            )

    def _scroll(self) -> None:
        self._chars.pop(0)
        self._colours.pop(0)
        self._codes.pop(0)
        self._glyph_bank.pop(0)
        self._reverse_flags.pop(0)
        self._underline_flags.pop(0)
        blank_chars = [" " for _ in range(self.width)]
        blank_colours = [self._screen_colour for _ in range(self.width)]
        blank_codes = [0x20 for _ in range(self.width)]
        blank_bank = [0 for _ in range(self.width)]
        blank_reverse = [False for _ in range(self.width)]
        blank_underline = [False for _ in range(self.width)]
        self._chars.append(blank_chars)
        self._colours.append(blank_colours)
        self._codes.append(blank_codes)
        self._glyph_bank.append(blank_bank)
        self._reverse_flags.append(blank_reverse)
        self._underline_flags.append(blank_underline)
        self._cursor.apply_scroll()

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
            if not self._cursor.lowercase_mode:
                return char.upper()
            return char
        return " "

    def _write_cell(
        self,
        x: int,
        y: int,
        *,
        code: int,
        char: str,
        glyph_bank: int,
        colour: int,
        reverse: bool,
        underline: bool,
    ) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        resolved_colour = _resolve_palette_colour(
            colour, self._palette, default_index=0
        )
        self._chars[y][x] = char
        self._colours[y][x] = resolved_colour
        self._codes[y][x] = code & 0xFF
        self._glyph_bank[y][x] = glyph_bank & 0x01
        self._reverse_flags[y][x] = bool(reverse)
        self._underline_flags[y][x] = bool(underline)

    def _resolve_glyph_bank(self, glyph_bank: int | None) -> int:
        if glyph_bank is not None:
            return int(glyph_bank) & 0x01
        return 1 if self._cursor.lowercase_mode else 0

    def _apply_vic_register_default(self, address: int, value: int | None) -> None:
        if value is None:
            return
        if address == _VIC_REGISTER_SCREEN:
            self.set_screen_colour(value)
        elif address == _VIC_REGISTER_BACKGROUND:
            self.set_background_colour(value)
        elif address == _VIC_REGISTER_BORDER:
            self.set_border_colour(value)


class _TracingPetsciiScreen(PetsciiScreen):
    """Instrumented screen that records glyphs drawn during rendering."""

    def __init__(
        self,
        recorder: list[GlyphCell],
        *,
        defaults: ml_extra_defaults.MLExtraDefaults | None = None,
    ) -> None:
        super().__init__(defaults=defaults)
        self._recorder = recorder

    def _put_character(
        self,
        byte: int,
        char: str,
        *,
        glyph_bank: int | None = None,
        reverse: bool | None = None,
    ) -> None:
        x, y = self._cursor.x, self._cursor.y
        super()._put_character(
            byte,
            char,
            glyph_bank=glyph_bank,
            reverse=reverse,
        )
        lowercase = bool(self._glyph_bank[y][x])
        code = self.code_matrix[y][x]
        glyph_index = self.glyph_index_matrix[y][x]
        glyph_bitmap = self.glyph_matrix[y][x]
        reverse_flag = self.reverse_matrix[y][x]
        self._recorder.append(
            GlyphCell(
                code=code,
                position=(x, y),
                lowercase=lowercase,
                reverse=reverse_flag,
                glyph_index=glyph_index,
                glyph=glyph_bitmap,
            )
        )


def _strip_terminator(payload: Iterable[int]) -> tuple[int, ...]:
    """Return ``payload`` truncated at the first zero terminator."""

    trimmed: list[int] = []
    for raw in payload:
        value = raw & 0xFF
        if value == 0x00:
            break
        trimmed.append(value)
    return tuple(trimmed)


def _render_payload_glyphs(
    payload: Iterable[int],
    *,
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> tuple[GlyphCell, ...]:
    """Render ``payload`` through :class:`PetsciiScreen` and capture glyph metadata."""

    data = _strip_terminator(payload)
    if not data:
        return ()
    recorder: list[GlyphCell] = []
    screen = _TracingPetsciiScreen(recorder, defaults=defaults)
    screen.write(bytes(data))
    return tuple(recorder)


def _make_glyph_run(
    payload: Iterable[int],
    text: str,
    *,
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> GlyphRun:
    """Return a :class:`GlyphRun` describing ``payload`` rendered as PETSCII."""

    raw = tuple(int(byte) & 0xFF for byte in payload)
    rendered = _strip_terminator(raw)
    glyphs = _render_payload_glyphs(rendered, defaults=defaults)
    return GlyphRun(text=text, payload=raw, rendered=rendered, glyphs=glyphs)


def _optional_glyph_run(
    payload: Iterable[int] | None,
    text: str,
    *,
    defaults: ml_extra_defaults.MLExtraDefaults,
) -> GlyphRun | None:
    if payload is None:
        return None
    return _make_glyph_run(payload, text, defaults=defaults)


def build_overlay_glyph_lookup(
    defaults: ml_extra_defaults.MLExtraDefaults | None = None,
) -> OverlayGlyphLookup:
    """Return glyph metadata derived from the recovered overlay text tables."""

    resolved = defaults or _load_editor_defaults()

    macro_runs: list[GlyphRun] = []
    macros_by_slot: dict[int, GlyphRun] = {}
    macros_by_text: dict[str, GlyphRun] = {}
    for entry in resolved.macros:
        run = _make_glyph_run(entry.payload, entry.decoded_text, defaults=resolved)
        macro_runs.append(run)
        macros_by_slot[entry.slot] = run
        macros_by_text.setdefault(entry.decoded_text, run)

    flag_runs: list[FlagGlyphMapping] = []
    for record in resolved.flag_records:
        match_run = _make_glyph_run(
            record.match_sequence,
            record.match_text,
            defaults=resolved,
        )
        replacement_run = _optional_glyph_run(
            record.replacement,
            record.replacement_text,
            defaults=resolved,
        )
        if replacement_run is None:
            pointer_run = macros_by_slot.get(record.pointer)
            if pointer_run is not None:
                # Why: pointer slots publish the runtime replacement payload when the overlay omits inline bytes.
                replacement_run = pointer_run
        flag_runs.append(
            FlagGlyphMapping(
                record=record,
                match=match_run,
                replacement=replacement_run,
                page1=_optional_glyph_run(
                    record.page1_payload,
                    record.page1_text,
                    defaults=resolved,
                ),
                page2=_optional_glyph_run(
                    record.page2_payload,
                    record.page2_text,
                    defaults=resolved,
                ),
            )
        )

    directory_run = _make_glyph_run(
        resolved.flag_directory_tail,
        resolved.flag_directory_text,
        defaults=resolved,
    )

    directory_block_run = _make_glyph_run(
        resolved.flag_directory_block,
        ml_extra_extract.decode_petscii(resolved.flag_directory_block),
        defaults=resolved,
    )

    return OverlayGlyphLookup(
        macros=tuple(macro_runs),
        macros_by_slot=MappingProxyType(macros_by_slot),
        macros_by_text=MappingProxyType(macros_by_text),
        flag_records=tuple(flag_runs),
        flag_directory_tail=directory_run,
        flag_directory_block=directory_block_run,
    )


def render_petscii_payload(
    payload: Iterable[int],
    *,
    defaults: ml_extra_defaults.MLExtraDefaults | None = None,
    text: str | None = None,
) -> GlyphRun:
    """Render ``payload`` and return a :class:`GlyphRun` describing the glyphs."""

    resolved = defaults or _load_editor_defaults()
    label = text if text is not None else ""
    return _make_glyph_run(payload, label, defaults=resolved)
@dataclass(frozen=True)
class GlyphCell:
    """Single rendered glyph sampled from a PETSCII payload."""

    code: int
    position: tuple[int, int]
    lowercase: bool
    reverse: bool
    glyph_index: int
    glyph: petscii_glyphs.GlyphMatrix


@dataclass(frozen=True)
class GlyphRun:
    """Rendered snapshot of a PETSCII byte sequence."""

    text: str
    payload: tuple[int, ...]
    rendered: tuple[int, ...]
    glyphs: tuple[GlyphCell, ...]

    @property
    def codes(self) -> tuple[int, ...]:
        """Return the rendered PETSCII codes in draw order."""

        return tuple(cell.code for cell in self.glyphs)


@dataclass(frozen=True)
class FlagGlyphMapping:
    """Rendered glyph runs for a decoded ampersand flag record."""

    record: ml_extra_defaults.FlagRecord
    match: GlyphRun
    replacement: GlyphRun | None
    page1: GlyphRun | None
    page2: GlyphRun | None


@dataclass(frozen=True)
class OverlayGlyphLookup:
    """Lookup table mirroring overlay text rendered through :class:`PetsciiScreen`."""

    macros: tuple[GlyphRun, ...]
    macros_by_slot: Mapping[int, GlyphRun]
    macros_by_text: Mapping[str, GlyphRun]
    flag_records: tuple[FlagGlyphMapping, ...]
    flag_directory_tail: GlyphRun
    flag_directory_block: GlyphRun
