"""Interactive command-line shell for the runtime session."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import importlib
import sys
from pathlib import Path
from typing import IO, Callable, Sequence, Tuple

from ..message_editor import SessionContext
from ..session_kernel import SessionState
from ..setup_defaults import SetupDefaults
from .console_ui import IdleTimerScheduler, SysopConsoleApp
from .editor_submission import EditorSubmissionHandler, SyncEditorIO
from .indicator_controller import IndicatorController
from .message_store import MessageStore
from .session_factory import (
    DEFAULT_RUNTIME_SESSION_FACTORY,
    RuntimeSessionFactory,
)
from .session_instrumentation import SessionInstrumentation
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


def _ensure_factory(factory: RuntimeSessionFactory | None) -> RuntimeSessionFactory:
    if factory is None:
        return DEFAULT_RUNTIME_SESSION_FACTORY
    return factory


def _build_defaults(
    args: argparse.Namespace, *, factory: RuntimeSessionFactory | None = None
) -> SetupDefaults:
    runtime_factory = _ensure_factory(factory)
    return runtime_factory.build_defaults(args)


def _build_message_store(
    args: argparse.Namespace, *, factory: RuntimeSessionFactory | None = None
) -> MessageStore:
    runtime_factory = _ensure_factory(factory)
    return runtime_factory.build_message_store(args)


def _build_session_context(
    defaults: SetupDefaults,
    *,
    store: MessageStore,
    messages_path: Path | None,
    factory: RuntimeSessionFactory | None = None,
) -> SessionContext:
    runtime_factory = _ensure_factory(factory)
    return runtime_factory.build_session_context(
        defaults, store=store, messages_path=messages_path
    )


def create_runner(
    args: argparse.Namespace, *, factory: RuntimeSessionFactory | None = None
) -> SessionRunner:
    """Instantiate :class:`SessionRunner` according to ``args``."""

    runtime_factory = _ensure_factory(factory)
    return runtime_factory.create_runner(args)


def _resolve_indicator_controller_cls() -> type[IndicatorController]:
    if _LEGACY_RUNTIME_CLI is None:
        return IndicatorController
    return getattr(_LEGACY_RUNTIME_CLI, "IndicatorController", IndicatorController)


def _resolve_idle_timer_scheduler_cls() -> type[IdleTimerScheduler]:
    if _LEGACY_RUNTIME_CLI is None:
        return IdleTimerScheduler
    return getattr(_LEGACY_RUNTIME_CLI, "IdleTimerScheduler", IdleTimerScheduler)


def _persist_messages(
    args: argparse.Namespace,
    runner: SessionRunner,
    *,
    factory: RuntimeSessionFactory | None = None,
) -> None:
    runtime_factory = _ensure_factory(factory)
    runtime_factory.persist_messages(args, runner)


async def run_stream_session(
    args: argparse.Namespace,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    *,
    factory: RuntimeSessionFactory | None = None,
    telnet_transport_factory: Callable[
        [
            SessionRunner,
            asyncio.StreamReader,
            asyncio.StreamWriter,
            SessionInstrumentation,
        ],
        TelnetModemTransport,
    ]
    | None = None,
    baud_limited_transport_factory: Callable[
        [TelnetModemTransport, int], BaudLimitedTransport
    ]
    | None = None,
) -> None:
    """Create a runner and bridge it to ``reader``/``writer``."""

    runtime_factory = _ensure_factory(factory)
    runner = create_runner(args, factory=runtime_factory)
    instrumentation = SessionInstrumentation(
        runner,
        indicator_controller_cls=_resolve_indicator_controller_cls(),
        idle_timer_scheduler_cls=_resolve_idle_timer_scheduler_cls(),
    )
    instrumentation.ensure_indicator_controller()
    if telnet_transport_factory is None:
        telnet_transport_factory = (
            lambda runner, reader, writer, instrumentation: TelnetModemTransport(
                runner,
                reader,
                writer,
                instrumentation=instrumentation,
            )
        )
    telnet_transport = telnet_transport_factory(
        runner,
        reader,
        writer,
        instrumentation,
    )
    baud_limit = getattr(getattr(runner.defaults, "modem", None), "baud_limit", None)
    if baud_limit is not None:
        if baud_limited_transport_factory is None:
            baud_limited_transport_factory = (
                lambda transport, limit: BaudLimitedTransport(transport, limit)
            )
        transport = baud_limited_transport_factory(telnet_transport, baud_limit)
    else:
        transport = telnet_transport
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
        _persist_messages(args, runner, factory=runtime_factory)


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


def _write_and_flush(stream: IO[str], text: str) -> None:
    stream.write(text)
    stream.flush()


def _maybe_collect_editor_submission(
    runner: SessionRunner, *, input_stream: IO[str], output_stream: IO[str]
) -> bool:
    class _StreamEditorIO:
        def __init__(self, input_stream: IO[str], output_stream: IO[str]) -> None:
            self._input = input_stream
            self._output = output_stream

        def write_line(self, text: str = "") -> None:
            _write_and_flush(self._output, text + "\n")

        def write_prompt(self, prompt: str) -> None:
            _write_and_flush(self._output, prompt)

        def readline(self) -> str | None:
            line = self._input.readline()
            if line == "":
                return None
            return line.rstrip("\r\n")

    handler = EditorSubmissionHandler(runner)
    stream_io: SyncEditorIO = _StreamEditorIO(input_stream, output_stream)
    return handler.collect_sync(stream_io)


def run_session(
    runner: SessionRunner,
    *,
    input_stream: IO[str] = sys.stdin,
    output_stream: IO[str] = sys.stdout,
) -> SessionState:
    """Drive ``runner`` using ``input_stream`` and ``output_stream``."""

    instrumentation = SessionInstrumentation(
        runner,
        indicator_controller_cls=_resolve_indicator_controller_cls(),
        idle_timer_scheduler_cls=_resolve_idle_timer_scheduler_cls(),
    )
    instrumentation.ensure_indicator_controller()
    instrumentation.reset_idle_timer()

    def _strip_pause_tokens(text: str) -> str:
        if not text:
            return text
        filtered: list[str] = []
        for char in text:
            code = ord(char)
            if code == 0x13:
                runner.set_pause_indicator_state(True)
                continue
            if code == 0x11:
                runner.set_pause_indicator_state(False)
                continue
            filtered.append(char)
        return "".join(filtered)

    while True:
        instrumentation.on_idle_cycle()

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
            raw_line = input_stream.readline()
        except KeyboardInterrupt:  # pragma: no cover - user interrupt
            output_stream.write("\n")
            output_stream.flush()
            return runner.state

        if raw_line == "":  # EOF
            return runner.state

        line = _strip_pause_tokens(raw_line)
        if not line:
            continue
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
    runtime_factory = DEFAULT_RUNTIME_SESSION_FACTORY
    runner = create_runner(args, factory=runtime_factory)
    if args.curses_ui:
        instrumentation = SessionInstrumentation(
            runner,
            indicator_controller_cls=_resolve_indicator_controller_cls(),
            idle_timer_scheduler_cls=_resolve_idle_timer_scheduler_cls(),
        )
        instrumentation.ensure_indicator_controller()
        instrumentation.reset_idle_timer()
        app = SysopConsoleApp(
            runner.console,
            runner=runner,
            instrumentation=instrumentation,
        )
        app.run()
    else:
        run_session(runner)
    _persist_messages(args, runner, factory=runtime_factory)
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
