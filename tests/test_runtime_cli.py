import asyncio
import io
import unittest.mock as mock
from pathlib import Path

from imagebbs.runtime.cli import (
    create_runner,
    parse_args,
    run_session,
    start_session_server,
)
from imagebbs.session_kernel import SessionState
from imagebbs.setup_defaults import (
    DEFAULT_MODEM_BAUD_LIMIT,
    FilesystemDriveLocator,
)
from imagebbs.device_context import ConsoleService
from imagebbs.runtime.console_ui import IdleTimerScheduler
from imagebbs.runtime.indicator_controller import IndicatorController


def test_run_session_handles_exit_sequence() -> None:
    args = parse_args([])
    runner = create_runner(args)

    input_stream = io.StringIO("EX\n")
    output_stream = io.StringIO()

    final_state = run_session(
        runner, input_stream=input_stream, output_stream=output_stream
    )

    assert final_state is SessionState.EXIT
    transcript = output_stream.getvalue()
    assert transcript
    assert transcript.isascii()
    assert args.listen is None
    assert args.connect is None
    assert runner.defaults.modem.baud_limit == DEFAULT_MODEM_BAUD_LIMIT


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

    final_state = run_session(
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
        final_state = run_session(
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
        final_state = run_session(
            runner, input_stream=input_stream, output_stream=output_stream
        )

    assert final_state is SessionState.EXIT
    indicator = RecordingIndicator.instance
    assert indicator is not None
    assert indicator.pause_states == [True, False]


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

    final_state = run_session(
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

    final_state = run_session(
        runner, input_stream=input_stream, output_stream=output_stream
    )

    assert final_state is SessionState.EXIT
    assert list(runner.message_store.iter_records()) == []
    assert runner.editor_context.draft_buffer == []
    assert runner.editor_context.drafts == {}
