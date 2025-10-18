"""Runtime kernel that wires prototype session modules to device services."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Mapping, Protocol, Sequence

from .ampersand_dispatcher import AmpersandDispatcher
from .device_context import DeviceContext, bootstrap_device_context
from .setup_defaults import DriveAssignment, SetupDefaults


class SessionState(Enum):
    """High-level lifecycle states exposed by :class:`SessionKernel`."""

    BOOTSTRAP = auto()
    ACTIVE = auto()
    COMPLETED = auto()


class SessionModule(Protocol):
    """Protocol implemented by prototype session modules."""

    def start(self, kernel: "SessionKernel") -> SessionState:
        """Wire the module into ``kernel`` and return the initial state."""

    def handle_event(
        self, kernel: "SessionKernel", event: object, *args: object, **kwargs: object
    ) -> SessionState:
        """Handle ``event`` routed from ``kernel.step``."""


@dataclass
class SessionKernel:
    """Coordinate device wiring and state transitions for a session module."""

    module: SessionModule
    defaults: SetupDefaults = field(default_factory=SetupDefaults.stub)
    context: DeviceContext = field(init=False)
    dispatcher: AmpersandDispatcher = field(init=False)
    services: Mapping[str, object] = field(init=False)
    state: SessionState = field(init=False, default=SessionState.BOOTSTRAP)

    def __post_init__(self) -> None:
        assignments: Sequence[DriveAssignment] = self.defaults.active_drives
        self.context = bootstrap_device_context(assignments)
        dispatcher = self.context.get_service("ampersand")
        if not isinstance(dispatcher, AmpersandDispatcher):
            raise TypeError("ampersand service missing from device context")
        self.dispatcher = dispatcher
        self.services = dispatcher.services
        self.state = self.module.start(self)

    def step(self, event: object, *args: object, **kwargs: object) -> SessionState:
        """Route ``event`` to :attr:`module` and update :attr:`state`."""

        self.state = self.module.handle_event(self, event, *args, **kwargs)
        return self.state


__all__ = [
    "SessionKernel",
    "SessionModule",
    "SessionState",
]

