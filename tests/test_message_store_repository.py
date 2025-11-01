"""Unit tests for the message store repository helpers."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

import pytest

from imagebbs.runtime.message_store import MessageStore
from imagebbs.runtime.message_store_repository import (
    load_message_store,
    load_records,
    message_store_lock,
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


def test_load_message_store_accepts_version_one(tmp_path: Path) -> None:
    path = tmp_path / "valid_version.json"
    payload = {"version": 1, "records": []}
    path.write_text(json.dumps(payload), encoding="utf-8")

    store = load_message_store(path)
    assert isinstance(store, MessageStore)


def test_load_message_store_accepts_missing_version(tmp_path: Path) -> None:
    path = tmp_path / "legacy.json"
    payload = {"records": []}
    path.write_text(json.dumps(payload), encoding="utf-8")

    store = load_message_store(path)
    assert isinstance(store, MessageStore)


def test_load_message_store_rejects_mismatched_version(tmp_path: Path) -> None:
    path = tmp_path / "unsupported.json"
    payload = {"version": 2, "records": []}
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported message store version"):
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


def test_save_message_store_persists_deletions(tmp_path: Path) -> None:
    path = tmp_path / "messages.json"
    store = MessageStore()
    record = store.append(board_id="main", subject="Hello", author_handle="Sysop")

    save_message_store(store, path)

    reloaded = load_message_store(path)
    initial_keys = {
        (loaded.board_id, loaded.message_id)
        for loaded in reloaded.iter_records()
    }

    reloaded.delete("main", record.message_id)
    assert reloaded.deleted_keys == {("main", record.message_id)}

    save_message_store(reloaded, path, initial_keys=initial_keys)

    after_delete = load_message_store(path)
    assert after_delete.list("main") == []

    subsequent_initial_keys = {
        (loaded.board_id, loaded.message_id)
        for loaded in after_delete.iter_records()
    }

    save_message_store(after_delete, path, initial_keys=subsequent_initial_keys)

    final = load_message_store(path)
    assert final.list("main") == []


def test_message_store_lock_times_out_under_contention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Why: ensure environment-driven lock deadlines prevent hung sessions during persistence.
    path = tmp_path / "messages.json"
    monkeypatch.setenv("IMAGEBBS_MESSAGE_LOCK_TIMEOUT", "0.1")

    holder = message_store_lock(path)
    holder.acquire(owner_id=1)
    try:
        competitor = message_store_lock(path)
        start_time = time.monotonic()
        with pytest.raises(TimeoutError, match="Timed out acquiring message store lock"):
            competitor.acquire(owner_id=2)
        elapsed = time.monotonic() - start_time
        assert elapsed >= 0.1
    finally:
        holder.release()


def test_message_store_lock_times_out_when_os_lock_held_unix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Why: confirm OS-level lock contention triggers the same timeout path on Unix hosts.
    if os.name == "nt":
        pytest.skip("Unix-specific assertion")

    monkeypatch.setenv("IMAGEBBS_MESSAGE_LOCK_TIMEOUT", "0.2")
    path = tmp_path / "messages.json"
    lock_path = path.parent / f"{path.name}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    ready = threading.Event()
    release = threading.Event()

    def holder() -> None:
        # Why: occupy the fcntl lock to simulate inter-process contention.
        import fcntl

        with open(lock_path, "a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            ready.set()
            try:
                release.wait()
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    thread = threading.Thread(target=holder, name="unix-lock-holder", daemon=True)
    thread.start()
    assert ready.wait(timeout=5)

    competitor = message_store_lock(path)
    start_time = time.monotonic()
    with pytest.raises(TimeoutError, match="Timed out acquiring message store lock"):
        competitor.acquire(owner_id=3)
    elapsed = time.monotonic() - start_time
    assert elapsed >= 0.2

    release.set()
    thread.join(timeout=5)
    assert not thread.is_alive()


def test_message_store_lock_times_out_when_os_lock_held_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Why: confirm OS-level lock contention triggers the same timeout path on Windows hosts.
    if os.name != "nt":
        pytest.skip("Windows-specific assertion")

    import msvcrt

    monkeypatch.setenv("IMAGEBBS_MESSAGE_LOCK_TIMEOUT", "0.2")
    path = tmp_path / "messages.json"
    lock_path = path.parent / f"{path.name}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    ready = threading.Event()
    release = threading.Event()

    def holder() -> None:
        # Why: occupy the Windows byte-range lock to simulate inter-process contention.
        with open(lock_path, "a+b") as handle:
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            ready.set()
            try:
                release.wait()
            finally:
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)

    thread = threading.Thread(target=holder, name="windows-lock-holder", daemon=True)
    thread.start()
    assert ready.wait(timeout=5)

    competitor = message_store_lock(path)
    start_time = time.monotonic()
    with pytest.raises(TimeoutError, match="Timed out acquiring message store lock"):
        competitor.acquire(owner_id=4)
    elapsed = time.monotonic() - start_time
    assert elapsed >= 0.2

    release.set()
    thread.join(timeout=5)
    assert not thread.is_alive()

