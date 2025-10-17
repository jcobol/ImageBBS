from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.ampersand_registry import AmpersandRegistry, AmpersandResult
from scripts.prototypes.message_editor import Event, MessageEditor, SessionContext


def test_registry_default_dispatch_exposes_overlay_data() -> None:
    registry = AmpersandRegistry()
    defaults = registry.defaults
    flag_index = next(iter(registry.available_flag_indices()))

    result = registry.dispatch(flag_index, context=None, use_default=True)

    assert isinstance(result, AmpersandResult)
    assert result.flag_records == defaults.flag_records
    assert result.flag_directory_tail == defaults.flag_directory_tail
    assert result.flag_directory_text == defaults.flag_directory_text


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
