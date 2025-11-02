"""Handlers that mirror ImageBBS configuration editor modules."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Optional, Sequence, Tuple, TYPE_CHECKING

from ...session_kernel import SessionKernel, SessionState
from ...setup_defaults import CommodoreDeviceDrive, DriveAssignment, SetupDefaults

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from ..configuration_editor import ConfigurationEditorModule


@dataclass
class _DriveSummary:
    """Immutable snapshot summarising a logical drive assignment."""

    slot: int
    locator: Optional[str]
    read_only: bool


class ConfigurationEditorHandler:
    """Base class shared by configuration-editor submodules."""

    # Why: capture shared services so menu handlers mirror BASIC workflow scaffolding.
    def __init__(self, kernel: SessionKernel, editor: "ConfigurationEditorModule") -> None:
        self.kernel = kernel
        self.editor = editor
        defaults = getattr(kernel, "defaults", None)
        if not isinstance(defaults, SetupDefaults):
            defaults = SetupDefaults.stub()
            try:
                setattr(kernel, "defaults", defaults)
            except (AttributeError, TypeError):  # pragma: no cover - defensive stub hook
                pass
        self.defaults = defaults
        self.console = editor._require_console()

    # Why: provide a consistent rendering hook so derived handlers emit status text and restore prompts.
    def _status(self, message: str) -> None:
        self.editor._show_status(message)
        self.editor._render_prompt()

    # Why: surface Commodore-style drive descriptions for confirmation prompts and status text.
    def _summarise_drives(self, assignments: Sequence[DriveAssignment]) -> Tuple[_DriveSummary, ...]:
        summary: list[_DriveSummary] = []
        for assignment in assignments:
            locator = assignment.locator
            if isinstance(locator, CommodoreDeviceDrive):
                description = f"{locator.device}/{locator.drive}"
            elif locator is None:
                description = None
            else:
                description = locator.describe()
            summary.append(
                _DriveSummary(
                    slot=assignment.slot,
                    locator=description,
                    read_only=assignment.read_only,
                )
            )
        return tuple(summary)

    # Why: allow concrete handlers to respond to command arguments and update defaults accordingly.
    def handle(self, argument: Optional[str]) -> SessionState:
        raise NotImplementedError

    # Why: persist mutated copies of :class:`SetupDefaults` so subsequent handlers see committed state.
    def _replace_defaults(self, **changes: object) -> SetupDefaults:
        updated = replace(self.defaults, **changes)
        try:
            setattr(self.kernel, "defaults", updated)
        except (AttributeError, TypeError):  # pragma: no cover - defensive stub hook
            pass
        self.defaults = updated
        return updated


class MacrosEditorHandler(ConfigurationEditorHandler):
    """Expose overlay sequencing derived from ``setup.bas``."""

    # Why: present the overlay load order and accept simple reassignment commands.
    def handle(self, argument: Optional[str]) -> SessionState:
        overlays = tuple(self.defaults.macro_modules)
        if argument:
            entries = [segment.strip().upper() for segment in argument.replace(";", ",").split(",")]
            modules = tuple(entry for entry in entries if entry)
            if modules:
                self._replace_defaults(macro_modules=modules)
                self._status(f"Overlay order updated: {', '.join(modules)}")
                return SessionState.CONFIGURATION_EDITOR
            self._status("Overlay update ignored: no modules supplied.")
            return SessionState.CONFIGURATION_EDITOR
        overlay_text = ", ".join(overlays) if overlays else "No overlays configured"
        self._status(f"Overlay order: {overlay_text}")
        return SessionState.CONFIGURATION_EDITOR


class CommandSetHandler(ConfigurationEditorHandler):
    """Summarise command options pulled from ``setup.bas`` data records."""

    # Why: surface the CO-option menu text so sysops can cross-reference BASIC behaviour.
    def handle(self, argument: Optional[str]) -> SessionState:
        records = self.defaults.data_records
        options = ", ".join(records.co_options)
        self._status(f"CO options: {options}")
        return SessionState.CONFIGURATION_EDITOR


class PayrollEditorHandler(ConfigurationEditorHandler):
    """Report credit and statistics defaults maintained by setup."""

    # Why: remind sysops how many credits new callers receive alongside current totals.
    def handle(self, argument: Optional[str]) -> SessionState:
        credits = self.defaults.new_user_credits
        banner = self.defaults.stats_banner
        self._status(f"Credits {credits}; banner: {banner[:20]}")
        return SessionState.CONFIGURATION_EDITOR


class LogonEditorHandler(ConfigurationEditorHandler):
    """Expose logon banners and identifiers from the setup manifest."""

    # Why: reiterate the board name and prompt so operators know the active identity.
    def handle(self, argument: Optional[str]) -> SessionState:
        board = self.defaults.board_name
        prompt = self.defaults.prompt
        self._status(f"Board {board} / Prompt {prompt}")
        return SessionState.CONFIGURATION_EDITOR


class AccessGroupsHandler(ConfigurationEditorHandler):
    """Show library codes configured by setup."""

    # Why: list provisioned access codes so the Commodore menu groupings remain visible.
    def handle(self, argument: Optional[str]) -> SessionState:
        codes = ", ".join(self.defaults.library_codes)
        self._status(f"Access codes: {codes or 'None'}")
        return SessionState.CONFIGURATION_EDITOR


class FileListsHandler(ConfigurationEditorHandler):
    """Summarise file library descriptors seeded by setup."""

    # Why: present library counts so operators gauge catalogue coverage before entering subsystems.
    def handle(self, argument: Optional[str]) -> SessionState:
        libraries = self.defaults.file_libraries
        if not libraries:
            self._status("No file libraries configured")
            return SessionState.CONFIGURATION_EDITOR
        names = ", ".join(descriptor.name for descriptor in libraries[:3])
        self._status(f"Libraries: {names}")
        return SessionState.CONFIGURATION_EDITOR


class FunctionKeysHandler(ConfigurationEditorHandler):
    """Highlight PETSCII bindings mirrored from ``setup.bas`` records."""

    # Why: expose lightbar PETSCII codes so sysops can verify key mappings.
    def handle(self, argument: Optional[str]) -> SessionState:
        records = self.defaults.data_records
        codes = " ".join(f"{value:02X}" for value in records.lightbar_char_codes)
        self._status(f"Lightbar codes: {codes}")
        return SessionState.CONFIGURATION_EDITOR


class LightbarAlarmHandler(ConfigurationEditorHandler):
    """List lightbar labels that back the alarm display."""

    # Why: echo the recovered label text so Commodore prompts can be verified quickly.
    def handle(self, argument: Optional[str]) -> SessionState:
        records = self.defaults.data_records
        labels = ", ".join(records.lightbar_labels[:3])
        self._status(f"Alarm labels: {labels}")
        return SessionState.CONFIGURATION_EDITOR


class MiscFeaturesHandler(ConfigurationEditorHandler):
    """Summarise miscellaneous configuration hints."""

    # Why: showcase chat banners and last caller metadata without leaving the editor.
    def handle(self, argument: Optional[str]) -> SessionState:
        caller = self.defaults.last_caller
        chat = self.defaults.chat_mode_entering
        self._status(f"Last caller {caller}; chat: {chat[:12]}")
        return SessionState.CONFIGURATION_EDITOR


class ModemConfigHandler(ConfigurationEditorHandler):
    """Expose modem defaults lifted from the setup stub."""

    # Why: confirm the baud cap so serial workflows can be reasoned about before editing.
    def handle(self, argument: Optional[str]) -> SessionState:
        baud = getattr(self.defaults.modem, "baud_limit", None)
        self._status(f"Modem baud: {baud or 'auto'}")
        return SessionState.CONFIGURATION_EDITOR


class SetTimeHandler(ConfigurationEditorHandler):
    """Echo prime-time windows stored in ``e.data``."""

    # Why: show stored prime-time hours so sysops can decide if adjustments are required.
    def handle(self, argument: Optional[str]) -> SessionState:
        window = self.defaults.prime_time
        self._status(f"Prime {window.start_hour}-{window.end_hour} flag {window.indicator}")
        return SessionState.CONFIGURATION_EDITOR


class SystemDrivesHandler(ConfigurationEditorHandler):
    """Display configured device mappings and accept reassignment commands."""

    # Why: allow sysops to update legacy device tuples while providing a quick summary of current wiring.
    def handle(self, argument: Optional[str]) -> SessionState:
        assignments = list(self.defaults.drives)
        if argument:
            updated = self._apply_drive_assignment(assignments, argument)
            if updated:
                self._replace_defaults(drives=tuple(updated))
                summary = self._summarise_drives(updated)
                self._status(self._format_drive_summary(summary))
                return SessionState.CONFIGURATION_EDITOR
        summary = self._summarise_drives(assignments)
        self._status(self._format_drive_summary(summary))
        return SessionState.CONFIGURATION_EDITOR

    # Why: parse simple ``slot=device/drive`` tokens into immutable drive assignments.
    def _apply_drive_assignment(
        self, assignments: Sequence[DriveAssignment], argument: str
    ) -> Tuple[DriveAssignment, ...] | None:
        tokens = [segment.strip() for segment in argument.split()] if argument else []
        if not tokens:
            return None
        mapping = {assignment.slot: assignment for assignment in assignments}
        updates: dict[int, DriveAssignment] = {}
        for token in tokens:
            if "=" not in token:
                continue
            slot_text, device_text = token.split("=", 1)
            try:
                slot = int(slot_text)
            except ValueError:
                continue
            if "/" not in device_text:
                continue
            device_part, drive_part = device_text.split("/", 1)
            try:
                device = int(device_part)
                drive = int(drive_part)
            except ValueError:
                continue
            updates[slot] = DriveAssignment(
                slot=slot,
                locator=CommodoreDeviceDrive(device=device, drive=drive),
            )
        if not updates:
            return None
        merged: list[DriveAssignment] = []
        max_slot = max(max(mapping.keys(), default=0), max(updates.keys(), default=0))
        for slot in range(1, max_slot + 1):
            merged.append(updates.get(slot, mapping.get(slot, DriveAssignment(slot=slot))))
        return tuple(merged)

    # Why: format drive summaries so status text mirrors Commodore prompts.
    def _format_drive_summary(self, summary: Iterable[_DriveSummary]) -> str:
        parts = []
        for entry in summary:
            locator = entry.locator or "--"
            suffix = "*" if entry.read_only else ""
            parts.append(f"{entry.slot}:{locator}{suffix}")
        return "Drives: " + ", ".join(parts)


class NetmailConfigHandler(ConfigurationEditorHandler):
    """Expose board identifiers used by the netmail subsystem."""

    # Why: remind sysops of the configured board identifier so netmail overlays can be staged correctly.
    def handle(self, argument: Optional[str]) -> SessionState:
        identifier = self.defaults.board_identifier
        self._status(f"Netmail board id: {identifier}")
        return SessionState.CONFIGURATION_EDITOR


__all__ = [
    "ConfigurationEditorHandler",
    "MacrosEditorHandler",
    "CommandSetHandler",
    "PayrollEditorHandler",
    "LogonEditorHandler",
    "AccessGroupsHandler",
    "FileListsHandler",
    "FunctionKeysHandler",
    "LightbarAlarmHandler",
    "MiscFeaturesHandler",
    "ModemConfigHandler",
    "SetTimeHandler",
    "SystemDrivesHandler",
    "NetmailConfigHandler",
]
