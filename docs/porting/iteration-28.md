## Goals
- Surface the new overlay metadata across the sanity/dump/disassembly CLIs and protect the output with regression tests.
- Attach deterministic payload hashes to the recovered macro directory so tooling can spot byte-level drift.
- Refresh contributor guidance (AGENTS.md) to point at the modern ml.extra tooling pipeline and notation updates.

## Findings
- `ml_extra_sanity.run_checks` now records SHA-256 digests for every recovered payload and threads them through the JSON/text reports alongside the existing flag/lightbar metadata. Companion tests keep the hashes and formatting stable.
- The macro dump and disassembly CLIs expose the same overlay metadata plus per-slot hashes in both JSON and human-readable modes. Fresh pytest coverage captures the `--metadata` pathways so future edits cannot silently drop the fields.
- PETSCII control codes are rendered as `{CBM-$xx}` tokens, aligning the extractor output with the notation used in prior documentation snapshots. The decode unit tests pin the new representation.
- Running `python -m scripts.prototypes.ml_extra_sanity` confirms the transplanted stub data still matches the recovered overlay (lightbar bitmaps, palette bytes, and macro payloads) after the hashing changes.
- `AGENTS.md` has been streamlined so the entry-point overview is no longer duplicated and the collaboration tips reference `ml_extra_defaults`/`ml_extra_sanity` as the canonical tooling surface.

## Next steps
- Map additional PETSCII control codes to human-readable names (for example `{CBM-G}` or `{SHIFT-*}`) so reports can mirror the historic transcription style instead of raw hex markers.
- Consider snapshotting the hashed macro directory to disk for quick diffing between archived disk images.
