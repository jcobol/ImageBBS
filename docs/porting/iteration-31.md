# Iteration 31 – Canonical metadata diffs from ml.extra sanity runs

## Goals
- Capture the enriched overlay metadata produced by `ml_extra_sanity` as a persistent artefact alongside the text report.
- Close out the snapshot follow-up from iteration 30 by standardising where the diff payload lives.
- Document how the new JSON output complements the metadata surfacing work from iterations 29 and 30.

## Findings
- `ml_extra_sanity` now accepts a `--metadata-json` flag that writes the canonical overlay snapshot to disk while still emitting the human-readable diff, giving automation the same metadata payload that `ml_extra_dump_macros` serialises for spot checks.【F:scripts/prototypes/ml_extra_sanity.py†L600-L638】
- Running `python -m imagebbs.ml_extra_sanity --metadata-json docs/porting/artifacts/ml-extra-overlay-metadata.json` produces the persisted snapshot that downstream tooling can diff across overlay rescans. The artefact captures the flag directory, macro directory, hashes, and hardware defaults recovered in earlier passes.【23a911†L1-L111】【F:docs/porting/artifacts/ml-extra-overlay-metadata.json†L1-L197】
- Treating the JSON as the canonical metadata diff closes the loop from iteration 29’s reporting audit and iteration 30’s snapshot helper: the CLI that validates stub fidelity now also publishes the structured overlay view needed for longitudinal comparison.【F:docs/porting/iteration-29.md†L4-L15】【F:docs/porting/iteration-30.md†L4-L14】

## Workflow
1. Invoke `python -m imagebbs.ml_extra_sanity --metadata-json docs/porting/artifacts/ml-extra-overlay-metadata.json` after any overlay refresh. The CLI recreates parent directories, writes a stable, sorted JSON snapshot, and prints the full diff report for interactive review.【F:src/imagebbs/ml_extra_sanity.py†L1-L12】
2. Commit the updated `docs/porting/artifacts/ml-extra-overlay-metadata.json` file alongside the iteration log so the repository history tracks overlay metadata changes without re-running the tooling.

## Next steps
- Automate multi-run comparisons by diffing successive `ml_extra_sanity` snapshots during overlay rescans or CI runs so regressions are flagged without manual report review.
- Extend the CLI harness to accept a baseline snapshot path and emit a human-readable delta when the recovered metadata diverges from the committed artefact.
