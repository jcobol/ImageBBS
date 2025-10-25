"""Persistence helpers for :mod:`imagebbs.runtime.message_store`."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .message_store import MessageRecord, MessageStore


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


def load_message_store(path: Path) -> MessageStore:
    """Return a :class:`MessageStore` populated from ``path`` if it exists."""

    if not path.exists():
        return MessageStore()

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return MessageStore()

    payload = json.loads(text)
    if isinstance(payload, Mapping):
        records = payload.get("records", [])
    else:
        raise TypeError("message store payload must be a mapping")

    return MessageStore(records=load_records(records))


def save_message_store(store: MessageStore, path: Path) -> None:
    """Persist ``store`` to ``path`` using the repository format."""

    payload = {"version": 1, "records": dump_records(store)}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")


__all__ = [
    "dump_records",
    "load_message_store",
    "load_records",
    "record_from_dict",
    "record_to_dict",
    "save_message_store",
]

