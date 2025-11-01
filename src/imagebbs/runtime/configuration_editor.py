"""Runtime configuration editor that mirrors the documented menu layout."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar, Mapping, Optional

from ..device_context import ConsoleService
from ..session_kernel import SessionKernel, SessionState


@dataclass(frozen=True)
class _EntryLayout:
    """Cache screen metadata required to toggle selection highlighting."""

    address: int
    glyphs: tuple[int, ...]
    colours: tuple[int, ...]


class ConfigurationEditorState(Enum):
    """High-level phases exposed by :class:`ConfigurationEditorModule`."""

    INTRO = auto()
    READY = auto()


class ConfigurationEditorEvent(Enum):
    """Events that drive rendering and command handling."""

    ENTER = auto()
    COMMAND = auto()


@dataclass
class ConfigurationEditorModule:
    """Finite-state controller that mirrors the V2.0 configuration editor layout."""

    state: ConfigurationEditorState = field(init=False, default=ConfigurationEditorState.INTRO)
    last_selection: str = field(init=False, default="")
    _console: ConsoleService | None = field(init=False, default=None)
    _entry_layouts: dict[str, "_EntryLayout"] = field(init=False, default_factory=dict)

    MENU_ENTRIES: ClassVar[tuple[tuple[str, str], ...]] = (
        ("A", "Macros Editor"),
        ("B", "Command Set"),
        ("C", "Payroll Editor"),
        ("D", "Logon Editor"),
        ("E", "Access Groups"),
        ("F", "File Lists"),
        ("G", "Function Keys"),
        ("H", "Lightbar/Alarm"),
        ("I", "Misc. Features"),
        ("J", "Modem Config"),
        ("K", "Set Time"),
        ("L", "System Drives"),
        ("M", "Netmail Config"),
        ("N", "Quit"),
    )

    _ENTRY_LOOKUP: ClassVar[Mapping[str, str]] = {code: name for code, name in MENU_ENTRIES}
    _PROMPT: ClassVar[str] = "CONFIG> "

    # Why: bind console access and draw the dual-column menu before accepting commands.
    def start(self, kernel: SessionKernel) -> SessionState:
        console = kernel.services.get("console")
        if not isinstance(console, ConsoleService):
            raise TypeError("console service missing from session kernel")
        self._console = console
        self.state = ConfigurationEditorState.INTRO
        self.last_selection = ""
        self._render_intro()
        self._render_prompt()
        return SessionState.CONFIGURATION_EDITOR

    # Why: translate session events into menu rendering and command dispatches.
    def handle_event(
        self,
        kernel: SessionKernel,
        event: ConfigurationEditorEvent,
        selection: Optional[str] = None,
    ) -> SessionState:
        if event is ConfigurationEditorEvent.ENTER:
            self._render_intro()
            self.state = ConfigurationEditorState.READY
            self._render_prompt()
            return SessionState.CONFIGURATION_EDITOR

        if event is ConfigurationEditorEvent.COMMAND:
            if self.state is not ConfigurationEditorState.READY:
                self._render_intro()
                self.state = ConfigurationEditorState.READY
                self._render_prompt()
                return SessionState.CONFIGURATION_EDITOR
            return self._handle_command(selection)

        raise ValueError(f"unsupported configuration-editor event: {event!r}")

    # Why: present the configuration editor heading and menu entries.
    def _render_intro(self) -> None:
        console = self._require_console()
        self._clear_screen(console)
        self._draw_title(console)
        self._render_panels(console)
        self._render_prompt()

    # Why: display the interactive prompt between commands.
    def _render_prompt(self) -> None:
        console = self._require_console()
        self._clear_prompt_row(console)
        console.set_cursor(self._PROMPT_COLUMN, self._PROMPT_ROW)
        console.write(self._PROMPT)

    # Why: normalise selection text and trigger command side effects.
    def _handle_command(self, selection: Optional[str]) -> SessionState:
        command = self._normalise_command(selection)
        if not command:
            self._render_prompt()
            return SessionState.CONFIGURATION_EDITOR
        if command == "N":
            self._set_selection(command)
            self._show_status("Leaving configuration editor...")
            return SessionState.MAIN_MENU
        name = self._ENTRY_LOOKUP.get(command)
        if name is not None:
            self._set_selection(command)
            self._show_status(f"{name} module is not yet implemented.")
            self._render_prompt()
            return SessionState.CONFIGURATION_EDITOR
        self._show_status("?INVALID CONFIGURATION COMMAND")
        self._render_prompt()
        return SessionState.CONFIGURATION_EDITOR

    # Why: derive the canonical command token from arbitrary input text.
    def _normalise_command(self, selection: Optional[str]) -> str:
        if not selection:
            return ""
        text = selection.strip().upper()
        if not text:
            return ""
        return text[0]

    # Why: ensure the console service is available before rendering spans.
    def _require_console(self) -> ConsoleService:
        if not isinstance(self._console, ConsoleService):
            raise RuntimeError("console service is unavailable")
        return self._console

    # Why: compute absolute screen addresses for the layout helpers.
    def _screen_address(self, x: int, y: int) -> int:
        return ConsoleService._SCREEN_BASE + (y * self._SCREEN_WIDTH) + x

    # Why: translate screen addresses into matching colour-RAM offsets.
    def _colour_address(self, address: int) -> int:
        return ConsoleService._colour_address_for(address)

    # Why: blank the display so panel rendering can start from a clean buffer.
    def _clear_screen(self, console: ConsoleService) -> None:
        console.write(chr(0x93))

    # Why: write ASCII text at a specific coordinate while tracking colour hints.
    def _write_text(
        self,
        console: ConsoleService,
        x: int,
        y: int,
        text: str,
        *,
        colour: int | None = None,
    ) -> None:
        if not text:
            return
        glyphs = [ord(char) & 0x7F for char in text]
        address = self._screen_address(x, y)
        kwargs: dict[str, object] = {"screen_address": address, "screen_bytes": glyphs}
        if colour is not None:
            colour_value = int(colour) & 0x0F
            colours = [colour_value] * len(glyphs)
            kwargs["colour_address"] = self._colour_address(address)
            kwargs["colour_bytes"] = colours
        console.poke_block(**kwargs)

    # Why: centre the configuration editor heading above the panel layout.
    def _draw_title(self, console: ConsoleService) -> None:
        title = "IMAGE BBS CONFIGURATION EDITOR"
        intro = "Select a module by its highlighted letter:".upper()
        offset = max(0, (self._SCREEN_WIDTH - len(title)) // 2)
        self._write_text(console, offset, 0, title)
        self._write_text(console, 2, 2, intro)

    # Why: draw both bordered panels and populate them with menu entries.
    def _render_panels(self, console: ConsoleService) -> None:
        self._entry_layouts.clear()
        left_entries = self.MENU_ENTRIES[:7]
        right_entries = self.MENU_ENTRIES[7:14]
        self._render_panel(console, self._LEFT_PANEL_X, self._PANEL_Y, left_entries)
        self._render_panel(console, self._RIGHT_PANEL_X, self._PANEL_Y, right_entries)
        default_code = left_entries[0][0]
        if not self.last_selection:
            self.last_selection = default_code
        self._set_selection(self.last_selection)

    # Why: draw a single bordered panel and stage entry glyph metadata.
    def _render_panel(
        self,
        console: ConsoleService,
        origin_x: int,
        origin_y: int,
        entries: tuple[tuple[str, str], ...],
    ) -> None:
        panel_height = len(entries) + 2
        panel_width = self._PANEL_WIDTH
        for index in range(panel_height):
            address = self._screen_address(origin_x, origin_y + index)
            if index == 0:
                glyphs = self._panel_top_row(panel_width)
            elif index == panel_height - 1:
                glyphs = self._panel_bottom_row(panel_width)
            else:
                glyphs = self._panel_middle_row(panel_width)
            colours = self._panel_colour_row(panel_width)
            console.poke_block(
                screen_address=address,
                screen_bytes=glyphs,
                colour_address=self._colour_address(address),
                colour_bytes=colours,
            )

        for row, (code, name) in enumerate(entries):
            self._render_entry_row(
                console,
                origin_x + 1,
                origin_y + 1 + row,
                code,
                name,
            )

    # Why: build the top border row for a panel using PETSCII line art.
    def _panel_top_row(self, width: int) -> list[int]:
        if width < 2:
            raise ValueError("panel width must be at least two cells")
        return [
            self._CHAR_TOP_LEFT,
            *([self._CHAR_HORIZONTAL] * (width - 2)),
            self._CHAR_TOP_RIGHT,
        ]

    # Why: build the bottom border row for a panel using PETSCII line art.
    def _panel_bottom_row(self, width: int) -> list[int]:
        if width < 2:
            raise ValueError("panel width must be at least two cells")
        return [
            self._CHAR_BOTTOM_LEFT,
            *([self._CHAR_BOTTOM] * (width - 2)),
            self._CHAR_BOTTOM_RIGHT,
        ]

    # Why: build an interior panel row with vertical rails and space padding.
    def _panel_middle_row(self, width: int) -> list[int]:
        if width < 2:
            raise ValueError("panel width must be at least two cells")
        return [
            self._CHAR_VERTICAL_LEFT,
            *([0x20] * (width - 2)),
            self._CHAR_VERTICAL_RIGHT,
        ]

    # Why: assign consistent border colours while leaving room for entry accents.
    def _panel_colour_row(self, width: int) -> list[int]:
        if width < 0:
            raise ValueError("panel width must be non-negative")
        return [self._PANEL_BORDER_COLOUR] * width

    # Why: render a single entry row, cache its glyph metadata, and highlight the shortcut.
    def _render_entry_row(
        self,
        console: ConsoleService,
        x: int,
        y: int,
        code: str,
        name: str,
    ) -> None:
        label = f"{code.upper()}) {name.upper()}"
        text = label[: self._PANEL_WIDTH - 2].ljust(self._PANEL_WIDTH - 2)
        glyphs = [ord(char) & 0x7F for char in text]
        colours = [self._ENTRY_COLOUR] * len(glyphs)
        if colours:
            colours[0] = self._ENTRY_HIGHLIGHT_COLOUR
        address = self._screen_address(x, y)
        console.poke_block(
            screen_address=address,
            screen_bytes=glyphs,
            colour_address=self._colour_address(address),
            colour_bytes=colours,
        )
        self._entry_layouts[code.upper()] = _EntryLayout(
            address=address,
            glyphs=tuple(glyphs),
            colours=tuple(colours),
        )

    # Why: apply or clear reverse-video highlighting for a specific entry row.
    def _render_entry_selection(self, code: str, *, selected: bool) -> None:
        layout = self._entry_layouts.get(code.upper())
        if layout is None:
            return
        console = self._require_console()
        if selected:
            glyphs = [value | 0x80 for value in layout.glyphs]
        else:
            glyphs = [value & 0x7F for value in layout.glyphs]
        console.poke_block(
            screen_address=layout.address,
            screen_bytes=glyphs,
            colour_address=self._colour_address(layout.address),
            colour_bytes=layout.colours,
        )

    # Why: update selection state so the currently active entry remains inverted.
    def _set_selection(self, code: str) -> None:
        code_normalised = code.upper()
        if self.last_selection and self.last_selection.upper() != code_normalised:
            self._render_entry_selection(self.last_selection, selected=False)
        self._render_entry_selection(code_normalised, selected=True)
        self.last_selection = code_normalised

    # Why: clear any lingering status text before refreshing the prompt row.
    def _clear_prompt_row(self, console: ConsoleService) -> None:
        self._write_text(console, 0, self._PROMPT_ROW, " " * self._SCREEN_WIDTH)

    # Why: surface contextual responses without disturbing the panel layout.
    def _show_status(self, message: str) -> None:
        console = self._require_console()
        text = message[: self._SCREEN_WIDTH].ljust(self._SCREEN_WIDTH)
        self._write_text(console, 0, self._STATUS_ROW, text)

    _SCREEN_WIDTH: ClassVar[int] = 40
    _ENTRIES_PER_COLUMN: ClassVar[int] = len(MENU_ENTRIES) // 2
    _LEFT_PANEL_X: ClassVar[int] = 1
    _RIGHT_PANEL_X: ClassVar[int] = 20
    _PANEL_Y: ClassVar[int] = 3
    _PANEL_WIDTH: ClassVar[int] = 19
    _PROMPT_ROW: ClassVar[int] = _PANEL_Y + _ENTRIES_PER_COLUMN + 2
    _PROMPT_COLUMN: ClassVar[int] = 0
    _STATUS_ROW: ClassVar[int] = _PROMPT_ROW + 1
    _PANEL_BORDER_COLOUR: ClassVar[int] = 0x01
    _ENTRY_COLOUR: ClassVar[int] = 0x01
    _ENTRY_HIGHLIGHT_COLOUR: ClassVar[int] = 0x0E
    _CHAR_TOP_LEFT: ClassVar[int] = 0x4F
    _CHAR_TOP_RIGHT: ClassVar[int] = 0x50
    _CHAR_BOTTOM_LEFT: ClassVar[int] = 0x4C
    _CHAR_BOTTOM_RIGHT: ClassVar[int] = 0x7A
    _CHAR_HORIZONTAL: ClassVar[int] = 0x63
    _CHAR_BOTTOM: ClassVar[int] = 0x64
    _CHAR_VERTICAL_LEFT: ClassVar[int] = 0x74
    _CHAR_VERTICAL_RIGHT: ClassVar[int] = 0x76


__all__ = [
    "ConfigurationEditorEvent",
    "ConfigurationEditorModule",
    "ConfigurationEditorState",
]
