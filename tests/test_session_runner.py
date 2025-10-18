import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import SessionRunner, SessionState
from scripts.prototypes.runtime.file_transfers import FileTransfersModule
from scripts.prototypes.runtime.main_menu import MainMenuModule
from scripts.prototypes.runtime.sysop_options import SysopOptionsModule


@pytest.fixture()
def runner() -> SessionRunner:
    return SessionRunner()


def test_session_runner_initialises_and_emits_enter(runner: SessionRunner) -> None:
    kernel = runner.kernel
    assert runner.state is SessionState.MAIN_MENU

    main_menu = kernel._modules[SessionState.MAIN_MENU]
    assert isinstance(main_menu, MainMenuModule)
    assert main_menu.rendered_slots[:4] == [
        main_menu.MENU_HEADER_SLOT,
        main_menu.MENU_PROMPT_SLOT,
        main_menu.MENU_HEADER_SLOT,
        main_menu.MENU_PROMPT_SLOT,
    ]

    flushed = runner.read_output()
    assert isinstance(flushed, str)
    assert runner.read_output() == ""


def test_session_runner_transitions_and_replays_enter(runner: SessionRunner) -> None:
    kernel = runner.kernel
    main_menu = kernel._modules[SessionState.MAIN_MENU]
    file_transfers = kernel._modules[SessionState.FILE_TRANSFERS]
    sysop_options = kernel._modules[SessionState.SYSOP_OPTIONS]

    runner.read_output()  # discard bootstrap output

    state = runner.send_command("UD")
    assert state is SessionState.FILE_TRANSFERS
    assert isinstance(file_transfers, FileTransfersModule)
    assert file_transfers.rendered_slots[:4] == [
        file_transfers.MENU_HEADER_SLOT,
        file_transfers.MENU_PROMPT_SLOT,
        file_transfers.MENU_HEADER_SLOT,
        file_transfers.MENU_PROMPT_SLOT,
    ]

    state = runner.send_command("Q")
    assert state is SessionState.MAIN_MENU
    assert main_menu.rendered_slots[-2:] == [
        main_menu.MENU_HEADER_SLOT,
        main_menu.MENU_PROMPT_SLOT,
    ]

    state = runner.send_command("SY")
    assert state is SessionState.SYSOP_OPTIONS
    assert isinstance(sysop_options, SysopOptionsModule)
    assert sysop_options.rendered_slots[:4] == [
        sysop_options.MENU_HEADER_SLOT,
        sysop_options.MENU_PROMPT_SLOT,
        sysop_options.MENU_HEADER_SLOT,
        sysop_options.MENU_PROMPT_SLOT,
    ]

    state = runner.send_command("Q")
    assert state is SessionState.MAIN_MENU
    assert main_menu.rendered_slots[-2:] == [
        main_menu.MENU_HEADER_SLOT,
        main_menu.MENU_PROMPT_SLOT,
    ]


def test_session_runner_reuses_editor_context(runner: SessionRunner) -> None:
    context = runner.editor_context

    state = runner.send_command("MF")
    assert state is SessionState.MESSAGE_EDITOR
    assert len(context.modem_buffer) >= 1
    assert context.modem_buffer[-1]

    before = len(context.modem_buffer)
    state = runner.send_command("Q")
    assert state is SessionState.MAIN_MENU

    state = runner.send_command("MF")
    assert state is SessionState.MESSAGE_EDITOR
    assert runner.editor_context is context
    assert len(context.modem_buffer) == before + 1
    assert context.modem_buffer[-1]
