import argparse
import asyncio
import contextlib
import io
from collections import deque
from dataclasses import replace
import unittest.mock as mock
from pathlib import Path
import types
import typing

import pytest
from imagebbs.runtime.cli import (
    _install_indicator_controller,
    create_runner,
    drive_session,
    parse_args,
    run_session,
    run_stream_session,
    start_session_server,
)
from imagebbs.runtime.editor_submission import (
    DEFAULT_EDITOR_ABORT_COMMAND,
    DEFAULT_EDITOR_SUBMIT_COMMAND,
)
from imagebbs.runtime.message_store_repository import load_message_store
from imagebbs.session_kernel import SessionState
from imagebbs.setup_defaults import (
    DEFAULT_MODEM_BAUD_LIMIT,
    FilesystemDriveLocator,
    IndicatorDefaults,
    SetupDefaults,
)
from imagebbs.device_context import ConsoleService
from imagebbs.message_editor import SessionContext
from imagebbs.runtime.console_ui import IdleTimerScheduler
from imagebbs.runtime.indicator_controller import IndicatorController
from imagebbs.runtime.message_store import MessageStore
from imagebbs.runtime.session_factory import DEFAULT_RUNTIME_SESSION_FACTORY
from imagebbs.runtime.session_instrumentation import SessionInstrumentation
from imagebbs.runtime.session_runner import SessionRunner

# Why: verifies the CLI session loop exits cleanly and surfaces the board banner on startup.
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
    defaults = runner.defaults
    assert transcript.startswith(defaults.board_name)
    segments = transcript.split("\r")
    assert len(segments) >= 3
    assert segments[1] == defaults.prompt
    assert segments[2] == defaults.copyright_notice
    assert args.listen is None
    assert args.connect is None
    assert runner.defaults.modem.baud_limit == DEFAULT_MODEM_BAUD_LIMIT


# Why: ensure paused console output surfaces even if the session exits while paused.
def test_drive_session_flushes_pause_buffer_on_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    class StubInstrumentation:
        def __init__(self, runner: object, **_: object) -> None:
            self.runner = runner

        def ensure_indicator_controller(self) -> None:
            return None

        def reset_idle_timer(self) -> None:
            return None

        def on_idle_cycle(self) -> None:
            return None

    class StubRunner:
        def __init__(self) -> None:
            self.state = SessionState.MAIN_MENU
            self.read_calls = 0
            self.pause_states: list[bool] = []
            self.commands: list[str] = []

        def read_output(self) -> str:
            self.read_calls += 1
            if self.read_calls == 2:
                self.state = SessionState.EXIT
                return "buffered message"
            return ""

        def set_indicator_controller(self, controller: object) -> None:
            # Why: mirror CLI wiring so instrumentation cache detection respects stub state.
            self.controller = controller
            self._indicator_controller = controller

        def set_pause_indicator_state(self, active: bool) -> None:
            self.pause_states.append(active)

        def requires_editor_submission(self) -> bool:
            return False

        def send_command(self, command: str) -> None:
            self.commands.append(command)

    monkeypatch.setattr(
        "imagebbs.runtime.cli.SessionInstrumentation", StubInstrumentation
    )

    runner = StubRunner()
    input_stream = io.StringIO("\x13")
    output_stream = io.StringIO()

    final_state = drive_session(
        runner, input_stream=input_stream, output_stream=output_stream
    )

    assert final_state is SessionState.EXIT
    assert runner.pause_states == [True]
    assert output_stream.getvalue() == "buffered message"


