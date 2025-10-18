"""Interactive command-line shell for the runtime session prototypes."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path
from typing import IO, Sequence

from ..message_editor import SessionContext
from ..session_kernel import SessionState
from ..setup_config import load_drive_config
from ..setup_defaults import SetupDefaults
from .main_menu import MainMenuModule
from .session_runner import SessionRunner


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Return parsed arguments for the runtime CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--drive-config",
        type=Path,
        default=None,
        help="Path to a TOML file describing drive assignments",
    )
    parser.add_argument(
        "--message-store-load",
        type=Path,
        default=None,
        help="Optional path to load message store state from",
    )
    parser.add_argument(
        "--message-store-save",
        type=Path,
        default=None,
        help="Optional path to persist message store state to",
    )
    return parser.parse_args(argv)


def _build_defaults(args: argparse.Namespace) -> SetupDefaults:
    defaults = SetupDefaults.stub()

    config_path: Path | None = args.drive_config
    if config_path is None:
        return defaults

    if not config_path.exists():
        raise SystemExit(f"drive configuration not found: {config_path}")

    config = load_drive_config(config_path)
    defaults = replace(defaults, drives=config.drives)
    object.__setattr__(defaults, "ampersand_overrides", dict(config.ampersand_overrides))
    return defaults


def _build_session_context(
    defaults: SetupDefaults, args: argparse.Namespace
) -> SessionContext | None:
    options: dict[str, Path] = {}
    if args.message_store_load is not None:
        options["load_path"] = args.message_store_load
    if args.message_store_save is not None:
        options["save_path"] = args.message_store_save

    if not options:
        return None

    board_id = getattr(defaults, "board_identifier", None) or "main"
    sysop = getattr(defaults, "sysop", None)
    user_id = getattr(sysop, "login_id", None) or "sysop"

    context = SessionContext(board_id=board_id, user_id=user_id)
    services = dict(context.services or {})
    services["message_store_persistence"] = options
    context.services = services
    return context


def create_runner(args: argparse.Namespace) -> SessionRunner:
    """Instantiate :class:`SessionRunner` according to ``args``."""

    defaults = _build_defaults(args)
    session_context = _build_session_context(defaults, args)
    return SessionRunner(
        defaults=defaults,
        main_menu_module=MainMenuModule(),
        session_context=session_context,
    )


def run_session(
    runner: SessionRunner,
    *,
    input_stream: IO[str] = sys.stdin,
    output_stream: IO[str] = sys.stdout,
) -> SessionState:
    """Drive ``runner`` using ``input_stream`` and ``output_stream``."""

    while True:
        flushed = runner.read_output()
        if flushed:
            output_stream.write(flushed)
            output_stream.flush()

        if runner.state is SessionState.EXIT:
            return SessionState.EXIT

        try:
            line = input_stream.readline()
        except KeyboardInterrupt:  # pragma: no cover - user interrupt
            output_stream.write("\n")
            output_stream.flush()
            return runner.state

        if line == "":  # EOF
            return runner.state

        runner.send_command(line.rstrip("\r\n"))


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the runtime CLI."""

    args = parse_args(argv)
    runner = create_runner(args)
    run_session(runner)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via python -m
    raise SystemExit(main())


__all__ = [
    "create_runner",
    "main",
    "parse_args",
    "run_session",
]
