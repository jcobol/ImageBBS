import argparse
import asyncio
import contextlib
import io
from collections import deque
import unittest.mock as mock
from pathlib import Path

from imagebbs.runtime.cli import (
    create_runner,
    drive_session,
    parse_args,
    run_session,
    run_stream_session,
    start_session_server,
)
from imagebbs.runtime.message_store_repository import load_message_store
from imagebbs.session_kernel import SessionState
from imagebbs.setup_defaults import (
    DEFAULT_MODEM_BAUD_LIMIT,
    FilesystemDriveLocator,
    SetupDefaults,
)
from imagebbs.device_context import ConsoleService
from imagebbs.message_editor import SessionContext
from imagebbs.runtime.console_ui import IdleTimerScheduler
from imagebbs.runtime.indicator_controller import IndicatorController
from imagebbs.runtime.message_store import MessageStore
from imagebbs.runtime.session_factory import DEFAULT_RUNTIME_SESSION_FACTORY
from imagebbs.runtime.session_runner import SessionRunner


def test_drive_session_handles_exit_sequence() -> None:
    args = parse_args([])
    runner = create_runner(args)

    input_stream = io.StringIO("EX\n")
    output_stream = io.StringIO()

    final_state = drive_session(
        runner, input_stream=input_stream, output_stream=output_stream
    )

    assert final_state is SessionState.EXIT
    transcript = output_stream.getvalue()
    assert transcript
    assert transcript.isascii()
    assert args.listen is None
    assert args.connect is None
    assert runner.defaults.modem.baud_limit == DEFAULT_MODEM_BAUD_LIMIT


def test_run_session_acquires_lock_and_persists(tmp_path: Path) -> None:
    messages_path = tmp_path / "messages.json"
    args = parse_args(["--messages-path", str(messages_path)])

    input_stream = io.StringIO("EX\n")
    output_stream = io.StringIO()

    final_state = run_session(
        args, input_stream=input_stream, output_stream=output_stream
    )

    assert final_state is SessionState.EXIT
    assert messages_path.exists()
    stored = load_message_store(messages_path)
    assert list(stored.iter_records()) == []
    assert output_stream.getvalue()


def test_parse_args_defaults_to_curses_ui() -> None:
    args = parse_args([])

    assert args.curses_ui is True


def test_parse_args_console_flag_disables_curses_ui() -> None:
    args = parse_args(["--console-ui"])

    assert args.curses_ui is False


def test_create_runner_applies_configuration_and_persistence(tmp_path: Path) -> None:
    config_path = tmp_path / "drives.toml"
    config_path.write_text(
        "\n".join(
            [
                "[slots]",
                '1 = "."',
                "[ampersand_overrides]",
                '1 = "imagebbs.runtime.ampersand_overrides:handle_chkflags"',
                "[modem]",
                "baud_limit = 2400",
                "",
            ]
        )
    )

    messages_path = tmp_path / "messages.json"

    args = parse_args(
        [
            "--drive-config",
            str(config_path),
            "--messages-path",
            str(messages_path),
        ]
    )

    runner = create_runner(args)
    defaults = runner.defaults

    first_drive = defaults.drives[0]
    assert isinstance(first_drive.locator, FilesystemDriveLocator)
    assert first_drive.locator.path == tmp_path.resolve()
    assert getattr(defaults, "ampersand_overrides") == {
        1: "imagebbs.runtime.ampersand_overrides:handle_chkflags"
    }
    assert defaults.modem.baud_limit == 2400

    services = runner.editor_context.services
    assert services is not None
    options = services.get("message_store_persistence")
    assert options == {"path": messages_path}
    assert runner.editor_context.board_id
    assert runner.editor_context.user_id
    assert runner.message_store_path == messages_path
    assert runner.editor_context.store is runner.message_store


def test_cli_baud_limit_overrides_config(tmp_path: Path) -> None:
    config_path = tmp_path / "drives.toml"
    config_path.write_text(
        "\n".join(
            [
                "[slots]",
                '1 = "."',
                "[modem]",
                "baud_limit = 2400",
                "",
            ]
        )
    )

    args = parse_args(
        [
            "--drive-config",
            str(config_path),
            "--baud-limit",
            "9600",
        ]
    )

    runner = create_runner(args)
    assert runner.defaults.modem.baud_limit == 9600


