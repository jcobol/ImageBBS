"""Interactive command-line shell for the runtime session."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import sys
import threading
from pathlib import Path
from typing import IO, Callable, Dict, Iterator, Sequence, Tuple

from ..message_editor import SessionContext
from ..session_kernel import SessionState
from ..setup_defaults import SetupDefaults
from .console_ui import IdleTimerScheduler, SysopConsoleApp
from .editor_submission import (
    DEFAULT_EDITOR_ABORT_COMMAND,
    DEFAULT_EDITOR_SUBMIT_COMMAND,
    EditorSubmissionHandler,
    SyncEditorIO,
)
from .indicator_controller import IndicatorController
from .message_store import MessageStore
from .message_store_repository import message_store_lock, message_store_lock_owner
from .session_factory import (
    DEFAULT_RUNTIME_SESSION_FACTORY,
    RuntimeSessionFactory,
)
from .session_instrumentation import SessionInstrumentation
from .session_runner import SessionRunner
from .transports import BaudLimitedTransport, TelnetModemTransport


_TELNET_NEWLINE_MAP = {
    "crlf": "\r\n",
    "lf": "\n",
    "none": None,
}


def _resolve_telnet_newline(choice: str) -> str | None:
    """Convert the CLI newline option into the transport expectation."""

    return _TELNET_NEWLINE_MAP[choice]


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
        "--storage-config",
        type=Path,
        default=None,
        help="Path to a TOML file describing filesystem storage mappings",
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
    parser.add_argument(
        "--telnet-newline",
        choices=("crlf", "lf", "none"),
        default="crlf",
        help=(
            "Newline translation applied to Telnet sessions "
            "(default: CRLF translation)"
        ),
    )
    parser.add_argument(
        "--editor-submit-command",
        default=DEFAULT_EDITOR_SUBMIT_COMMAND,
        help="Command token that saves the current editor buffer",
    )
    parser.add_argument(
        "--editor-abort-command",
        default=DEFAULT_EDITOR_ABORT_COMMAND,
        help="Command token that cancels the current editor buffer",
    )
    parser.add_argument(
        "--board-id",
        default=None,
        help="Override the board identifier for the session context",
    )
    parser.add_argument(
        "--user-id",
        default=None,
        help="Override the user identifier for the session context",
    )
    # Why: allow operators to tune idle timer updates for slow or fast polling loops.
    parser.add_argument(
        "--idle-tick-interval",
        type=float,
        default=1.0,
        help="Seconds between idle timer updates for sysop displays",
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
    args: argparse.Namespace,
    factory: RuntimeSessionFactory | None = None,
) -> SessionContext:
    runtime_factory = _ensure_factory(factory)
    return runtime_factory.build_session_context(
        defaults, store=store, messages_path=messages_path, args=args
    )


def create_runner(
    args: argparse.Namespace, *, factory: RuntimeSessionFactory | None = None
) -> SessionRunner:
    """Instantiate :class:`SessionRunner` according to ``args``."""

    runtime_factory = _ensure_factory(factory)
    return runtime_factory.create_runner(args)


def _resolve_indicator_controller_cls() -> type[IndicatorController]:
    legacy_module = sys.modules.get("scripts.prototypes.runtime.cli")
    if legacy_module is not None:
        return getattr(legacy_module, "IndicatorController", IndicatorController)
    return IndicatorController


def _install_indicator_controller(
    runner: SessionRunner, controller_cls: type[IndicatorController] | None
) -> IndicatorController | None:
    if controller_cls is None:
        return None
    console = getattr(runner, "console", None)
    if console is None:
        return None
    indicator_kwargs: Dict[str, object] = {}
    indicator_defaults = getattr(getattr(runner, "defaults", None), "indicator", None)
    controller_kwargs = getattr(indicator_defaults, "controller_kwargs", None)
    if callable(controller_kwargs):
        # Why: forward configured indicator colours so CLI installations respect host customisations.
        indicator_kwargs = dict(controller_kwargs())
    controller = controller_cls(console, **indicator_kwargs)
    sync_from_console = getattr(controller, "sync_from_console", None)
    if callable(sync_from_console):
        sync_from_console()
    runner.set_indicator_controller(controller)
    context = getattr(getattr(runner, "kernel", None), "context", None)
    register_service = getattr(context, "register_service", None)
    if callable(register_service):
        register_service("indicator_controller", controller)
    return controller


def _resolve_idle_timer_scheduler_cls() -> type[IdleTimerScheduler]:
    legacy_module = sys.modules.get("scripts.prototypes.runtime.cli")
    if legacy_module is not None:
        return getattr(legacy_module, "IdleTimerScheduler", IdleTimerScheduler)
    return IdleTimerScheduler


def _persist_messages(
    args: argparse.Namespace,
    runner: SessionRunner,
    *,
    factory: RuntimeSessionFactory | None = None,
) -> None:
    runtime_factory = _ensure_factory(factory)
    runtime_factory.persist_messages(args, runner)


@contextlib.contextmanager
def _runner_with_persistence(
    args: argparse.Namespace,
    *,
    factory: RuntimeSessionFactory | None = None,
) -> Iterator[SessionRunner]:
    runtime_factory = _ensure_factory(factory)
    messages_path: Path | None = getattr(args, "messages_path", None)
    if messages_path is None:
        lock_cm: contextlib.AbstractContextManager[object] = contextlib.nullcontext()
    else:
        lock_cm = message_store_lock(messages_path)
    with lock_cm:
        runner = create_runner(args, factory=runtime_factory)
        try:
            yield runner
        finally:
            _persist_messages(args, runner, factory=runtime_factory)


@contextlib.asynccontextmanager
async def _async_runner_with_persistence(
    args: argparse.Namespace,
    *,
    factory: RuntimeSessionFactory | None = None,
) -> Iterator[SessionRunner]:
    runtime_factory = _ensure_factory(factory)
    messages_path: Path | None = getattr(args, "messages_path", None)
    if messages_path is None:
        runner = create_runner(args, factory=runtime_factory)
        try:
            yield runner
        finally:
            _persist_messages(args, runner, factory=runtime_factory)
        return

    def _current_owner_id() -> int:
        thread_id = threading.get_ident()
        task = asyncio.current_task()
        if task is None:
            return thread_id
        return (thread_id << 32) ^ id(task)

    owner_id = _current_owner_id()
    lock = message_store_lock(messages_path)
    try:
        await asyncio.to_thread(lock.acquire, owner_id=owner_id)
    except TimeoutError:
        # Why: inform callers that persistence is locked by another session before disconnecting.
        print(
            "Unable to acquire the message store lock because another session is persisting messages.",
            file=sys.stderr,
        )
        raise
    runner: SessionRunner | None = None
    try:
        with message_store_lock_owner(owner_id):
            runner = create_runner(args, factory=runtime_factory)
            try:
                yield runner
            finally:
                if runner is not None:
                    _persist_messages(args, runner, factory=runtime_factory)
    finally:
        await asyncio.to_thread(lock.release)


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
    newline_translation = _resolve_telnet_newline(args.telnet_newline)
    async with _async_runner_with_persistence(args, factory=runtime_factory) as runner:
        # Why: propagate CLI idle timer preferences into instrumentation and transport wiring.
        instrumentation = SessionInstrumentation(
            runner,
            indicator_controller_cls=_resolve_indicator_controller_cls(),
            idle_timer_scheduler_cls=_resolve_idle_timer_scheduler_cls(),
            idle_tick_interval=args.idle_tick_interval,
        )
        instrumentation.ensure_indicator_controller()
        if telnet_transport_factory is None:
            telnet_transport_factory = (
                lambda runner, reader, writer, instrumentation: TelnetModemTransport(
                    runner,
                    reader,
                    writer,
                    instrumentation=instrumentation,
                    idle_tick_interval=args.idle_tick_interval,
                    editor_submit_command=args.editor_submit_command,
                    editor_abort_command=args.editor_abort_command,
                    newline_translation=newline_translation,
                )
            )
        telnet_transport = telnet_transport_factory(
            runner,
            reader,
            writer,
            instrumentation,
        )
        baud_limit = getattr(
            getattr(runner.defaults, "modem", None), "baud_limit", None
        )
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
    runner: SessionRunner,
    *,
    input_stream: IO[str],
    output_stream: IO[str],
    submit_command: str = DEFAULT_EDITOR_SUBMIT_COMMAND,
    abort_command: str = DEFAULT_EDITOR_ABORT_COMMAND,
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

    handler = EditorSubmissionHandler(
        runner,
        submit_command=submit_command,
        abort_command=abort_command,
    )
    stream_io: SyncEditorIO = _StreamEditorIO(input_stream, output_stream)
    return handler.collect_sync(stream_io)


def drive_session(
    runner: SessionRunner,
    *,
    input_stream: IO[str] = sys.stdin,
    output_stream: IO[str] = sys.stdout,
    editor_submit_command: str = DEFAULT_EDITOR_SUBMIT_COMMAND,
    editor_abort_command: str = DEFAULT_EDITOR_ABORT_COMMAND,
    idle_tick_interval: float = 1.0,
) -> SessionState:
    """Drive ``runner`` using ``input_stream`` and ``output_stream``."""

    # Why: orchestrate console I/O loops so transport-agnostic tests can drive sessions.
    # Why: feed CLI-specified idle cadence into shared instrumentation for console loops.
    instrumentation = SessionInstrumentation(
        runner,
        indicator_controller_cls=_resolve_indicator_controller_cls(),
        idle_timer_scheduler_cls=_resolve_idle_timer_scheduler_cls(),
        idle_tick_interval=idle_tick_interval,
    )
    instrumentation.ensure_indicator_controller()
    instrumentation.reset_idle_timer()

    paused = False
    pause_buffer: list[str] = []

    def _flush_pause_buffer() -> None:
        # Why: deliver buffered output accumulated while paused once the session resumes or exits.
        if not pause_buffer:
            return
        _write_and_flush(output_stream, "".join(pause_buffer))
        pause_buffer.clear()

    def _set_paused(active: bool) -> None:
        nonlocal paused
        runner.set_pause_indicator_state(active)
        if paused == active:
            return
        paused = active
        if not active:
            _flush_pause_buffer()

    def _strip_pause_tokens(text: str) -> str:
        if not text:
            return text
        filtered: list[str] = []
        for char in text:
            code = ord(char)
            if code == 0x13:
                _set_paused(True)
                continue
            if code == 0x11:
                _set_paused(False)
                continue
            filtered.append(char)
        return "".join(filtered)

    def _finalize_exit(state: SessionState) -> SessionState:
        # Why: make sure paused text reaches the console before signalling the terminal session state.
        _flush_pause_buffer()
        return state

    while True:
        instrumentation.on_idle_cycle()

        flushed = runner.read_output()
        if flushed:
            if paused:
                pause_buffer.append(flushed)
            else:
                _write_and_flush(output_stream, flushed)

        if runner.state is SessionState.EXIT:
            return _finalize_exit(SessionState.EXIT)

        if _maybe_collect_editor_submission(
            runner,
            input_stream=input_stream,
            output_stream=output_stream,
            submit_command=editor_submit_command,
            abort_command=editor_abort_command,
        ):
            continue

        try:
            raw_line = input_stream.readline()
        except KeyboardInterrupt:  # pragma: no cover - user interrupt
            output_stream.write("\n")
            output_stream.flush()
            return _finalize_exit(runner.state)

        if raw_line == "":  # EOF
            return _finalize_exit(runner.state)

        line = _strip_pause_tokens(raw_line)
        if not line:
            continue
        runner.send_command(line.rstrip("\r\n"))
        if runner.state is SessionState.EXIT:
            return _finalize_exit(SessionState.EXIT)


def run_session(
    args: argparse.Namespace,
    *,
    factory: RuntimeSessionFactory | None = None,
    input_stream: IO[str] = sys.stdin,
    output_stream: IO[str] = sys.stdout,
) -> SessionState:
    """Create a runner for ``args`` and drive it using the console streams."""

    runtime_factory = _ensure_factory(factory)
    with _runner_with_persistence(args, factory=runtime_factory) as runner:
        return drive_session(
            runner,
            input_stream=input_stream,
            output_stream=output_stream,
            editor_submit_command=args.editor_submit_command,
            editor_abort_command=args.editor_abort_command,
            idle_tick_interval=args.idle_tick_interval,
        )


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
    indicator_controller_cls = _resolve_indicator_controller_cls()
    with _runner_with_persistence(args, factory=runtime_factory) as runner:
        _install_indicator_controller(runner, indicator_controller_cls)
        if args.curses_ui:
            instrumentation = SessionInstrumentation(
                runner,
                indicator_controller_cls=indicator_controller_cls,
                idle_timer_scheduler_cls=_resolve_idle_timer_scheduler_cls(),
                idle_tick_interval=args.idle_tick_interval,
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
            drive_session(
                runner,
                editor_submit_command=args.editor_submit_command,
                editor_abort_command=args.editor_abort_command,
                idle_tick_interval=args.idle_tick_interval,
            )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via python -m
    raise SystemExit(main())


__all__ = [
    "drive_session",
    "create_runner",
    "main",
    "parse_args",
    "run_connect",
    "run_listen",
    "run_session",
    "run_stream_session",
    "start_session_server",
]
