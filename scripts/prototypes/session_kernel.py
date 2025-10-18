"""Runtime kernel that wires prototype session modules to device services."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Mapping, MutableMapping, Protocol, Sequence, Set

from .ampersand_dispatcher import AmpersandDispatcher
from .device_context import DeviceContext, bootstrap_device_context
from .runtime.ampersand_overrides import BUILTIN_AMPERSAND_OVERRIDES
from .setup_defaults import DriveAssignment, SetupDefaults


class SessionState(Enum):
    """High-level lifecycle states exposed by :class:`SessionKernel`."""

    BOOTSTRAP = auto()
    MAIN_MENU = auto()
    MESSAGE_EDITOR = auto()
    FILE_TRANSFERS = auto()
    SYSOP_OPTIONS = auto()
    EXIT = auto()


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
    service_map: MutableMapping[str, object] = field(init=False)
    services: Mapping[str, object] = field(init=False)
    state: SessionState = field(init=False, default=SessionState.BOOTSTRAP)
    _modules: Dict[SessionState, SessionModule] = field(init=False, default_factory=dict)
    _started_modules: Set[SessionState] = field(init=False, default_factory=set)
    _active_state: SessionState = field(init=False, default=SessionState.BOOTSTRAP)

    def __post_init__(self) -> None:
        assignments: Sequence[DriveAssignment] = self.defaults.active_drives
        runtime_overrides = dict(BUILTIN_AMPERSAND_OVERRIDES)
        configured_overrides = getattr(self.defaults, "ampersand_overrides", None)
        if isinstance(configured_overrides, Mapping):
            runtime_overrides.update(configured_overrides)
        self.context = bootstrap_device_context(
            assignments, ampersand_overrides=runtime_overrides
        )
        dispatcher = self.context.get_service("ampersand")
        if not isinstance(dispatcher, AmpersandDispatcher):
            raise TypeError("ampersand service missing from device context")
        self.dispatcher = dispatcher
        self.service_map = self.context.services
        self.services = dispatcher.services
        self._modules = {}
        self._started_modules = set()
        self._active_state = SessionState.BOOTSTRAP
        initial_state = self.module.start(self)
        self._register_initial_module(initial_state, self.module)

    def step(self, event: object, *args: object, **kwargs: object) -> SessionState:
        """Route ``event`` to :attr:`module` and update :attr:`state`."""

        next_state = self.module.handle_event(self, event, *args, **kwargs)
        self._transition(next_state)
        return self.state

    def register_module(self, state: SessionState, module: SessionModule) -> None:
        """Expose ``module`` as the handler for ``state`` transitions."""

        self._modules[state] = module

    def _register_initial_module(
        self, state: SessionState, module: SessionModule
    ) -> None:
        self.register_module(state, module)
        self._started_modules.add(state)
        self._active_state = state
        self.state = state

    def _transition(self, next_state: SessionState) -> None:
        if next_state is SessionState.EXIT:
            self.state = SessionState.EXIT
            return

        module = self._modules.get(next_state)
        if module is not None and next_state != self._active_state:
            if next_state not in self._started_modules:
                start_state = module.start(self)
                if start_state is not next_state:
                    raise RuntimeError(
                        "module initialised to unexpected state "
                        f"{start_state!r} for {next_state!r}"
                    )
                self._started_modules.add(next_state)
            self.module = module
            self._active_state = next_state

        self.state = next_state


__all__ = [
    "SessionKernel",
    "SessionModule",
    "SessionState",
]