# Why: ensure CLI loops translate abort control bytes into transfer abort requests.
def test_drive_session_routes_abort_control_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    class StubInstrumentation:
        def __init__(self, runner: object, **_: object) -> None:
            self.runner = runner

        # Why: bypass indicator allocation while matching the runtime signature.
        def ensure_indicator_controller(self) -> None:
            return None

        # Why: prevent idle timer setup during the unit test loop.
        def reset_idle_timer(self) -> None:
            return None

        # Why: emulate idle-cycle hooks without performing work.
        def on_idle_cycle(self) -> None:
            return None

    class RecordingAbortService:
        def __init__(self) -> None:
            self.requests: list[bool] = []

        # Why: capture abort toggles issued by the CLI for assertions.
        def request_abort(self, abort: bool = True) -> None:
            self.requests.append(bool(abort))

    abort_service = RecordingAbortService()

    class StubRunner:
        def __init__(self) -> None:
            self.state = SessionState.MAIN_MENU
            self.pause_states: list[bool] = []
            self.commands: list[str] = []
            context = types.SimpleNamespace(
                service_registry={"file_transfer_abort": abort_service}
            )
            self.kernel = types.SimpleNamespace(context=context)

        # Why: surface no console output so the loop relies on commands to exit.
        def read_output(self) -> str:
            return ""

        # Why: record indicator wiring performed by instrumentation.
        def set_indicator_controller(self, controller: object) -> None:
            self.controller = controller
            self._indicator_controller = controller

        # Why: record pause toggles triggered by control tokens for verification.
        def set_pause_indicator_state(self, active: bool) -> None:
            self.pause_states.append(active)

        # Why: avoid editor submission prompts during the loop.
        def requires_editor_submission(self) -> bool:
            return False

        # Why: record commands and request exit so the loop terminates.
        def send_command(self, command: str) -> SessionState:
            self.commands.append(command)
            self.state = SessionState.EXIT
            return self.state

    monkeypatch.setattr(
        "imagebbs.runtime.cli.SessionInstrumentation", StubInstrumentation
    )

    runner = StubRunner()
    input_stream = io.StringIO("\x18HELLO\n")
    output_stream = io.StringIO()

    final_state = drive_session(
        runner, input_stream=input_stream, output_stream=output_stream
    )

    assert final_state is SessionState.EXIT
    assert runner.commands == ["HELLO"]
    assert abort_service.requests == [True]


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
    assert args.editor_submit_command == DEFAULT_EDITOR_SUBMIT_COMMAND
    assert args.editor_abort_command == DEFAULT_EDITOR_ABORT_COMMAND
    assert args.board_id is None
    assert args.user_id is None
    assert args.telnet_newline == "crlf"


def test_parse_args_console_flag_disables_curses_ui() -> None:
    args = parse_args(["--console-ui"])

    assert args.curses_ui is False


def test_parse_args_accepts_editor_command_overrides() -> None:
    args = parse_args(
        [
            "--editor-submit-command",
            "/save",
            "--editor-abort-command",
            "/cancel",
            "--board-id",
            "custom-board",
            "--user-id",
            "custom-user",
        ]
    )

    assert args.editor_submit_command == "/save"
    assert args.editor_abort_command == "/cancel"
    assert args.board_id == "custom-board"
    assert args.user_id == "custom-user"


def test_parse_args_accepts_telnet_newline_choice() -> None:
    args = parse_args(["--telnet-newline", "none"])

    assert args.telnet_newline == "none"


def test_parse_args_rejects_invalid_telnet_newline() -> None:
    with pytest.raises(SystemExit):
        parse_args(["--telnet-newline", "cr"])


# Why: confirm operators can tune Telnet polling cadence and observe defaults.
def test_parse_args_telnet_poll_interval_default_and_override() -> None:
    args = parse_args([])

    assert args.telnet_poll_interval == pytest.approx(0.02)

    custom = parse_args(["--telnet-poll-interval", "0.1"])

    assert custom.telnet_poll_interval == pytest.approx(0.1)


