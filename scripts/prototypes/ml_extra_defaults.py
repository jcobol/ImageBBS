"""Structured view of the recovered ``ml.extra`` overlay for host tooling.

This module wraps :mod:`scripts.prototypes.ml_extra_extract` so callers can
consume the pointer-directory records (macro slots, relocation addresses, and
raw PETSCII payloads) without reimplementing the extraction logic.  The helper
mirrors :mod:`scripts.prototypes.setup_defaults`: it resolves the archived
binary from ``v1.2/from-floppy/ml.extra`` by default and exposes dataclasses for
each recovered table, including the lightbar defaults and editor palette stored
near the overlay's tail section.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from . import ml_extra_extract

# Additional macro payloads recovered from ancillary disk files.  The original
# ``ml.extra`` overlay only publishes slots tied to the ampersand flag
# dispatcher; menu macros such as the file-transfer header live in the
# ``e.i.macro`` REL file loaded by the BASIC runtime.  The archival dump is not
# bundled with the repository, so the recovered PETSCII payloads are mirrored
# here to keep host tooling in sync with the 1.2B experience.
_EXTRA_MACRO_PAYLOADS: dict[int, tuple[int, ...]] = {
    0x28: (
        0x93,
        # "           FILE TRANSFER MENU           "
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0xC6,
        0xC9,
        0xCC,
        0xC5,
        0x20,
        0xD4,
        0xD2,
        0xC1,
        0xCE,
        0xD3,
        0xC6,
        0xC5,
        0xD2,
        0x20,
        0xCD,
        0xC5,
        0xCE,
        0xD5,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x0D,
        # " UD UPLOAD FILES      UL UPLOAD LIBRARY "
        0x20,
        0xD5,
        0xC4,
        0x20,
        0xD5,
        0xD0,
        0xCC,
        0xCF,
        0xC1,
        0xC4,
        0x20,
        0xC6,
        0xC9,
        0xCC,
        0xC5,
        0xD3,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0x20,
        0xD5,
        0xCC,
        0x20,
        0xD5,
        0xD0,
        0xCC,
        0xCF,
        0xC1,
        0xC4,
        0x20,
        0xCC,
        0xC9,
        0xC2,
        0xD2,
        0xC1,
        0xD2,
        0xD9,
        0x20,
        0x0D,
        # " UX UPLOAD XMODEM   VB VIEW BY BLOCKS   "
        0x20,
        0xD5,
        0xD8,
        0x20,
        0xD5,
        0xD0,
        0xCC,
        0xCF,
        0xC1,
        0xC4,
        0x20,
        0xD8,
        0xCD,
        0xCF,
        0xC4,
        0xC5,
        0xCD,
        0x20,
        0x20,
        0x20,
        0xD6,
        0xC2,
        0x20,
        0xD6,
        0xC9,
        0xC5,
        0xD7,
        0x20,
        0xC2,
        0xD9,
        0x20,
        0xC2,
        0xCC,
        0xCF,
        0xC3,
        0xCB,
        0xD3,
        0x20,
        0x20,
        0x20,
        0x0D,
        # " BB BULLETIN BOARD   RD READ DIRECTORY  "
        0x20,
        0xC2,
        0xC2,
        0x20,
        0xC2,
        0xD5,
        0xCC,
        0xCC,
        0xC5,
        0xD4,
        0xC9,
        0xCE,
        0x20,
        0xC2,
        0xCF,
        0xC1,
        0xD2,
        0xC4,
        0x20,
        0x20,
        0x20,
        0xD2,
        0xC4,
        0x20,
        0xD2,
        0xC5,
        0xC1,
        0xC4,
        0x20,
        0xC4,
        0xC9,
        0xD2,
        0xC5,
        0xC3,
        0xD4,
        0xCF,
        0xD2,
        0xD9,
        0x20,
        0x20,
        0x0D,
        # " DC DIRECTORY CHANGE  CA CARRIER ALERT  "
        0x20,
        0xC4,
        0xC3,
        0x20,
        0xC4,
        0xC9,
        0xD2,
        0xC5,
        0xC3,
        0xD4,
        0xCF,
        0xD2,
        0xD9,
        0x20,
        0xC3,
        0xC8,
        0xC1,
        0xCE,
        0xC7,
        0xC5,
        0x20,
        0x20,
        0xC3,
        0xC1,
        0x20,
        0xC3,
        0xC1,
        0xD2,
        0xD2,
        0xC9,
        0xC5,
        0xD2,
        0x20,
        0xC1,
        0xCC,
        0xC5,
        0xD2,
        0xD4,
        0x20,
        0x20,
        0x0D,
        # " DR DOWNLOAD REQUEST  PF PROTOCOL FLAGS "
        0x20,
        0xC4,
        0xD2,
        0x20,
        0xC4,
        0xCF,
        0xD7,
        0xCE,
        0xCC,
        0xCF,
        0xC1,
        0xC4,
        0x20,
        0xD2,
        0xC5,
        0xD1,
        0xD5,
        0xC5,
        0xD3,
        0xD4,
        0x20,
        0x20,
        0xD0,
        0xC6,
        0x20,
        0xD0,
        0xD2,
        0xCF,
        0xD4,
        0xCF,
        0xC3,
        0xCF,
        0xCC,
        0x20,
        0xC6,
        0xCC,
        0xC1,
        0xC7,
        0xD3,
        0x20,
        0x00,
    ),
    0x29: (
        0xC3,
        0xCF,
        0xCD,
        0xCD,
        0xC1,
        0xCE,
        0xC4,
        0x20,
        0x28,
        0xD1,
        0x20,
        0xD4,
        0xCF,
        0x20,
        0xC5,
        0xD8,
        0xC9,
        0xD4,
        0x29,
        0x3A,
        0x20,
        0x00,
    ),
    0x2A: (
        0x3F,
        0x3F,
        0x20,
        0xD5,
        0xCE,
        0xCB,
        0xCE,
        0xCF,
        0xD7,
        0xCE,
        0x20,
        0xC3,
        0xCF,
        0xCD,
        0xCD,
        0xC1,
        0xCE,
        0xC4,
        0x00,
    ),
}


def _strip_macro_terminator(payload: Iterable[int]) -> Tuple[int, ...]:
    """Normalise ``payload`` by trimming the first trailing zero byte."""

    trimmed: list[int] = []
    for raw in payload:
        value = int(raw) & 0xFF
        if value == 0x00:
            break
        trimmed.append(value)
    return tuple(trimmed)


def _render_macro_screen(
    payload: Iterable[int],
    *,
    defaults: object,
) -> "MacroScreen" | None:
    """Render ``payload`` through :class:`PetsciiScreen` and capture screen buffers."""

    rendered = _strip_macro_terminator(payload)
    if not rendered:
        return None

    from .console_renderer import PetsciiScreen

    screen = PetsciiScreen(defaults=defaults)
    screen.write(bytes(rendered))
    return MacroScreen(
        glyph_matrix=screen.code_matrix,
        colour_matrix=screen.colour_matrix,
    )

_LIGHTBAR_TABLE_ADDR = 0xD3F6
_LIGHTBAR_TABLE_LENGTH = 6  # four flag bytes + underline char/colour
_PALETTE_ADDR = 0xC66A
_PALETTE_LENGTH = 4
_FLAG_TABLE_ADDR = 0xD9C3
_FLAG_TABLE_LENGTH = 0x46

_VIC_TARGETS = (0xD403, 0xD404, 0xD405, 0xD406)
_POINTER_LOW = 0x42FE
_POINTER_HIGH = 0x42FF
_SID_VOLUME = 0xD418


@dataclass(frozen=True)
class MacroScreen:
    """Snapshot of glyph and colour buffers rendered for a macro payload."""

    glyph_matrix: Tuple[Tuple[int, ...], ...]
    colour_matrix: Tuple[Tuple[int, ...], ...]

    def __post_init__(self) -> None:
        if len(self.glyph_matrix) != len(self.colour_matrix):
            raise ValueError("glyph and colour matrices must have matching heights")
        for glyph_row, colour_row in zip(self.glyph_matrix, self.colour_matrix, strict=True):
            if len(glyph_row) != len(colour_row):
                raise ValueError("glyph and colour rows must have matching widths")

    @property
    def height(self) -> int:
        """Return the number of rows captured in the snapshot."""

        return len(self.glyph_matrix)

    @property
    def width(self) -> int:
        """Return the number of columns captured per row."""

        return len(self.glyph_matrix[0]) if self.glyph_matrix else 0

    @property
    def glyph_bytes(self) -> Tuple[int, ...]:
        """Return the flattened PETSCII glyph buffer in row-major order."""

        return tuple(value for row in self.glyph_matrix for value in row)

    @property
    def colour_bytes(self) -> Tuple[int, ...]:
        """Return the flattened colour RAM buffer in row-major order."""

        return tuple(value for row in self.colour_matrix for value in row)


@dataclass(frozen=True)
class MacroDirectoryEntry:
    """Single pointer-directory record recovered from ``ml.extra``."""

    slot: int
    address: int
    payload: Tuple[int, ...]
    decoded_text: str
    screen: MacroScreen | None = None

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the entry."""

        return {
            "slot": self.slot,
            "address": f"${self.address:04x}",
            "bytes": [f"${value:02x}" for value in self.payload],
            "text": self.decoded_text,
        }

    def byte_preview(self, limit: int = 8) -> str:
        """Return a short hex preview of the payload for reporting."""

        prefix = (f"${value:02x}" for value in self.payload[:limit])
        preview = ", ".join(prefix)
        if len(self.payload) > limit:
            preview += ", …"
        return preview


