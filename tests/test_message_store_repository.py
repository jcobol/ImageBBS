"""Unit tests for the message store repository helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from imagebbs.runtime.message_store import MessageStore
from imagebbs.runtime.message_store_repository import (
    load_message_store,
    load_records,
    save_message_store,
)


def test_load_message_store_returns_empty_for_missing_path(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    store = load_message_store(path)
    assert isinstance(store, MessageStore)
    assert list(store.iter_records()) == []


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    store = MessageStore()
    store.append(board_id="main", subject="Hello", author_handle="Sysop")
    store.append(
        board_id="tech",
        subject="Status",
        author_handle="Coder",
        lines=["Line one", "Line two"],
    )

    path = tmp_path / "messages.json"
    save_message_store(store, path)

    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert len(payload["records"]) == 2

    reloaded = load_message_store(path)
    assert reloaded.list("main") == store.list("main")
    assert reloaded.list("tech") == store.list("tech")


def test_load_message_store_rejects_non_mapping_payload(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(["not", "a", "mapping"]), encoding="utf-8")

    with pytest.raises(TypeError, match="payload must be a mapping"):
        load_message_store(path)


def test_load_message_store_rejects_non_iterable_records(tmp_path: Path) -> None:
    path = tmp_path / "invalid_records.json"
    payload = {"version": 1, "records": 42}
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(TypeError, match="records payload must be iterable"):
        load_message_store(path)


def test_load_records_rejects_non_mapping_entries() -> None:
    with pytest.raises(TypeError, match="record payload must be a mapping"):
        load_records([{"message_id": 1, "board_id": "main"}, "invalid"])


def test_save_message_store_atomic_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "messages.json"
    original_payload = {"version": 1, "records": []}
    path.write_text(
        json.dumps(original_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    original_contents = path.read_text(encoding="utf-8")

    store = MessageStore()
    store.append(board_id="main", subject="Updated", author_handle="Sysop")

    with monkeypatch.context() as context:
        def failing_dump(*args: object, **kwargs: object) -> None:
            raise RuntimeError("boom")

        context.setattr(
            "imagebbs.runtime.message_store_repository.json.dump", failing_dump
        )

        with pytest.raises(RuntimeError, match="boom"):
            save_message_store(store, path)

    assert path.read_text(encoding="utf-8") == original_contents
    remaining = sorted(entry.name for entry in tmp_path.iterdir())
    assert remaining[0] == "messages.json"
    assert set(remaining).issubset({"messages.json", "messages.json.lock"})

    save_message_store(store, path)
    remaining = sorted(entry.name for entry in tmp_path.iterdir())
    assert remaining[0] == "messages.json"
    assert set(remaining).issubset({"messages.json", "messages.json.lock"})

