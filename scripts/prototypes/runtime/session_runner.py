"""High-level driver that bridges :class:`SessionKernel` to CLI input."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from ..device_context import ConsoleService
from ..message_editor import EditorState, Event as MessageEditorEvent
from ..message_editor import MessageEditor, SessionContext
from ..session_kernel import SessionKernel, SessionState
from ..setup_defaults import SetupDefaults
from .file_transfers import FileTransferEvent
from .main_menu import MainMenuModule, MainMenuEvent
from .sysop_options import SysopOptionsEvent


@dataclass(slots=True)
class SessionRunner:
    """Wrapper that feeds textual input into :class:`SessionKernel`."""

    defaults: SetupDefaults = field(default_factory=SetupDefaults.stub)
    main_menu_module: MainMenuModule = field(default_factory=MainMenuModule)
    board_id: str = "main"
    user_id: str = "sysop"
    session_context: SessionContext | None = None

    kernel: SessionKernel = field(init=False)
    console: ConsoleService = field(init=False)
    _editor_context: SessionContext = field(init=False)

    _ENTER_EVENTS: Mapping[SessionState, object] = field(
        init=False,
        default_factory=lambda: {
            SessionState.MAIN_MENU: MainMenuEvent.ENTER,
            SessionState.FILE_TRANSFERS: FileTransferEvent.ENTER,
            SessionState.SYSOP_OPTIONS: SysopOptionsEvent.ENTER,
            SessionState.MESSAGE_EDITOR: MessageEditorEvent.ENTER,
        },
    )
    _COMMAND_EVENTS: Mapping[SessionState, object] = field(
        init=False,
        default_factory=lambda: {
            SessionState.MAIN_MENU: MainMenuEvent.SELECTION,
            SessionState.FILE_TRANSFERS: FileTransferEvent.COMMAND,
            SessionState.SYSOP_OPTIONS: SysopOptionsEvent.COMMAND,
            SessionState.MESSAGE_EDITOR: MessageEditorEvent.COMMAND_SELECTED,
        },
    )

    def __post_init__(self) -> None:
        self.kernel = SessionKernel(module=self.main_menu_module, defaults=self.defaults)
        console = self.kernel.services.get("console")
        if not isinstance(console, ConsoleService):
            raise TypeError("console service missing from session kernel")
        self.console = console
        self._editor_context = (
            self.session_context
            if isinstance(self.session_context, SessionContext)
            else SessionContext(board_id=self.board_id, user_id=self.user_id)
        )
        self._enter_state(self.kernel.state)

    # Public API ---------------------------------------------------------

    @property
    def state(self) -> SessionState:
        """Return the kernel's active :class:`SessionState`."""

        return self.kernel.state

    @property
    def editor_context(self) -> SessionContext:
        """Expose the persistent :class:`SessionContext` used by the editor."""

        return self._editor_context

    def read_output(self) -> str:
        """Flush buffered console output and return it as a string."""

        buffer: list[str] = []
        output = self.console.device.output
        while output:
            buffer.append(output.popleft())
        return "".join(buffer)

    def send_command(self, text: str) -> SessionState:
        """Deliver ``text`` to the active module and propagate transitions."""

        state = self.kernel.state
        if state is SessionState.EXIT:
            return state

        command_event = self._COMMAND_EVENTS.get(state)
        if command_event is None:
            raise ValueError(f"state {state!r} does not accept textual input")

        if state is SessionState.MESSAGE_EDITOR:
            context = self._editor_context
            context.current_message = text
            return self._dispatch(command_event, context)

        return self._dispatch(command_event, text)

    def abort_editor(self) -> SessionState:
        """Request that the message editor abort back to the main menu."""

        if self.kernel.state is not SessionState.MESSAGE_EDITOR:
            raise RuntimeError("abort_editor requires the message editor to be active")
        return self._dispatch(MessageEditorEvent.ABORT, self._editor_context)

    # Internal helpers ---------------------------------------------------

    def _dispatch(self, event: object, *args: object) -> SessionState:
        previous_state = self.kernel.state
        next_state = self.kernel.step(event, *args)
        if next_state is not SessionState.EXIT and next_state is not previous_state:
            self._enter_state(next_state)
        return next_state

    def _enter_state(self, state: SessionState) -> None:
        if state is SessionState.EXIT:
            return

        enter_event = self._ENTER_EVENTS.get(state)
        if enter_event is None:
            return

        if state is SessionState.MESSAGE_EDITOR:
            self._prepare_editor_for_enter()
            self._dispatch(enter_event, self._editor_context)
            return

        self._dispatch(enter_event)

    def _prepare_editor_for_enter(self) -> None:
        module = self.kernel._modules.get(SessionState.MESSAGE_EDITOR)
        if isinstance(module, MessageEditor) and module.state is EditorState.EXIT:
            module.state = EditorState.INTRO


__all__ = ["SessionRunner"]

