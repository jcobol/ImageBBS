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


# Why: drain console output so tests can assert against fresh transcripts.
def _read_output(console: ConsoleService) -> str:
    device = console.device
    chunks: list[str] = []
    while device.output:
        chunks.append(device.output.popleft())
    return "".join(chunks)


# Why: ensure initial renders mirror the documented layout and prompt behaviour.
def test_configuration_editor_renders_menu_on_start_and_enter() -> None:
    kernel, module = _bootstrap_kernel()
    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)

    transcript = _read_output(console)
    assert "IMAGE BBS CONFIGURATION EDITOR\r" in transcript
    assert "A. Macros Editor" in transcript
    assert "H. Lightbar/Alarm" in transcript
    assert transcript.rstrip().endswith("CONFIG>")

    state = kernel.step(ConfigurationEditorEvent.ENTER)
    assert state is SessionState.CONFIGURATION_EDITOR
    assert module.state is ConfigurationEditorState.READY

    transcript = _read_output(console)
    assert "IMAGE BBS CONFIGURATION EDITOR\r" in transcript
    assert transcript.rstrip().endswith("CONFIG>")


# Why: confirm valid selections update module state and echo placeholder messaging.
def test_configuration_editor_valid_command_records_selection() -> None:
    kernel, module = _bootstrap_kernel()
    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)
    _read_output(console)

    kernel.step(ConfigurationEditorEvent.ENTER)
    _read_output(console)

    state = kernel.step(ConfigurationEditorEvent.COMMAND, "a")

    assert state is SessionState.CONFIGURATION_EDITOR
    assert module.last_selection == "A"

    transcript = _read_output(console)
    assert "Macros Editor module is not yet implemented." in transcript
    assert transcript.rstrip().endswith("CONFIG>")


# Why: verify the quit command returns callers to the main menu state.
def test_configuration_editor_quit_returns_to_main_menu() -> None:
    kernel, module = _bootstrap_kernel()
    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)
    _read_output(console)

    kernel.step(ConfigurationEditorEvent.ENTER)
    _read_output(console)

    state = kernel.step(ConfigurationEditorEvent.COMMAND, "n")

    assert state is SessionState.MAIN_MENU
    assert module.last_selection == "N"

    transcript = _read_output(console)
    assert "Leaving configuration editor" in transcript


# Why: confirm unrecognised commands leave the module active and render an error.
def test_configuration_editor_rejects_unknown_commands() -> None:
    kernel, _module = _bootstrap_kernel()
    console = kernel.services["console"]
    assert isinstance(console, ConsoleService)
    _read_output(console)

    kernel.step(ConfigurationEditorEvent.ENTER)
    _read_output(console)

    state = kernel.step(ConfigurationEditorEvent.COMMAND, "?")

    assert state is SessionState.CONFIGURATION_EDITOR

    transcript = _read_output(console)
    assert "?INVALID CONFIGURATION COMMAND" in transcript
    assert transcript.rstrip().endswith("CONFIG>")