@dataclass(frozen=True)
class LightbarDefaults:
    """Initial flag bitmaps and underline settings exported by the overlay."""

    page1_left: int
    page1_right: int
    page2_left: int
    page2_right: int
    underline_char: int
    underline_color: int

    @property
    def bitmaps(self) -> Tuple[int, int, int, int]:
        """Return the lightbar bitmaps as a tuple in overlay order."""

        return (self.page1_left, self.page1_right, self.page2_left, self.page2_right)

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the defaults."""

        return {
            "page1_left": f"${self.page1_left:02x}",
            "page1_right": f"${self.page1_right:02x}",
            "page2_left": f"${self.page2_left:02x}",
            "page2_right": f"${self.page2_right:02x}",
            "underline_char": f"${self.underline_char:02x}",
            "underline_color": f"${self.underline_color:02x}",
        }


@dataclass(frozen=True)
class EditorPalette:
    """VIC-II colour IDs used by the recovered ml.extra overlay."""

    colours: Tuple[int, int, int, int]

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the palette."""

        return {
            "colours": [f"${value:02x}" for value in self.colours],
        }


@dataclass(frozen=True)
class FlagRecord:
    """Single entry from the overlay's lightbar flag table."""

    header: int
    mask_c0db: int
    mask_c0dc: int
    long_form: bool
    match_sequence: Tuple[int, ...]
    replacement: Tuple[int, ...] | None
    page1_payload: Tuple[int, ...] | None
    page2_payload: Tuple[int, ...] | None
    pointer: int

    @property
    def match_text(self) -> str:
        """Decoded PETSCII representation of :attr:`match_sequence`."""

        return ml_extra_extract.decode_petscii(self.match_sequence)

    @property
    def replacement_text(self) -> str:
        """Decoded PETSCII string for the short-form replacement bytes."""

        if self.replacement is None:
            return ""
        return ml_extra_extract.decode_petscii(self.replacement)

    @property
    def page1_text(self) -> str:
        """Decoded PETSCII representation of the page-one payload."""

        if self.page1_payload is None:
            return ""
        return ml_extra_extract.decode_petscii(self.page1_payload)

    @property
    def page2_text(self) -> str:
        """Decoded PETSCII representation of the page-two payload."""

        if self.page2_payload is None:
            return ""
        return ml_extra_extract.decode_petscii(self.page2_payload)

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON description of the record."""

        data: Dict[str, object] = {
            "header": f"${self.header:02x}",
            "mask_c0db": f"${self.mask_c0db:02x}",
            "mask_c0dc": f"${self.mask_c0dc:02x}",
            "long_form": self.long_form,
            "match_bytes": [f"${byte:02x}" for byte in self.match_sequence],
            "match_text": self.match_text,
            "pointer": f"${self.pointer:02x}",
        }
        if self.replacement is not None:
            data["replacement_bytes"] = [
                f"${byte:02x}" for byte in self.replacement
            ]
            data["replacement_text"] = self.replacement_text
        if self.page1_payload is not None:
            data["page1_bytes"] = [f"${byte:02x}" for byte in self.page1_payload]
            data["page1_text"] = self.page1_text
        if self.page2_payload is not None:
            data["page2_bytes"] = [f"${byte:02x}" for byte in self.page2_payload]
            data["page2_text"] = self.page2_text
        return data


@dataclass(frozen=True)
class FlagDispatchEntry:
    """Maps a flag index to its macro slot and handler address."""

    flag_index: int
    slot: int
    handler_address: int

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON description of the dispatch entry."""

        return {
            "flag_index": f"${self.flag_index:02x}",
            "slot": f"${self.slot:02x}",
            "handler": f"${self.handler_address:04x}",
        }


