"""Utilities for reading Commodore 1541 disk images used by ImageBBS."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

_SECTOR_COUNT: Dict[int, int] = {
    **{track: 21 for track in range(1, 18)},
    **{track: 19 for track in range(18, 25)},
    **{track: 18 for track in range(25, 31)},
    **{track: 17 for track in range(31, 36)},
}

_DIRECTORY_TRACK = 18
_DIRECTORY_SECTOR = 1
_SECTOR_BYTES = 256
_DATA_BYTES = _SECTOR_BYTES - 2


def _track_sector_to_offset(track: int, sector: int) -> int:
    if track not in _SECTOR_COUNT:
        raise ValueError(f"unsupported track {track}")
    if sector >= _SECTOR_COUNT[track]:
        raise ValueError(f"sector {sector} out of range for track {track}")

    offset = 0
    for current_track in range(1, track):
        offset += _SECTOR_COUNT[current_track] * _SECTOR_BYTES
    return offset + sector * _SECTOR_BYTES


def _decode_petscii_name(raw: bytes) -> str:
    def _map(byte: int) -> str:
        if byte == 0xA0:
            return " "
        value = byte & 0x7F
        if 0x20 <= value <= 0x5F:
            return chr(value)
        return f"\\x{byte:02x}"

    return "".join(_map(b) for b in raw).rstrip()


def _decode_file_type(file_type: int) -> str:
    types = {
        0: "DEL",
        1: "SEQ",
        2: "PRG",
        3: "USR",
        4: "REL",
    }
    return types.get(file_type & 0x07, "UNK")


@dataclass(frozen=True)
class DirectoryEntry:
    """Represents a single file entry within a D64 directory."""

    name: str
    file_type: str
    start_track: int
    start_sector: int
    size_blocks: int
    locked: bool
    closed: bool

    @property
    def is_program(self) -> bool:
        return self.file_type == "PRG"


class D64Image:
    """Provides read-only access to files within a standard D64 image."""

    def __init__(self, data: bytes):
        self._data = data
        self._directory: Optional[List[DirectoryEntry]] = None

    @classmethod
    def load(cls, path: Path | str) -> "D64Image":
        with open(Path(path), "rb") as source:
            return cls(source.read())

    def iter_directory(self) -> Iterator[DirectoryEntry]:
        if self._directory is None:
            self._directory = list(self._parse_directory())
        return iter(self._directory)

    def get_entry(self, name: str) -> Optional[DirectoryEntry]:
        normalized = name.strip().upper()
        for entry in self.iter_directory():
            if entry.name.upper() == normalized:
                return entry
        return None

    def read_file(self, name: str) -> bytes:
        entry = self.get_entry(name)
        if entry is None:
            available = ", ".join(e.name for e in self.iter_directory())
            raise FileNotFoundError(f"{name!r} not found (available: {available})")
        if entry.start_track == 0:
            return b""
        return self._follow_chain(entry.start_track, entry.start_sector)

    def _parse_directory(self) -> Iterable[DirectoryEntry]:
        track, sector = _DIRECTORY_TRACK, _DIRECTORY_SECTOR
        while track != 0:
            offset = _track_sector_to_offset(track, sector)
            sector_bytes = self._data[offset : offset + _SECTOR_BYTES]
            track, sector = sector_bytes[0], sector_bytes[1]
            for index in range(0, _DATA_BYTES, 32):
                entry = sector_bytes[2 + index : 2 + index + 32]
                file_type = entry[2]
                start_track = entry[3]
                if file_type & 0x0F == 0 or start_track == 0:
                    continue
                start_sector = entry[4]
                name = _decode_petscii_name(entry[5:21])
                size_blocks = entry[30] + (entry[31] << 8)
                locked = bool(file_type & 0x40)
                closed = bool(file_type & 0x80)
                decoded_type = _decode_file_type(file_type)
                yield DirectoryEntry(
                    name=name,
                    file_type=decoded_type,
                    start_track=start_track,
                    start_sector=start_sector,
                    size_blocks=size_blocks,
                    locked=locked,
                    closed=closed,
                )

    def _follow_chain(self, track: int, sector: int) -> bytes:
        chunks: List[bytes] = []
        while track != 0:
            offset = _track_sector_to_offset(track, sector)
            sector_bytes = self._data[offset : offset + _SECTOR_BYTES]
            next_track, next_sector = sector_bytes[0], sector_bytes[1]
            if next_track == 0:
                length = next_sector
                chunks.append(sector_bytes[2 : 2 + length])
                break
            chunks.append(sector_bytes[2:])
            track, sector = next_track, next_sector
        return b"".join(chunks)


__all__ = ["D64Image", "DirectoryEntry"]
