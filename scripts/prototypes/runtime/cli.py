"""Interactive command-line shell for the runtime session prototypes."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import sys
from dataclasses import replace
from pathlib import Path
from typing import IO, Sequence, Tuple

from ..message_editor import MessageEditor, SessionContext
from ..session_kernel import SessionState
from ..setup_config import load_drive_config
from ..setup_defaults import SetupDefaults
from .main_menu import MainMenuModule
from .message_store import MessageStore
from .message_store_repository import load_message_store, save_message_store
from .session_runner import SessionRunner
from .transports import TelnetModemTransport


def _parse_host_port(value: str) -> Tuple[str, int]:
    try:
        host, port_text = value.rsplit(":", 1)
        port = int(port_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected HOST:PORT") from exc
    return host, port


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
        "--messages-path",
        type=Path,
        default=None,
        help="Optional path backing the persisted message store",
    )
    parser.add_argument(
        "--listen",
        type=_parse_host_port,
        default=None,
        help="Listen on HOST:PORT and bridge sessions over TCP",
    )
    parser.add_argument(
        "--connect",
        type=_parse_host_port,
        default=None,
        help="Dial HOST:PORT and bridge the session over TCP",
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


def _build_message_store(args: argparse.Namespace) -> MessageStore:
    messages_path: Path | None = args.messages_path
    if messages_path is None:
        return MessageStore()
    return load_message_store(messages_path)


def _build_session_context(
    defaults: SetupDefaults,
    *,
    store: MessageStore,
    messages_path: Path | None,
) -> SessionContext:
    board_id = getattr(defaults, "board_identifier", None) or "main"
    sysop = getattr(defaults, "sysop", None)
    user_id = getattr(sysop, "login_id", None) or "sysop"

    context = SessionContext(board_id=board_id, user_id=user_id, store=store)
    services = dict(context.services or {})
    if messages_path is not None:
        services["message_store_persistence"] = {"path": messages_path}
    context.services = services
    return context


def create_runner(args: argparse.Namespace) -> SessionRunner:
    """Instantiate :class:`SessionRunner` according to ``args``."""

    defaults = _build_defaults(args)
    store = _build_message_store(args)
    messages_path: Path | None = args.messages_path
    session_context = _build_session_context(
        defaults, store=store, messages_path=messages_path
    )
    return SessionRunner(
        defaults=defaults,
        main_menu_module=MainMenuModule(
            message_editor_factory=lambda: MessageEditor(store=store)
        ),
        session_context=session_context,
        message_store=store,
        message_store_path=messages_path,
    )


def _persist_messages(args: argparse.Namespace, runner: SessionRunner) -> None:
    path: Path | None = args.messages_path
    if path is None:
        return
    save_message_store(runner.message_store, path)


async def run_stream_session(
    args: argparse.Namespace,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    """Create a runner and bridge it to ``reader``/``writer``."""

    runner = create_runner(args)
    transport = TelnetModemTransport(runner, reader, writer)
    context = runner.kernel.context
    context.register_modem_device(transport=transport)
    transport.open()
    try:
        await transport.wait_closed()
    finally:
        transport.close()
        try:
            writer.close()
            await writer.wait_closed()
        except ConnectionError:
            pass
        _persist_messages(args, runner)


async def start_session_server(
    args: argparse.Namespace, host: str, port: int
) -> asyncio.AbstractServer:
    """Start a TCP server that spawns sessions per connection."""

    async def _client_handler(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            await run_stream_session(args, reader, writer)
        except Exception:
            if not writer.is_closing():
                writer.close()
                with contextlib.suppress(Exception):
                    await writer.wait_closed()
            raise

    return await asyncio.start_server(_client_handler, host, port)


async def run_listen(args: argparse.Namespace, host: str, port: int) -> None:
    """Serve incoming TCP sessions until cancelled."""

    server = await start_session_server(args, host, port)
    async with server:
        await server.serve_forever()


async def run_connect(args: argparse.Namespace, host: str, port: int) -> None:
    """Connect to a remote TCP endpoint and bridge the session."""

    reader, writer = await asyncio.open_connection(host, port)
    await run_stream_session(args, reader, writer)


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
    if args.listen and args.connect:
        raise SystemExit("--listen and --connect are mutually exclusive")
    if args.listen is not None:
        host, port = args.listen
        asyncio.run(run_listen(args, host, port))
        return 0
    if args.connect is not None:
        host, port = args.connect
        asyncio.run(run_connect(args, host, port))
        return 0
    runner = create_runner(args)
    run_session(runner)
    _persist_messages(args, runner)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via python -m
    raise SystemExit(main())


__all__ = [
    "create_runner",
    "main",
    "parse_args",
    "run_connect",
    "run_listen",
    "run_session",
    "run_stream_session",
    "start_session_server",
]