@dataclass(frozen=True)
class FlagDispatchTable:
    """Recovered dispatch metadata for the ampersand flag handlers."""

    leading_marker: int
    trailing_marker: int
    entries: Tuple[FlagDispatchEntry, ...]

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the table."""

        return {
            "leading_marker": f"${self.leading_marker:02x}",
            "trailing_marker": f"${self.trailing_marker:02x}",
            "entries": [entry.as_dict() for entry in self.entries],
        }


@dataclass(frozen=True)
class MLExtraDefaults:
    """Aggregates recovered tables from the ``ml.extra`` overlay."""

    load_address: int
    lightbar: LightbarDefaults
    palette: EditorPalette
    flag_records: Tuple[FlagRecord, ...]
    flag_directory_tail: Tuple[int, ...]
    flag_directory_block: Tuple[int, ...]
    flag_dispatch: FlagDispatchTable
    macros: Tuple[MacroDirectoryEntry, ...]
    hardware: HardwareDefaults

    @property
    def macro_slots(self) -> Tuple[int, ...]:
        """Return the slot identifiers in pointer-directory order."""

        return tuple(entry.slot for entry in self.macros)

    @property
    def macros_by_slot(self) -> Dict[int, MacroDirectoryEntry]:
        """Expose a mapping from slot identifier to macro payload."""

        return {entry.slot: entry for entry in self.macros}

    @property
    def flag_directory_text(self) -> str:
        """Return the PETSCII-decoded tail that stores flag strings."""

        return ml_extra_extract.decode_petscii(self.flag_directory_tail)

    @classmethod
    def from_overlay(cls, overlay_path: Optional[Path] = None) -> "MLExtraDefaults":
        """Load the archived ``ml.extra`` overlay and decode its tables."""

        path = overlay_path or default_overlay_path()
        load_address, memory = ml_extra_extract.load_prg(path)

        lightbar_raw = _slice_memory(
            memory,
            load_address,
            _LIGHTBAR_TABLE_ADDR,
            _LIGHTBAR_TABLE_LENGTH,
        )
        lightbar = LightbarDefaults(
            page1_left=lightbar_raw[0],
            page1_right=lightbar_raw[1],
            page2_left=lightbar_raw[2],
            page2_right=lightbar_raw[3],
            underline_char=lightbar_raw[4],
            underline_color=lightbar_raw[5],
        )

        palette = EditorPalette(
            colours=tuple(
                _slice_memory(memory, load_address, _PALETTE_ADDR, _PALETTE_LENGTH)
            ),
        )

        flag_records, flag_tail, flag_block = _decode_flag_table(memory, load_address)
        flag_dispatch = _decode_flag_dispatch(memory, load_address)

        hardware = HardwareDefaults(
            vic_registers=_collect_vic_register_writes(memory, load_address),
            pointer=_collect_pointer_defaults(memory, load_address),
            sid_volume=_read_sid_volume(memory, load_address),
        )

        macro_defaults = SimpleNamespace(
            lightbar=lightbar,
            palette=palette,
            hardware=hardware,
        )

        macro_entries: list[MacroDirectoryEntry] = []
        for entry in ml_extra_extract.iter_pointer_directory(
            memory, load_addr=load_address
        ):
            payload = tuple(entry.data)
            macro_entries.append(
                MacroDirectoryEntry(
                    slot=entry.slot,
                    address=entry.address,
                    payload=payload,
                    decoded_text=entry.text,
                    screen=_render_macro_screen(payload, defaults=macro_defaults),
                )
            )

        existing_slots = {entry.slot for entry in macro_entries}
        for slot, payload in sorted(_EXTRA_MACRO_PAYLOADS.items()):
            if slot in existing_slots:
                continue
            macro_entries.append(
                MacroDirectoryEntry(
                    slot=slot,
                    address=0x0000,
                    payload=payload,
                    decoded_text=ml_extra_extract.decode_petscii(payload),
                    screen=_render_macro_screen(payload, defaults=macro_defaults),
                )
            )

        macro_entries.sort(key=lambda entry: entry.slot)
        macros = tuple(macro_entries)
        return cls(
            load_address=load_address,
            lightbar=lightbar,
            palette=palette,
            flag_records=flag_records,
            flag_directory_tail=flag_tail,
            flag_dispatch=flag_dispatch,
            macros=macros,
            hardware=hardware,
            flag_directory_block=flag_block,
        )


def _decode_flag_table(
    memory: Sequence[int], load_address: int
) -> Tuple[Tuple[FlagRecord, ...], Tuple[int, ...], Tuple[int, ...]]:
    """Return the flag records and trailing directory bytes from the overlay."""

    raw = _slice_memory(memory, load_address, _FLAG_TABLE_ADDR, _FLAG_TABLE_LENGTH)
    table = [byte ^ 0xFF for byte in raw]

    records: list[FlagRecord] = []
    index = 0
    length = len(table)
    while index < length:
        header = table[index]
        if header < 0x80:
            break
        if index + 3 >= length:
            raise ValueError("truncated flag record header")
        mask_c0db = table[index + 1]
        mask_c0dc = table[index + 2]
        long_form = (header & 0x08) == 0
        record_length = 0x20 if long_form else 0x08
        end = index + record_length
        if end > length:
            raise ValueError("flag record exceeds table length")
        payload = table[index + 3 : end]
        if long_form:
            if len(payload) != 0x20 - 3:
                raise ValueError("unexpected long-form payload length")
            match_sequence = tuple(payload[0:7])
            page1 = tuple(payload[7 : 7 + 14])
            page2 = tuple(payload[21 : 21 + 8])
            pointer = payload[-1]
            replacement = None
        else:
            if len(payload) != 5:
                raise ValueError("unexpected short-form payload length")
            match_sequence = tuple(payload[0:2])
            replacement = tuple(payload[2:4])
            page1 = None
            page2 = None
            pointer = payload[4]
        records.append(
            FlagRecord(
                header=header,
                mask_c0db=mask_c0db,
                mask_c0dc=mask_c0dc,
                long_form=long_form,
                match_sequence=match_sequence,
                replacement=replacement,
                page1_payload=page1,
                page2_payload=page2,
                pointer=pointer,
            )
        )
        index = end

    trailing = tuple(table[index:])
    return tuple(records), trailing, tuple(raw)


def _decode_flag_dispatch(
    memory: Sequence[int], load_address: int
) -> FlagDispatchTable:
    """Return the flag-to-macro dispatch table recovered from the overlay."""

    # The overlay stores a 14-entry descriptor list at ``$d115``. The first and
    # last bytes are markers used by the runtime loop; the remaining twelve
    # entries map directly onto the slot and handler tables at ``$d116`` and
    # ``$d123`` respectively.
    slot_count = ml_extra_extract.FLAG_SLOT_COUNT
    flag_indices = _slice_memory(memory, load_address, 0xD115, slot_count + 2)
    slot_ids = _slice_memory(memory, load_address, 0xD116, slot_count)
    pointer_bytes = _slice_memory(memory, load_address, 0xD123, slot_count * 2)

    handlers = [
        pointer_bytes[index] | (pointer_bytes[index + 1] << 8)
        for index in range(0, len(pointer_bytes), 2)
    ]

    entries: list[FlagDispatchEntry] = []
    for offset in range(1, slot_count + 1):
        flag_index = flag_indices[offset]
        slot = slot_ids[offset - 1]
        handler = handlers[offset - 1]
        entries.append(
            FlagDispatchEntry(
                flag_index=flag_index, slot=slot, handler_address=handler
            )
        )

    return FlagDispatchTable(
        leading_marker=flag_indices[0],
        trailing_marker=flag_indices[-1],
        entries=tuple(entries),
    )


def _collect_vic_register_writes(
    memory: Sequence[int], load_address: int
) -> Tuple[HardwareRegisterWrite, ...]:
    """Return the write sequences for ``$d403-$d406`` in runtime order."""

    results: list[HardwareRegisterWrite] = []
    for target in _VIC_TARGETS:
        writes = _scan_register_writes(memory, load_address, target)
        results.append(
            HardwareRegisterWrite(address=target, writes=tuple(writes))
        )
    return tuple(results)


def _collect_pointer_defaults(
    memory: Sequence[int], load_address: int
) -> BufferPointerDefaults:
    """Return the initial pointer configuration recovered from the overlay."""

    low_writes = _scan_register_writes(memory, load_address, _POINTER_LOW)
    high_writes = _scan_register_writes(memory, load_address, _POINTER_HIGH)
    if not low_writes or not high_writes:
        raise ValueError("failed to locate pointer initialisation writes")

    low_initial = low_writes[0][1]
    high_initial = high_writes[0][1]
    if low_initial is None or high_initial is None:
        raise ValueError("pointer initialisation is not immediate")

    scan_limit, reset_value = _collect_pointer_limits(memory, load_address)
    return BufferPointerDefaults(
        initial=(low_initial, high_initial),
        scan_limit=scan_limit,
        reset_value=reset_value,
    )


def _collect_pointer_limits(
    memory: Sequence[int], load_address: int
) -> Tuple[int, int]:
    """Return the ``cmp`` bounds used while scanning ``$42ff``."""

    pattern = [0xAD, _POINTER_HIGH & 0xFF, _POINTER_HIGH >> 8, 0xC9]
    matches: list[Tuple[int, int]] = []
    for index in range(len(memory) - len(pattern)):
        if list(memory[index : index + len(pattern)]) != pattern:
            continue
        cmp_index = index + len(pattern)
        runtime = _index_to_runtime(cmp_index - 1, load_address)
        matches.append((runtime, memory[cmp_index]))
    if len(matches) < 2:
        raise ValueError("pointer scan limits were not recovered")
    matches.sort(key=lambda item: item[0])
    values = [value for _, value in matches]
    return values[0], values[1]


def _read_sid_volume(memory: Sequence[int], load_address: int) -> int:
    """Return the immediate value written to ``$d418``."""

    writes = _scan_register_writes(memory, load_address, _SID_VOLUME)
    for _, value in writes:
        if value is not None:
            return value
    raise ValueError("no immediate write to $d418 found")


def _scan_register_writes(
    memory: Sequence[int], load_address: int, target: int
) -> list[Tuple[int, Optional[int]]]:
    """Return ``(store_address, value)`` pairs for the requested register."""

    entries: list[Tuple[int, Optional[int]]] = []
    lo = target & 0xFF
    hi = target >> 8
    for index in range(len(memory) - 2):
        opcode = memory[index]
        if opcode not in (0x8D, 0x8E):  # sta/stx abs
            continue
        if memory[index + 1] != lo or memory[index + 2] != hi:
            continue
        runtime = _index_to_runtime(index, load_address)
        value = _previous_immediate(memory, index, opcode)
        entries.append((runtime, value))
    return entries


def _index_to_runtime(index: int, load_address: int) -> int:
    """Map ``memory`` index to runtime address respecting overlay segments."""

    for runtime_base, load_base in ml_extra_extract.SEGMENT_BASES:
        start = load_base - ml_extra_extract.LOAD_ADDRESS
        end = start + 0x1000
        if start <= index < end:
            offset = index - start
            runtime = runtime_base + offset
            adjust = load_address - ml_extra_extract.LOAD_ADDRESS
            if adjust:
                runtime += adjust
            return runtime
    raise ValueError(f"index {index} is outside recognised overlay segments")


def _previous_immediate(
    memory: Sequence[int], index: int, opcode: int
) -> Optional[int]:
    """Return the immediate operand used before a store instruction."""

    loader = {0x8D: 0xA9, 0x8E: 0xA2}.get(opcode)
    if loader is None:
        return None
    for offset in range(1, 10):
        pos = index - offset
        if pos < 0:
            break
        if memory[pos] in (0x60, 0x40):  # rts/rti terminate the search
            break
        if memory[pos] == loader:
            operand_index = pos + 1
            if operand_index < 0 or operand_index >= len(memory):
                break
            return memory[operand_index]
    return None


def _slice_memory(
    memory: Sequence[int], load_address: int, runtime_addr: int, length: int
) -> Tuple[int, ...]:
    """Return ``length`` bytes from ``memory`` starting at ``runtime_addr``."""

    index = ml_extra_extract.runtime_to_index(runtime_addr, load_addr=load_address)
    data = memory[index : index + length]
    if len(data) != length:
        raise ValueError(
            f"requested {length} bytes at ${runtime_addr:04x}, got {len(data)}"
        )
    return tuple(data)


_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_OVERLAY_PATH = _REPO_ROOT / "v1.2/from-floppy/ml.extra"


def default_overlay_path() -> Path:
    """Return the archived overlay path used by :class:`MLExtraDefaults`."""

    return _DEFAULT_OVERLAY_PATH


__all__ = [
    "EditorPalette",
    "LightbarDefaults",
    "MacroDirectoryEntry",
    "FlagRecord",
    "FlagDispatchEntry",
    "FlagDispatchTable",
    "MLExtraDefaults",
    "HardwareDefaults",
    "HardwareRegisterWrite",
    "BufferPointerDefaults",
    "default_overlay_path",
]

@dataclass(frozen=True)
class HardwareRegisterWrite:
    """Concrete write sequence for a single hardware register."""

    address: int
    writes: Tuple[Tuple[int, Optional[int]], ...]

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the write sequence."""

        entries: list[Dict[str, object]] = []
        for store, value in self.writes:
            entry: Dict[str, object] = {"store": f"${store:04x}"}
            if value is not None:
                entry["value"] = f"${value:02x}"
            entries.append(entry)
        return {
            "address": f"${self.address:04x}",
            "writes": entries,
        }


@dataclass(frozen=True)
class BufferPointerDefaults:
    """Initial ``$42fe/$42ff`` pointer configuration recovered from the overlay."""

    initial: Tuple[int, int]
    scan_limit: int
    reset_value: int

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the pointer defaults."""

        lo, hi = self.initial
        return {
            "initial": {
                "low": f"${lo:02x}",
                "high": f"${hi:02x}",
            },
            "scan_limit": f"${self.scan_limit:02x}",
            "reset_value": f"${self.reset_value:02x}",
        }


@dataclass(frozen=True)
class HardwareDefaults:
    """Hardware initialisation recovered from the ``ml.extra`` overlay."""

    vic_registers: Tuple[HardwareRegisterWrite, ...]
    pointer: BufferPointerDefaults
    sid_volume: int

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON summary of the recovered hardware defaults."""

        return {
            "vic_registers": [entry.as_dict() for entry in self.vic_registers],
            "pointer": self.pointer.as_dict(),
            "sid_volume": f"${self.sid_volume:02x}",
        }
