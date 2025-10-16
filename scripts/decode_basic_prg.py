#!/usr/bin/env python3
"""Decode tokenised Commodore BASIC PRG files into textual listings.

The ImageBBS tree stores original overlay binaries recovered from the 1.2B
distribution disks under ``v1.2/from-floppy/``.  Iteration 19 surfaced the
``setup`` BASIC program but only provided a raw PETCAT dump for inspection.
This helper script re-creates the decoding step in pure Python so the build
does not depend on an external ``petcat`` binary when the listing needs to be
refreshed.

The output intentionally mirrors the “upper/graphics” character set emitted by
VICE PETCAT.  Printable ASCII is written directly while control characters and
graphics with no natural Unicode analogue are represented as ``{$XX}``
placeholders matching the hexadecimal PETSCII code.  These markers keep the
stream lossless so downstream tools can substitute their own glyph tables when
rendering user-facing views of the listing.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Sequence


# Commodore BASIC V2 token table.  Entries track whether the token should be
# padded by spaces when rendered in a listing.  The defaults provide a readable
# approximation of PETCAT output while remaining conservative enough to avoid
# altering string or REM literal content.
@dataclass(frozen=True)
class BasicToken:
    text: str
    space_before: bool = True
    space_after: bool = True


TOKENS: Dict[int, BasicToken] = {
    0x80: BasicToken("END"),
    0x81: BasicToken("FOR"),
    0x82: BasicToken("NEXT"),
    0x83: BasicToken("DATA"),
    0x84: BasicToken("INPUT#"),
    0x85: BasicToken("INPUT"),
    0x86: BasicToken("DIM"),
    0x87: BasicToken("READ"),
    0x88: BasicToken("LET"),
    0x89: BasicToken("GOTO"),
    0x8A: BasicToken("RUN"),
    0x8B: BasicToken("IF"),
    0x8C: BasicToken("RESTORE"),
    0x8D: BasicToken("GOSUB"),
    0x8E: BasicToken("RETURN"),
    0x8F: BasicToken("REM"),
    0x90: BasicToken("STOP"),
    0x91: BasicToken("ON"),
    0x92: BasicToken("WAIT"),
    0x93: BasicToken("LOAD"),
    0x94: BasicToken("SAVE"),
    0x95: BasicToken("VERIFY"),
    0x96: BasicToken("DEF"),
    0x97: BasicToken("POKE"),
    0x98: BasicToken("PRINT#"),
    0x99: BasicToken("PRINT"),
    0x9A: BasicToken("CONT"),
    0x9B: BasicToken("LIST"),
    0x9C: BasicToken("CLR"),
    0x9D: BasicToken("CMD"),
    0x9E: BasicToken("SYS"),
    0x9F: BasicToken("OPEN"),
    0xA0: BasicToken("CLOSE"),
    0xA1: BasicToken("GET"),
    0xA2: BasicToken("NEW"),
    0xA3: BasicToken("TAB(", space_after=False),
    0xA4: BasicToken("TO"),
    0xA5: BasicToken("FN", space_after=False),
    0xA6: BasicToken("SPC(", space_after=False),
    0xA7: BasicToken("THEN"),
    0xA8: BasicToken("NOT"),
    0xA9: BasicToken("STEP"),
    0xAA: BasicToken("+"),
    0xAB: BasicToken("-"),
    0xAC: BasicToken("*"),
    0xAD: BasicToken("/"),
    0xAE: BasicToken("^"),
    0xAF: BasicToken("AND"),
    0xB0: BasicToken("OR"),
    0xB1: BasicToken(">"),
    0xB2: BasicToken("="),
    0xB3: BasicToken("<"),
    0xB4: BasicToken("SGN"),
    0xB5: BasicToken("INT"),
    0xB6: BasicToken("ABS"),
    0xB7: BasicToken("USR"),
    0xB8: BasicToken("FRE"),
    0xB9: BasicToken("POS"),
    0xBA: BasicToken("SQR"),
    0xBB: BasicToken("RND"),
    0xBC: BasicToken("LOG"),
    0xBD: BasicToken("EXP"),
    0xBE: BasicToken("COS"),
    0xBF: BasicToken("SIN"),
    0xC0: BasicToken("TAN"),
    0xC1: BasicToken("ATN"),
    0xC2: BasicToken("PEEK"),
    0xC3: BasicToken("LEN"),
    0xC4: BasicToken("STR$"),
    0xC5: BasicToken("VAL"),
    0xC6: BasicToken("ASC"),
    0xC7: BasicToken("CHR$"),
    0xC8: BasicToken("LEFT$"),
    0xC9: BasicToken("RIGHT$"),
    0xCA: BasicToken("MID$"),
    0xCB: BasicToken("GO"),
    0xFF: BasicToken("PI", space_before=True, space_after=False),
}


CONTROL_CODES: Dict[int, str] = {
    0x00: "{NUL}",
    0x01: "{CTRL-A}",
    0x02: "{CTRL-B}",
    0x03: "{CTRL-C}",
    0x04: "{CTRL-D}",
    0x05: "{WHITE}",
    0x06: "{CTRL-F}",
    0x07: "{BELL}",
    0x08: "{BACKSPACE}",
    0x09: "{TAB}",
    0x0A: "{LF}",
    0x0B: "{CTRL-K}",
    0x0C: "{CLEAR}",
    0x0D: "{RETURN}",
    0x0E: "{RVS-ON}",
    0x0F: "{CTRL-O}",
    0x10: "{CTRL-P}",
    0x11: "{CURSOR-DOWN}",
    0x12: "{RVS-ON}",
    0x13: "{HOME}",
    0x14: "{DEL}",
    0x15: "{CTRL-U}",
    0x16: "{CTRL-V}",
    0x17: "{CTRL-W}",
    0x18: "{CTRL-X}",
    0x19: "{CTRL-Y}",
    0x1A: "{CTRL-Z}",
    0x1B: "{ESC}",
    0x1C: "{RED}",
    0x1D: "{CURSOR-RIGHT}",
    0x1E: "{GREEN}",
    0x1F: "{BLUE}",
}


def decode_prg(data: bytes) -> Iterator[tuple[int, str]]:
    """Yield ``(line_number, source)`` pairs from a tokenised PRG payload."""

    cursor = 2  # Skip load address.
    length = len(data)
    while cursor + 4 <= length:
        next_line = data[cursor] | (data[cursor + 1] << 8)
        cursor += 2
        if next_line == 0:
            break

        line_number = data[cursor] | (data[cursor + 1] << 8)
        cursor += 2

        line_parts: List[str] = []
        in_string = False
        in_rem = False

        while cursor < length:
            byte = data[cursor]
            cursor += 1
            if byte == 0:
                break

            if not in_string and not in_rem and byte in TOKENS:
                token = TOKENS[byte]
                if line_parts and token.space_before and not line_parts[-1].endswith(" "):
                    line_parts.append(" ")
                line_parts.append(token.text)
                if token.space_after:
                    line_parts.append(" ")

                if byte == 0x8F:  # REM – consume the remainder verbatim.
                    in_rem = True
                continue

            char = decode_petscii_char(byte, literal=in_string or in_rem)
            if not line_parts:
                line_parts.append("")

            if not in_rem:
                if not in_string and char == '"':
                    in_string = True
                elif in_string and char == '"':
                    # Handle doubled quotes representing literal " inside strings.
                    if cursor < length and data[cursor] == 0x22:
                        # Append the escaped quote and skip the duplicate.
                        line_parts[-1] += '""'
                        cursor += 1
                        continue
                    in_string = False

            line_parts[-1] += char

        yield line_number, "".join(line_parts).rstrip()


def decode_petscii_char(byte: int, *, literal: bool = False) -> str:
    """Return a textual representation for a PETSCII character code."""

    if byte < 0x20:
        return CONTROL_CODES.get(byte, f"{{${byte:02x}}}")

    if not literal and byte in TOKENS:
        # Should be unreachable – tokens are handled before calling this helper.
        return TOKENS[byte].text

    if byte >= 0x80:
        candidate = byte & 0x7F
        if 0x20 <= candidate <= 0x7E:
            if (
                0x30 <= candidate <= 0x39
                or 0x41 <= candidate <= 0x5A
                or candidate in {
                    0x20,
                    0x22,
                    0x23,
                    0x24,
                    0x25,
                    0x26,
                    0x27,
                    0x28,
                    0x29,
                    0x2C,
                    0x2D,
                    0x2E,
                    0x2F,
                    0x3A,
                    0x3B,
                    0x3D,
                    0x3F,
                    0x40,
                    0x5B,
                    0x5D,
                }
            ):
                return chr(candidate)
        if literal and 0x41 <= candidate <= 0x5A:
            # PETSCII uppercase/graphics set stores A-Z as $C1-$DA when the high
            # bit is set.  Masking the bit restores the ASCII glyph so listings
            # render plain text inside strings.
            return chr(candidate)
        if literal and byte in TOKENS:
            if byte == 0x8B:
                return "{RETURN}"
            return TOKENS[byte].text
        return f"{{${byte:02x}}}"

    if 0x20 <= byte <= 0x7E:
        return chr(byte)

    return f"{{${byte:02x}}}"


def write_listing(lines: Iterable[tuple[int, str]], output: Path) -> None:
    """Write the decoded BASIC listing to *output*."""

    with output.open("w", encoding="utf-8") as handle:
        for line_number, text in lines:
            if text:
                handle.write(f"{line_number} {text}\n")
            else:
                handle.write(f"{line_number}\n")


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prg", type=Path, help="Tokenised BASIC PRG to decode")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Destination for the decoded listing (defaults to stdout)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_arguments(argv)
    payload = args.prg.read_bytes()
    listing = list(decode_prg(payload))

    if args.output:
        write_listing(listing, args.output)
    else:
        for line_number, text in listing:
            if text:
                print(f"{line_number} {text}")
            else:
                print(line_number)


if __name__ == "__main__":  # pragma: no cover - manual entry point
    main()