# Why: expose indicator overrides so operators can align console palettes with host expectations.
def test_parse_args_indicator_colour_and_frames_overrides() -> None:
    args = parse_args(
        [
            "--indicator-pause-colour",
            "0x0e",
            "--indicator-abort-colour",
            "7",
            "--indicator-spinner-colour",
            "15",
            "--indicator-carrier-leading-colour",
            "0x92",
            "--indicator-carrier-indicator-colour",
            "145",
            "--indicator-spinner-frames",
            "0xb0,0xb1,178",
        ]
    )

    assert args.indicator_pause_colour == 0x0E
    assert args.indicator_abort_colour == 7
    assert args.indicator_spinner_colour == 15
    assert args.indicator_carrier_leading_colour == 0x92
    assert args.indicator_carrier_indicator_colour == 145
    assert args.indicator_spinner_frames == (0xB0, 0xB1, 178)


# Why: reject out-of-range indicator overrides so invalid palettes fail fast.
def test_parse_args_indicator_colour_rejects_out_of_range() -> None:
    with pytest.raises(SystemExit):
        parse_args(["--indicator-pause-colour", "256"])


# Why: guard spinner parsing against malformed entries so runtime controllers see valid sequences.
def test_parse_args_indicator_spinner_frames_rejects_gaps() -> None:
    with pytest.raises(SystemExit):
        parse_args(["--indicator-spinner-frames", "0xb0,,0xb1"])


# Why: ensure CLI indicator overrides propagate into instrumentation controller wiring.
def test_cli_indicator_overrides_reach_indicator_controller() -> None:
    args = parse_args(
        [
            "--indicator-pause-colour",
            "1",
            "--indicator-abort-colour",
            "2",
            "--indicator-spinner-colour",
            "3",
            "--indicator-carrier-leading-colour",
            "4",
            "--indicator-carrier-indicator-colour",
            "5",
            "--indicator-spinner-frames",
            "6,7,8",
        ]
    )
    runner = create_runner(args)

    captured_kwargs: dict[str, object] = {}

    class RecordingIndicator:
        def __init__(self, console: object, **kwargs: object) -> None:
            self.console = console
            self.kwargs = dict(kwargs)
            captured_kwargs.update(kwargs)

        def sync_from_console(self) -> None:
            return None

    instrumentation = SessionInstrumentation(
        runner, indicator_controller_cls=RecordingIndicator
    )

    controller = instrumentation.ensure_indicator_controller()

    assert isinstance(controller, RecordingIndicator)
    assert captured_kwargs == {
        "pause_colour": 1,
        "abort_colour": 2,
        "spinner_colour": 3,
        "carrier_leading_colour": 4,
        "carrier_indicator_colour": 5,
        "spinner_frames": (6, 7, 8),
    }


