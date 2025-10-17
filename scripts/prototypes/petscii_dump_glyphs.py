"""Dump Commodore 64 PETSCII glyphs into an ASCII text format."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, TextIO

_ROW_BITS = tuple(1 << bit for bit in range(7, -1, -1))


def _expand_rom(data: bytes) -> bytes:
    """Return a 4 KiB character ROM payload."""

    if len(data) == 2048:
        data = data + data
    if len(data) != 4096:
        raise ValueError("character ROM must be 2 KiB or 4 KiB long")
    return data


def _iter_glyph_rows(payload: bytes) -> Iterable[tuple[int, int, list[str]]]:
    for bank in range(2):
        for code in range(256):
            offset = (bank * 256 + code) * 8
            chunk = payload[offset : offset + 8]
            if len(chunk) < 8:
                raise ValueError("character ROM payload truncated")
            rows = []
            for byte in chunk:
                rows.append("".join("#" if byte & bit else "." for bit in _ROW_BITS))
            yield bank, code, rows


def dump_glyphs(payload: bytes, target: TextIO) -> None:
    """Serialise a 4 KiB PETSCII ROM payload as ASCII rows."""

    for bank, code, rows in _iter_glyph_rows(payload):
        target.write(f"bank={bank} code=${code:02X} index={bank * 256 + code}\n")
        for row in rows:
            target.write(f"{row}\n")
        target.write("\n")


def _default_rom_path() -> Path:
    return Path(__file__).with_name("c64.bin")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dump Commodore 64 PETSCII glyphs from a character ROM",
    )
    parser.add_argument(
        "--rom",
        type=Path,
        default=_default_rom_path(),
        help="Path to the 2 KiB or 4 KiB character ROM (default: c64.bin next to this script)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional destination file (defaults to stdout)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    rom_path: Path = args.rom
    if not rom_path.exists():
        parser.error(f"ROM file not found: {rom_path}")

    payload = rom_path.read_bytes()

    try:
        rom = _expand_rom(payload)
    except ValueError as exc:  # pragma: no cover - CLI validation
        parser.error(str(exc))

    if args.output is None:
        dump_glyphs(rom, target=sys.stdout)
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        dump_glyphs(rom, handle)

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
