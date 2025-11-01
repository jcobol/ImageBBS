"""Shared helpers for baseline comparison workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import ml_extra_metadata_io
from ..ml_extra.sanity import core as sanity_core

__all__ = ["BaselineWorkflowResult", "run_baseline_workflow"]


# Why: Provide a structured record so callers can share diff, snapshot, and write outcomes.
@dataclass(frozen=True)
class BaselineWorkflowResult:
    """Represents the outcomes from a baseline comparison workflow."""

    report: sanity_core.SanityReport
    metadata_snapshot: dict[str, Any]
    baseline_snapshot: dict[str, Any] | None
    diff: sanity_core.MetadataDiff | None
    metadata_path: Path | None
    metadata_updated: bool | None
    baseline_path: Path | None
    baseline_updated: bool | None


# Why: Centralise snapshot export, diffing, and optional baseline updates for the CLIs.
def run_baseline_workflow(
    *,
    overlay_path: Path | None,
    baseline_path: Path | None,
    metadata_path: Path | None = None,
    metadata_only_if_changed: bool = False,
    update_baseline: bool = False,
) -> BaselineWorkflowResult:
    """Execute sanity checks, compare against the baseline, and persist outputs."""

    report = sanity_core.run_checks(overlay_path)
    metadata_snapshot = report.metadata_snapshot
    if not metadata_snapshot:
        raise RuntimeError("metadata snapshot unavailable from ml_extra_sanity.run_checks")

    baseline_snapshot: dict[str, Any] | None = None
    diff: sanity_core.MetadataDiff | None = None
    resolved_baseline_path: Path | None = baseline_path
    if baseline_path is not None:
        if not baseline_path.exists():
            raise FileNotFoundError(f"baseline metadata not found: {baseline_path}")
        baseline_snapshot = ml_extra_metadata_io.read_metadata_snapshot(baseline_path)
        diff = sanity_core.diff_metadata_snapshots(baseline_snapshot, metadata_snapshot)

    metadata_updated: bool | None = None
    if metadata_path is not None:
        metadata_updated = ml_extra_metadata_io.write_metadata_snapshot(
            metadata_path,
            metadata_snapshot,
            only_if_changed=metadata_only_if_changed,
        )

    baseline_updated: bool | None = None
    if update_baseline:
        if baseline_path is None:
            raise ValueError("baseline path required when update_baseline is true")
        baseline_updated = ml_extra_metadata_io.write_metadata_snapshot(
            baseline_path,
            metadata_snapshot,
            only_if_changed=True,
        )

    return BaselineWorkflowResult(
        report=report,
        metadata_snapshot=metadata_snapshot,
        baseline_snapshot=baseline_snapshot,
        diff=diff,
        metadata_path=metadata_path,
        metadata_updated=metadata_updated,
        baseline_path=resolved_baseline_path,
        baseline_updated=baseline_updated,
    )
