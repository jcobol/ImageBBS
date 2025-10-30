"""Persistence helpers for :mod:`imagebbs.runtime.message_store`.

The persisted JSON payload is versioned. The loader currently recognises
version ``1`` (the format emitted by :func:`save_message_store`) and legacy
dumps that predate explicit versioning.
"""

from __future__ import annotations

import contextlib
import contextvars
import json
import os
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import IO, Any

import errno
import threading
import time
from types import TracebackType

if os.name == "nt":  # pragma: no cover - exercised via Windows CI
    import msvcrt
else:  # pragma: no cover - exercised via Unix CI
    import fcntl

from .message_store import MessageRecord, MessageStore


_LOCK_RETRY_DELAY = 0.05
_LOCK_OWNER_OVERRIDE: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "_message_store_lock_owner", default=None
)


class MessageStoreLock(contextlib.AbstractContextManager["MessageStoreLock"]):
    """Context manager providing a re-entrant filesystem lock."""

    _state_lock = threading.Lock()
    _owners: dict[Path, tuple[int, IO[bytes], int]] = {}

    def __init__(self, path: Path) -> None:
        self._target = Path(path).resolve()
        self._lock_path = self._target.parent / f"{self._target.name}.lock"
        self._handle: IO[bytes] | None = None
        self._owns_lock = False
        self._owner_id: int | None = None

    def __enter__(self) -> "MessageStoreLock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        self.release()
        return False

    def acquire(self, *, owner_id: int | None = None) -> None:
        """Acquire the lock for ``owner_id`` (defaulting to current thread)."""

        if owner_id is None:
            override = _LOCK_OWNER_OVERRIDE.get()
            owner_id = override if override is not None else threading.get_ident()
        while True:
            with self._state_lock:
                record = self._owners.get(self._lock_path)
                if record is None:
                    self._lock_path.parent.mkdir(parents=True, exist_ok=True)
                    handle = open(self._lock_path, "a+b")
                    break
                count, handle, record_owner = record
                if record_owner == owner_id:
                    self._owners[self._lock_path] = (count + 1, handle, owner_id)
                    self._handle = handle
                    self._owner_id = owner_id
                    return
            time.sleep(_LOCK_RETRY_DELAY)

        try:
            self._acquire_os_lock(handle)
        except Exception:
            handle.close()
            raise
        with self._state_lock:
            self._owners[self._lock_path] = (1, handle, owner_id)
        self._handle = handle
        self._owns_lock = True
        self._owner_id = owner_id

    def release(self) -> None:
        """Release the lock previously acquired by :meth:`acquire`."""

        owner_id = self._owner_id
        if owner_id is None:
            return
        handle: IO[bytes] | None = None
        with self._state_lock:
            record = self._owners.get(self._lock_path)
            if record is None or record[2] != owner_id:
                self._handle = None
                self._owns_lock = False
                self._owner_id = None
                return
            count, handle_ref, _ = record
            if count > 1:
                self._owners[self._lock_path] = (count - 1, handle_ref, owner_id)
                self._handle = handle_ref
                return
            handle = handle_ref
            del self._owners[self._lock_path]
        if handle is not None and self._owns_lock:
            try:
                self._release_os_lock(handle)
            finally:
                handle.close()
        self._handle = None
        self._owns_lock = False
        self._owner_id = None

    @staticmethod
    def _acquire_os_lock(handle: IO[bytes]) -> None:
        if os.name == "nt":  # pragma: no cover - Windows only
            while True:
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                    break
                except OSError as exc:
                    if exc.errno not in {errno.EACCES, errno.EDEADLK}:
                        raise
                    time.sleep(_LOCK_RETRY_DELAY)
        else:  # pragma: no cover - Unix only
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)

    @staticmethod
    def _release_os_lock(handle: IO[bytes]) -> None:
        if os.name == "nt":  # pragma: no cover - Windows only
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:  # pragma: no cover - Unix only
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def message_store_lock(path: Path) -> MessageStoreLock:
    """Return a context manager guarding access to ``path``."""

    return MessageStoreLock(path)

def record_to_dict(record: MessageRecord) -> dict[str, Any]:
    """Serialise ``record`` to a JSON-friendly mapping."""

    return {
        "message_id": record.message_id,
        "board_id": record.board_id,
        "subject": record.subject,
        "author_handle": record.author_handle,
        "author_real_name": record.author_real_name,
        "author_location": record.author_location,
        "lines": list(record.lines),
    }


