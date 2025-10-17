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
        self._underline_colour: int = self._resolve_palette_colour(
            lightbar.underline_color, default_index=0
        )

        screen_colour = self._palette[0]
        background_colour = self._palette[2]
        border_colour = self._palette[3]

        for entry in self._vic_register_timeline:
            value = entry.value
            if value is None:
                continue
            if entry.address == _VIC_REGISTER_SCREEN:
                screen_colour = value
            elif entry.address == _VIC_REGISTER_BACKGROUND:
                background_colour = value
            elif entry.address == _VIC_REGISTER_BORDER:
                border_colour = value

        self._screen_colour: int = self._resolve_palette_colour(
            screen_colour, default_index=0
        )
        self._background_colour: int = self._resolve_palette_colour(
            background_colour, default_index=2
        )
        self._border_colour: int = self._resolve_palette_colour(
            border_colour, default_index=3
        )
        self._cursor_x: int = 0
        self._cursor_y: int = 0
        self._lowercase_mode = False
        self._reverse_mode = False
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
    def cursor_position(self) -> tuple[int, int]:
        """Return the current cursor position as ``(x, y)`` coordinates."""

        return self._cursor_x, self._cursor_y

    def home_cursor(self) -> None:
        """Home the cursor without clearing the backing character matrix."""

        self._cursor_x = 0
        self._cursor_y = 0

    def set_cursor(self, x: int, y: int) -> None:
        """Position the cursor, clamping to the renderer's visible bounds."""

        clamped_x = max(0, min(int(x), self.width - 1))
        clamped_y = max(0, min(int(y), self.height - 1))
        self._cursor_x = clamped_x
        self._cursor_y = clamped_y

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

        background = self._resolve_palette_colour(
            self._background_colour, default_index=2
        )
        return tuple(
            tuple(
                (
                    background if reverse else self._resolve_palette_colour(
                        colour, default_index=0
                    ),
                    self._resolve_palette_colour(colour, default_index=0)
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
            self._underline_colour = self._resolve_palette_colour(
                int(colour), default_index=0
            )

    def clear(self) -> None:
        """Clear the screen and home the cursor."""

        for y in range(self.height):
            for x in range(self.width):
                self._chars[y][x] = " "
                self._colours[y][x] = self._screen_colour
                self._codes[y][x] = 0x20
                self._glyph_bank[y][x] = 0
                self._reverse_flags[y][x] = False
                self._underline_flags[y][x] = False
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
            self._put_character(0x20, " ", glyph_bank=0, reverse=False)
            return True
        if byte == 0x12:  # reverse on
            self._reverse_mode = True
            return True
        if byte == 0x92:  # reverse off
            self._reverse_mode = False
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
        self._screen_colour = self._resolve_palette_colour(colour, default_index=0)
        return True

    def _draw_character(self, byte: int) -> None:
        char = self._translate_character(byte)
        self._put_character(byte, char)
        self._cursor_x += 1
        if self._cursor_x >= self.width:
            self._cursor_x = 0
            self._cursor_y += 1
            self._clamp_cursor()

    def _put_character(
        self,
        byte: int,
        char: str,
        *,
        glyph_bank: int | None = None,
        reverse: bool | None = None,
        underline: bool | None = None,
    ) -> None:
        if 0 <= self._cursor_y < self.height and 0 <= self._cursor_x < self.width:
            bank = glyph_bank if glyph_bank is not None else (1 if self._lowercase_mode else 0)
            reverse_flag = self._reverse_mode if reverse is None else reverse
            raw_code = byte & 0xFF
            underline_flag = (
                bool(underline)
                if underline is not None
                else raw_code == self._underline_char
            )
            colour = (
                self._underline_colour if underline_flag else self._screen_colour
            )
            self._chars[self._cursor_y][self._cursor_x] = char
            self._colours[self._cursor_y][self._cursor_x] = colour
            self._codes[self._cursor_y][self._cursor_x] = raw_code
            self._glyph_bank[self._cursor_y][self._cursor_x] = bank
            self._reverse_flags[self._cursor_y][self._cursor_x] = reverse_flag
            self._underline_flags[self._cursor_y][self._cursor_x] = underline_flag

    def _clamp_cursor(self) -> None:
        if self._cursor_y < self.height:
            return
        self._scroll()

    def _scroll(self) -> None:
        self._chars.pop(0)
        self._colours.pop(0)
        self._codes.pop(0)
        self._glyph_bank.pop(0)
        self._reverse_flags.pop(0)
        self._underline_flags.pop(0)
        self._chars.append([" " for _ in range(self.width)])
        self._colours.append([self._screen_colour for _ in range(self.width)])
        self._codes.append([0x20 for _ in range(self.width)])
        self._glyph_bank.append([0 for _ in range(self.width)])
        self._reverse_flags.append([False for _ in range(self.width)])
        self._underline_flags.append([False for _ in range(self.width)])
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

    def _resolve_palette_colour(self, value: int, *, default_index: int) -> int:
        """Clamp ``value`` to one of the four palette entries."""

        resolved = int(value) & 0xFF
        if resolved in self._palette:
            return resolved
        if 0 <= resolved < len(self._palette):
            return self._palette[resolved]
        if not 0 <= default_index < len(self._palette):
            raise ValueError("default_index must reference a palette entry")
        return self._palette[default_index]


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
        x, y = self._cursor_x, self._cursor_y
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
        flag_runs.append(
            FlagGlyphMapping(
                record=record,
                match=match_run,
                replacement=_optional_glyph_run(
                    record.replacement,
                    record.replacement_text,
                    defaults=resolved,
                ),
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
