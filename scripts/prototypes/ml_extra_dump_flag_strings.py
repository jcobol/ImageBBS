"""Dump the XOR-encoded flag directory tail stored in ``ml.extra``."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from scripts.prototypes import ml_extra_defaults, ml_extra_extract  # type: ignore
else:  # pragma: no cover - import resolution when packaged
    from . import ml_extra_defaults, ml_extra_extract


_FLAG_DATA_START = 0xD9C3
_FLAG_DATA_LENGTH = 0x46


def _decode_block(memory: list[int], load_addr: int) -> tuple[list[int], list[int], str]:
    """Return raw/decoded bytes plus PETSCII for the flag tail block."""

    index = ml_extra_extract.runtime_to_index(_FLAG_DATA_START, load_addr=load_addr)
    raw = memory[index : index + _FLAG_DATA_LENGTH]
    decoded = [byte ^ 0xFF for byte in raw]
    text = ml_extra_extract.decode_petscii(decoded)
    return raw, decoded, text


def _format_bytes(values: Iterable[int]) -> str:
    return " ".join(f"${value:02x}" for value in values)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overlay",
        type=Path,
        help="Override the default ml.extra path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    overlay = args.overlay or ml_extra_defaults._DEFAULT_OVERLAY_PATH
    load_addr, memory = ml_extra_extract.load_prg(overlay)
    raw, decoded, text = _decode_block(memory, load_addr)

    print(f"overlay: {overlay}")
    print(f"load address: ${load_addr:04x}")
    print(f"flag data start: ${_FLAG_DATA_START:04x}")
    print(f"raw bytes ({len(raw)}): {_format_bytes(raw)}")
    print(f"decoded bytes ({len(decoded)}): {_format_bytes(decoded)}")
    print(f"PETSCII: {text}")


if __name__ == "__main__":  # pragma: no cover - CLI wrapper
    main()
