"""Runtime session runner that integrates the concrete main-menu module."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

from ..device_context import ConsoleService
from ..message_editor import EditorState, Event as MessageEditorEvent
from ..message_editor import MessageEditor, SessionContext
from ..session_kernel import SessionKernel, SessionState
from ..setup_defaults import IndicatorDefaults, SetupDefaults
from .configuration_editor import ConfigurationEditorEvent
from .file_library import FileLibraryEvent
from .file_transfers import FileTransferEvent
from .main_menu import MainMenuEvent, MainMenuModule
from .message_store import MessageStore
from .message_store_repository import save_message_store
from .sysop_options import SysopOptionsEvent


# Why: capture parsed dot-command submissions so message composition inputs can be normalised before dispatching events.
@dataclass(slots=True)
class _CompositionInput:
    command: str | None
    subject: str
    lines: list[str]

# Why: mirror overlay glyphs so console fallbacks preserve ImageBBS indicator semantics.
from .indicator_controller import (
    IndicatorController,
    _ABORT_GLYPH,
    _PAUSE_GLYPH,
    _SPACE_GLYPH,
)


@dataclass(slots=True)
class SessionRunner:
    """Wrapper that feeds textual input into :class:`SessionKernel`."""

    defaults: SetupDefaults = field(default_factory=SetupDefaults.stub)
    main_menu_module: MainMenuModule = field(default_factory=MainMenuModule)
    board_id: str = "main"
    user_id: str = "sysop"
    session_context: SessionContext | None = None
    message_store: MessageStore = field(default_factory=MessageStore)
    message_store_path: Path | None = None

    kernel: SessionKernel = field(init=False)
    console: ConsoleService = field(init=False)
    _editor_context: SessionContext = field(init=False)
    _editor_module: MessageEditor | None = field(init=False, default=None)
    _indicator_controller: "IndicatorController" | None = field(
        init=False, default=None, repr=False
    )
    _initial_message_keys: set[tuple[str, int]] = field(init=False, repr=False)
    _dirty: bool = field(init=False, default=False, repr=False)

    _ENTER_EVENTS: Mapping[SessionState, object] = field(
        init=False,
        default_factory=lambda: {
            SessionState.MAIN_MENU: MainMenuEvent.ENTER,
            SessionState.FILE_TRANSFERS: FileTransferEvent.ENTER,
            SessionState.FILE_LIBRARY: FileLibraryEvent.ENTER,
            SessionState.SYSOP_OPTIONS: SysopOptionsEvent.ENTER,
            SessionState.MESSAGE_EDITOR: MessageEditorEvent.ENTER,
            SessionState.CONFIGURATION_EDITOR: ConfigurationEditorEvent.ENTER,
        },
    )
    _COMMAND_EVENTS: Mapping[SessionState, object] = field(
        init=False,
        default_factory=lambda: {
            SessionState.MAIN_MENU: MainMenuEvent.SELECTION,
            SessionState.FILE_TRANSFERS: FileTransferEvent.COMMAND,
            SessionState.FILE_LIBRARY: FileLibraryEvent.COMMAND,
            SessionState.SYSOP_OPTIONS: SysopOptionsEvent.COMMAND,
            SessionState.MESSAGE_EDITOR: MessageEditorEvent.COMMAND_SELECTED,
            SessionState.CONFIGURATION_EDITOR: ConfigurationEditorEvent.COMMAND,
        },
    )

    # Why: configure the kernel dependencies and advertise board identity before processing state transitions.
    def __post_init__(self) -> None:
        if (
            getattr(self.main_menu_module, "message_editor_factory", None)
            is MessageEditor
        ):
            self.main_menu_module.message_editor_factory = (
                lambda store=self.message_store: MessageEditor(store=store)
            )
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
        self._editor_context.store = self.message_store
        banner_strings: list[str] = [
            f"{line}\r"
            for line in (
                self.defaults.board_name,
                self.defaults.prompt,
                self.defaults.copyright_notice,
            )
            if line
        ]
        if banner_strings:
            device = self.console.device
            banner_bytes = [
                payload.encode("latin-1", errors="replace")
                for payload in banner_strings
            ]
            for payload in banner_strings:
                device.write(payload)
            output_buffer = device.output
            moved: list[str] = []
            for _ in banner_strings:
                if not output_buffer:
                    break
                moved.append(output_buffer.pop())
            for payload in moved:
                output_buffer.appendleft(payload)
            byte_count = sum(len(chunk) for chunk in banner_bytes)
            if byte_count:
                transcript = device._transcript  # noqa: SLF001 - internal reordering
                tail = transcript[-byte_count:]
                del transcript[-byte_count:]
                transcript[:0] = tail
        self._initial_message_keys: set[tuple[str, int]] = {
            (record.board_id, record.message_id)
            for record in self.message_store.iter_records()
        }
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

    def get_editor_state(self) -> EditorState | None:
        """Return the active :class:`EditorState` when the editor is loaded."""

        editor = self._get_message_editor()
        if editor is None:
            return None
        return editor.state

    def requires_editor_submission(self) -> bool:
        """Return ``True`` when the editor expects a draft submission."""

        state = self.get_editor_state()
        if state is None:
            return False
        if state is EditorState.POST_MESSAGE:
            return True
        if state is EditorState.EDIT_DRAFT:
            return self._editor_context.selected_message_id is not None
        return False

    def submit_editor_draft(
        self,
        *,
        subject: str | None = None,
        lines: Iterable[str] | None = None,
    ) -> SessionState:
        """Populate the editor context and dispatch ``DRAFT_SUBMITTED``."""

        editor = self._get_message_editor()
        if editor is None:
            raise RuntimeError("message editor module is unavailable")
        context = self._editor_context
        if subject is not None:
            context.current_message = subject
        if lines is not None:
            context.draft_buffer = list(lines)
        return self._dispatch(MessageEditorEvent.DRAFT_SUBMITTED, context)

    def read_output(self) -> str:
        """Flush buffered console output and return it as a string."""

        buffer: list[str] = []
        output = self.console.device.output
        while output:
            buffer.append(output.popleft())
        return "".join(buffer)

    # Why: integrate indicator controllers with console state and keep the service registry aligned when controllers change.
    def set_indicator_controller(
        self, controller: "IndicatorController" | None
    ) -> None:
        """Register ``controller`` to mirror pause/abort signals."""

        register_service = getattr(self.kernel.context, "register_service", None)
        unregister_service = getattr(self.kernel.context, "unregister_service", None)

        if controller is None:
            if callable(unregister_service):
                unregister_service("indicator_controller")
            self._indicator_controller = None
            return

        already_registered = self._indicator_controller is controller

        sync_from_console = getattr(controller, "sync_from_console", None)
        if callable(sync_from_console):
            sync_from_console()

        if callable(register_service):
            register_service("indicator_controller", controller)

        if not already_registered:
            self._indicator_controller = controller

    # Why: reuse CLI palette overrides when console fallbacks paint indicator cells directly.
    def _indicator_colour_override(self, field: str) -> int | None:
        indicator_defaults = getattr(self.defaults, "indicator", None)
        if isinstance(indicator_defaults, IndicatorDefaults):
            value = getattr(indicator_defaults, field, None)
            if value is not None:
                return int(value) & 0xFF
        return None

    def set_pause_indicator_state(self, active: bool) -> None:
        """Forward pause state to the registered indicator controller."""

        # Why: drive pause toggles directly through the console when controllers are absent so the overlay palette stays intact.
        controller = self._indicator_controller
        if controller is not None:
            controller.set_pause(active)
            return
        console = getattr(self, "console", None)
        setter = getattr(console, "set_pause_indicator", None)
        if not callable(setter):
            return
        glyph = _PAUSE_GLYPH if active else _SPACE_GLYPH
        colour = self._indicator_colour_override("pause_colour")
        if colour is None:
            snapshot = getattr(console, "indicator_snapshot", None)
            if callable(snapshot):
                colour = snapshot().pause.colour
        if colour is not None:
            setter(glyph, colour=colour)
        else:
            setter(glyph)

    # Why: keep abort indicator fallbacks aligned with CLI palette overrides when controllers are absent.
    def set_abort_indicator_state(self, active: bool) -> None:
        """Forward abort state to the registered indicator controller."""

        # Why: fall back to console writes that reuse the current palette so abort toggles match overlay rendering without a controller.
        controller = self._indicator_controller
        if controller is not None:
            controller.set_abort(active)
            return
        console = getattr(self, "console", None)
        setter = getattr(console, "set_abort_indicator", None)
        if not callable(setter):
            return
        glyph = _ABORT_GLYPH if active else _SPACE_GLYPH
        colour = self._indicator_colour_override("abort_colour")
        if colour is None:
            snapshot = getattr(console, "indicator_snapshot", None)
            if callable(snapshot):
                colour = snapshot().abort.colour
        if colour is not None:
            setter(glyph, colour=colour)
        else:
            setter(glyph)

    def send_command(self, text: str) -> SessionState:
        """Deliver ``text`` to the active module and propagate transitions."""

        state = self.kernel.state
        if state is SessionState.EXIT:
            return state

        command_event = self._COMMAND_EVENTS.get(state)
        if command_event is None:
            raise ValueError(f"state {state!r} does not accept textual input")

        if state is SessionState.MESSAGE_EDITOR:
            return self._send_editor_command(text)

        return self._dispatch(command_event, text)

    def abort_editor(self) -> SessionState:
        """Request that the message editor abort back to the main menu."""

        if self.kernel.state is not SessionState.MESSAGE_EDITOR:
            raise RuntimeError("abort_editor requires the message editor to be active")
        return self._dispatch(MessageEditorEvent.ABORT, self._editor_context)

    # Internal helpers ---------------------------------------------------

    def _dispatch(self, event: object, *args: object) -> SessionState:
        previous_state = self.kernel.state
        editor_before_state: EditorState | None = None
        if previous_state is SessionState.MESSAGE_EDITOR:
            editor = self._get_message_editor()
            if editor is not None:
                editor_before_state = editor.state
        next_state = self.kernel.step(event, *args)
        if previous_state is SessionState.MESSAGE_EDITOR:
            self._update_dirty_flag(event, editor_before_state)
        if next_state is not SessionState.EXIT and next_state is not previous_state:
            self._enter_state(next_state)
        elif (
            next_state is SessionState.MESSAGE_EDITOR
            and previous_state is SessionState.MESSAGE_EDITOR
        ):
            self._handle_editor_state_change(editor_before_state)
        if next_state is SessionState.EXIT:
            self._persist_message_store(force=True)
        else:
            self._persist_message_store()
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
        module = self._get_message_editor()
        if isinstance(module, MessageEditor) and module.state is EditorState.EXIT:
            module.state = EditorState.INTRO

    def _get_message_editor(self) -> MessageEditor | None:
        module = self.kernel._modules.get(SessionState.MESSAGE_EDITOR)
        if isinstance(module, MessageEditor):
            self._editor_module = module
            return module
        return None

    def _handle_editor_state_change(
        self, previous_state: EditorState | None
    ) -> None:
        editor = self._get_message_editor()
        if editor is None:
            return
        current_state = editor.state
        if previous_state is None or current_state is previous_state:
            return
        self._dispatch(MessageEditorEvent.ENTER, self._editor_context)

    def _update_dirty_flag(
        self, event: object, previous_state: EditorState | None
    ) -> None:
        if self.message_store_path is None:
            return
        if previous_state is None:
            return
        if not isinstance(event, MessageEditorEvent):
            return
        if event is not MessageEditorEvent.DRAFT_SUBMITTED:
            return
        if previous_state not in (EditorState.POST_MESSAGE, EditorState.EDIT_DRAFT):
            return
        editor = self._get_message_editor()
        if editor is None:
            return
        if editor.state is EditorState.MAIN_MENU:
            self._dirty = True

    def _persist_message_store(self, *, force: bool = False) -> None:
        if not self._dirty and not force:
            return
        path = self.message_store_path
        if path is None:
            self._dirty = False
            return
        if not self._dirty and force:
            self._dirty = False
            return
        save_message_store(
            self.message_store,
            path,
            initial_keys=self._initial_message_keys,
        )
        self._initial_message_keys = {
            (record.board_id, record.message_id)
            for record in self.message_store.iter_records()
        }
        self._dirty = False

    def _send_editor_command(self, text: str) -> SessionState:
        editor = self._get_message_editor()
        if editor is None:
            raise RuntimeError("message editor module is unavailable")
        context = self._editor_context
        event = self._resolve_editor_event(editor, context, text)
        return self._dispatch(event, context)

    # Why: translate textual submissions into editor events while preserving the legacy dot-command controls.
    def _resolve_editor_event(
        self, editor: MessageEditor, context: SessionContext, text: str
    ) -> MessageEditorEvent:
        state = editor.state
        if state is EditorState.READ_MESSAGES:
            context.current_message = text
            return MessageEditorEvent.MESSAGE_SELECTED
        if state is EditorState.POST_MESSAGE:
            parsed = self._parse_composition_input(
                text, include_subject=True, context=context
            )
            command = parsed.command
            if command and command in MessageEditor.DOT_ABORT_COMMANDS:
                context.command_buffer = command
                return MessageEditorEvent.ABORT
            if command and command in (
                MessageEditor.DOT_HELP_COMMANDS
                | MessageEditor.DOT_LINE_NUMBER_COMMANDS
            ):
                context.command_buffer = command
                return MessageEditorEvent.COMMAND_SELECTED
            context.current_message = parsed.subject
            context.draft_buffer = parsed.lines
            return MessageEditorEvent.DRAFT_SUBMITTED
        if state is EditorState.EDIT_DRAFT:
            if context.selected_message_id is None:
                context.current_message = text
                context.draft_buffer.clear()
                return MessageEditorEvent.ENTER
            parsed = self._parse_composition_input(
                text, include_subject=False, context=context
            )
            command = parsed.command
            if command and command in MessageEditor.DOT_ABORT_COMMANDS:
                context.command_buffer = command
                return MessageEditorEvent.ABORT
            if command and command in (
                MessageEditor.DOT_HELP_COMMANDS
                | MessageEditor.DOT_LINE_NUMBER_COMMANDS
            ):
                context.command_buffer = command
                return MessageEditorEvent.COMMAND_SELECTED
            context.draft_buffer = parsed.lines
            context.current_message = parsed.subject
            return MessageEditorEvent.DRAFT_SUBMITTED

        context.current_message = text
        return MessageEditorEvent.COMMAND_SELECTED

    # Why: normalise subject/body text and trailing commands emitted by the editor front-ends.
    def _parse_composition_input(
        self,
        text: str,
        *,
        include_subject: bool,
        context: SessionContext,
    ) -> _CompositionInput:
        lines = list(self._split_editor_lines(text))
        while lines and not lines[-1].strip():
            lines.pop()
        command: str | None = None
        if lines:
            candidate = lines[-1].strip()
            if candidate.startswith(".") or candidate.startswith("/"):
                command = candidate.upper()
                lines.pop()
        if include_subject:
            if lines:
                subject = lines[0]
                body = lines[1:]
            else:
                subject = context.current_message
                body: list[str] = []
        else:
            subject = context.current_message
            body = lines
        subject = subject or context.current_message
        return _CompositionInput(command=command, subject=subject, lines=body)

    def _split_editor_lines(self, text: str) -> Iterable[str]:
        if not text:
            return ()
        normalised = text.replace("\r\n", "\n").replace("\r", "\n")
        return normalised.split("\n")


__all__ = ["SessionRunner"]
