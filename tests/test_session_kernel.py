"""Tests for the prototype session kernel coordinator."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import (
    ConsoleService,
    DeviceContext,
    MessageEditor,
    SessionContext,
    SessionKernel,
    SessionState,
    SetupDefaults,
)
from scripts.prototypes.message_editor import Event


@dataclass
class StubModule:
    """Simple module implementation for kernel tests."""

    responses: List[SessionState] = field(default_factory=lambda: [SessionState.ACTIVE])
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
    module = StubModule(responses=[SessionState.ACTIVE])
    kernel = SessionKernel(module=module)

    assert module.started is True
    assert isinstance(kernel.context, DeviceContext)
    stub_defaults = SetupDefaults.stub()
    assert kernel.defaults.board_name == stub_defaults.board_name
    assert kernel.state is SessionState.ACTIVE


def test_kernel_service_wiring_shared_mapping() -> None:
    module = StubModule(responses=[SessionState.ACTIVE])
    kernel = SessionKernel(module=module)

    dispatcher = kernel.dispatcher
    assert dispatcher is kernel.context.get_service("ampersand")
    assert kernel.services["ampersand"] is dispatcher

    console_service = kernel.context.get_service("console")
    assert isinstance(console_service, ConsoleService)
    assert kernel.services["console"] is console_service


def test_kernel_step_routes_events_and_updates_state() -> None:
    module = StubModule(
        responses=[SessionState.ACTIVE, SessionState.ACTIVE, SessionState.COMPLETED]
    )
    kernel = SessionKernel(module=module)

    state = kernel.step("noop")
    assert state is SessionState.ACTIVE

    state = kernel.step("terminate")
    assert state is SessionState.COMPLETED
    assert kernel.state is SessionState.COMPLETED
    assert module.handled_events[0][0] == "noop"
    assert module.handled_events[1][0] == "terminate"


def test_message_editor_module_completes_session() -> None:
    module = MessageEditor()
    kernel = SessionKernel(module=module)
    session = SessionContext(board_id="123", user_id="abc")

    state = kernel.step(Event.ENTER, session)
    assert state is SessionState.ACTIVE

    session.current_message = "Q"
    state = kernel.step(Event.COMMAND_SELECTED, session)
    assert state is SessionState.COMPLETED
    assert kernel.state is SessionState.COMPLETED
