"""Runtime approximation of the ImageBBS upload/download libraries."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional

from ..ampersand_registry import AmpersandRegistry
from ..device_context import ConsoleService
from ..session_kernel import SessionKernel, SessionState
from ..setup_defaults import FileLibraryDescriptor, FileLibraryEntry


class FileLibraryState(Enum):
    """High-level states exposed by :class:`FileLibraryModule`."""

    INTRO = auto()
    READY = auto()


class FileLibraryEvent(Enum):
    """Events that drive :class:`FileLibraryModule` transitions."""

    ENTER = auto()
    COMMAND = auto()


@dataclass
class FileLibraryModule:
    """Finite-state approximation of the BASIC UD/UX library dispatcher."""

    library_code: str
    invoked_command: str
    registry: Optional[AmpersandRegistry] = None
    state: FileLibraryState = field(init=False, default=FileLibraryState.INTRO)
    last_command: str = field(init=False, default="")
    _console: ConsoleService | None = field(init=False, default=None)
    _libraries: tuple[FileLibraryDescriptor, ...] = field(
        init=False, default_factory=tuple
    )
    _entries_by_id: Dict[str, list[FileLibraryEntry]] = field(
        init=False, default_factory=dict
    )
    _stats_by_id: Dict[str, Dict[str, int]] = field(init=False, default_factory=dict)
    _active_identifier: str = field(init=False, default="")
    _macro_name: str | None = field(init=False, default=None)
    _defaults: object | None = field(init=False, default=None)

    # Why: wire runtime services and seed cached metadata so commands can execute deterministically.
    def start(self, kernel: SessionKernel) -> SessionState:
        console = kernel.services.get("console")
        if not isinstance(console, ConsoleService):
            raise TypeError("console service missing from session kernel")
        self._console = console
        self.registry = kernel.dispatcher.registry
        defaults = kernel.defaults
        self._defaults = defaults
        code = (self.library_code or "UD").upper()
        self._libraries = defaults.libraries_for_code(code)
        if not self._libraries:
            raise RuntimeError(f"no libraries available for code {code!r}")
        self._entries_by_id.clear()
        self._stats_by_id.clear()
        for descriptor in self._libraries:
            self._entries_by_id[descriptor.identifier] = [
                FileLibraryEntry(
                    number=entry.number,
                    filename=entry.filename,
                    blocks=entry.blocks,
                    downloads=entry.downloads,
                    description=entry.description,
                    uploader=entry.uploader,
                    validated=entry.validated,
                )
                for entry in descriptor.entries
            ]
            self._stats_by_id[descriptor.identifier] = {
                "total_files": descriptor.total_files,
                "new_files": descriptor.new_files,
                "credit_balance": descriptor.credit_balance,
            }
        self._active_identifier = self._libraries[0].identifier
        self._macro_name = self._libraries[0].macro
        self.state = FileLibraryState.INTRO
        self.last_command = ""
        self._render_intro()
        self._render_prompt()
        return SessionState.FILE_LIBRARY

    # Why: translate terminal input into library actions that mirror BASIC command groups.
    def handle_event(
        self,
        kernel: SessionKernel,
        event: FileLibraryEvent,
        selection: Optional[str] = None,
    ) -> SessionState:
        if event is FileLibraryEvent.ENTER:
            self._render_status()
            self.state = FileLibraryState.READY
            self._render_prompt()
            return SessionState.FILE_LIBRARY

        if event is FileLibraryEvent.COMMAND:
            if self.state is not FileLibraryState.READY:
                self._render_status()
                self.state = FileLibraryState.READY
                self._render_prompt()
                return SessionState.FILE_LIBRARY

            command = (selection or "").strip()
            if not command:
                self._render_prompt()
                return SessionState.FILE_LIBRARY

            upper = command.upper()
            self.last_command = upper

            if upper.startswith("Q"):
                self._write_line("Returning to file transfers...")
                return SessionState.FILE_TRANSFERS
            if upper.startswith("L"):
                self._list_libraries()
            elif upper.startswith("N"):
                self._show_library_name()
            elif upper.startswith("M"):
                self._move_library(command)
            elif upper.startswith("S") or upper.startswith("$"):
                self._list_entries()
            elif upper.startswith("A"):
                self._add_entry(command)
            elif upper.startswith("K"):
                self._delete_entry(command)
            else:
                self._write_line("?UNRECOGNIZED LIBRARY COMMAND")
            self._render_prompt()
            return SessionState.FILE_LIBRARY

        raise ValueError(f"unsupported file-library event: {event!r}")

    # Why: inject macro text and current statistics so callers see the BASIC entry banner.
    def _render_intro(self) -> None:
        self._render_status()
        defaults = self._defaults
        macro_text: Optional[str] = None
        if hasattr(defaults, "library_macro"):
            macro_text = defaults.library_macro(self._macro_name or "")  # type: ignore[union-attr]
        if macro_text:
            for line in macro_text.splitlines():
                self._write_line(line)

    # Why: summarise active library metadata after transitions and mutations.
    def _render_status(self) -> None:
        library = self._current_library()
        stats = self._stats_by_id.get(library.identifier, {})
        entries = self._entries_for_library(library.identifier)
        total = stats.get("total_files", len(entries))
        new = stats.get("new_files", 0)
        credits = stats.get("credit_balance", 0)
        self._write_line(
            f"Library: {library.display_path} ({library.code}-{library.identifier})"
        )
        self._write_line(
            f"Total files: {total}  New: {new}  Credits: {credits}"
        )
        subops = ", ".join(library.subops) if library.subops else "None"
        self._write_line(
            f"Protocol: {library.protocol}  Subop: {subops}"
        )

    # Why: mirror BASIC's prompt updates between commands.
    def _render_prompt(self) -> None:
        library = self._current_library()
        self._write_line(f"{library.code}> ")

    # Why: provide visibility into available libraries and their hierarchy.
    def _list_libraries(self) -> None:
        self._write_line("Available libraries:")
        for descriptor in self._libraries:
            prefix = "*" if descriptor.identifier == self._active_identifier else " "
            self._write_line(
                f"{prefix} {descriptor.identifier}: {descriptor.display_path} (drive {descriptor.drive_slot})"
            )

    # Why: echo the human-readable name for the currently active library.
    def _show_library_name(self) -> None:
        library = self._current_library()
        self._write_line(f"You are in {library.display_path}.")

    # Why: switch the active library based on either identifier tokens or sequential rotation.
    def _move_library(self, command: str) -> None:
        tokens = command.strip().split(maxsplit=1)
        if len(tokens) == 1:
            target = self._next_identifier()
        else:
            target = tokens[1].strip()
        if not target:
            target = self._next_identifier()
        for descriptor in self._libraries:
            if descriptor.identifier == target or descriptor.name.upper() == target.upper():
                self._active_identifier = descriptor.identifier
                self._macro_name = descriptor.macro
                defaults = self._defaults
                macro_text = None
                if hasattr(defaults, "library_macro"):
                    macro_text = defaults.library_macro(descriptor.macro)  # type: ignore[union-attr]
                self._write_line(f"Moved to {descriptor.display_path}.")
                if macro_text:
                    for line in macro_text.splitlines():
                        self._write_line(line)
                self._render_status()
                return
        self._write_line("?NO SUCH LIBRARY")

    # Why: present the file directory with metadata similar to the BASIC listings.
    def _list_entries(self) -> None:
        entries = self._entries_for_library(self._active_identifier)
        if not entries:
            self._write_line("No entries in this library.")
            return
        for entry in sorted(entries, key=lambda item: item.number):
            status = "VALID" if entry.validated else "PENDING"
            self._write_line(
                f"#{entry.number:02d} {entry.blocks:>3} blocks {entry.downloads:>3} downloads {entry.filename} - {entry.description} ({status})"
            )

    # Why: allow tests to simulate uploads by injecting new directory records.
    def _add_entry(self, command: str) -> None:
        parts = command.split(maxsplit=3)
        if len(parts) < 3:
            self._write_line("?USAGE: A <FILENAME> <BLOCKS> [DESCRIPTION]")
            return
        filename = parts[1].strip().upper()
        try:
            blocks = int(parts[2])
        except ValueError:
            self._write_line("?BLOCK COUNT MUST BE NUMERIC")
            return
        description = parts[3].strip() if len(parts) > 3 else ""
        entries = self._entries_for_library(self._active_identifier)
        next_number = max((entry.number for entry in entries), default=0) + 1
        uploader = self._default_uploader()
        record = FileLibraryEntry(
            number=next_number,
            filename=filename,
            blocks=blocks,
            downloads=0,
            description=description or "No description provided",
            uploader=uploader,
            validated=False,
        )
        entries.append(record)
        stats = self._stats_by_id.setdefault(self._active_identifier, {})
        stats["total_files"] = stats.get("total_files", len(entries) - 1) + 1
        stats["new_files"] = stats.get("new_files", 0) + 1
        self._write_line(f"Added {filename} as entry #{next_number}.")

    # Why: emulate the BASIC delete command for integration testing.
    def _delete_entry(self, command: str) -> None:
        parts = command.split(maxsplit=1)
        if len(parts) < 2:
            self._write_line("?USAGE: K <NUMBER>")
            return
        try:
            target = int(parts[1].strip())
        except ValueError:
            self._write_line("?ENTRY NUMBER REQUIRED")
            return
        entries = self._entries_for_library(self._active_identifier)
        for index, entry in enumerate(list(entries)):
            if entry.number == target:
                entries.pop(index)
                stats = self._stats_by_id.setdefault(self._active_identifier, {})
                stats["total_files"] = max(stats.get("total_files", len(entries) + 1) - 1, 0)
                self._write_line(f"Removed entry #{target}.")
                return
        self._write_line("?NO SUCH ENTRY")

    # Why: resolve the active library descriptor for downstream helpers.
    def _current_library(self) -> FileLibraryDescriptor:
        for descriptor in self._libraries:
            if descriptor.identifier == self._active_identifier:
                return descriptor
        return self._libraries[0]

    # Why: supply a mutable list for the active library while preserving stored descriptors.
    def _entries_for_library(self, identifier: str) -> list[FileLibraryEntry]:
        return self._entries_by_id.setdefault(identifier, [])

    # Why: compute the next identifier when callers omit explicit targets.
    def _next_identifier(self) -> str:
        identifiers = [descriptor.identifier for descriptor in self._libraries]
        if self._active_identifier not in identifiers:
            return identifiers[0]
        index = identifiers.index(self._active_identifier)
        return identifiers[(index + 1) % len(identifiers)]

    # Why: provide a consistent uploader tag for synthetic test entries.
    def _default_uploader(self) -> str:
        library = self._current_library()
        if library.subops:
            return library.subops[0]
        return "SYSOP"

    # Why: centralise console writes so tests can inspect emitted lines.
    def _write_line(self, text: str, *, end: str = "\r") -> None:
        if not isinstance(self._console, ConsoleService):
            raise RuntimeError("console service is unavailable")
        payload = text if end else text.rstrip("\r")
        self._console.device.write(f"{payload}{end}")


__all__ = [
    "FileLibraryEvent",
    "FileLibraryModule",
    "FileLibraryState",
]