def test_run_stream_session_honours_telnet_newline_setting() -> None:
    args = parse_args(["--telnet-newline", "lf"])

    class StubRunner:
        def __init__(self) -> None:
            modem_defaults = types.SimpleNamespace(baud_limit=None)
            self.defaults = types.SimpleNamespace(modem=modem_defaults)
            context = types.SimpleNamespace()
            context.register_modem_device = mock.Mock()
            kernel = types.SimpleNamespace(context=context)
            self.kernel = kernel
            self.console = object()

        def set_indicator_controller(self, controller: object) -> None:
            # Why: emulate runner bookkeeping so instrumentation comparisons observe telnet wiring.
            self._indicator_controller = controller

        def read_output(self) -> str:
            return ""

    class StubInstrumentation:
        def __init__(self, runner: StubRunner, **_: object) -> None:
            self.runner = runner

        def ensure_indicator_controller(self) -> None:
            return None

    class RecordingTelnetTransport:
        instances: list["RecordingTelnetTransport"] = []

        def __init__(
            self,
            runner: StubRunner,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            *,
            instrumentation: StubInstrumentation,
            poll_interval: float = 0.02,
            idle_timer_scheduler_cls: type[IdleTimerScheduler] | None = None,
            idle_tick_interval: float = 1.0,
            editor_submit_command: str,
            editor_abort_command: str,
            newline_translation: str | None,
        ) -> None:
            # Why: mirror the production transport signature for newline translation tests.
            self.runner = runner
            self.reader = reader
            self.writer = writer
            self.instrumentation = instrumentation
            self.poll_interval = poll_interval
            self.idle_timer_scheduler_cls = idle_timer_scheduler_cls
            self.idle_tick_interval = idle_tick_interval
            self.editor_submit_command = editor_submit_command
            self.editor_abort_command = editor_abort_command
            self.newline_translation = newline_translation
            self.open_calls = 0
            self.close_calls = 0
            RecordingTelnetTransport.instances.append(self)

        def open(self) -> None:
            self.open_calls += 1

        async def wait_closed(self) -> None:
            return None

        def close(self) -> None:
            self.close_calls += 1

    @contextlib.asynccontextmanager
    async def _stub_async_runner(*_: object, **__: object) -> typing.Iterator[StubRunner]:
        runner = StubRunner()
        yield runner

    class _StubReader:
        pass

    class _StubWriter:
        def __init__(self) -> None:
            self.closed = False

        def write(self, data: bytes) -> None:
            pass

        async def drain(self) -> None:
            return None

        def close(self) -> None:
            self.closed = True

        async def wait_closed(self) -> None:
            return None

        def is_closing(self) -> bool:
            return self.closed

    reader = typing.cast(asyncio.StreamReader, _StubReader())
    writer = _StubWriter()

    with mock.patch(
        "imagebbs.runtime.cli._async_runner_with_persistence",
        _stub_async_runner,
    ), mock.patch(
        "imagebbs.runtime.cli.SessionInstrumentation",
        StubInstrumentation,
    ), mock.patch(
        "imagebbs.runtime.cli.TelnetModemTransport",
        RecordingTelnetTransport,
    ):
        asyncio.run(
            run_stream_session(
                args,
                reader,
                typing.cast(asyncio.StreamWriter, writer),
            )
        )

    assert RecordingTelnetTransport.instances
    telnet = RecordingTelnetTransport.instances[0]
    assert telnet.newline_translation == "\n"
    assert telnet.poll_interval == args.telnet_poll_interval



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
            "--board-id",
            "test-board",
            "--user-id",
            "test-user",
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
    assert runner.editor_context.board_id == "test-board"
    assert runner.editor_context.user_id == "test-user"
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
        # Why: coordinate the telnet negotiation and banner readback for a served session.
        expected_runner = create_runner(args)
        banner_text = expected_runner.read_output()
        translation_map = {"crlf": "\r\n", "lf": "\n", "none": None}
        translation = translation_map[args.telnet_newline]
        if translation is None:
            expected_banner = banner_text.encode("latin-1")
        else:
            normalized = banner_text.replace("\r\n", "\n")
            expected_banner = normalized.replace("\n", translation).encode("latin-1")

        negotiation_frames = [
            bytes([0xFF, 0xFB, 0x01]),
            bytes([0xFF, 0xFB, 0x03]),
            bytes([0xFF, 0xFD, 0x03]),
            bytes([0xFF, 0xFD, 0x00]),
            bytes([0xFF, 0xFB, 0x00]),
        ]
        expected_negotiation = b"".join(negotiation_frames)

        server = await start_session_server(args, "127.0.0.1", 0)
        sockets = server.sockets or []
        assert sockets
        host, port = sockets[0].getsockname()[:2]

        reader, writer = await asyncio.open_connection(host, port)
        try:
            negotiation = await asyncio.wait_for(
                reader.readexactly(len(expected_negotiation)), timeout=1.0
            )
            assert negotiation == expected_negotiation

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


def test_drive_session_uses_custom_editor_commands() -> None:
    args = parse_args(
        [
            "--editor-submit-command",
            "/save",
            "--editor-abort-command",
            "/cancel",
        ]
    )
    runner = create_runner(args)

    script = "MB\nP\nCustom Subject\nCustom body\n/save\nQ\nEX\n"
    input_stream = io.StringIO(script)
    output_stream = io.StringIO()

    final_state = drive_session(
        runner,
        input_stream=input_stream,
        output_stream=output_stream,
        editor_submit_command=args.editor_submit_command,
        editor_abort_command=args.editor_abort_command,
    )

    assert final_state is SessionState.EXIT
    transcript = output_stream.getvalue()
    assert "Type /save to save or /cancel to cancel." in transcript

    records = list(runner.message_store.iter_records())
    assert len(records) == 1
    record = records[0]
    assert record.subject == "Custom Subject"
    assert record.lines == ("Custom body",)


