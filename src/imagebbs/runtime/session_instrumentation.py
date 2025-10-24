"""Helpers for wiring session instrumentation across interfaces."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .console_ui import IdleTimerScheduler
from .indicator_controller import IndicatorController

if TYPE_CHECKING:  # pragma: no cover - only imported for type checking
    from .session_runner import SessionRunner


class SessionInstrumentation:
    """Coordinate indicator controllers and idle timers for a session runner."""

    def __init__(
        self,
        runner: "SessionRunner",
        *,
        indicator_controller_cls: type[IndicatorController] | None = IndicatorController,
        idle_timer_scheduler_cls: type[IdleTimerScheduler] | None = IdleTimerScheduler,
    ) -> None:
        self.runner = runner
        self._indicator_controller_cls = indicator_controller_cls
        self._idle_timer_scheduler_cls = idle_timer_scheduler_cls
        self._indicator_controller: IndicatorController | None = None
        self._idle_timer_scheduler: IdleTimerScheduler | None = None

    @property
    def indicator_controller(self) -> IndicatorController | None:
        """Return the indicator controller associated with the runner, if any."""

        return self._indicator_controller

    @property
    def idle_timer_scheduler(self) -> IdleTimerScheduler | None:
        """Return the idle timer scheduler associated with the runner, if any."""

        return self._idle_timer_scheduler

    def ensure_indicator_controller(self) -> IndicatorController | None:
        """Instantiate and bind the indicator controller if required."""

        if self._indicator_controller is not None:
            return self._indicator_controller
        controller_cls = self._indicator_controller_cls
        if controller_cls is None:
            return None
        console = getattr(self.runner, "console", None)
        if console is None:
            return None
        controller = controller_cls(console)
        sync_from_console = getattr(controller, "sync_from_console", None)
        if callable(sync_from_console):
            sync_from_console()
        self.runner.set_indicator_controller(controller)
        context = getattr(getattr(self.runner, "kernel", None), "context", None)
        register_service = getattr(context, "register_service", None)
        if callable(register_service):
            register_service("indicator_controller", controller)
        self._indicator_controller = controller
        return controller

    def ensure_idle_timer_scheduler(self) -> IdleTimerScheduler | None:
        """Instantiate and cache the idle timer scheduler if available."""

        if self._idle_timer_scheduler is not None:
            return self._idle_timer_scheduler
        scheduler_cls = self._idle_timer_scheduler_cls
        if scheduler_cls is None:
            return None
        console = getattr(self.runner, "console", None)
        if console is None:
            return None
        scheduler = scheduler_cls(console)
        self._idle_timer_scheduler = scheduler
        return scheduler

    def reset_idle_timer(self) -> None:
        """Reset the idle timer if one has been configured."""

        scheduler = self.ensure_idle_timer_scheduler()
        if scheduler is not None:
            scheduler.reset()

    def on_idle_cycle(self) -> None:
        """Advance indicator and idle timer state for an idle loop iteration."""

        controller = self.ensure_indicator_controller()
        if controller is not None:
            controller.on_idle_tick()
        scheduler = self.ensure_idle_timer_scheduler()
        if scheduler is not None:
            scheduler.tick()

    def set_carrier(self, active: bool) -> None:
        """Notify the indicator controller about carrier state changes."""

        controller = self.ensure_indicator_controller()
        if controller is not None:
            controller.set_carrier(active)


__all__ = ["SessionInstrumentation"]
