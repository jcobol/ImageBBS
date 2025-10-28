from __future__ import annotations

import sys
from pathlib import Path

from imagebbs.ampersand_registry import AmpersandRegistry, AmpersandResult
from imagebbs.device_context import ConsoleService, bootstrap_device_context
from imagebbs.message_editor import Event, MessageEditor, SessionContext


def test_registry_default_dispatch_exposes_overlay_data() -> None:
    registry = AmpersandRegistry()
    defaults = registry.defaults
    flag_index = next(iter(registry.available_flag_indices()))

    result = registry.dispatch(flag_index, context=None, use_default=True)

    assert isinstance(result, AmpersandResult)
    assert result.flag_records == defaults.flag_records
    assert result.flag_directory_tail == defaults.flag_directory_tail
    assert result.flag_directory_text == defaults.flag_directory_text
    assert "console" in result.services
    assert isinstance(result.services["console"], ConsoleService)
    assert result.rendered_text is not None


def test_registry_override_can_call_default() -> None:
    registry = AmpersandRegistry()
    defaults = registry.defaults
    flag_index = next(iter(registry.available_flag_indices()))

    def custom_handler(context: object) -> AmpersandResult:
        return AmpersandResult(
            flag_index=flag_index,
            slot=0xFF,
            handler_address=0xDEAD,
            flag_records=defaults.flag_records,
            flag_directory_block=defaults.flag_directory_block,
            flag_directory_tail=defaults.flag_directory_tail,
            flag_directory_text=defaults.flag_directory_text,
            context=context,
            rendered_text="custom",
        )

    registry.register_handler(flag_index, custom_handler)

    override_result = registry.dispatch(flag_index, context=None)
    assert override_result.rendered_text == "custom"
    assert override_result.slot == 0xFF

    default_result = registry.dispatch(flag_index, context=None, use_default=True)
    dispatch_entry = next(
        entry for entry in defaults.flag_dispatch.entries if entry.flag_index == flag_index
    )
    assert default_result.slot == dispatch_entry.slot
    assert default_result.handler_address == dispatch_entry.handler_address


def test_registry_loads_override_imports(tmp_path: Path) -> None:
    flag_index = MessageEditor.INTRO_MACRO_INDEX

    module_path = tmp_path / "custom_ampersand.py"
    module_path.write_text(
        "from imagebbs.ampersand_registry import AmpersandResult\n"
        "from imagebbs.ml_extra_defaults import MLExtraDefaults\n"
        f"FLAG_INDEX = {flag_index}\n"
        "_DEFAULTS = MLExtraDefaults.from_overlay()\n\n"
        "def intro_override(context):\n"
        "    return AmpersandResult(\n"
        "        flag_index=FLAG_INDEX,\n"
        "        slot=0xFE,\n"
        "        handler_address=0xBEEF,\n"
        "        flag_records=_DEFAULTS.flag_records,\n"
        "        flag_directory_block=_DEFAULTS.flag_directory_block,\n"
        "        flag_directory_tail=_DEFAULTS.flag_directory_tail,\n"
        "        flag_directory_text=_DEFAULTS.flag_directory_text,\n"
        "        context=context,\n"
        "        rendered_text=\"CONFIG OVERRIDE\",\n"
        "    )\n",
        encoding="utf-8",
    )

    sys.path.insert(0, str(tmp_path))
    try:
        registry = AmpersandRegistry(override_imports={flag_index: "custom_ampersand:intro_override"})
        result = registry.dispatch(flag_index, context=None)
        assert result.rendered_text == "CONFIG OVERRIDE"

        default_result = registry.dispatch(flag_index, context=None, use_default=True)
        assert default_result.rendered_text != "CONFIG OVERRIDE"
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("custom_ampersand", None)


def test_registry_default_handler_uses_device_context_console_service() -> None:
    context = bootstrap_device_context(assignments=())
    console_service = context.get_service("console")
    assert isinstance(console_service, ConsoleService)
    before = console_service.device.transcript_bytes

    registry = AmpersandRegistry(services=context.services)
    flag_index = next(iter(registry.available_flag_indices()))

    result = registry.dispatch(flag_index, context=None, use_default=True)

    assert result.services["console"] is console_service
    assert console_service.device.transcript_bytes != before
    assert result.rendered_text is not None
    after = console_service.device.transcript_bytes
    appended = after[len(before) :]
    glyph_run = console_service.glyph_lookup.macros_by_slot[result.slot]
    assert appended == bytes(glyph_run.payload)
    assert result.rendered_text == glyph_run.text


def test_registry_register_service_merges_custom_service() -> None:
    registry = AmpersandRegistry()
    sentinel = object()
    registry.register_service("custom", sentinel)
    flag_index = next(iter(registry.available_flag_indices()))

    result = registry.dispatch(flag_index, context=None, use_default=True)

    assert result.services["custom"] is sentinel


def test_message_editor_uses_registry_override_for_intro_banner() -> None:
    registry = AmpersandRegistry()
    flag_index = MessageEditor.INTRO_MACRO_INDEX

    def intro_override(context: object) -> AmpersandResult:
        defaults = registry.defaults
        return AmpersandResult(
            flag_index=flag_index,
            slot=0xAB,
            handler_address=0x1234,
            flag_records=defaults.flag_records,
            flag_directory_block=defaults.flag_directory_block,
            flag_directory_tail=defaults.flag_directory_tail,
            flag_directory_text=defaults.flag_directory_text,
            context=context,
            rendered_text="\rCUSTOM BANNER\r",
        )

    registry.register_handler(flag_index, intro_override)

    editor = MessageEditor(registry=registry)
    session = SessionContext(board_id="board", user_id="user")

    editor.dispatch(Event.ENTER, session)

    assert session.modem_buffer == ["\rCUSTOM BANNER\r"]
