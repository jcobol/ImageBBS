"""Runtime approximation of the ImageBBS upload/download libraries."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Mapping, Optional

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
    _storage_config: object | None = field(init=False, default=None)
    _filesystem_drive_roots: Dict[int, Path] = field(
        init=False, default_factory=dict
    )
    _filesystem_drive_slots: Dict[int, int] = field(
        init=False, default_factory=dict
    )
    _host_directories: Dict[str, "HostLibraryDirectory"] = field(
        init=False, default_factory=dict
    )

    _BLOCK_PAYLOAD_SIZE: int = 254

    # Why: wire runtime services and seed cached metadata so commands can execute deterministically.
    def start(self, kernel: SessionKernel) -> SessionState:
        console = kernel.services.get("console")
        if not isinstance(console, ConsoleService):
            raise TypeError("console service missing from session kernel")
        self._console = console
        self.registry = kernel.dispatcher.registry
        defaults = kernel.defaults
        self._defaults = defaults
        self._storage_config = getattr(defaults, "storage_config", None)
        self._filesystem_drive_roots = self._coerce_drive_roots(
            getattr(defaults, "filesystem_drive_roots", None)
        )
        self._filesystem_drive_slots = self._coerce_drive_slots(
            getattr(defaults, "filesystem_drive_slots", None)
        )
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
        self._initialise_host_directories()
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

    # Why: allow tests to simulate uploads while keeping host directories in sync with filesystem state.
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
        host_directory = self._host_directories.get(self._active_identifier)
        if host_directory and host_directory.read_only:
            self._write_line("?DRIVE IS READ-ONLY")
            return
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
        host_directory = self._host_directories.get(self._active_identifier)
        if host_directory and not host_directory.read_only:
            target_path = host_directory.path / record.filename
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.touch(exist_ok=True)
            except OSError:
                self._write_line("?FAILED TO CREATE HOST FILE")
                return
        entries.append(record)
        stats = self._stats_by_id.setdefault(self._active_identifier, {})
        stats["total_files"] = stats.get("total_files", len(entries) - 1) + 1
        stats["new_files"] = stats.get("new_files", 0) + 1
        if host_directory is not None:
            host_directory.entries = entries
            host_directory.stats = stats
            if not host_directory.read_only:
                self._refresh_host_directory(self._active_identifier)
        self._write_line(f"Added {filename} as entry #{next_number}.")

    # Why: emulate the BASIC delete command while propagating removals to host directories.
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
                removed = entries.pop(index)
                stats = self._stats_by_id.setdefault(self._active_identifier, {})
                stats["total_files"] = max(stats.get("total_files", len(entries) + 1) - 1, 0)
                host_directory = self._host_directories.get(
                    self._active_identifier
                )
                if host_directory is not None:
                    host_directory.entries = entries
                    host_directory.stats = stats
                    if not host_directory.read_only:
                        target_path = host_directory.path / removed.filename
                        try:
                            target_path.unlink(missing_ok=True)
                        except TypeError:
                            # Python versions without missing_ok support.
                            try:
                                if target_path.exists():
                                    target_path.unlink()
                            except OSError:
                                pass
                        except OSError:
                            pass
                    self._refresh_host_directory(self._active_identifier)
                self._write_line(f"Removed entry #{target}.")
                return
        self._write_line("?NO SUCH ENTRY")

    # Why: rescan host-backed libraries so cached metadata mirrors the filesystem immediately after mutations.
    def _refresh_host_directory(self, identifier: str) -> None:
        host_directory = self._host_directories.get(identifier)
        if host_directory is None:
            return
        stub_entries = list(self._entries_by_id.get(identifier, []))
        entries = self._enumerate_host_entries(host_directory.path, stub_entries)
        stats = dict(self._stats_by_id.get(identifier, {}))
        stats["total_files"] = len(entries)
        stats.setdefault("new_files", 0)
        host_directory.entries = entries
        host_directory.stats = stats
        self._entries_by_id[identifier] = entries
        self._stats_by_id[identifier] = stats

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

    # Why: normalise kernel annotations so host-backed directories can be resolved safely.
    def _coerce_drive_roots(self, raw: object) -> Dict[int, Path]:
        roots: Dict[int, Path] = {}
        if isinstance(raw, Mapping):
            for drive, path in raw.items():
                try:
                    drive_number = int(drive)
                except (TypeError, ValueError):
                    continue
                roots[drive_number] = Path(path)
        return roots

    # Why: capture drive-slot mappings even when storage configuration is partially defined.
    def _coerce_drive_slots(self, raw: object) -> Dict[int, int]:
        slots: Dict[int, int] = {}
        if isinstance(raw, Mapping):
            for drive, slot in raw.items():
                try:
                    drive_number = int(drive)
                    slot_number = int(slot)
                except (TypeError, ValueError):
                    continue
                slots[drive_number] = slot_number
        return slots

    # Why: seed host metadata so listings reflect live filesystem state when available.
    def _initialise_host_directories(self) -> None:
        self._host_directories = {}
        defaults = self._defaults
        if defaults is None:
            return
        views = self._build_host_library_views(defaults)
        for identifier, view in views.items():
            self._host_directories[identifier] = view
            self._entries_by_id[identifier] = view.entries
            self._stats_by_id[identifier] = view.stats

    # Why: merge storage configuration details with stub metadata for each library.
    def _build_host_library_views(
        self, defaults: object
    ) -> Dict[str, "HostLibraryDirectory"]:
        views: Dict[str, HostLibraryDirectory] = {}
        storage = getattr(defaults, "storage_config", None)
        storage_drives: Mapping[int, object] | None = None
        if storage is not None and hasattr(storage, "drives"):
            potential = getattr(storage, "drives")
            if isinstance(potential, Mapping):
                storage_drives = potential
        for descriptor in self._libraries:
            drive_number = descriptor.drive_slot
            root_path = self._filesystem_drive_roots.get(drive_number)
            read_only = False
            if storage_drives and drive_number in storage_drives:
                mapping = storage_drives[drive_number]
                if hasattr(mapping, "root"):
                    root_path = Path(getattr(mapping, "root"))
                read_only = bool(getattr(mapping, "read_only", False))
            if root_path is None:
                continue
            directory_path = self._resolve_library_path(
                root_path, descriptor.directory
            )
            if directory_path is None:
                continue
            stub_entries = list(self._entries_by_id.get(descriptor.identifier, []))
            entries = self._enumerate_host_entries(directory_path, stub_entries)
            stats = dict(self._stats_by_id.get(descriptor.identifier, {}))
            stats["total_files"] = len(entries)
            stats.setdefault("new_files", 0)
            view = HostLibraryDirectory(
                path=directory_path,
                read_only=read_only,
                entries=entries,
                stats=stats,
            )
            views[descriptor.identifier] = view
        return views

    # Why: guard against path escapes while tolerating legacy directory tokens.
    def _resolve_library_path(self, root: Path, directory: str) -> Path | None:
        base = Path(directory) if directory else Path()
        candidate = (root / base).resolve() if not base.is_absolute() else base
        try:
            candidate.relative_to(root)
        except ValueError:
            return None
        if not candidate.exists() or not candidate.is_dir():
            return None
        return candidate

    # Why: derive FileLibraryEntry records from host filesystem data.
    def _enumerate_host_entries(
        self, directory: Path, stub_entries: list[FileLibraryEntry]
    ) -> list[FileLibraryEntry]:
        entries: list[FileLibraryEntry] = []
        stub_lookup = {entry.filename.upper(): entry for entry in stub_entries}
        try:
            candidates = sorted(directory.iterdir())
        except OSError:
            return entries
        number = 1
        for path in candidates:
            if not path.is_file():
                continue
            stub_entry = stub_lookup.get(path.name.upper())
            entry = self._entry_from_path(number, path, stub_entry)
            entries.append(entry)
            number += 1
        return entries

    # Why: convert host file statistics into Commodore-style directory metadata.
    def _entry_from_path(
        self, number: int, path: Path, stub_entry: FileLibraryEntry | None
    ) -> FileLibraryEntry:
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        blocks = max(1, math.ceil(size / self._BLOCK_PAYLOAD_SIZE))
        filename = path.name.upper()
        description = (
            stub_entry.description
            if stub_entry is not None and stub_entry.description
            else "Host file"
        )
        uploader = (
            stub_entry.uploader if stub_entry is not None else self._default_uploader()
        )
        downloads = stub_entry.downloads if stub_entry is not None else 0
        validated = stub_entry.validated if stub_entry is not None else True
        return FileLibraryEntry(
            number=number,
            filename=filename,
            blocks=blocks,
            downloads=downloads,
            description=description,
            uploader=uploader,
            validated=validated,
        )


@dataclass
class HostLibraryDirectory:
    """Snapshot of a host-backed library directory."""

    path: Path
    read_only: bool
    entries: list[FileLibraryEntry]
    stats: Dict[str, int]


__all__ = [
    "FileLibraryEvent",
    "FileLibraryModule",
    "FileLibraryState",
]
