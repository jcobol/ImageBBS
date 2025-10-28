"""Dispatch helper for the ``ml.extra`` tooling suite."""

from __future__ import annotations

import sys
from typing import Callable, Dict, Sequence

from . import ml_extra_disasm
from . import ml_extra_dump_flag_strings
from . import ml_extra_dump_macros
from . import ml_extra_refresh_pipeline
from . import ml_extra_screen_dumps
from . import ml_extra_snapshot_guard
from . import ml_extra_sanity

CommandFunc = Callable[[Sequence[str] | None], int | None]

COMMANDS: Dict[str, CommandFunc] = {
    "dump-macros": ml_extra_dump_macros.main,
    "dump-flag-strings": ml_extra_dump_flag_strings.main,
    "disasm": ml_extra_disasm.main,
    "screen-dumps": ml_extra_screen_dumps.main,
    "sanity": ml_extra_sanity.main,
    "snapshot-guard": ml_extra_snapshot_guard.main,
    "refresh-pipeline": ml_extra_refresh_pipeline.main,
}

__all__ = ["COMMANDS", "main"]


def _print_usage() -> None:
    print("Usage: python -m imagebbs.ml_extra_cli <command> [args...]")
    print("Available commands:")
    for name in sorted(COMMANDS):
        print(f"  {name}")


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help", "help"}:
        _print_usage()
        return 0 if args and args[0] != "help" else 0

    command = args[0]
    handler = COMMANDS.get(command)
    if handler is None:
        print(f"Unknown command: {command}")
        _print_usage()
        return 1

    remainder = args[1:]
    result = handler(remainder)
    return int(result) if isinstance(result, int) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
