"""Unit tests for the message store repository helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.runtime.message_store import MessageStore
from scripts.prototypes.runtime.message_store_repository import (
    load_message_store,
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

