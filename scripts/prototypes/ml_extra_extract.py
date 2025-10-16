"""Extract data tables from the recovered ``ml.extra`` overlay."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

LOAD_ADDRESS = 0x1000
SEGMENT_BASES = (
    (0xC000, 0x1000),
    (0xD000, 0x2000),
)

FLAG_SLOT_COUNT = 12


@dataclass
class PointerDirectoryEntry:
    slot: int
    address: int
    data: list[int]
    text: str

    def to_dict(self) -> dict[str, object]:
        return {
            "slot": self.slot,
            "address": f"${self.address:04x}",
            "bytes": [f"${value:02x}" for value in self.data],
            "text": self.text,
        }


def load_prg(path: Path) -> tuple[int, list[int]]:
    payload = path.read_bytes()
    if len(payload) < 2:
        raise ValueError("PRG file is too short")
    load_addr = payload[0] | (payload[1] << 8)
    return load_addr, list(payload[2:])


def runtime_to_index(address: int, *, load_addr: int) -> int:
    for runtime_base, load_base in SEGMENT_BASES:
        if runtime_base <= address < runtime_base + 0x1000:
            offset = address - runtime_base
            idx = offset + (load_base - LOAD_ADDRESS)
            if load_addr != LOAD_ADDRESS:
                idx += load_addr - LOAD_ADDRESS
            return idx
    raise ValueError(f"runtime address ${address:04x} is outside recognised segments")


_PRINTABLE_ASCII = set(range(0x20, 0x7F))
_PRINTABLE_EXTRA = {
    0x0D: "\n",  # carriage return
    0x8D: "\n",  # shifted carriage return (ml.extra uses both forms)
}


def _decode_petscii_byte(byte: int) -> str | None:
    """Return a printable representation for ``byte`` when recognised."""

    if byte in _PRINTABLE_EXTRA:
        return _PRINTABLE_EXTRA[byte]
    if byte in _PRINTABLE_ASCII:
        return chr(byte)
    if byte >= 0x80:
        candidate = byte & 0x7F
        if candidate in _PRINTABLE_ASCII:
            return chr(candidate)
        if candidate in _PRINTABLE_EXTRA:
            return _PRINTABLE_EXTRA[candidate]
    return None


def decode_petscii(data: Iterable[int]) -> str:
    result: list[str] = []
    for byte in data:
        if byte == 0x00:
            break
        decoded = _decode_petscii_byte(byte)
        if decoded is None:
            result.append(f"{{$${byte:02x}}}")
        else:
            result.append(decoded)
    return "".join(result)


def iter_pointer_directory(memory: list[int], *, load_addr: int) -> Iterator[PointerDirectoryEntry]:
    slot_index = runtime_to_index(0xD116, load_addr=load_addr)
    slots = memory[slot_index : slot_index + FLAG_SLOT_COUNT]

    pointer_index = runtime_to_index(0xD123, load_addr=load_addr)
    raw = memory[pointer_index : pointer_index + FLAG_SLOT_COUNT * 2]

    for slot, lo, hi in zip(slots, raw[0::2], raw[1::2]):
        address = lo | (hi << 8)
        try:
            idx = runtime_to_index(address, load_addr=load_addr)
        except ValueError:
            chunk: list[int] = []
            text = ""
        else:
            chunk = []
            for byte in memory[idx:]:
                chunk.append(byte)
                if byte == 0x00:
                    break
            text = decode_petscii(chunk)
        yield PointerDirectoryEntry(slot=slot, address=address, data=chunk, text=text)


def extract_overlay(path: Path) -> dict[str, object]:
    load_addr, memory = load_prg(path)
    directory = list(iter_pointer_directory(memory, load_addr=load_addr))
    return {
        "load_address": f"${load_addr:04x}",
        "pointer_directory": [entry.to_dict() for entry in directory],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prg", type=Path, help="ml.extra binary to analyse")
    parser.add_argument("--output", "-o", type=Path, help="Destination JSON file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    report = extract_overlay(args.prg)
    if args.output:
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    else:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
