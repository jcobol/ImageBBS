"""State-machine skeleton for porting the ImageBBS message editor."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Iterable, List, Mapping, Optional, TYPE_CHECKING

from .ampersand_registry import AmpersandRegistry, AmpersandResult
from .runtime.message_store import MessageRecord, MessageStore, MessageSummary
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
    store: MessageStore | None = None
    services: Mapping[str, object] | None = None
    modem_buffer: List[str] = field(default_factory=list)
    drafts: Dict[int, List[str]] = field(default_factory=dict)
    command_buffer: str = ""
    selected_message_id: Optional[int] = None
    draft_buffer: List[str] = field(default_factory=list)
    _pending_state: SessionState | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        if self.store is None:
            self.store = MessageStore()
        if self.services is None:
            self.services = {}
        self.command_buffer = self.command_buffer or ""

    def push_output(self, text: str) -> None:
        self.modem_buffer.append(text)

    @property
    def current_message(self) -> str:
        return self.command_buffer

    @current_message.setter
    def current_message(self, value: Optional[str]) -> None:
        self.command_buffer = value or ""

    def attach_services(
        self, *, store: MessageStore, services: Mapping[str, object]
    ) -> None:
        self.store = store
        self.services = services

    def set_next_state(self, state: SessionState) -> None:
        self._pending_state = state

    def consume_state(self, fallback: SessionState) -> SessionState:
        state = self._pending_state or fallback
        self._pending_state = None
        return state

    def cache_draft(self, message_id: Optional[int] = None) -> None:
        if message_id is None:
            message_id = self.selected_message_id
        if message_id is None:
            return
        self.drafts[message_id] = list(self.draft_buffer)

    def load_draft(self, message_id: Optional[int] = None) -> List[str]:
        if message_id is None:
            message_id = self.selected_message_id
        if message_id is None:
            return []
        return list(self.drafts.get(message_id, []))

    def clear_draft(self) -> None:
        self.draft_buffer.clear()

    def reset_selection(self) -> None:
        self.selected_message_id = None


class TransitionError(RuntimeError):
    """Raised when an invalid state transition is attempted."""


class MessageEditor:
    """Finite-state-machine approximation of the editor's dispatcher."""

    INTRO_MACRO_INDEX = 0x04
    MAIN_MENU_MACRO_INDEX = 0x09
    READ_MESSAGE_MACRO_INDEX = 0x0D
    POST_MESSAGE_MACRO_INDEX = 0x14
    EDIT_DRAFT_MACRO_INDEX = 0x15
    MAIN_MENU_PROMPT = "(R)ead, (P)ost, (E)dit Draft, (Q)uit? "

    def __init__(
        self,
        *,
        registry: AmpersandRegistry | None = None,
        store: MessageStore | None = None,
    ) -> None:
        self.state = EditorState.INTRO
        self.ampersand_registry = registry or AmpersandRegistry()
        self.services: Mapping[str, object] = self.ampersand_registry.services
        self.store = store or MessageStore()
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
                self.MAIN_MENU_PROMPT,
                event,
            )
            return EditorState.MAIN_MENU
        if event is Event.COMMAND_SELECTED:
            selection = ctx.command_buffer or ""
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
        if event is Event.ABORT:
            ctx.set_next_state(SessionState.MAIN_MENU)
            return EditorState.EXIT
        raise TransitionError("Main menu requires ENTER or COMMAND_SELECTED")

    def _handle_read_messages(self, event: Event, ctx: SessionContext) -> EditorState:
        store = self._resolve_store(ctx)
        if event is Event.ENTER:
            summaries = store.list(ctx.board_id)
            fallback = self._format_message_listing(summaries)
            self._ampersand_dispatch(
                self.READ_MESSAGE_MACRO_INDEX,
                ctx,
                fallback,
                event,
            )
            if not summaries:
                ctx.push_output("?NO MESSAGES AVAILABLE\r")
            else:
                for summary in summaries:
                    ctx.push_output(self._format_summary_line(summary))
            return EditorState.READ_MESSAGES
        if event is Event.MESSAGE_SELECTED:
            selection = (ctx.command_buffer or "").strip()
            if selection.upper().startswith("Q"):
                ctx.reset_selection()
                ctx.clear_draft()
                self._ampersand_dispatch(
                    self.MAIN_MENU_MACRO_INDEX,
                    ctx,
                    self.MAIN_MENU_PROMPT,
                    event,
                )
                return EditorState.MAIN_MENU
            message_id = self._resolve_message_id(ctx)
            if message_id is None:
                ctx.push_output("?INVALID MESSAGE SELECTION\r")
                return EditorState.READ_MESSAGES
            try:
                record = store.fetch(ctx.board_id, message_id)
            except KeyError:
                ctx.push_output("?MESSAGE NOT FOUND\r")
                return EditorState.READ_MESSAGES
            ctx.selected_message_id = record.message_id
            fallback = self._format_message_header(record)
            self._ampersand_dispatch(
                self.READ_MESSAGE_MACRO_INDEX,
                ctx,
                fallback,
                event,
            )
            for line in record.lines:
                ctx.push_output(f"{line}\r")
            if not record.lines:
                ctx.push_output("\r")
            return EditorState.READ_MESSAGES
        if event is Event.ABORT:
            ctx.reset_selection()
            return EditorState.MAIN_MENU
        raise TransitionError("Read messages requires MESSAGE_SELECTED or ABORT")

    def _handle_post_message(self, event: Event, ctx: SessionContext) -> EditorState:
        store = self._resolve_store(ctx)
        if event is Event.ENTER:
            self._ampersand_dispatch(
                self.POST_MESSAGE_MACRO_INDEX,
                ctx,
                "POSTING...\r",
                event,
            )
            ctx.clear_draft()
            return EditorState.POST_MESSAGE
        if event is Event.DRAFT_SUBMITTED:
            subject = ctx.command_buffer or "Untitled"
            lines: Iterable[str] = ctx.draft_buffer or ctx.load_draft(None)
            record = store.append(
                board_id=ctx.board_id,
                subject=subject,
                author_handle=ctx.user_id,
                lines=lines,
            )
            ctx.selected_message_id = record.message_id
            ctx.cache_draft(record.message_id)
            ctx.clear_draft()
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
            ctx.clear_draft()
            return EditorState.MAIN_MENU
        raise TransitionError("Post message requires ENTER, DRAFT_SUBMITTED, or ABORT")

    def _handle_edit_draft(self, event: Event, ctx: SessionContext) -> EditorState:
        store = self._resolve_store(ctx)
        if event is Event.ENTER:
            message_id = self._resolve_message_id(ctx)
            if message_id is None:
                ctx.push_output("?SELECT A MESSAGE FIRST\r")
                return EditorState.EDIT_DRAFT
            try:
                record = store.fetch(ctx.board_id, message_id)
            except KeyError:
                ctx.push_output("?MESSAGE NOT FOUND\r")
                return EditorState.EDIT_DRAFT
            ctx.selected_message_id = record.message_id
            ctx.draft_buffer = list(record.lines)
            ctx.cache_draft(record.message_id)
            self._ampersand_dispatch(
                self.EDIT_DRAFT_MACRO_INDEX,
                ctx,
                "EDIT DRAFT MODE\r",
                event,
            )
            return EditorState.EDIT_DRAFT
        if event is Event.DRAFT_SUBMITTED:
            message_id = self._resolve_message_id(ctx)
            if message_id is None:
                ctx.push_output("?NO MESSAGE SELECTED\r")
                return EditorState.EDIT_DRAFT
            lines = ctx.draft_buffer or ctx.load_draft(message_id)
            store.update(
                ctx.board_id,
                message_id,
                lines=lines,
            )
            ctx.cache_draft(message_id)
            ctx.clear_draft()
            self._ampersand_dispatch(
                self.EDIT_DRAFT_MACRO_INDEX,
                ctx,
                "DRAFT SAVED\r",
                event,
            )
            return EditorState.MAIN_MENU
        if event is Event.ABORT:
            ctx.clear_draft()
            ctx.reset_selection()
            self._ampersand_dispatch(
                self.EDIT_DRAFT_MACRO_INDEX,
                ctx,
                "CANCELLED\r",
                event,
            )
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
        self.ampersand_registry.register_service("message_store", self.store)
        self.services = self.ampersand_registry.services
        self.state = EditorState.INTRO
        return SessionState.MESSAGE_EDITOR

    def handle_event(
        self,
        kernel: "SessionKernel",
        event: Event,
        session: SessionContext,
    ) -> SessionState:
        """Route ``event`` through :meth:`dispatch` and translate kernel state."""

        self._prepare_session(session)
        next_state = self.dispatch(event, session)
        if next_state is EditorState.EXIT:
            return session.consume_state(SessionState.MAIN_MENU)
        return session.consume_state(SessionState.MESSAGE_EDITOR)

    # Internal helpers -------------------------------------------------

    def _prepare_session(self, session: SessionContext) -> None:
        store = session.store or self.store
        services = session.services or self.services
        session.attach_services(store=store, services=services)

    def _resolve_store(self, session: SessionContext) -> MessageStore:
        store = session.store
        if store is None:
            store = self.store
            session.store = store
        return store

    def _resolve_message_id(self, session: SessionContext) -> Optional[int]:
        if session.selected_message_id is not None:
            return session.selected_message_id
        text = session.command_buffer.strip()
        if not text:
            return None
        try:
            message_id = int(text, 10)
        except ValueError:
            return None
        session.selected_message_id = message_id
        return message_id

    def _format_message_listing(self, summaries: Iterable[MessageSummary]) -> str:
        if not summaries:
            return ""
        lines = [self._format_summary_line(summary) for summary in summaries]
        return "\r".join(lines) + "\r"

    def _format_summary_line(self, summary: MessageSummary) -> str:
        return (
            f"#{summary.message_id:03d} {summary.subject}"
            f" ({summary.author_handle}) [{summary.line_count} lines]\r"
        )

    def _format_message_header(self, record: MessageRecord) -> str:
        return (
            f"\r#{record.message_id:03d} {record.subject}"
            f" ({record.author_handle})\r"
        )


__all__ = [
    "EditorState",
    "Event",
    "MessageEditor",
    "SessionContext",
    "TransitionError",
]


def _mirror_prototype_module() -> None:
    try:
        import scripts.prototypes.message_editor as _prototype  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - prototype mirrors optional at runtime
        return

    for name in __all__:
        setattr(_prototype, name, globals()[name])

    try:
        import scripts.prototypes as _prototypes  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - prototype mirrors optional at runtime
        _prototypes = None
    if _prototypes is not None:
        for name in __all__:
            setattr(_prototypes, name, globals()[name])

    import sys

    pkg = sys.modules.get("imagebbs")
    if pkg is not None:
        for name in __all__:
            setattr(pkg, name, globals()[name])
            try:
                exported = pkg.__all__  # type: ignore[attr-defined]
            except AttributeError:  # pragma: no cover - defensive guard
                continue
            if name not in exported:
                exported.append(name)


_mirror_prototype_module()
