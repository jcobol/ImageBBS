"""In-memory message store mirroring ImageBBS BASIC arrays."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, Iterable, Iterator, List, MutableMapping, Optional, Tuple


@dataclass(frozen=True)
class MessageRecord:
    """Canonical representation of a stored message."""

    message_id: int
    board_id: str
    subject: str
    author_handle: str
    author_real_name: str = ""
    author_location: str = ""
    lines: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def line_count(self) -> int:
        return len(self.lines)

    def with_updates(
        self,
        *,
        subject: Optional[str] = None,
        author_handle: Optional[str] = None,
        author_real_name: Optional[str] = None,
        author_location: Optional[str] = None,
        lines: Optional[Iterable[str]] = None,
    ) -> "MessageRecord":
        return replace(
            self,
            subject=subject if subject is not None else self.subject,
            author_handle=author_handle if author_handle is not None else self.author_handle,
            author_real_name=(
                author_real_name if author_real_name is not None else self.author_real_name
            ),
            author_location=(
                author_location if author_location is not None else self.author_location
            ),
            lines=tuple(lines) if lines is not None else self.lines,
        )


@dataclass(frozen=True)
class MessageSummary:
    """Message metadata mirroring BASIC header arrays (e.g., ``TI%``/``TL%``)."""

    message_id: int
    board_id: str
    subject: str
    author_handle: str
    author_real_name: str
    author_location: str
    line_count: int


class MessageStore:
    """Track message metadata and text similarly to ImageBBS BASIC arrays."""

    def __init__(self, *, records: Optional[Iterable[MessageRecord]] = None) -> None:
        self._messages: MutableMapping[str, Dict[int, MessageRecord]] = {}
        self._next_message_ids: MutableMapping[str, int] = {}
        if records is not None:
            for record in records:
                self._add_record(record)

    def list(self, board_id: str) -> List[MessageSummary]:
        records = self._messages.get(board_id, {})
        summaries = [
            MessageSummary(
                message_id=record.message_id,
                board_id=record.board_id,
                subject=record.subject,
                author_handle=record.author_handle,
                author_real_name=record.author_real_name,
                author_location=record.author_location,
                line_count=record.line_count,
            )
            for record in sorted(records.values(), key=lambda r: r.message_id)
        ]
        return summaries

    def fetch(self, board_id: str, message_id: int) -> MessageRecord:
        try:
            board_messages = self._messages[board_id]
        except KeyError as exc:
            raise KeyError(f"unknown message board: {board_id}") from exc
        try:
            return board_messages[message_id]
        except KeyError as exc:
            raise KeyError(f"message {message_id} not found for board {board_id}") from exc

    def append(
        self,
        *,
        board_id: str,
        subject: str,
        author_handle: str,
        author_real_name: str = "",
        author_location: str = "",
        lines: Optional[Iterable[str]] = None,
    ) -> MessageRecord:
        message_id = self._allocate_message_id(board_id)
        record = MessageRecord(
            message_id=message_id,
            board_id=board_id,
            subject=subject,
            author_handle=author_handle,
            author_real_name=author_real_name,
            author_location=author_location,
            lines=tuple(lines or ()),
        )
        self._messages.setdefault(board_id, {})[message_id] = record
        return record

    def update(
        self,
        board_id: str,
        message_id: int,
        *,
        subject: Optional[str] = None,
        author_handle: Optional[str] = None,
        author_real_name: Optional[str] = None,
        author_location: Optional[str] = None,
        lines: Optional[Iterable[str]] = None,
    ) -> MessageRecord:
        record = self.fetch(board_id, message_id)
        updated = record.with_updates(
            subject=subject,
            author_handle=author_handle,
            author_real_name=author_real_name,
            author_location=author_location,
            lines=lines,
        )
        self._messages[board_id][message_id] = updated
        return updated

    def iter_records(self) -> Iterator[MessageRecord]:
        """Yield all records in board/message order."""

        for board_id in sorted(self._messages):
            board_messages = self._messages[board_id]
            for message_id in sorted(board_messages):
                yield board_messages[message_id]

    # Internal helpers -------------------------------------------------

    def _allocate_message_id(self, board_id: str) -> int:
        next_id = self._next_message_ids.get(board_id, 1)
        self._next_message_ids[board_id] = next_id + 1
        return next_id

    def _add_record(self, record: MessageRecord) -> None:
        board_messages = self._messages.setdefault(record.board_id, {})
        board_messages[record.message_id] = record
        next_id = max(self._next_message_ids.get(record.board_id, 1), record.message_id + 1)
        self._next_message_ids[record.board_id] = next_id


__all__ = [
    "MessageRecord",
    "MessageStore",
    "MessageSummary",
]

