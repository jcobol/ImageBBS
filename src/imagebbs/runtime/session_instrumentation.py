"""Helpers for wiring session instrumentation across interfaces."""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict

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
        idle_tick_interval: float = 1.0,
    ) -> None:
        # Why: centralise instrumentation wiring so transports share indicator and timer state.
        self.runner = runner
        self._indicator_controller_cls = indicator_controller_cls
        self._idle_timer_scheduler_cls = idle_timer_scheduler_cls
        self._indicator_controller: IndicatorController | None = None
        self._idle_timer_scheduler: IdleTimerScheduler | None = None
        self._idle_tick_interval = float(idle_tick_interval)

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

        # Why: keep instrumentation cache aligned with the runner's wiring so controller swaps mirror the active console state.
        runner_controller = getattr(self.runner, "_indicator_controller", None)
        cached_controller = self._indicator_controller
        if cached_controller is not None and cached_controller is not runner_controller:
            self._indicator_controller = None
            cached_controller = None
        if cached_controller is not None:
            controller = cached_controller
            sync_from_console = getattr(controller, "sync_from_console", None)
            if callable(sync_from_console):
                sync_from_console()
            return controller
        existing_controller = runner_controller
        if isinstance(existing_controller, IndicatorController):
            self._indicator_controller = existing_controller
            sync_from_console = getattr(existing_controller, "sync_from_console", None)
            if callable(sync_from_console):
                sync_from_console()
            return existing_controller
        controller_cls = self._indicator_controller_cls
        if controller_cls is None:
            return None
        console = getattr(self.runner, "console", None)
        if console is None:
            return None
        indicator_kwargs: Dict[str, object] = {}
        indicator_defaults = getattr(getattr(self.runner, "defaults", None), "indicator", None)
        controller_kwargs = getattr(indicator_defaults, "controller_kwargs", None)
        if callable(controller_kwargs):
            # Why: pass through configured colours and spinner frames so controller instances mirror host preferences.
            indicator_kwargs = dict(controller_kwargs())
        controller = controller_cls(console, **indicator_kwargs)
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
        scheduler = scheduler_cls(
            console,
            idle_tick_interval=self._idle_tick_interval,
        )
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