def test_listen_session_serves_banner_and_exits_cleanly() -> None:
    args = parse_args([])

    async def _exercise() -> None:
        expected_runner = create_runner(args)
        expected_banner = expected_runner.read_output().encode("latin-1")

        server = await start_session_server(args, "127.0.0.1", 0)
        sockets = server.sockets or []
        assert sockets
        host, port = sockets[0].getsockname()[:2]

        reader, writer = await asyncio.open_connection(host, port)
        try:
            received = await asyncio.wait_for(
                reader.readexactly(len(expected_banner)), timeout=1.0
            )
            assert received == expected_banner

            writer.write(b"EX\r\n")
            await writer.drain()

            remaining = await asyncio.wait_for(reader.read(), timeout=1.0)
            assert remaining == b""
        finally:
            writer.close()
            await writer.wait_closed()
            server.close()
            await server.wait_closed()

    asyncio.run(_exercise())


def test_run_session_posts_message_via_editor() -> None:
    args = parse_args([])
    runner = create_runner(args)

    script = "MB\nP\nHello World\nThis is the body\n/send\nQ\nEX\n"
    input_stream = io.StringIO(script)
    output_stream = io.StringIO()

    final_state = drive_session(
        runner, input_stream=input_stream, output_stream=output_stream
    )

    assert final_state is SessionState.EXIT
    transcript = output_stream.getvalue()
    assert "Type /send to save or /abort to cancel." in transcript

    records = list(runner.message_store.iter_records())
    assert len(records) == 1
    record = records[0]
    assert record.subject == "Hello World"
    assert record.lines == ("This is the body",)


def test_run_session_pauses_and_flushes_output_on_flow_control() -> None:
    class RecordingIndicatorController:
        def __init__(self, console: ConsoleService) -> None:
            self.console = console
            self.pause_states: list[bool] = []
            self.carrier_states: list[bool] = []
            self.idle_ticks = 0

        def set_pause(self, active: bool) -> None:
            self.pause_states.append(active)

        def set_carrier(self, active: bool) -> None:
            self.carrier_states.append(active)

        def on_idle_tick(self) -> None:
            self.idle_ticks += 1

    class RecordingScheduler:
        def __init__(self, console: ConsoleService) -> None:
            self.console = console
            self.reset_calls = 0
            self.tick_calls = 0

        def reset(self) -> None:
            self.reset_calls += 1

        def tick(self) -> None:
            self.tick_calls += 1

    class ScriptedRunner:
        def __init__(self) -> None:
            self.console = object()
            self.state = SessionState.MAIN_MENU
            self.outputs = deque(["READY", "PAUSED", "AFTER"])
            self.pause_states: list[bool] = []
            self.commands: list[str] = []
            self.indicator_controller: RecordingIndicatorController | None = None

        def read_output(self) -> str:
            if self.outputs:
                return self.outputs.popleft()
            return ""

        def send_command(self, command: str) -> SessionState:
            self.commands.append(command)
            if command == "EX":
                self.state = SessionState.EXIT
            return self.state

        def set_indicator_controller(self, controller) -> None:
            self.indicator_controller = controller

        def set_pause_indicator_state(self, active: bool) -> None:
            self.pause_states.append(active)
            controller = self.indicator_controller
            if controller is not None:
                controller.set_pause(active)

        def requires_editor_submission(self) -> bool:
            return False

    class RecordingOutput:
        def __init__(self, runner: ScriptedRunner) -> None:
            self.runner = runner
            self.entries: list[tuple[str, list[bool]]] = []

        def write(self, text: str) -> None:
            if text:
                self.entries.append((text, list(self.runner.pause_states)))

        def flush(self) -> None:
            pass

    runner = ScriptedRunner()
    input_stream = io.StringIO("\x13\n\x11\nEX\n")
    output_stream = RecordingOutput(runner)

    with mock.patch(
        "imagebbs.runtime.cli._resolve_indicator_controller_cls",
        return_value=RecordingIndicatorController,
    ), mock.patch(
        "imagebbs.runtime.cli._resolve_idle_timer_scheduler_cls",
        return_value=RecordingScheduler,
    ):
        final_state = drive_session(
            runner, input_stream=input_stream, output_stream=output_stream
        )

    assert final_state is SessionState.EXIT
    assert runner.commands == ["", "", "EX"]
    assert runner.pause_states == [True, False]
    controller = runner.indicator_controller
    assert controller is not None
    assert controller.pause_states == [True, False]

    writes = output_stream.entries
    assert [text for text, _ in writes] == ["READY", "PAUSED", "AFTER"]
    paused_entry_states = [states for text, states in writes if text == "PAUSED"]
    assert paused_entry_states == [[True, False]]


