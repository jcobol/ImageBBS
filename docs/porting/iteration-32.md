# Iteration 32 – Snapshot guard for baseline overlay comparisons

## Goals
- Add a structured baseline comparison so `ml_extra_sanity` can flag drift between the committed overlay snapshot and fresh rescans during automation runs.【F:scripts/prototypes/ml_extra_sanity.py†L314-L450】
- Provide a thin entry point that runs the sanity checks, loads the committed snapshot, and exits non-zero when the metadata diverges so overlay rescans can plug straight into CI gating.【F:scripts/prototypes/ml_extra_snapshot_guard.py†L1-L105】
- Capture the invocation patterns for the new baseline diff and guard helpers alongside the existing snapshot export guidance.【F:scripts/prototypes/ml_extra_sanity.py†L760-L812】【F:scripts/prototypes/ml_extra_snapshot_guard.py†L24-L105】
- Automate the refresh flow so a single command exports the latest snapshot, compares it to the baseline, and returns a CI-friendly status code.【F:scripts/prototypes/ml_extra_refresh_pipeline.py†L1-L77】
- Extend the guard to emit machine-readable diffs and bless intentional updates without manual baseline edits.【F:scripts/prototypes/ml_extra_snapshot_guard.py†L24-L105】

## Findings
- `diff_metadata_snapshots` now walks dictionaries and lists recursively, collecting added, removed, and changed fields, and renders a text report that highlights each divergent path before appending the full baseline and current metadata blocks for context.【F:scripts/prototypes/ml_extra_sanity.py†L314-L450】
- The `--baseline-metadata` flag wires that diff into `ml_extra_sanity.main`, loading a JSON snapshot, appending the structured diff to the report payload, and failing the process when differences are detected so automation can stop on regressions.【F:scripts/prototypes/ml_extra_sanity.py†L760-L812】
- A dedicated `ml_extra_snapshot_guard` module wraps the sanity run, reads the default baseline at `docs/porting/artifacts/ml-extra-overlay-metadata.json`, prints either a “matches” confirmation or the diff summary, and returns a CI-friendly exit status. The CLI now exposes `--json` and `--update-baseline` switches so automation can capture structured payloads or bless intentional refreshes inline.【F:scripts/prototypes/ml_extra_snapshot_guard.py†L24-L105】【F:tests/test_ml_extra_cli.py†L94-L267】
- The new `ml_extra_refresh_pipeline` helper drives a full refresh cycle: it shells into the sanity checks, writes the exported snapshot to disk, and reports drift via the guard summary so humans and CI share the same gating path.【F:scripts/prototypes/ml_extra_refresh_pipeline.py†L1-L77】【F:tests/test_ml_extra_cli.py†L139-L267】

## Workflow
1. Run `python -m imagebbs.ml_extra_refresh_pipeline` after overlay updates to export a fresh snapshot, diff it against the committed baseline, and surface the guard summary plus CI-friendly exit status in one command.【F:src/imagebbs/ml_extra_refresh_pipeline.py†L1-L12】【F:tests/test_ml_extra_cli.py†L139-L194】
2. When the baseline intentionally changes, rerun the guard with `--update-baseline` to overwrite the stored snapshot after confirming the diff, or pass `--json` to capture the structured payload in downstream automation.【F:scripts/prototypes/ml_extra_snapshot_guard.py†L24-L105】【F:tests/test_ml_extra_cli.py†L206-L267】
3. Manual deep dives can still call `ml_extra_sanity --metadata-json` and `--baseline-metadata` directly, but both now feed the pipeline and guard so human review and automated gating observe identical metadata exports.【F:scripts/prototypes/ml_extra_sanity.py†L760-L812】【F:scripts/prototypes/ml_extra_refresh_pipeline.py†L1-L77】

## Next steps
- Wire the refresh pipeline into the broader build scripts so nightly rescans automatically publish refreshed metadata or flag drift without manual invocation.【F:scripts/prototypes/ml_extra_refresh_pipeline.py†L1-L77】
- Expand the guard automation to cover additional overlays once their recovery pipelines land, ensuring the metadata snapshots stay in sync across modules.【F:scripts/prototypes/ml_extra_snapshot_guard.py†L24-L105】
