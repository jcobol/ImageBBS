"""Sanity-check utilities for the recovered ``ml.extra`` overlay."""

from .core import (
    MacroComparison,
    MacroDirectoryRow,
    MacroHashEntry,
    MetadataChange,
    MetadataDiff,
    MetadataValue,
    NonTerminatedMacro,
    SanityReport,
    SequenceDiff,
    SequenceSnapshot,
    StubMacroSummary,
    StubStaticDiff,
    diff_metadata_snapshots,
    run_checks,
)
from .reporting import format_report
from .cli import main, parse_args

__all__ = [
    "MacroComparison",
    "MacroDirectoryRow",
    "MacroHashEntry",
    "MetadataChange",
    "MetadataDiff",
    "MetadataValue",
    "NonTerminatedMacro",
    "SanityReport",
    "SequenceDiff",
    "SequenceSnapshot",
    "StubMacroSummary",
    "StubStaticDiff",
    "diff_metadata_snapshots",
    "format_report",
    "main",
    "parse_args",
    "run_checks",
]
