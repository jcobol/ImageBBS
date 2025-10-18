import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes import SessionKernel, SessionState
from scripts.prototypes.device_context import ConsoleService
from scripts.prototypes.runtime.sysop_options import (
    SysopOptionsEvent,
    SysopOptionsModule,
    SysopOptionsState,
)


def _bootstrap_kernel() -> tuple[SessionKernel, SysopOptionsModule]:
    module = SysopOptionsModule()
    kernel = SessionKernel(module=module)
    return kernel, module


def test_sysop_options_renders_macros_on_start_and_enter() -> None:
    kernel, module = _bootstrap_kernel()

    assert module.registry is kernel.dispatcher.registry

    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)

    assert module.rendered_slots[:2] == [
        module.MENU_HEADER_SLOT,
        module.MENU_PROMPT_SLOT,
    ]

    state = kernel.step(SysopOptionsEvent.ENTER)

    assert state is SessionState.SYSOP_OPTIONS
    assert module.state is SysopOptionsState.READY
    assert module.rendered_slots[-2:] == [
        module.MENU_HEADER_SLOT,
        module.MENU_PROMPT_SLOT,
    ]


def test_sysop_options_saying_command_renders_text() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(SysopOptionsEvent.ENTER)

    state = kernel.step(SysopOptionsEvent.COMMAND, " sy ")

    assert state is SessionState.SYSOP_OPTIONS
    assert module.last_command == "SY"
    assert module.last_saying == module.sayings[0]
    assert module.rendered_slots[-3:] == [
        module.SAYING_PREAMBLE_SLOT,
        module.SAYING_OUTPUT_SLOT,
        module.MENU_PROMPT_SLOT,
    ]

    console_service = kernel.services["console"]
    assert isinstance(console_service, ConsoleService)
    transcript = "".join(console_service.device.output)
    assert module.last_saying in transcript


def test_sysop_options_abort_returns_to_main_menu() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(SysopOptionsEvent.ENTER)
    module.rendered_slots.clear()

    state = kernel.step(SysopOptionsEvent.COMMAND, "abort")

    assert state is SessionState.MAIN_MENU
    assert module.last_command == "A"
    assert module.rendered_slots == [module.ABORT_SLOT]


def test_sysop_options_exit_terminates_session() -> None:
    kernel, module = _bootstrap_kernel()
    kernel.step(SysopOptionsEvent.ENTER)

    state = kernel.step(SysopOptionsEvent.COMMAND, "exit")

    assert state is SessionState.EXIT
    assert module.last_command == "EX"
