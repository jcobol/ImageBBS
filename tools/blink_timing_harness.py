"""Generate blink timing traces for authentic and host timer prototypes."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple
import csv
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.prototypes.device_context import (
    MaskedPaneBlinkScheduler,
    MaskedPaneBlinkState,
)


@dataclass
class TraceRow:
    """Single observation captured from a blink scheduler."""

    tick: int
    countdown: int
    reverse: bool
    elapsed_ms: int
    toggled: bool


class HostTimerBlinkScheduler:
    """Simplified two-phase blink driven by a fixed host timer."""

    def __init__(self, toggle_every: int = 2) -> None:
        if toggle_every <= 0:
            raise ValueError("toggle_every must be positive")
        self._toggle_every = toggle_every
        self._remaining = toggle_every
        self._reverse = False

    def advance(self) -> MaskedPaneBlinkState:
        """Advance the timer and toggle reverse every ``toggle_every`` ticks."""

        self._remaining -= 1
        if self._remaining <= 0:
            self._reverse = not self._reverse
            self._remaining = self._toggle_every
        return MaskedPaneBlinkState(self._remaining, self._reverse)


def _capture_trace(
    scheduler: MaskedPaneBlinkScheduler,
    *,
    tick_count: int,
    tick_duration_ms: int,
) -> List[TraceRow]:
    rows: List[TraceRow] = []
    elapsed = 0
    previous_reverse: bool | None = None
    for index in range(tick_count):
        state = scheduler.advance()
        elapsed += tick_duration_ms
        toggled = previous_reverse is not None and state.reverse != previous_reverse
        rows.append(
            TraceRow(
                tick=index + 1,
                countdown=state.countdown,
                reverse=state.reverse,
                elapsed_ms=elapsed,
                toggled=toggled,
            )
        )
        previous_reverse = state.reverse
    return rows


def _write_trace_csv(path: Path, scheme: str, rows: Sequence[TraceRow]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["scheme", "tick", "countdown", "reverse", "elapsed_ms", "toggled"])
        for row in rows:
            writer.writerow(
                [
                    scheme,
                    row.tick,
                    row.countdown,
                    int(row.reverse),
                    row.elapsed_ms,
                    int(row.toggled),
                ]
            )


def generate_traces(
    *,
    authentic_ticks: int = 20,
    authentic_tick_ms: int = 200,
    host_ticks: int = 20,
    host_tick_ms: int = 250,
    host_toggle_every: int = 2,
) -> Tuple[List[TraceRow], List[TraceRow]]:
    """Produce trace rows for authentic and host-timer schedulers."""

    authentic = _capture_trace(
        MaskedPaneBlinkScheduler(),
        tick_count=authentic_ticks,
        tick_duration_ms=authentic_tick_ms,
    )
    host = _capture_trace(
        HostTimerBlinkScheduler(toggle_every=host_toggle_every),
        tick_count=host_ticks,
        tick_duration_ms=host_tick_ms,
    )
    return authentic, host


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    trace_dir = repo_root / "docs" / "porting" / "blink-traces"
    trace_dir.mkdir(parents=True, exist_ok=True)

    authentic, host = generate_traces()

    _write_trace_csv(trace_dir / "authentic-five-phase.csv", "authentic", authentic)
    _write_trace_csv(trace_dir / "host-timer.csv", "host_timer", host)

    combined_path = trace_dir / "blink-timing-comparison.csv"
    with combined_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["scheme", "tick", "countdown", "reverse", "elapsed_ms", "toggled"])
        for scheme, rows in (
            ("authentic", authentic),
            ("host_timer", host),
        ):
            for row in rows:
                writer.writerow(
                    [
                        scheme,
                        row.tick,
                        row.countdown,
                        int(row.reverse),
                        row.elapsed_ms,
                        int(row.toggled),
                    ]
                )


if __name__ == "__main__":
    main()
