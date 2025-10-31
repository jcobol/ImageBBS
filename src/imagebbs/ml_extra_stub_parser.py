"""Helpers for reading data from ``ml_extra_stub.asm``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, Sequence, Tuple

from . import ml_extra_defaults


StubSource = Sequence[str]


@dataclass
class StubMacroEntry:
    """Concrete macro payload recovered from ``ml_extra_stub.asm``."""

    slot: int
    address: int
    payload: Sequence[int]

    def decoded_text(self) -> str:
        """Return the PETSCII rendering of :attr:`payload`."""

        return ml_extra_defaults.ml_extra_extract.decode_petscii(self.payload)

    def byte_preview(self, limit: int = 8) -> str:
        """Return a short hex preview of the payload."""

        prefix = (f"${value:02x}" for value in self.payload[:limit])
        preview = ", ".join(prefix)
        if len(self.payload) > limit:
            preview += ", …"
        return preview


@dataclass
class StubStaticData:
    """Structured view of fixed data copied into ``ml_extra_stub.asm``."""

    lightbar: Tuple[int, ...]
    underline: Tuple[int, ...]
    palette: Tuple[int, ...]
    flag_directory_block: Tuple[int, ...]
    flag_directory_tail: Tuple[int, ...]


def load_stub_source(stub_path: Path) -> Tuple[str, ...]:
    """Return the raw source lines from ``ml_extra_stub.asm``."""

    return tuple(stub_path.read_text(encoding="utf-8").splitlines())


def read_macro_slot_ids(stub_source: Path | StubSource) -> Tuple[int, ...]:
    """Return macro slot identifiers lifted from the stub."""

    lines = _ensure_lines(stub_source)
    slot_ids: list[int] = []
    for label, statement in _iter_labelled_statements(lines):
        if label == "macro_slot_ids" and statement.startswith(".byte"):
            slot_ids.extend(_parse_numeric_tokens(statement[len(".byte") :]))
    return tuple(slot_ids)


def read_macro_runtime_targets(stub_source: Path | StubSource) -> Tuple[int, ...]:
    """Return runtime dispatch addresses recovered from the stub."""

    lines = _ensure_lines(stub_source)
    targets: list[int] = []
    for label, statement in _iter_labelled_statements(lines):
        if label == "macro_runtime_targets" and statement.startswith(".word"):
            targets.extend(_parse_numeric_tokens(statement[len(".word") :]))
    return tuple(targets)


def read_macro_payload_directory(stub_source: Path | StubSource) -> Tuple[str, ...]:
    """Return labels referenced by the stub macro directory."""

    lines = _ensure_lines(stub_source)
    directory: list[str] = []
    for label, statement in _iter_labelled_statements(lines):
        if label == "macro_payload_directory" and statement.startswith(".word"):
            directory.extend(_parse_label_tokens(statement[len(".word") :]))
    return tuple(directory)


def read_macro_payloads(stub_source: Path | StubSource) -> Mapping[str, Tuple[int, ...]]:
    """Return raw macro payloads keyed by their labels."""

    lines = _ensure_lines(stub_source)
    payloads: Dict[str, List[int]] = {}
    for label, statement in _iter_labelled_statements(lines):
        if label.startswith("macro_payload_") and statement.startswith(".byte"):
            payloads.setdefault(label, []).extend(
                _parse_numeric_tokens(statement[len(".byte") :])
            )
    return {name: tuple(values) for name, values in payloads.items()}


def parse_stub_macro_directory(stub_source: Path | StubSource) -> List[StubMacroEntry]:
    """Return concrete macro payloads recovered from the stub module."""

    lines = _ensure_lines(stub_source)
    slot_ids = read_macro_slot_ids(lines)
    runtime_targets = read_macro_runtime_targets(lines)
    directory_labels = read_macro_payload_directory(lines)
    payloads = read_macro_payloads(lines)

    if not slot_ids or not directory_labels or not runtime_targets:
        raise ValueError("failed to parse macro directory from stub")
    if not (
        len(slot_ids) == len(directory_labels) == len(runtime_targets)
    ):
        raise ValueError("stub macro directory has mismatched counts")

    entries: list[StubMacroEntry] = []
    for slot, label, address in zip(slot_ids, directory_labels, runtime_targets):
        if label not in payloads:
            raise ValueError(f"macro payload {label} missing from stub")
        entries.append(
            StubMacroEntry(slot=slot, address=address, payload=payloads[label])
        )
    return entries


def parse_stub_static_data(stub_source: Path | StubSource) -> StubStaticData:
    """Recover fixed data tables stored in ``ml_extra_stub.asm``."""

    lines = _ensure_lines(stub_source)
    symbols = _collect_symbol_table(lines)
    targets: Dict[str, List[int]] = {
        "lightbar_default_bitmaps": [],
        "underline_default": [],
        "editor_palette_default": [],
        "flag_directory_block": [],
        "flag_directory_tail_decoded": [],
    }

    for label, statement in _iter_labelled_statements(lines):
        if label not in targets:
            continue
        if statement.startswith(".byte"):
            targets[label].extend(
                _parse_stub_numeric_tokens(statement[len(".byte") :], symbols)
            )

    missing = [label for label, values in targets.items() if not values]
    if missing:
        raise ValueError(
            "failed to recover stub tables: " + ", ".join(sorted(missing))
        )

    return StubStaticData(
        lightbar=tuple(targets["lightbar_default_bitmaps"]),
        underline=tuple(targets["underline_default"]),
        palette=tuple(targets["editor_palette_default"]),
        flag_directory_block=tuple(targets["flag_directory_block"]),
        flag_directory_tail=tuple(targets["flag_directory_tail_decoded"]),
    )


def _ensure_lines(stub_source: Path | StubSource) -> Tuple[str, ...]:
    if isinstance(stub_source, Path):
        return load_stub_source(stub_source)
    if isinstance(stub_source, (str, bytes)):
        raise TypeError("stub_source must be a Path or sequence of lines")
    return tuple(stub_source)


def _strip_comment(line: str) -> str:
    return line.split(";", 1)[0].rstrip()


def _iter_labelled_statements(lines: Iterable[str]) -> Iterator[Tuple[str, str]]:
    current_label: str | None = None
    for raw_line in lines:
        line = _strip_comment(raw_line)
        if not line:
            continue
        if line.endswith(":"):
            current_label = line[:-1]
            continue
        if current_label is None:
            continue
        yield current_label, line.strip()


def _collect_symbol_table(lines: Iterable[str]) -> Dict[str, int]:
    symbols: Dict[str, int] = {}
    for raw_line in lines:
        line = _strip_comment(raw_line)
        if not line:
            continue
        stripped = line.strip()
        if "=" not in stripped or stripped.startswith(".") or ":" in stripped:
            continue
        name, value = (part.strip() for part in stripped.split("=", 1))
        if not name or not value:
            continue
        try:
            symbols[name] = _parse_numeric_value(value)
        except ValueError:
            continue
    return symbols


def _parse_numeric_tokens(spec: str) -> List[int]:
    values: list[int] = []
    for token in spec.split(","):
        chunk = token.strip()
        if not chunk:
            continue
        values.append(_parse_numeric_value(chunk))
    return values


def _parse_stub_numeric_tokens(spec: str, symbols: Mapping[str, int]) -> List[int]:
    values: list[int] = []
    for token in spec.split(","):
        chunk = token.strip()
        if not chunk:
            continue
        if chunk in symbols:
            values.append(symbols[chunk])
        else:
            values.append(_parse_numeric_value(chunk))
    return values


def _parse_label_tokens(spec: str) -> List[str]:
    labels: list[str] = []
    for token in spec.split(","):
        name = token.strip()
        if name:
            labels.append(name)
    return labels


def _parse_numeric_value(token: str) -> int:
    chunk = token.strip()
    if not chunk:
        raise ValueError("empty numeric token")
    if chunk.startswith("$"):
        return int(chunk[1:], 16)
    if chunk.lower().startswith("0x"):
        return int(chunk[2:], 16)
    if chunk.startswith("%"):
        return int(chunk[1:], 2)
    return int(chunk, 10)

