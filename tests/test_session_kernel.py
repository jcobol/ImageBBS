"""Tests for the prototype session kernel coordinator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from imagebbs import (
    ConsoleService,
    DeviceContext,
    MessageEditor,
    SessionContext,
    SessionKernel,
    SessionState,
    SetupDefaults,
)
from imagebbs.message_editor import Event


@dataclass
class StubModule:
    """Simple module implementation for kernel tests."""

    responses: List[SessionState] = field(
        default_factory=lambda: [SessionState.MAIN_MENU]
    )
    handled_events: List[Tuple[object, tuple, dict]] = field(default_factory=list)
    started: bool = False

    def start(self, kernel: SessionKernel) -> SessionState:  # pragma: no cover - protocol
        self.started = True
        return self.responses[0]

    def handle_event(
        self, kernel: SessionKernel, event: object, *args: object, **kwargs: object
    ) -> SessionState:
        self.handled_events.append((event, args, kwargs))
        try:
            return self.responses[len(self.handled_events)]
        except IndexError:
            return self.responses[-1]


def test_kernel_initialises_with_stub_defaults() -> None:
    module = StubModule(responses=[SessionState.MAIN_MENU])
    kernel = SessionKernel(module=module)

    assert module.started is True
    assert isinstance(kernel.context, DeviceContext)
    stub_defaults = SetupDefaults.stub()
    assert kernel.defaults.board_name == stub_defaults.board_name
    assert kernel.state is SessionState.MAIN_MENU


def test_kernel_service_wiring_shared_mapping() -> None:
    module = StubModule(responses=[SessionState.MAIN_MENU])
    kernel = SessionKernel(module=module)

    dispatcher = kernel.dispatcher
    assert dispatcher is kernel.context.get_service("ampersand")
    assert kernel.services["ampersand"] is dispatcher
    assert kernel.services is dispatcher.services
    assert kernel.service_map is kernel.context.services

    console_service = kernel.context.get_service("console")
    assert isinstance(console_service, ConsoleService)
    assert kernel.services["console"] is console_service
    assert kernel.service_map["console"] is console_service


def test_kernel_step_routes_events_and_updates_state() -> None:
    primary = StubModule(
        responses=[SessionState.MAIN_MENU, SessionState.MESSAGE_EDITOR, SessionState.EXIT]
    )
    kernel = SessionKernel(module=primary)
    secondary = StubModule(
        responses=[SessionState.MESSAGE_EDITOR, SessionState.MAIN_MENU]
    )
    kernel.register_module(SessionState.MESSAGE_EDITOR, secondary)

    state = kernel.step("launch")
    assert state is SessionState.MESSAGE_EDITOR
    assert kernel.module is secondary

    state = kernel.step("return")
    assert state is SessionState.MAIN_MENU
    assert kernel.module is primary

    state = kernel.step("terminate")
    assert state is SessionState.EXIT
    assert kernel.state is SessionState.EXIT
    assert primary.handled_events[0][0] == "launch"
    assert secondary.handled_events[0][0] == "return"
    assert primary.handled_events[1][0] == "terminate"


def test_message_editor_module_completes_session() -> None:
    module = MessageEditor()
    kernel = SessionKernel(module=module)
    session = SessionContext(board_id="123", user_id="abc")

    state = kernel.step(Event.ENTER, session)
    assert state is SessionState.MESSAGE_EDITOR

    session.current_message = "Q"
    state = kernel.step(Event.COMMAND_SELECTED, session)
    assert state is SessionState.MAIN_MENU
    assert kernel.state is SessionState.MAIN_MENU
