#!/usr/bin/env python3
"""Search tokenised Commodore 64 reference extracts for planning research."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List


def load_passages(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
                raise ValueError(f"Invalid JSONL line in {path}: {exc}") from exc
            tokens: List[str] = payload.get("tokens") or []
            if not isinstance(tokens, list):
                raise ValueError(f"Line missing token list: {payload}")
            yield " ".join(str(token) for token in tokens)


def select_matches(passages: Iterable[str], keywords: List[str]) -> Iterable[str]:
    lowered = [kw.lower() for kw in keywords]
    for text in passages:
        haystack = text.lower()
        if all(keyword in haystack for keyword in lowered):
            yield text


def format_output(matches: Iterable[str], width: int) -> str:
    import textwrap

    wrapped_blocks: List[str] = []
    for idx, match in enumerate(matches, start=1):
        wrapped = textwrap.fill(match, width=width)
        wrapped_blocks.append(f"Match {idx}:\n{wrapped}")
    return "\n\n".join(wrapped_blocks)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Search the Commodore 64 reference token dump for passages that "
            "contain all requested keywords."
        )
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to the commodore64_reference_tj_tokens.jsonl dataset",
    )
    parser.add_argument(
        "keywords",
        nargs="+",
        help="Keywords that must be present in the passage (case-insensitive)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=88,
        help="Wrap output to this column width (default: 88)",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    passages = load_passages(args.path)
    matches = list(select_matches(passages, args.keywords))

    if not matches:
        return 1

    output = format_output(matches, args.width)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
