from dataclasses import dataclass

from imagebbs.device_context import Console, ConsoleService
from imagebbs.runtime.configuration_editor import (
    ConfigurationEditorEvent,
    ConfigurationEditorModule,
    ConfigurationEditorState,
)
from imagebbs.session_kernel import SessionState


@dataclass
class _KernelStub:
    """Bind a console service so the module can access session wiring."""

    console: ConsoleService

    def __post_init__(self) -> None:
        # Why: Mirror SessionKernel.services lookups for module initialisation.
        self.services = {"console": self.console}


# Why: Provide a real console service so layout helpers can operate normally.
def _build_console() -> ConsoleService:
    console = Console()
    return ConsoleService(console)


# Why: Translate (x, y) coordinates into the corresponding screen address.
def _screen_address(x: int, y: int) -> int:
    return ConsoleService._SCREEN_BASE + (y * ConfigurationEditorModule._SCREEN_WIDTH) + x


# Why: Extract a textual representation of a rendered PETSCII row.
def _read_row(console: ConsoleService, y: int) -> str:
    base = _screen_address(0, y)
    chars: list[str] = []
    for offset in range(ConfigurationEditorModule._SCREEN_WIDTH):
        code = console.screen.peek_screen_address(base + offset) & 0x7F
        chars.append(chr(code))
    return "".join(chars)


# Why: Verify the boot layout mirrors the documented dual-panel configuration.
def test_start_renders_bordered_panels_with_selection() -> None:
    console = _build_console()
    kernel = _KernelStub(console)
    module = ConfigurationEditorModule()

    state = module.start(kernel)  # type: ignore[arg-type]

    assert state is SessionState.CONFIGURATION_EDITOR
    assert module.state is ConfigurationEditorState.INTRO

    top_left = console.screen.peek_screen_address(_screen_address(1, 3))
    right_top = console.screen.peek_screen_address(_screen_address(20, 3))
    assert top_left == module._CHAR_TOP_LEFT
    assert right_top == module._CHAR_TOP_LEFT

    left_entry_address = _screen_address(2, 4)
    left_entry_code = console.screen.peek_screen_address(left_entry_address)
    layout = module._entry_layouts["A"]

    assert left_entry_code & 0x80  # current selection inverted
    assert layout.colours[0] == module._ENTRY_HIGHLIGHT_COLOUR

    prompt_text = _read_row(console, module._PROMPT_ROW)[: len(module._PROMPT)]
    assert prompt_text == module._PROMPT


# Why: Ensure menu selections update highlighting and status feedback.
def test_selection_moves_between_entries_and_updates_status() -> None:
    console = _build_console()
    kernel = _KernelStub(console)
    module = ConfigurationEditorModule()
    module.start(kernel)  # type: ignore[arg-type]

    module.handle_event(kernel, ConfigurationEditorEvent.ENTER)  # type: ignore[arg-type]

    result_state = module.handle_event(
        kernel,  # type: ignore[arg-type]
        ConfigurationEditorEvent.COMMAND,
        "C",
    )

    assert result_state is SessionState.CONFIGURATION_EDITOR
    a_address = _screen_address(2, 4)
    c_address = _screen_address(2, 6)

    a_code = console.screen.peek_screen_address(a_address)
    c_code = console.screen.peek_screen_address(c_address)

    assert not (a_code & 0x80)
    assert c_code & 0x80

    status_text = _read_row(console, module._STATUS_ROW).strip()
    assert status_text.startswith("Credits")
