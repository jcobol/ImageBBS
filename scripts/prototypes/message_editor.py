"""State-machine skeleton for porting the ImageBBS message editor."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, TYPE_CHECKING

from .ampersand_registry import AmpersandRegistry, AmpersandResult

from .session_kernel import SessionState

if TYPE_CHECKING:
    from .session_kernel import SessionKernel


class EditorState(Enum):
    """High-level menus exposed by the message editor overlays."""

    INTRO = auto()
    MAIN_MENU = auto()
    READ_MESSAGES = auto()
    POST_MESSAGE = auto()
    EDIT_DRAFT = auto()
    EXIT = auto()


class Event(Enum):
    """Stimuli that drive transitions between BASIC line-number blocks."""

    ENTER = auto()
    COMMAND_SELECTED = auto()
    MESSAGE_SELECTED = auto()
    DRAFT_SUBMITTED = auto()
    ABORT = auto()


@dataclass
class SessionContext:
    """Subset of BASIC globals used by the editor overlay."""

    board_id: str
    user_id: str
    modem_buffer: List[str] = field(default_factory=list)
    drafts: Dict[str, str] = field(default_factory=dict)
    current_message: Optional[str] = None

    def push_output(self, text: str) -> None:
        self.modem_buffer.append(text)


class TransitionError(RuntimeError):
    pass


class MessageEditor:
    """Finite-state-machine approximation of the editor's dispatcher."""

    INTRO_MACRO_INDEX = 0x04
    MAIN_MENU_MACRO_INDEX = 0x09
    READ_MESSAGE_MACRO_INDEX = 0x0D
    POST_MESSAGE_MACRO_INDEX = 0x14
    EDIT_DRAFT_MACRO_INDEX = 0x15

    def __init__(self, registry: Optional[AmpersandRegistry] = None) -> None:
        self.state = EditorState.INTRO
        self.ampersand_registry = registry or AmpersandRegistry()
        self.handlers = {
            EditorState.INTRO: self._handle_intro,
            EditorState.MAIN_MENU: self._handle_main_menu,
            EditorState.READ_MESSAGES: self._handle_read_messages,
            EditorState.POST_MESSAGE: self._handle_post_message,
            EditorState.EDIT_DRAFT: self._handle_edit_draft,
        }

    def dispatch(self, event: Event, ctx: SessionContext) -> EditorState:
        handler = self.handlers.get(self.state)
        if handler is None:
            raise TransitionError(f"No handler for state {self.state}")
        self.state = handler(event, ctx)
        return self.state

    def _handle_intro(self, event: Event, ctx: SessionContext) -> EditorState:
        if event is Event.ENTER:
            self._ampersand_dispatch(
                self.INTRO_MACRO_INDEX,
                ctx,
                "\r*** IMAGE MESSAGE EDITOR ***\r",
                event,
            )
            return EditorState.MAIN_MENU
        raise TransitionError("Intro state only accepts ENTER")

    def _handle_main_menu(self, event: Event, ctx: SessionContext) -> EditorState:
        if event is Event.ENTER:
            self._ampersand_dispatch(
                self.MAIN_MENU_MACRO_INDEX,
                ctx,
                "(R)ead, (P)ost, (E)dit Draft, (Q)uit? ",
                event,
            )
            return EditorState.MAIN_MENU
        if event is Event.COMMAND_SELECTED:
            selection = ctx.current_message or ""
            normalized = selection.strip().upper()
            if normalized.startswith("R"):
                return EditorState.READ_MESSAGES
            if normalized.startswith("P"):
                return EditorState.POST_MESSAGE
            if normalized.startswith("E"):
                return EditorState.EDIT_DRAFT
            if normalized.startswith("Q"):
                return EditorState.EXIT
            ctx.push_output("?UNRECOGNIZED OPTION\r")
            return EditorState.MAIN_MENU
        raise TransitionError("Main menu requires ENTER or COMMAND_SELECTED")

    def _handle_read_messages(self, event: Event, ctx: SessionContext) -> EditorState:
        if event is Event.MESSAGE_SELECTED:
            fallback = f"\r#{ctx.current_message}: ...\r"
            self._ampersand_dispatch(
                self.READ_MESSAGE_MACRO_INDEX,
                ctx,
                fallback,
                event,
            )
            return EditorState.READ_MESSAGES
        if event is Event.ABORT:
            return EditorState.MAIN_MENU
        raise TransitionError("Read messages requires MESSAGE_SELECTED or ABORT")

    def _handle_post_message(self, event: Event, ctx: SessionContext) -> EditorState:
        if event is Event.ENTER:
            self._ampersand_dispatch(
                self.POST_MESSAGE_MACRO_INDEX,
                ctx,
                "POSTING...\r",
                event,
            )
            return EditorState.POST_MESSAGE
        if event is Event.DRAFT_SUBMITTED:
            self._ampersand_dispatch(
                self.POST_MESSAGE_MACRO_INDEX,
                ctx,
                "MESSAGE SAVED\r",
                event,
            )
            return EditorState.MAIN_MENU
        if event is Event.ABORT:
            self._ampersand_dispatch(
                self.POST_MESSAGE_MACRO_INDEX,
                ctx,
                "CANCELLED\r",
                event,
            )
            return EditorState.MAIN_MENU
        raise TransitionError("Post message requires ENTER, DRAFT_SUBMITTED, or ABORT")

    def _handle_edit_draft(self, event: Event, ctx: SessionContext) -> EditorState:
        if event is Event.ENTER:
            self._ampersand_dispatch(
                self.EDIT_DRAFT_MACRO_INDEX,
                ctx,
                "EDIT DRAFT MODE\r",
                event,
            )
            return EditorState.EDIT_DRAFT
        if event is Event.DRAFT_SUBMITTED:
            ctx.drafts[ctx.current_message or "new"] = "submitted"
            return EditorState.MAIN_MENU
        if event is Event.ABORT:
            return EditorState.MAIN_MENU
        raise TransitionError("Edit draft requires ENTER, DRAFT_SUBMITTED, or ABORT")

    def _ampersand_dispatch(
        self,
        flag_index: int,
        session: SessionContext,
        fallback_text: Optional[str],
        event: Event,
    ) -> AmpersandResult:
        """Dispatch a registry handler and honour overrides."""

        context = {"session": session, "event": event}
        result = self.ampersand_registry.dispatch(flag_index, context)
        rendered = result.rendered_text
        if rendered is not None:
            session.push_output(rendered)
        elif fallback_text is not None:
            session.push_output(fallback_text)
        return result

    # SessionModule protocol -------------------------------------------------

    def start(self, kernel: "SessionKernel") -> SessionState:
        """Bind the editor to the kernel's ampersand registry."""

        self.ampersand_registry = kernel.dispatcher.registry
        self.state = EditorState.INTRO
        return SessionState.MESSAGE_EDITOR

    def handle_event(
        self,
        kernel: "SessionKernel",
        event: Event,
        session: SessionContext,
    ) -> SessionState:
        """Route ``event`` through :meth:`dispatch` and translate kernel state."""

        next_state = self.dispatch(event, session)
        if next_state is EditorState.EXIT:
            return SessionState.MAIN_MENU
        return SessionState.MESSAGE_EDITOR


__all__ = [
    "EditorState",
    "Event",
    "MessageEditor",
    "SessionContext",
    "TransitionError",
]
