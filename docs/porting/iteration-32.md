# Iteration 32 – Snapshot guard for baseline overlay comparisons

## Goals
- Add a structured baseline comparison so `ml_extra_sanity` can flag drift between the committed overlay snapshot and fresh rescans during automation runs.【F:scripts/prototypes/ml_extra_sanity.py†L314-L450】
- Provide a thin entry point that runs the sanity checks, loads the committed snapshot, and exits non-zero when the metadata diverges so overlay rescans can plug straight into CI gating.【F:scripts/prototypes/ml_extra_snapshot_guard.py†L1-L96】
- Capture the invocation patterns for the new baseline diff and guard helpers alongside the existing snapshot export guidance.【F:scripts/prototypes/ml_extra_sanity.py†L760-L812】【F:scripts/prototypes/ml_extra_snapshot_guard.py†L1-L96】

## Findings
- `diff_metadata_snapshots` now walks dictionaries and lists recursively, collecting added, removed, and changed fields, and renders a text report that highlights each divergent path before appending the full baseline and current metadata blocks for context.【F:scripts/prototypes/ml_extra_sanity.py†L314-L450】
- The `--baseline-metadata` flag wires that diff into `ml_extra_sanity.main`, loading a JSON snapshot, appending the structured diff to the report payload, and failing the process when differences are detected so automation can stop on regressions.【F:scripts/prototypes/ml_extra_sanity.py†L760-L812】
- A dedicated `ml_extra_snapshot_guard` module wraps the sanity run, reads the default baseline at `docs/porting/artifacts/ml-extra-overlay-metadata.json`, prints either a “matches” confirmation or the diff summary, and returns a CI-friendly exit status.【F:scripts/prototypes/ml_extra_snapshot_guard.py†L1-L96】【F:tests/test_ml_extra_cli.py†L94-L135】

## Workflow
1. Refresh the canonical snapshot after updating overlays with `python -m scripts.prototypes.ml_extra_sanity --metadata-json docs/porting/artifacts/ml-extra-overlay-metadata.json`, then review the text diff emitted alongside the JSON export.【F:scripts/prototypes/ml_extra_sanity.py†L760-L812】
2. Validate rescans by running `python -m scripts.prototypes.ml_extra_sanity --baseline-metadata docs/porting/artifacts/ml-extra-overlay-metadata.json`; a non-zero exit indicates the structured diff found drift that needs investigation.【F:scripts/prototypes/ml_extra_sanity.py†L760-L812】
3. For standalone regression gates, call `python -m scripts.prototypes.ml_extra_snapshot_guard --baseline docs/porting/artifacts/ml-extra-overlay-metadata.json` to run the sanity checks and emit the condensed diff summary that the new tests assert on.【F:scripts/prototypes/ml_extra_snapshot_guard.py†L1-L96】【F:tests/test_ml_extra_cli.py†L94-L135】

## Next steps
- Integrate `ml_extra_snapshot_guard` into the overlay refresh automation so rescans automatically fail when the recovered metadata drifts from the committed baseline.【F:scripts/prototypes/ml_extra_snapshot_guard.py†L1-L96】
- Extend the guard to optionally emit machine-readable JSON or update baselines intentionally so CI pipelines can distinguish expected metadata evolution from regressions.【F:scripts/prototypes/ml_extra_snapshot_guard.py†L49-L96】