def test_run_session_advances_spinner_and_idle_timer() -> None:
    args = parse_args([])
    runner = create_runner(args)

    class FakeClock:
        def __init__(self, values: list[float]):
            self._values = list(values)
            self.calls = 0

        def __call__(self) -> float:
            if not self._values:
                raise AssertionError("fake clock requires at least one value")
            if self.calls < len(self._values):
                value = self._values[self.calls]
            else:
                value = self._values[-1]
            self.calls += 1
            return value

    fake_clock = FakeClock([0.0, 1.0, 2.0])

    class RecordingScheduler(IdleTimerScheduler):
        def __init__(self, console: ConsoleService):
            super().__init__(console, time_source=fake_clock)

    class RecordingIndicatorController(IndicatorController):
        def __init__(self, console: ConsoleService):
            super().__init__(console)
            self.set_spinner_enabled(True)

    class ScriptedInput:
        def __init__(self, lines: list[str]):
            self._lines = list(lines)

        def readline(self) -> str:
            if self._lines:
                return self._lines.pop(0)
            return ""

    input_stream = ScriptedInput(["\n", "\n", "EX\n"])
    output_stream = io.StringIO()

    with mock.patch(
        "scripts.prototypes.runtime.cli.IdleTimerScheduler", RecordingScheduler
    ), mock.patch(
        "scripts.prototypes.runtime.cli.IndicatorController", RecordingIndicatorController
    ):
        final_state = drive_session(
            runner, input_stream=input_stream, output_stream=output_stream
        )

    assert final_state is SessionState.EXIT
    assert fake_clock.calls >= 3

    spinner_bytes, _ = runner.console.peek_block(
        screen_address=ConsoleService._SPINNER_SCREEN_ADDRESS,
        screen_length=1,
    )
    assert spinner_bytes is not None
    assert spinner_bytes[0] == 0xAF

    digit_values: list[int] = []
    for address in ConsoleService._IDLE_TIMER_SCREEN_ADDRESSES:
        digit_bytes, _ = runner.console.peek_block(
            screen_address=address,
            screen_length=1,
        )
        assert digit_bytes is not None
        digit_values.append(digit_bytes[0])

    assert digit_values == [0x30, 0x30, 0x32]


def test_run_session_toggles_pause_indicator_from_control_tokens() -> None:
    args = parse_args([])
    runner = create_runner(args)

    class RecordingIndicator:
        instance: "RecordingIndicator | None" = None

        def __init__(self, console: ConsoleService) -> None:
            self.console = console
            self.pause_states: list[bool] = []
            RecordingIndicator.instance = self

        def set_pause(self, active: bool) -> None:
            self.pause_states.append(active)

        def set_carrier(self, active: bool) -> None:  # pragma: no cover - not used
            pass

        def on_idle_tick(self) -> None:  # pragma: no cover - not used
            pass

        def set_spinner_enabled(self, active: bool) -> None:  # pragma: no cover - not used
            pass

        def set_abort(self, active: bool) -> None:  # pragma: no cover - not used
            pass

    RecordingIndicator.instance = None
    input_stream = io.StringIO("\x13\r\n\x11EX\r\n")
    output_stream = io.StringIO()

    with mock.patch(
        "imagebbs.runtime.cli.IndicatorController", RecordingIndicator
    ), mock.patch(
        "scripts.prototypes.runtime.cli.IndicatorController", RecordingIndicator
    ):
        final_state = drive_session(
            runner, input_stream=input_stream, output_stream=output_stream
        )

    assert final_state is SessionState.EXIT
    indicator = RecordingIndicator.instance
    assert indicator is not None
    assert indicator.pause_states == [True, False]