def test_run_session_pauses_and_flushes_output_on_flow_control() -> None:
    class RecordingIndicatorController:
        def __init__(self, console: ConsoleService, **kwargs) -> None:
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
        def __init__(
            self,
            console: ConsoleService,
            *,
            idle_tick_interval: float = 1.0,
        ) -> None:
            # Why: expose counters so the test can assert idle loop interactions.
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
            # Why: retain instrumentation controllers so pause propagation can be asserted.
            self.indicator_controller = controller
            self._indicator_controller = controller

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
        def __init__(
            self,
            console: ConsoleService,
            *,
            idle_tick_interval: float = 1.0,
        ) -> None:
            # Why: wrap the concrete scheduler so tests can inject a deterministic clock.
            super().__init__(
                console,
                idle_tick_interval=idle_tick_interval,
                time_source=fake_clock,
            )

    class RecordingIndicatorController(IndicatorController):
        def __init__(self, console: ConsoleService, **kwargs):
            super().__init__(console, **kwargs)
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
    assert spinner_bytes[0] == 0xB3

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

        def __init__(self, console: ConsoleService, **kwargs) -> None:
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


def test_main_installs_indicator_controller_for_curses_ui() -> None:
    from imagebbs.runtime import cli as runtime_cli

    indicator_instances: list[object] = []
    app_instances: list["RecordingConsoleApp"] = []
    instrumentation_instances: list["RecordingInstrumentation"] = []

    class RecordingIndicator:
        def __init__(self, console: object, **kwargs) -> None:
            self.console = console
            self.sync_calls = 0
            indicator_instances.append(self)

        def sync_from_console(self) -> None:
            self.sync_calls += 1

    class RecordingContext:
        def __init__(self) -> None:
            self.services: dict[str, object] = {}

        def register_service(self, name: str, service: object) -> None:
            self.services[name] = service

    class RecordingKernel:
        def __init__(self) -> None:
            self.context = RecordingContext()

    class RecordingRunner:
        def __init__(self) -> None:
            self.console = object()
            self.kernel = RecordingKernel()
            self.state = SessionState.MAIN_MENU
            self._indicator_controller: object | None = None
            self.set_indicator_calls: list[object] = []

        def set_indicator_controller(self, controller: object) -> None:
            self._indicator_controller = controller
            self.set_indicator_calls.append(controller)

    class RecordingInstrumentation:
        def __init__(
            self,
            runner: RecordingRunner,
            *,
            indicator_controller_cls,
            idle_timer_scheduler_cls,
            idle_tick_interval: float = 1.0,
        ) -> None:
            # Why: capture instrumentation wiring while tolerating optional idle cadence overrides.
            self.runner = runner
            self.indicator_controller_cls = indicator_controller_cls
            self.idle_timer_scheduler_cls = idle_timer_scheduler_cls
            self.idle_tick_interval = idle_tick_interval
            self.ensure_calls = 0
            self.reset_calls = 0
            self.indicator_controller: object | None = None
            instrumentation_instances.append(self)

        def ensure_indicator_controller(self) -> object | None:
            self.ensure_calls += 1
            controller = getattr(self.runner, "_indicator_controller", None)
            self.indicator_controller = controller
            return controller

        def reset_idle_timer(self) -> None:
            self.reset_calls += 1

    class RecordingConsoleApp:
        def __init__(
            self,
            console: object,
            *,
            runner: RecordingRunner,
            instrumentation: RecordingInstrumentation,
        ) -> None:
            self.console = console
            self.runner = runner
            self.instrumentation = instrumentation
            self.run_calls = 0
            app_instances.append(self)

        def run(self) -> None:
            self.run_calls += 1

    runner = RecordingRunner()

    class _RunnerContextManager:
        def __enter__(self) -> RecordingRunner:
            return runner

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    def _fake_runner_with_persistence(*args, **kwargs):
        return _RunnerContextManager()

    with mock.patch.object(
        runtime_cli, "_runner_with_persistence", _fake_runner_with_persistence
    ), mock.patch.object(
        runtime_cli,
        "_resolve_indicator_controller_cls",
        return_value=RecordingIndicator,
    ), mock.patch.object(
        runtime_cli, "SessionInstrumentation", RecordingInstrumentation
    ), mock.patch.object(runtime_cli, "SysopConsoleApp", RecordingConsoleApp):
        exit_code = runtime_cli.main([])

    assert exit_code == 0
    assert len(indicator_instances) == 1
    indicator = indicator_instances[0]
    assert getattr(indicator, "sync_calls", 0) == 1
    assert runner.set_indicator_calls == [indicator]
    assert runner.kernel.context.services == {"indicator_controller": indicator}
    assert instrumentation_instances
    instrumentation = instrumentation_instances[0]
    assert instrumentation.indicator_controller is indicator
    assert instrumentation.ensure_calls == 1
    assert instrumentation.reset_calls == 1
    assert app_instances
    assert app_instances[0].run_calls == 1


