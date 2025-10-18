import asyncio
import io
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.runtime.cli import (
    create_runner,
    parse_args,
    run_session,
    start_session_server,
)
from scripts.prototypes.session_kernel import SessionState
from scripts.prototypes.setup_defaults import FilesystemDriveLocator


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
    assert args.listen is None
    assert args.connect is None


def test_create_runner_applies_configuration_and_persistence(tmp_path: Path) -> None:
    config_path = tmp_path / "drives.toml"
    config_path.write_text(
        "\n".join(
            [
                "[slots]",
                '1 = "."',
                "[ampersand_overrides]",
                '1 = "scripts.prototypes.runtime.ampersand_overrides:handle_chkflags"',
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
        1: "scripts.prototypes.runtime.ampersand_overrides:handle_chkflags"
    }

    services = runner.editor_context.services
    assert services is not None
    options = services.get("message_store_persistence")
    assert options == {"path": messages_path}
    assert runner.editor_context.board_id
    assert runner.editor_context.user_id
    assert runner.message_store_path == messages_path
    assert runner.editor_context.store is runner.message_store


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