def test_run_stream_session_bridges_telnet_and_persists_messages(tmp_path: Path) -> None:
    messages_path = tmp_path / "messages.json"
    args = parse_args(["--messages-path", str(messages_path)])

    class RecordingFactory:
        def __init__(self) -> None:
            self._delegate = DEFAULT_RUNTIME_SESSION_FACTORY
            self.runners: list[SessionRunner] = []
            self.persist_calls: list[tuple[argparse.Namespace, SessionRunner]] = []

        def build_defaults(self, namespace: argparse.Namespace) -> SetupDefaults:
            return self._delegate.build_defaults(namespace)

        def build_message_store(self, namespace: argparse.Namespace) -> MessageStore:
            return self._delegate.build_message_store(namespace)

        def build_session_context(
            self,
            defaults: SetupDefaults,
            *,
            store: MessageStore,
            messages_path: Path | None,
        ) -> SessionContext:
            return self._delegate.build_session_context(
                defaults, store=store, messages_path=messages_path
            )

        def create_runner(self, namespace: argparse.Namespace) -> SessionRunner:
            runner = self._delegate.create_runner(namespace)
            self.runners.append(runner)
            return runner

        def persist_messages(
            self, namespace: argparse.Namespace, runner: SessionRunner
        ) -> None:
            self.persist_calls.append((namespace, runner))
            self._delegate.persist_messages(namespace, runner)

    recording_factory = RecordingFactory()

    class RecordingIndicator(IndicatorController):
        instances: list["RecordingIndicator"] = []

        def __init__(self, console: ConsoleService) -> None:
            super().__init__(console)
            self.pause_updates: list[bool] = []
            self.carrier_updates: list[bool] = []
            RecordingIndicator.instances.append(self)

        def set_pause(self, active: bool) -> None:
            self.pause_updates.append(active)
            super().set_pause(active)

        def set_carrier(self, active: bool) -> None:
            self.carrier_updates.append(active)
            super().set_carrier(active)

    script = b"".join(
        [
            b"\x13",  # pause outbound delivery
            b"MB\r\n",
            b"P\r\n",
            b"Async Subject\r\n",
            b"Async Body\r\n",
            b"/send\r\n",
            b"Q\r\n",
            b"\x11",  # resume outbound delivery
            b"EX\r\n",
        ]
    )

    async def _exercise() -> str:
        session_done = asyncio.Event()
        transcript: list[bytes] = []

        async def _handle(
            reader: asyncio.StreamReader, writer: asyncio.StreamWriter
        ) -> None:
            try:
                await run_stream_session(
                    args, reader, writer, factory=recording_factory
                )
            finally:
                session_done.set()

        server = await asyncio.start_server(_handle, "127.0.0.1", 0)
        try:
            sockets = server.sockets or []
            assert sockets
            host, port = sockets[0].getsockname()[:2]

            reader, writer = await asyncio.open_connection(host, port)
            try:
                writer.write(script)
                await writer.drain()

                while True:
                    chunk = await asyncio.wait_for(reader.read(4096), timeout=5.0)
                    if not chunk:
                        break
                    transcript.append(chunk)

                await asyncio.wait_for(session_done.wait(), timeout=1.0)
            finally:
                writer.close()
                await writer.wait_closed()
        finally:
            server.close()
            await server.wait_closed()

        return b"".join(transcript).decode("latin-1", errors="ignore")

    with mock.patch(
        "imagebbs.runtime.cli._resolve_indicator_controller_cls",
        return_value=RecordingIndicator,
    ):
        transcript = asyncio.run(_exercise())

    assert transcript
    assert "Type /send to save or /abort to cancel." in transcript

    runners = recording_factory.runners
    assert len(runners) == 1
    runner = runners[0]

    records = list(runner.message_store.iter_records())
    assert len(records) == 1
    record = records[0]
    assert record.subject == "Async Subject"
    assert record.lines == ("Async Body",)

    assert len(recording_factory.persist_calls) == 1
    assert messages_path.exists()
    persisted_text = messages_path.read_text(encoding="utf-8")
    assert "Async Subject" in persisted_text

    assert RecordingIndicator.instances
    indicator = RecordingIndicator.instances[0]
    assert True in indicator.carrier_updates
    assert indicator.carrier_updates[-1] is False

    assert True in indicator.pause_updates
    assert False in indicator.pause_updates
    first_pause = indicator.pause_updates.index(True)
    resume_index = indicator.pause_updates.index(False, first_pause)
    assert resume_index > first_pause


def test_run_session_edits_existing_message_via_editor() -> None:
    args = parse_args([])
    runner = create_runner(args)
    store = runner.message_store
    board_id = runner.editor_context.board_id
    store.append(
        board_id=board_id,
        subject="Original",
        author_handle=runner.editor_context.user_id,
        lines=["old line"],
    )

    script = "MB\nE\n1\nUpdated line\n/send\nQ\nEX\n"
    input_stream = io.StringIO(script)
    output_stream = io.StringIO()

    final_state = drive_session(
        runner, input_stream=input_stream, output_stream=output_stream
    )

    assert final_state is SessionState.EXIT
    records = list(store.iter_records())
    assert len(records) == 1
    record = records[0]
    assert record.lines == ("Updated line",)


