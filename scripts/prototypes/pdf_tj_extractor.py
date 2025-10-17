"""Utilities for extracting Tj text tokens from FlateDecode streams in a PDF."""
from __future__ import annotations

import argparse
import json
import logging
import re
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence

LOGGER = logging.getLogger(__name__)

_LITERAL_TJ_PATTERN = re.compile(rb"\(((?:\\.|[^\\\)])*)\)\s*Tj", re.DOTALL)
_HEX_TJ_PATTERN = re.compile(rb"<([0-9A-Fa-f\s]+)>\s*Tj")
_OBJECT_STREAM_PATTERN = re.compile(
    rb"(\d+)\s+(\d+)\s+obj\s*<<(.*?)>>\s*stream\s*(?:\r\n|\n|\r)?(.*?)endstream",
    re.DOTALL,
)


@dataclass
class StreamTokens:
    """Tj token payloads discovered within a PDF stream."""

    object_id: int
    generation: int
    tokens: List[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "object": self.object_id,
                "generation": self.generation,
                "tokens": self.tokens,
            },
            ensure_ascii=False,
        )


def _decode_literal_string(value: str) -> str:
    """Decode a PDF literal string, handling escapes and octal sequences."""

    result: List[str] = []
    i = 0
    length = len(value)

    escape_map = {
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "b": "\b",
        "f": "\f",
        "(": "(",
        ")": ")",
        "\\": "\\",
    }

    while i < length:
        char = value[i]
        if char != "\\":
            result.append(char)
            i += 1
            continue

        i += 1
        if i >= length:
            break

        next_char = value[i]

        if next_char in "\n\r":
            # Line continuation: ignore the newline, optionally swallow \r\n.
            if next_char == "\r" and i + 1 < length and value[i + 1] == "\n":
                i += 1
            i += 1
            continue

        mapped = escape_map.get(next_char)
        if mapped is not None:
            result.append(mapped)
            i += 1
            continue

        if next_char in "01234567":
            oct_digits = next_char
            i += 1
            for _ in range(2):
                if i < length and value[i] in "01234567":
                    oct_digits += value[i]
                    i += 1
                else:
                    break
            result.append(chr(int(oct_digits, 8)))
            continue

        result.append(next_char)
        i += 1

    return "".join(result)


def _decode_hex_string(value: bytes) -> str:
    cleaned = b"".join(value.split())
    if len(cleaned) % 2 == 1:
        cleaned += b"0"
    decoded = bytes.fromhex(cleaned.decode("ascii"))
    return decoded.decode("latin-1")


def _extract_tj_tokens(stream_bytes: bytes) -> List[str]:
    tokens: List[str] = []

    for literal_match in _LITERAL_TJ_PATTERN.finditer(stream_bytes):
        literal = literal_match.group(1).decode("latin-1")
        tokens.append(_decode_literal_string(literal))

    for hex_match in _HEX_TJ_PATTERN.finditer(stream_bytes):
        hex_payload = hex_match.group(1)
        tokens.append(_decode_hex_string(hex_payload))

    return tokens


def iter_flate_streams(pdf_bytes: bytes) -> Iterator[StreamTokens]:
    """Yield FlateDecode streams and their Tj tokens from raw PDF bytes."""

    for match in _OBJECT_STREAM_PATTERN.finditer(pdf_bytes):
        object_id = int(match.group(1))
        generation = int(match.group(2))
        dictionary_bytes = match.group(3)
        if b"FlateDecode" not in dictionary_bytes:
            continue

        raw_stream = match.group(4)
        try:
            inflated = zlib.decompress(raw_stream)
        except zlib.error as error:
            LOGGER.warning(
                "Skipping object %s %s: unable to decompress Flate stream (%s)",
                object_id,
                generation,
                error,
            )
            continue

        tokens = _extract_tj_tokens(inflated)
        if tokens:
            yield StreamTokens(object_id=object_id, generation=generation, tokens=tokens)


def write_tokens_to_jsonl(tokens: Iterable[StreamTokens], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8") as fh:
        for token_group in tokens:
            fh.write(token_group.to_json())
            fh.write("\n")
            count += len(token_group.tokens)
    return count


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract Tj text tokens from the FlateDecode streams in a PDF.",
    )
    parser.add_argument("pdf", type=Path, help="Path to the PDF file to inspect.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/analysis/pdf_tj_tokens.jsonl"),
        help="Where to store the collected tokens (JSON Lines).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity for the helper.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level))

    pdf_path: Path = args.pdf
    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")

    pdf_bytes = pdf_path.read_bytes()
    LOGGER.info("Scanning PDF: %s", pdf_path)
    token_groups = list(iter_flate_streams(pdf_bytes))
    LOGGER.info("Identified %d streams with Tj tokens", len(token_groups))

    token_count = write_tokens_to_jsonl(token_groups, args.output)
    LOGGER.info(
        "Wrote %d tokens across %d streams to %s",
        token_count,
        len(token_groups),
        args.output,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
