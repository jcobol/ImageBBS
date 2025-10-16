# Iteration 30 – Snapshotting ml.extra metadata

## Goals
- Persist the recovered overlay metadata to disk so future rescans can diff the JSON payload directly.
- Extend CLI coverage so the new snapshot path is tested alongside the existing text and JSON reporters.

## Findings
- `ml_extra_dump_macros` accepts a `--metadata-json` flag that writes the enriched metadata snapshot to disk while preserving the existing text/JSON report flows.【F:scripts/prototypes/ml_extra_dump_macros.py†L95-L153】
- The CLI creates parent directories on demand and serialises the snapshot with stable formatting, making ad-hoc diffs between overlay revisions straightforward.【F:scripts/prototypes/ml_extra_dump_macros.py†L133-L145】
- A dedicated regression test exercises the file-writing path and validates the record and slot counts against the in-memory defaults so future tooling changes cannot silently drop fields from the snapshot.【F:tests/test_ml_extra_cli.py†L38-L67】

## Next steps
- Thread the snapshot helper through `ml_extra_sanity` so a full verification run can emit a canonical metadata diff artefact.
- Promote the disk snapshot into the iteration backlog for wider automation once additional overlays are recovered.
