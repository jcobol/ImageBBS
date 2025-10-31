"""Helpers for persisting overlay metadata snapshots as JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "read_metadata_snapshot",
    "write_metadata_snapshot",
]

_ENCODING = "utf-8"
_DEFAULT_INDENT = 2


def _encode_snapshot(payload: Any, *, indent: int | None = _DEFAULT_INDENT) -> str:
    """Return a canonical JSON encoding for ``payload`` suitable for disk writes."""

    encoded = json.dumps(payload, indent=indent)
    # Ensure a POSIX-friendly trailing newline regardless of the payload.
    if not encoded.endswith("\n"):
        encoded += "\n"
    return encoded


def read_metadata_snapshot(path: Path) -> dict[str, Any]:
    """Return the decoded JSON snapshot stored at ``path``."""

    return json.loads(path.read_text(encoding=_ENCODING))


def write_metadata_snapshot(
    path: Path,
    payload: Any,
    *,
    only_if_changed: bool = False,
    indent: int | None = _DEFAULT_INDENT,
) -> bool:
    """Persist ``payload`` to ``path`` if necessary.

    The function always ensures the parent directory exists and writes the encoded snapshot
    using a consistent newline-terminated JSON serialisation. When ``only_if_changed`` is
    set, the on-disk file is only replaced when the new payload differs from the current
    contents.

    Returns ``True`` if the file on disk was updated, ``False`` otherwise.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded_payload = _encode_snapshot(payload, indent=indent)

    if only_if_changed and path.exists():
        current_contents = path.read_text(encoding=_ENCODING)
        if current_contents == encoded_payload:
            return False

    path.write_text(encoded_payload, encoding=_ENCODING)
    return True
