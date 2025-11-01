from __future__ import annotations

from imagebbs.device_context import ConsoleService
from imagebbs.runtime.configuration_editor import (
    ConfigurationEditorEvent,
    ConfigurationEditorModule,
    ConfigurationEditorState,
)
from imagebbs.session_kernel import SessionKernel, SessionState


# Why: provide a consistent kernel/module pair for configuration-editor tests.
def _bootstrap_kernel() -> tuple[SessionKernel, ConfigurationEditorModule]:
    module = ConfigurationEditorModule()
    kernel = SessionKernel(module=module)
    return kernel, module


# Why: translate PETSCII rows into ASCII strings for assertions.
def _read_row(console: ConsoleService, row: int) -> str:
    base = ConsoleService._SCREEN_BASE + row * ConfigurationEditorModule._SCREEN_WIDTH
    chars: list[str] = []
    for offset in range(ConfigurationEditorModule._SCREEN_WIDTH):
        code = console.screen.peek_screen_address(base + offset) & 0x7F
        chars.append(chr(code))
    return "".join(chars)


# Why: ensure initial renders mirror the documented layout and prompt behaviour.
def test_configuration_editor_renders_menu_on_start_and_enter() -> None:
    kernel, module = _bootstrap_kernel()
    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)

    title_row = _read_row(console, 0)
    prompt_row = _read_row(console, module._PROMPT_ROW)
    left_entry_row = _read_row(console, module._PANEL_Y + 1)
    right_entry_row = _read_row(console, module._PANEL_Y + 1)

    assert "IMAGE BBS CONFIGURATION EDITOR" in title_row
    assert "A) MACROS EDITOR" in left_entry_row
    assert "H) LIGHTBAR/ALARM" in right_entry_row
    assert prompt_row.startswith(module._PROMPT)

    state = kernel.step(ConfigurationEditorEvent.ENTER)
    assert state is SessionState.CONFIGURATION_EDITOR
    assert module.state is ConfigurationEditorState.READY

    prompt_row = _read_row(console, module._PROMPT_ROW)
    assert prompt_row.startswith(module._PROMPT)


# Why: confirm valid selections update module state and echo placeholder messaging.
def test_configuration_editor_valid_command_records_selection() -> None:
    kernel, module = _bootstrap_kernel()
    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)

    kernel.step(ConfigurationEditorEvent.ENTER)

    state = kernel.step(ConfigurationEditorEvent.COMMAND, "a")

    assert state is SessionState.CONFIGURATION_EDITOR
    assert module.last_selection == "A"

    status_row = _read_row(console, module._STATUS_ROW)
    prompt_row = _read_row(console, module._PROMPT_ROW)
    assert status_row.strip().startswith("Macros Editor module is not yet imple")
    assert prompt_row.startswith(module._PROMPT)


# Why: verify the quit command returns callers to the main menu state.
def test_configuration_editor_quit_returns_to_main_menu() -> None:
    kernel, module = _bootstrap_kernel()
    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)

    kernel.step(ConfigurationEditorEvent.ENTER)

    state = kernel.step(ConfigurationEditorEvent.COMMAND, "n")

    assert state is SessionState.MAIN_MENU
    assert module.last_selection == "N"

    status_row = _read_row(console, module._STATUS_ROW)
    assert "Leaving configuration editor" in status_row


# Why: confirm unrecognised commands leave the module active and render an error.
def test_configuration_editor_rejects_unknown_commands() -> None:
    kernel, module = _bootstrap_kernel()
    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)

    kernel.step(ConfigurationEditorEvent.ENTER)

    state = kernel.step(ConfigurationEditorEvent.COMMAND, "?")

    assert state is SessionState.CONFIGURATION_EDITOR

    status_row = _read_row(console, module._STATUS_ROW)
    prompt_row = _read_row(console, module._PROMPT_ROW)
    assert status_row.strip().startswith("?INVALID CONFIGURATION COMMAND")
    assert prompt_row.startswith(module._PROMPT)
