from __future__ import annotations

import pytest

from imagebbs.runtime.message_store import MessageRecord, MessageStore


def test_append_assigns_incrementing_ids_per_board() -> None:
    store = MessageStore()

    first = store.append(
        board_id="general",
        subject="First",
        author_handle="SYSOP",
        lines=["hello"],
    )
    second = store.append(
        board_id="general",
        subject="Second",
        author_handle="SYSOP",
        lines=["line1", "line2"],
    )
    other_board = store.append(
        board_id="sysop",
        subject="Third",
        author_handle="SYSOP",
    )

    assert first.message_id == 1
    assert second.message_id == 2
    assert other_board.message_id == 1
    assert second.line_count == 2


def test_update_and_fetch_roundtrip() -> None:
    store = MessageStore()
    record = store.append(
        board_id="general",
        subject="Draft",
        author_handle="SYSOP",
        lines=["original"],
    )

    updated = store.update(
        "general",
        record.message_id,
        subject="Final",
        author_real_name="Sys Op",
        lines=["updated", "body"],
    )

    fetched = store.fetch("general", record.message_id)

    assert fetched == updated
    assert fetched.subject == "Final"
    assert fetched.author_real_name == "Sys Op"
    assert fetched.lines == ("updated", "body")


def test_list_produces_summaries_in_id_order() -> None:
    store = MessageStore()
    store.append(
        board_id="general",
        subject="One",
        author_handle="SYSOP",
        lines=["one"],
    )
    store.append(
        board_id="general",
        subject="Two",
        author_handle="SYSOP",
        author_real_name="Sys Op",
        author_location="BBS",
        lines=["two", "lines"],
    )

    summaries = store.list("general")

    assert [summary.message_id for summary in summaries] == [1, 2]
    assert summaries[1].subject == "Two"
    assert summaries[1].author_real_name == "Sys Op"
    assert summaries[1].author_location == "BBS"
    assert summaries[1].line_count == 2


def test_iter_records_orders_by_board_and_message() -> None:
    records = [
        MessageRecord(
            message_id=2,
            board_id="b",
            subject="second",
            author_handle="SYSOP",
        ),
        MessageRecord(
            message_id=1,
            board_id="a",
            subject="first",
            author_handle="SYSOP",
        ),
        MessageRecord(
            message_id=3,
            board_id="a",
            subject="third",
            author_handle="SYSOP",
        ),
    ]
    store = MessageStore(records=records)

    ordered = list(store.iter_records())

    assert [
        (record.board_id, record.message_id)
        for record in ordered
    ] == [("a", 1), ("a", 3), ("b", 2)]

    appended = store.append(
        board_id="a",
        subject="fourth",
        author_handle="SYSOP",
    )
    assert appended.message_id == 4


def test_fetch_missing_board_and_message_raise_keyerror() -> None:
    store = MessageStore()
    store.append(
        board_id="general",
        subject="Hello",
        author_handle="SYSOP",
    )

    with pytest.raises(KeyError):
        store.fetch("unknown", 1)
    with pytest.raises(KeyError):
        store.fetch("general", 999)


def test_delete_tracks_removed_records() -> None:
    store = MessageStore()
    record = store.append(
        board_id="general",
        subject="Temporary",
        author_handle="SYSOP",
        lines=["body"],
    )

    removed = store.delete("general", record.message_id)

    assert removed == record
    assert store.list("general") == []
    assert store.deleted_keys == {("general", record.message_id)}
    with pytest.raises(KeyError):
        store.fetch("general", record.message_id)