def test_run_session_abort_editor_discards_draft() -> None:
    args = parse_args([])
    runner = create_runner(args)

    script = "MB\nP\nMy Subject\nLine 1\n/abort\nQ\nEX\n"
    input_stream = io.StringIO(script)
    output_stream = io.StringIO()

    final_state = drive_session(
        runner, input_stream=input_stream, output_stream=output_stream
    )

    assert final_state is SessionState.EXIT
    assert list(runner.message_store.iter_records()) == []
    assert runner.editor_context.draft_buffer == []
    assert runner.editor_context.drafts == {}


def test_run_stream_session_concurrent_persistence(tmp_path: Path) -> None:
    messages_path = tmp_path / "messages.json"
    args = parse_args(["--messages-path", str(messages_path)])

    async def _exercise() -> None:
        server = await start_session_server(args, "127.0.0.1", 0)
        async with server:
            sockets = server.sockets or []
            assert sockets
            host, port = sockets[0].getsockname()[:2]

            async def _run_client(subject: str, body: str) -> str:
                reader, writer = await asyncio.open_connection(host, port)
                try:
                    script = "\r\n".join(
                        [
                            "MB",
                            "P",
                            subject,
                            body,
                            "/send",
                            "Q",
                            "EX",
                            "",
                        ]
                    ).encode("latin-1")
                    writer.write(script)
                    await writer.drain()
                    with contextlib.suppress(Exception):
                        writer.write_eof()
                    transcript = await asyncio.wait_for(
                        reader.read(), timeout=5.0
                    )
                    return transcript.decode("latin-1", errors="ignore")
                finally:
                    writer.close()
                    await writer.wait_closed()

            transcripts = await asyncio.gather(
                _run_client("Hello One", "Body One"),
                _run_client("Hello Two", "Body Two"),
            )
            assert all(transcripts)

    asyncio.run(_exercise())

    stored = load_message_store(messages_path)
    subjects = {record.subject for record in stored.iter_records()}
    assert subjects == {"Hello One", "Hello Two"}


def test_run_stream_session_overlapping_tasks_persist_outputs(
    tmp_path: Path,
) -> None:
    messages_path = tmp_path / "messages.json"
    args = parse_args(["--messages-path", str(messages_path)])

    async def _exercise() -> None:
        queue: asyncio.Queue[
            tuple[asyncio.StreamReader, asyncio.StreamWriter, asyncio.Event]
        ] = asyncio.Queue()

        async def _handler(
            reader: asyncio.StreamReader, writer: asyncio.StreamWriter
        ) -> None:
            done = asyncio.Event()
            await queue.put((reader, writer, done))
            await done.wait()

        server = await asyncio.start_server(_handler, "127.0.0.1", 0)
        async with server:
            sockets = server.sockets or []
            assert sockets
            host, port = sockets[0].getsockname()[:2]

            async def _drive(subject: str, body: str) -> str:
                client_reader, client_writer = await asyncio.open_connection(
                    host, port
                )
                server_reader, server_writer, done = await queue.get()
                session_task = asyncio.create_task(
                    run_stream_session(args, server_reader, server_writer)
                )
                session_task.add_done_callback(lambda _: done.set())
                try:
                    script = "\r\n".join(
                        [
                            "MB",
                            "P",
                            subject,
                            body,
                            "/send",
                            "Q",
                            "EX",
                            "",
                        ]
                    ).encode("latin-1")
                    client_writer.write(script)
                    await client_writer.drain()
                    with contextlib.suppress(Exception):
                        client_writer.write_eof()
                    transcript = await asyncio.wait_for(
                        client_reader.read(), timeout=5.0
                    )
                    await asyncio.wait_for(session_task, timeout=5.0)
                    return transcript.decode("latin-1", errors="ignore")
                finally:
                    client_writer.close()
                    await client_writer.wait_closed()

            transcripts = await asyncio.gather(
                _drive("Subject One", "Body One"),
                _drive("Subject Two", "Body Two"),
            )
            assert all(transcripts)

    asyncio.run(_exercise())

    stored = load_message_store(messages_path)
    subjects = [record.subject for record in stored.iter_records()]
    bodies = [tuple(record.lines) for record in stored.iter_records()]
    assert {"Subject One", "Subject Two"} <= set(subjects)
    assert ("Body One",) in bodies
    assert ("Body Two",) in bodies
