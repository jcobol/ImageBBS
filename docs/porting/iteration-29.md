# Iteration 29 – Auditing ml.extra metadata consumers

## Goals
- Ensure every CLI that relies on `MLExtraDefaults` surfaces the recovered overlay metadata, including the flag dispatch and tail bytes.
- Confirm the transplanted stub data remains byte-identical to the recovered `ml.extra` overlay after the hashing/reporting updates.

## Findings
- `ml_extra_reporting.collect_overlay_metadata` now exposes the flag dispatch table, tail bytes, record count, and macro slot list so downstream CLIs emit the complete overlay snapshot alongside the lightbar, palette, and hardware defaults.【F:scripts/prototypes/ml_extra_reporting.py†L1-L111】
- The `ml_extra_dump_macros` and `ml_extra_disasm` `--metadata` output includes the new fields; regression tests assert the JSON/text variants retain the dispatch summary, tail text, and slot listing next to the per-slot hashes.【F:tests/test_ml_extra_cli.py†L1-L78】
- Fresh `ml_extra_sanity` coverage proves the stub macro payloads, static tables, and directory counts still match the recovered overlay byte-for-byte, tightening confidence in the transplanted defaults.【F:tests/test_ml_extra_sanity.py†L1-L84】

## Next steps
- Curate reference screenshots from existing video captures that demonstrate the lightbar and macro hotkeys, noting the source and timestamp so the visuals can supplement the automated byte-for-byte checks; capture the white reverse-text status bar along the bottom edge to anchor the lightbar terminology.
- Catalogue each screenshot with a short textual description (see `docs/porting/references/lightbar-screenshot-description.txt`) so the function-key legends embedded in the lightbar document the expected macro hotkeys without needing a separate legend.
- Consider snapshotting the enriched metadata payload to disk (JSON) for quick diffing between future overlay rescans.
