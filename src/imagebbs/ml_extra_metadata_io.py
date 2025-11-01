"""Helpers for persisting overlay metadata snapshots as JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "PRETTY_PRINT_THRESHOLD_BYTES",
    "read_metadata_snapshot",
    "write_metadata_snapshot",
]

_ENCODING = "utf-8"
_DEFAULT_INDENT = 2
PRETTY_PRINT_THRESHOLD_BYTES = 131_072


def _encode_snapshot(
    payload: Any,
    *,
    indent: int | None = _DEFAULT_INDENT,
    pretty_threshold_bytes: int | None = PRETTY_PRINT_THRESHOLD_BYTES,
) -> str:
    """Return a canonical JSON encoding for ``payload`` suitable for disk writes."""

    # Centralises snapshot encoding so every caller emits consistent JSON on disk.
    if indent is not None and pretty_threshold_bytes is not None:
        encoded = json.dumps(payload, indent=indent)
        if len(encoded.encode(_ENCODING)) > pretty_threshold_bytes:
            encoded = json.dumps(payload, indent=None)
    else:
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
    pretty_threshold_bytes: int | None = PRETTY_PRINT_THRESHOLD_BYTES,
) -> bool:
    """Persist ``payload`` to ``path`` if necessary.

    The function always ensures the parent directory exists and writes the encoded snapshot
    using a consistent newline-terminated JSON serialisation. Payloads whose pretty-printed
    representation exceed ``pretty_threshold_bytes`` automatically fall back to a compact
    encoding unless the threshold is ``None``. When ``only_if_changed`` is set, the on-disk
    file is only replaced when the new payload differs from the current contents.

    Returns ``True`` if the file on disk was updated, ``False`` otherwise.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded_payload = _encode_snapshot(
        payload,
        indent=indent,
        pretty_threshold_bytes=pretty_threshold_bytes,
    )

    if only_if_changed and path.exists():
        current_contents = path.read_text(encoding=_ENCODING)
        if current_contents == encoded_payload:
            return False

    path.write_text(encoded_payload, encoding=_ENCODING)
    return True
