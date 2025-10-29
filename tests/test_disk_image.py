from __future__ import annotations

from typing import Dict

import pytest

from imagebbs.disk_image import D64Image, DirectoryEntry

_SECTOR_COUNT: Dict[int, int] = {
    **{track: 21 for track in range(1, 18)},
    **{track: 19 for track in range(18, 25)},
    **{track: 18 for track in range(25, 31)},
    **{track: 17 for track in range(31, 36)},
}

_SECTOR_BYTES = 256


def _offset(track: int, sector: int) -> int:
    offset = 0
    for current in range(1, track):
        offset += _SECTOR_COUNT[current] * _SECTOR_BYTES
    return offset + sector * _SECTOR_BYTES


def _build_test_image() -> bytes:
    total_bytes = sum(count * _SECTOR_BYTES for count in _SECTOR_COUNT.values())
    image = bytearray(total_bytes)

    # Directory sector at track 18, sector 1
    directory_offset = _offset(18, 1)
    image[directory_offset] = 0  # no next track
    image[directory_offset + 1] = 0  # no next sector

    entry = bytearray(32)
    entry[2] = 0x82  # closed PRG file
    entry[3] = 1  # start track
    entry[4] = 0  # start sector
    name = b"HELLO"
    entry[5 : 5 + len(name)] = name
    entry[5 + len(name) : 21] = b"\xA0" * (16 - len(name))
    entry[30] = 2  # two blocks used
    image[directory_offset + 2 : directory_offset + 34] = entry

    # File data across two sectors
    first_offset = _offset(1, 0)
    image[first_offset] = 1  # next track
    image[first_offset + 1] = 1  # next sector
    first_payload = b"A" * (_SECTOR_BYTES - 2)
    image[first_offset + 2 : first_offset + _SECTOR_BYTES] = first_payload

    second_offset = _offset(1, 1)
    image[second_offset] = 0  # chain terminator
    image[second_offset + 1] = 3  # final payload length
    second_payload = b"END"
    image[second_offset + 2 : second_offset + 5] = second_payload

    return bytes(image)


def test_iter_directory_returns_entries():
    image = D64Image(_build_test_image())
    entries = list(image.iter_directory())
    assert entries == [
        DirectoryEntry(
            name="HELLO",
            file_type="PRG",
            start_track=1,
            start_sector=0,
            size_blocks=2,
            locked=False,
            closed=True,
        )
    ]


def test_get_entry_normalizes_name():
    image = D64Image(_build_test_image())
    entry = image.get_entry(" hello ")
    assert entry is not None
    assert entry.name == "HELLO"


def test_read_file_follows_chain():
    image = D64Image(_build_test_image())
    data = image.read_file("HELLO")
    assert data == b"A" * (_SECTOR_BYTES - 2) + b"END"


def test_read_file_raises_for_missing_entry():
    image = D64Image(_build_test_image())
    with pytest.raises(FileNotFoundError):
        image.read_file("MISSING")
