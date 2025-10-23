#!/usr/bin/env python3
"""Standalone harness to validate ASCII/PETSCII round-trip behaviour."""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

# Ensure the ImageBBS package is importable when running the script directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from imagebbs.device_context import Console  # noqa: E402  (import after sys.path tweak)
from imagebbs.petscii import decode_petscii_for_cli  # noqa: E402


DEFAULT_STRINGS: Sequence[str] = (
    "HELLO WORLD",
    "café",
    "ImageBBS 1.2",
    "PETSCII {CBM-$9D}",
)


@dataclass(frozen=True)
class RoundTripStep:
    """Capture the intermediate state of a single round-trip iteration."""

    source: str
    payload: bytes
    decoded: str

    def as_dict(self) -> dict[str, object]:
        """Expose the step for potential JSON serialisation."""

        return {
            "source": self.source,
            "payload": list(self.payload),
            "decoded": self.decoded,
        }


class PetsciiRoundTripValidator:
    """Validate conversions between ASCII strings and PETSCII payloads."""

    def __init__(self, *, iterations: int) -> None:
        if iterations < 1:
            raise ValueError("iterations must be at least 1")
        self._iterations = iterations

    @staticmethod
    def _encode_ascii(text: str) -> bytes:
        console = Console()
        console.write(text)
        return console.transcript_bytes

    @staticmethod
    def _decode_petscii(payload: bytes | bytearray | Iterable[int]) -> str:
        return decode_petscii_for_cli(payload)

    def run(self, text: str) -> list[RoundTripStep]:
        """Execute the configured number of round-trip iterations for ``text``."""

        steps: list[RoundTripStep] = []
        current_text = text
        for _ in range(self._iterations):
            payload = self._encode_ascii(current_text)
            decoded = self._decode_petscii(payload)
            steps.append(RoundTripStep(current_text, payload, decoded))
            current_text = decoded
        return steps


def _format_payload(payload: bytes) -> str:
    if not payload:
        return "<empty>"
    return " ".join(f"{byte:02X}" for byte in payload)


def _render_steps(steps: Sequence[RoundTripStep]) -> str:
    lines: list[str] = []
    for index, step in enumerate(steps, start=1):
        lines.append(f"Iteration {index}:")
        lines.append(f"  source : {step.source!r}")
        lines.append(f"  bytes  : {_format_payload(step.payload)}")
        lines.append(f"  decoded: {step.decoded!r}")
    return "\n".join(lines)


def _parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate ASCII to PETSCII conversions using the runtime console "
            "decoder. The script prints each iteration's intermediate results "
            "and exits with a non-zero status if any final decoded string "
            "differs from its original input."
        )
    )
    parser.add_argument(
        "strings",
        nargs="*",
        default=list(DEFAULT_STRINGS),
        help=(
            "Test cases to validate. If omitted, a built-in suite of sample "
            "strings is used."
        ),
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=1,
        help="Number of ASCII->PETSCII->ASCII iterations to perform for each string.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_arguments(argv or sys.argv[1:])
    validator = PetsciiRoundTripValidator(iterations=args.iterations)

    all_passed = True
    for text in args.strings:
        steps = validator.run(text)
        print(_render_steps(steps))
        final_decoded = steps[-1].decoded
        if final_decoded == text:
            print(f"Result : PASS (final decoded text matches original {text!r})\n")
        else:
            all_passed = False
            print(
                "Result : FAIL (final decoded text differs from original).\n"
                f"  original: {text!r}\n"
                f"  decoded : {final_decoded!r}\n"
            )
    if all_passed:
        print("All round-trip validations passed.")
        return 0
    print("One or more round-trip validations failed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