def record_from_dict(payload: Mapping[str, Any] | Any) -> MessageRecord:
    """Reconstruct a :class:`MessageRecord` from ``payload``."""

    if not isinstance(payload, Mapping):
        raise TypeError("message record payload must be a mapping")

    return MessageRecord(
        message_id=int(payload["message_id"]),
        board_id=str(payload["board_id"]),
        subject=str(payload.get("subject", "")),
        author_handle=str(payload.get("author_handle", "")),
        author_real_name=str(payload.get("author_real_name", "")),
        author_location=str(payload.get("author_location", "")),
        lines=tuple(str(line) for line in payload.get("lines", ()) or ()),
    )


def dump_records(store: MessageStore) -> list[dict[str, Any]]:
    """Return a stable ordering of ``store`` records for persistence."""

    return [record_to_dict(record) for record in store.iter_records()]


def load_records(records: Iterable[Mapping[str, Any]] | Any) -> list[MessageRecord]:
    """Convert persisted mappings into :class:`MessageRecord` objects."""

    if not isinstance(records, Iterable):
        raise TypeError("message store records payload must be iterable")

    return [record_from_dict(record) for record in records]


def merge_message_stores(
    persisted: MessageStore,
    updates: MessageStore,
    *,
    initial_keys: set[tuple[str, int]] | None = None,
) -> MessageStore:
    """Return a store combining ``persisted`` with ``updates`` records."""

    if initial_keys is None:
        initial_keys = set()

    merged: dict[tuple[str, int], MessageRecord] = {}
    next_ids: dict[str, int] = {}
    for record in persisted.iter_records():
        key = (record.board_id, record.message_id)
        merged[key] = record
        next_ids[record.board_id] = max(
            next_ids.get(record.board_id, 1), record.message_id + 1
        )
    for record in updates.iter_records():
        key = (record.board_id, record.message_id)
        existing = merged.get(key)
        if existing is None:
            merged[key] = record
            next_ids[record.board_id] = max(
                next_ids.get(record.board_id, 1), record.message_id + 1
            )
            continue
        if existing == record:
            continue
        if key in initial_keys:
            merged[key] = record
            continue
        next_id = next_ids.get(record.board_id, 1)
        merged[(record.board_id, next_id)] = MessageRecord(
            message_id=next_id,
            board_id=record.board_id,
            subject=record.subject,
            author_handle=record.author_handle,
            author_real_name=record.author_real_name,
            author_location=record.author_location,
            lines=record.lines,
        )
        next_ids[record.board_id] = next_id + 1
    return MessageStore(records=merged.values())


def load_message_store(path: Path) -> MessageStore:
    """Return a :class:`MessageStore` populated from ``path`` if it exists."""

    with message_store_lock(path):
        if not path.exists():
            return MessageStore()

        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return MessageStore()

        payload = json.loads(text)
        if not isinstance(payload, Mapping):
            raise TypeError("message store payload must be a mapping")

        version = payload.get("version")
        if version is None:
            records = payload.get("records", [])
        elif isinstance(version, int):
            if version != 1:
                raise ValueError(
                    f"unsupported message store version: {version}"
                )
            records = payload.get("records", [])
        else:
            raise ValueError("message store version must be an integer")

    return MessageStore(records=load_records(records))


def save_message_store(
    store: MessageStore,
    path: Path,
    *,
    initial_keys: set[tuple[str, int]] | None = None,
) -> None:
    """Persist ``store`` to ``path`` using the repository format."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    with message_store_lock(path):
        if path.exists():
            persisted_store = load_message_store(path)
            store = merge_message_stores(
                persisted_store, store, initial_keys=initial_keys
            )
        payload = {"version": 1, "records": dump_records(store)}
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                dir=str(path.parent),
                prefix=path.name,
                suffix=".tmp",
                encoding="utf-8",
                delete=False,
            ) as stream:
                temp_path = Path(stream.name)
                json.dump(
                    payload,
                    stream,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, path)
        except Exception:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()
            raise


__all__ = [
    "MessageStoreLock",
    "dump_records",
    "load_message_store",
    "load_records",
    "merge_message_stores",
    "message_store_lock",
    "record_from_dict",
    "record_to_dict",
    "save_message_store",
]

