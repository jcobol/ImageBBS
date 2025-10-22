"""Interactive command-line shell for the runtime session."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import importlib
import sys
from dataclasses import replace
from pathlib import Path
from typing import IO, Sequence, Tuple

from ..message_editor import EditorState, MessageEditor, SessionContext
from ..session_kernel import SessionState
from ..setup_config import load_drive_config
from ..setup_defaults import ModemDefaults, SetupDefaults
from .console_ui import IdleTimerScheduler, SysopConsoleApp
from .indicator_controller import IndicatorController
from .main_menu import MainMenuModule
from .message_store import MessageStore
from .message_store_repository import load_message_store, save_message_store
from .session_runner import SessionRunner
from .transports import BaudLimitedTransport, TelnetModemTransport


try:  # pragma: no cover - optional compatibility layer
    _LEGACY_RUNTIME_CLI = importlib.import_module("scripts.prototypes.runtime.cli")
except ModuleNotFoundError:  # pragma: no cover - legacy module absent
    _LEGACY_RUNTIME_CLI = None
else:  # pragma: no cover - exercised indirectly via monkeypatching tests
    setattr(_LEGACY_RUNTIME_CLI, "IdleTimerScheduler", IdleTimerScheduler)
    setattr(_LEGACY_RUNTIME_CLI, "IndicatorController", IndicatorController)


def _parse_host_port(value: str) -> Tuple[str, int]:
    try:
        host, port_text = value.rsplit(":", 1)
        port = int(port_text)
    except ValueError as exc:  # pragma: no cover - invalid CLI input
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
    ui_group = parser.add_mutually_exclusive_group()
    ui_group.add_argument(
        "--curses-ui",
        dest="curses_ui",
        action="store_true",
        help="Render the session using the curses sysop console",
    )
    ui_group.add_argument(
        "--console-ui",
        dest="curses_ui",
        action="store_false",
        help="Render the session using the plain console stream",
    )
    parser.set_defaults(curses_ui=True)
    parser.add_argument(
        "--baud-limit",
        type=int,
        default=None,
        help="Limit modem throughput to the specified bits per second",
    )
    return parser.parse_args(argv)


def _build_defaults(args: argparse.Namespace) -> SetupDefaults:
    defaults = SetupDefaults.stub()

    config_path: Path | None = args.drive_config
    if config_path is None:
        baud_override = args.baud_limit
        if baud_override is not None:
            defaults = replace(defaults, modem=ModemDefaults(baud_limit=baud_override))
        return defaults

    if not config_path.exists():
        raise SystemExit(f"drive configuration not found: {config_path}")

    config = load_drive_config(config_path)
    defaults = replace(defaults, drives=config.drives)
    ampersand_overrides = dict(config.ampersand_overrides)
    modem_override = config.modem_baud_limit
    if args.baud_limit is not None:
        modem_override = args.baud_limit
    if modem_override is not None:
        defaults = replace(defaults, modem=ModemDefaults(baud_limit=modem_override))
    object.__setattr__(defaults, "ampersand_overrides", ampersand_overrides)
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


def _resolve_indicator_controller_cls() -> type[IndicatorController]:
    if _LEGACY_RUNTIME_CLI is None:
        return IndicatorController
    return getattr(_LEGACY_RUNTIME_CLI, "IndicatorController", IndicatorController)


def _resolve_idle_timer_scheduler_cls() -> type[IdleTimerScheduler]:
    if _LEGACY_RUNTIME_CLI is None:
        return IdleTimerScheduler
    return getattr(_LEGACY_RUNTIME_CLI, "IdleTimerScheduler", IdleTimerScheduler)


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
    indicator_cls = _resolve_indicator_controller_cls()
    indicator_controller = indicator_cls(runner.console)
    runner.set_indicator_controller(indicator_controller)
    telnet_transport = TelnetModemTransport(
        runner,
        reader,
        writer,
        indicator_controller=indicator_controller,
    )
    baud_limit = getattr(getattr(runner.defaults, "modem", None), "baud_limit", None)
    transport = (
        BaudLimitedTransport(telnet_transport, baud_limit)
        if baud_limit is not None
        else telnet_transport
    )
    context = runner.kernel.context
    context.register_modem_device(transport=transport)
    transport.open()
    try:
        await telnet_transport.wait_closed()
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


_EDITOR_ABORT_COMMAND = "/abort"
_EDITOR_SUBMIT_COMMAND = "/send"


def _write_and_flush(stream: IO[str], text: str) -> None:
    stream.write(text)
    stream.flush()


def _maybe_collect_editor_submission(
    runner: SessionRunner, *, input_stream: IO[str], output_stream: IO[str]
) -> bool:
    if runner.state is not SessionState.MESSAGE_EDITOR:
        return False
    if not runner.requires_editor_submission():
        return False

    context = runner.editor_context
    editor_state = runner.get_editor_state()
    existing_subject = context.current_message if editor_state is not None else ""
    existing_lines = list(context.draft_buffer)

    def _readline(prompt: str | None = None) -> str | None:
        if prompt is not None:
            _write_and_flush(output_stream, prompt)
        line = input_stream.readline()
        if line == "":
            return None
        return line.rstrip("\r\n")

    _write_and_flush(
        output_stream,
        "\n-- Message Editor --\n"
        f"Type {_EDITOR_SUBMIT_COMMAND} to save or {_EDITOR_ABORT_COMMAND} to cancel.\n",
    )

    subject_text = existing_subject
    if editor_state is EditorState.POST_MESSAGE:
        prompt = "Subject"
        if existing_subject:
            prompt += f" [{existing_subject}]"
        prompt += ": "
        subject_line = _readline(prompt)
        if subject_line is None:
            runner.abort_editor()
            return True
        if subject_line.strip().lower() == _EDITOR_ABORT_COMMAND:
            runner.abort_editor()
            return True
        if subject_line:
            subject_text = subject_line

    if editor_state is EditorState.EDIT_DRAFT and existing_lines:
        _write_and_flush(output_stream, "Current message lines:\n")
        for line in existing_lines:
            _write_and_flush(output_stream, f"> {line}\n")

    _write_and_flush(output_stream, "Enter message body.\n")
    lines: list[str] = []
    while True:
        line = _readline("> ")
        if line is None:
            runner.abort_editor()
            return True
        command = line.strip().lower()
        if command == _EDITOR_ABORT_COMMAND:
            runner.abort_editor()
            return True
        if command == _EDITOR_SUBMIT_COMMAND:
            final_lines = lines if lines else existing_lines
            if editor_state is EditorState.POST_MESSAGE:
                runner.submit_editor_draft(subject=subject_text, lines=final_lines)
            else:
                runner.submit_editor_draft(subject=None, lines=final_lines)
            return True
        lines.append(line)


def run_session(
    runner: SessionRunner,
    *,
    input_stream: IO[str] = sys.stdin,
    output_stream: IO[str] = sys.stdout,
) -> SessionState:
    """Drive ``runner`` using ``input_stream`` and ``output_stream``."""

    indicator_cls = _resolve_indicator_controller_cls()
    indicator_controller = indicator_cls(runner.console)
    runner.set_indicator_controller(indicator_controller)
    idle_timer_cls = _resolve_idle_timer_scheduler_cls()
    idle_timer_scheduler = idle_timer_cls(runner.console)
    idle_timer_scheduler.reset()

    while True:
        indicator_controller.on_idle_tick()
        idle_timer_scheduler.tick()

        flushed = runner.read_output()
        if flushed:
            output_stream.write(flushed)
            output_stream.flush()

        if runner.state is SessionState.EXIT:
            return SessionState.EXIT

        if _maybe_collect_editor_submission(
            runner, input_stream=input_stream, output_stream=output_stream
        ):
            continue

        try:
            line = input_stream.readline()
        except KeyboardInterrupt:  # pragma: no cover - user interrupt
            output_stream.write("\n")
            output_stream.flush()
            return runner.state

        if line == "":  # EOF
            return runner.state

        runner.send_command(line.rstrip("\r\n"))
        if runner.state is SessionState.EXIT:
            return SessionState.EXIT


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
    if args.curses_ui:
        app = SysopConsoleApp(runner.console, runner=runner)
        app.run()
    else:
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
