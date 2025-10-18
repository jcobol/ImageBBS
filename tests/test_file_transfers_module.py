from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import SessionKernel, SessionState
from scripts.prototypes.device_context import ConsoleService
from scripts.prototypes.runtime.file_transfers import (
    FileTransferEvent,
    FileTransferMenuState,
    FileTransfersModule,
)


def _bootstrap_kernel() -> tuple[SessionKernel, FileTransfersModule]:
    module = FileTransfersModule()
    kernel = SessionKernel(module=module)
    return kernel, module


def test_file_transfers_renders_macros_on_start_and_enter() -> None:
    kernel, module = _bootstrap_kernel()

    assert module.registry is kernel.dispatcher.registry

    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    assert module.rendered_slots[:2] == [
        module.MENU_HEADER_SLOT,
        module.MENU_PROMPT_SLOT,
    ]

    state = kernel.step(FileTransferEvent.ENTER)

    assert state is SessionState.FILE_TRANSFERS
    assert module.state is FileTransferMenuState.READY
    assert module.rendered_slots[-2:] == [
        module.MENU_HEADER_SLOT,
        module.MENU_PROMPT_SLOT,
    ]


def test_file_transfers_accepts_known_command() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(FileTransferEvent.ENTER)

    state = kernel.step(FileTransferEvent.COMMAND, " ud ")

    assert state is SessionState.FILE_TRANSFERS
    assert module.last_command == "UD"
    assert module.rendered_slots[-1] == module.MENU_PROMPT_SLOT


def test_file_transfers_rejects_unknown_command() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(FileTransferEvent.ENTER)
    module.rendered_slots.clear()

    state = kernel.step(FileTransferEvent.COMMAND, "??")

    assert state is SessionState.FILE_TRANSFERS
    assert module.rendered_slots[-2:] == [
        module.INVALID_SELECTION_SLOT,
        module.MENU_PROMPT_SLOT,
    ]


def test_file_transfers_exit_returns_to_main_menu() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(FileTransferEvent.ENTER)

    state = kernel.step(FileTransferEvent.COMMAND, "q")

    assert state is SessionState.MAIN_MENU
    assert kernel.state is SessionState.MAIN_MENU
    assert module.last_command == "Q"

