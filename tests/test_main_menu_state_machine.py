import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import MessageEditor, SessionKernel, SessionState
from scripts.prototypes.runtime.main_menu import MainMenuEvent, MainMenuModule


def _bootstrap_kernel() -> tuple[SessionKernel, MainMenuModule]:
    module = MainMenuModule()
    kernel = SessionKernel(module=module)
    return kernel, module


def test_main_menu_renders_macros_on_start_and_enter() -> None:
    kernel, module = _bootstrap_kernel()

    assert module.rendered_slots[:2] == [
        module.MENU_HEADER_SLOT,
        module.MENU_PROMPT_SLOT,
    ]

    state = kernel.step(MainMenuEvent.ENTER)
    assert state is SessionState.MAIN_MENU
    assert module.rendered_slots[-2:] == [
        module.MENU_HEADER_SLOT,
        module.MENU_PROMPT_SLOT,
    ]


def test_main_menu_routes_to_message_editor() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(MainMenuEvent.ENTER)

    state = kernel.step(MainMenuEvent.SELECTION, "MF")

    assert state is SessionState.MESSAGE_EDITOR
    assert isinstance(kernel.module, MessageEditor)
    assert module.rendered_slots.count(module.MENU_PROMPT_SLOT) >= 2


def test_main_menu_routes_to_file_transfers() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(MainMenuEvent.ENTER)

    state = kernel.step(MainMenuEvent.SELECTION, "UD")

    assert state is SessionState.FILE_TRANSFERS
    assert module.rendered_slots[0] == module.MENU_HEADER_SLOT


def test_main_menu_routes_to_sysop_options() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(MainMenuEvent.ENTER)

    state = kernel.step(MainMenuEvent.SELECTION, "SY")

    assert state is SessionState.SYSOP_OPTIONS
    assert module.rendered_slots[0] == module.MENU_HEADER_SLOT


def test_main_menu_invalid_selection_renders_error_macro() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(MainMenuEvent.ENTER)
    module.rendered_slots.clear()

    state = kernel.step(MainMenuEvent.SELECTION, "??")

    assert state is SessionState.MAIN_MENU
    assert module.rendered_slots == [module.INVALID_SELECTION_SLOT]
