from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.ampersand_dispatcher import (  # noqa: E402
    AmpersandDispatchContext,
    AmpersandDispatcher,
)
from scripts.prototypes.ampersand_registry import (  # noqa: E402
    AmpersandRegistry,
    AmpersandResult,
)
from scripts.prototypes.device_context import (  # noqa: E402
    ConsoleService,
    DeviceContext,
    bootstrap_device_context,
)
from scripts.prototypes.setup_config import load_drive_config  # noqa: E402


def _registry_flag_index(dispatcher: AmpersandDispatcher) -> int:
    return next(iter(dispatcher.registry.available_flag_indices()))


def test_dispatcher_parses_invocation_and_delegates() -> None:
    context = DeviceContext()
    console_service = context.register_console_device()
    dispatcher = context.register_ampersand_dispatcher()
    flag_index = _registry_flag_index(dispatcher)

    expression = f"&,{flag_index},5,7:REM CHAIN"
    result = dispatcher.dispatch(expression)

    assert isinstance(result, AmpersandResult)
    assert result.flag_index == flag_index
    assert dispatcher.last_invocation is not None
    assert dispatcher.last_invocation.argument_x == 5
    assert dispatcher.last_invocation.argument_y == 7
    assert dispatcher.remainder == ":REM CHAIN"
    assert result.services["console"] is console_service


def test_dispatcher_uses_configured_overrides(tmp_path: Path) -> None:
    flag_index = next(iter(AmpersandRegistry().available_flag_indices()))
    module_path = tmp_path / "amp_override.py"
    module_path.write_text(
        "from scripts.prototypes.ampersand_registry import AmpersandResult\n"
        "def handler(ctx):\n"
        "    assert ctx.invocation.argument_x == 1\n"
        "    assert ctx.invocation.argument_y == 2\n"
        "    assert ctx.payload == {'origin': 'test'}\n"
        "    return AmpersandResult(\n"
        f"        flag_index={flag_index},\n"
        "        slot=0xFE,\n"
        "        handler_address=0xBEEF,\n"
        "        flag_records=(),\n"
        "        flag_directory_block=(),\n"
        "        flag_directory_tail=(),\n"
        "        flag_directory_text='',\n"
        "        context=ctx,\n"
        "        rendered_text='override',\n"
        "    )\n",
        encoding="utf-8",
    )

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "storage.toml"
    config_path.write_text(
        "[slots]\n"
        "8 = \"drive\"\n\n"
        "[ampersand_overrides]\n"
        f"0x{flag_index:x} = \"amp_override:handler\"\n",
        encoding="utf-8",
    )
    (config_dir / "drive").mkdir()

    sys.path.insert(0, str(tmp_path))
    try:
        config = load_drive_config(config_path)
        context = bootstrap_device_context(
            config.drives, ampersand_overrides=config.ampersand_overrides
        )
        dispatcher = context.get_service("ampersand")
        assert isinstance(dispatcher, AmpersandDispatcher)

        result = dispatcher.dispatch(f"&,{flag_index},1,2", payload={"origin": "test"})
        assert result.rendered_text == "override"
        assert isinstance(result.context, AmpersandDispatchContext)
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("amp_override", None)


def test_dispatcher_shares_console_service_with_registry() -> None:
    context = bootstrap_device_context(assignments=())
    dispatcher = context.get_service("ampersand")
    console_service = context.get_service("console")
    assert isinstance(dispatcher, AmpersandDispatcher)
    assert isinstance(console_service, ConsoleService)

    flag_index = _registry_flag_index(dispatcher)
    before = console_service.device.transcript_bytes

    result = dispatcher.dispatch(f"&,{flag_index}")

    assert result.services["console"] is console_service
    after = console_service.device.transcript_bytes
    assert after != before
    appended = after[len(before) :]
    glyph_run = console_service.glyph_lookup.macros_by_slot[result.slot]
    assert appended == bytes(glyph_run.payload)
