import io
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.runtime.cli import create_runner, parse_args, run_session
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

    load_path = tmp_path / "messages.json"
    save_path = tmp_path / "messages.out.json"

    args = parse_args(
        [
            "--drive-config",
            str(config_path),
            "--message-store-load",
            str(load_path),
            "--message-store-save",
            str(save_path),
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
    assert options == {"load_path": load_path, "save_path": save_path}
    assert runner.editor_context.board_id
    assert runner.editor_context.user_id