def test_install_indicator_controller_applies_indicator_overrides() -> None:
    overrides = IndicatorDefaults(
        pause_colour=5,
        abort_colour=6,
        spinner_colour=7,
        carrier_leading_colour=8,
        carrier_indicator_colour=9,
        spinner_frames=(0xAA, 0xAB),
    )
    runner = SessionRunner(defaults=replace(SetupDefaults.stub(), indicator=overrides))

    recorded: dict[str, dict[str, object]] = {}

    class RecordingIndicator(IndicatorController):
        def __init__(self, console: ConsoleService, **kwargs) -> None:
            recorded["kwargs"] = dict(kwargs)
            super().__init__(console, **kwargs)

    controller = _install_indicator_controller(runner, RecordingIndicator)
    assert controller is not None
    assert recorded["kwargs"] == overrides.controller_kwargs()
    assert controller.pause_colour == overrides.pause_colour
    assert controller.abort_colour == overrides.abort_colour
    assert controller.spinner_colour == overrides.spinner_colour
    assert controller.spinner_frames == overrides.spinner_frames


def test_run_stream_session_bridges_telnet_and_persists_messages(tmp_path: Path) -> None:
    messages_path = tmp_path / "messages.json"
    args = parse_args(
        [
            "--messages-path",
            str(messages_path),
            "--editor-submit-command",
            "/save",
            "--editor-abort-command",
            "/cancel",
            "--board-id",
            "async-board",
            "--user-id",
            "async-user",
        ]
    )

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
            args: argparse.Namespace | None = None,
        ) -> SessionContext:
            return self._delegate.build_session_context(
                defaults,
                store=store,
                messages_path=messages_path,
                args=args,
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

        def __init__(self, console: ConsoleService, **kwargs) -> None:
            super().__init__(console, **kwargs)
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
            b"/save\r\n",
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
    assert "Type /save to save or /cancel to cancel." in transcript

    runners = recording_factory.runners
    assert len(runners) == 1
    runner = runners[0]
    assert runner.editor_context.board_id == "async-board"
    assert runner.editor_context.user_id == "async-user"

    records = list(runner.message_store.iter_records())
    assert len(records) == 1
    record = records[0]
    assert record.subject == "Async Subject"
    assert record.lines == ("Async Body",)

    assert len(recording_factory.persist_calls) == 1
    persist_args, persisted_runner = recording_factory.persist_calls[0]
    assert persist_args.board_id == "async-board"
    assert persist_args.user_id == "async-user"
    assert persisted_runner is runner
    services = runner.editor_context.services
    assert services is not None
    assert services.get("message_store_persistence") == {"path": messages_path}
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
