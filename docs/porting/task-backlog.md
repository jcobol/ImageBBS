# Porting Backlog (Iteration 01 Seed)

## Research Tasks
- [x] Disassemble and annotate `sub_c21b`, `sub_c240`, `sub_c283`, `sub_c29a`, and
      `sub_c335` to understand initialization side effects. *(See iteration 02
      notes for a hardware/vector summary.)*
- [x] Map all file loads performed during bootstrap and identify their PRG sources
      within the repository. *(Documented gaps for `screen 1.2`, `setup`, and
      `ml.extra`; `ml.editor` source captured.)*
- [x] Create a memory map of zero-page and high-memory locations touched during
      startup (link equates to observed usage). *(Iteration 03 documents
      bootstrap state and vector hooks.)*
- [x] Trace RS-232 routines in `ml.rs232-192k.asm` to document expectations for
      modem hardware abstraction. *(See SwiftLink notes in iteration 03.)*
- [x] Confirm SwiftLink receive buffer geometry and wrap behaviour.
      *(Iteration 04 characterises the `$cb00` ring buffer.)*
- [x] Document how `sub_c2d4`/`gotocd4f` seed BASIC variables during bootstrap.
      *(Iteration 04 details the lookup-and-table workflow.)*
- [x] Evaluate whether the Python console layer needs to support direct writes to
      the emulated video RAM (e.g., exposing a $0400-style screen buffer or an
      equivalent API) to match Commodore 64 behaviour observed in the original
      machine-language overlays. *(Iteration 37 documents the direct screen and
      colour RAM mutations that require a host buffer interface alongside
      Kernal-compatible print paths.)*【F:docs/porting/iteration-37.md†L1-L37】
- [x] Recover the missing overlay PRGs (`setup`, `ml.extra`, etc.) so the remaining `lbl_c2e5` variables (`D5`, `AK`, `MW`, `C1`–`C3`, `KP`) can be traced and documented. The sysop manual confirms `setup` runs immediately after `im` to DIM variables and load configuration records, so sourcing the original boot disks is prerequisite to finishing the table audit.【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L6864-L6883】 *(Raised in iteration 05 follow-ups.)*
      - Iteration 10 added a D64 extraction helper so recovered disk images can be parsed directly within the repository tooling.
      - Iteration 11 provides placeholder stubs for `setup` and `ml.extra` so host prototypes have deterministic defaults while the authentic PRGs remained missing.【F:v1.2/core/setup.stub.txt†L1-L63】
      - Iteration 19 documents the recovered PRGs under `v1.2/from-floppy/`, including load addresses and PETCAT listings for `setup` and `ml.extra`. Disassembly and re-integration now proceed against the authentic overlays.【F:v1.2/from-floppy/README.md†L1-L21】【F:docs/porting/iteration-19.md†L1-L27】
      - Iteration 21 re-aligns the `setup` stub with the recovered BASIC overlay and exposes helpers that harvest overlay/data defaults straight from the listing for host tooling.【F:docs/porting/iteration-21.md†L1-L24】
      - Iteration 28 replaces the provisional `ml_extra_stub.asm` data with the recovered lightbar, palette, and macro payloads and extends the `MLExtraDefaults` helper so host tooling consumes the same bytes as the C64 overlay.【F:v1.2/source/ml_extra_stub.asm†L1-L119】【F:scripts/prototypes/ml_extra_defaults.py†L1-L149】【F:docs/porting/iteration-26.md†L1-L15】
      - Iteration 31 standardises the `ml_extra_sanity --metadata-json` snapshot so each verification run refreshes the committed overlay metadata diff alongside the text report.【F:docs/porting/iteration-31.md†L1-L15】

## Design Tasks
- [x] Outline a host-platform abstraction layer for disk, console, and modem I/O
      that can mimic Commodore DOS semantics used by the BASIC program.
- [x] Define an approach for representing the `im` BASIC program's control flow in
      a modern language (e.g., module decomposition, state machine extraction).

## Open Questions for Stakeholders
- [x] Confirm target runtime environment (emulation wrapper vs. full rewrite).
      *(Resolved in the [runtime strategy](design-decisions.md#runtime-strategy)
      section of the design decisions.)*
- [x] Determine priority subsystems for parity (sysop UI, messaging, file
      transfers, networking).
      *(Answered by the [preservation of experience](design-decisions.md#preservation-of-experience)
      guidance that names the must-have subsystems.)*
- [x] Identify acceptable deviations from original hardware behaviors (e.g.,
      timing, color codes, PETSCII rendering).
      *(See the [character set fidelity](design-decisions.md#character-set-fidelity)
      and [runtime strategy](design-decisions.md#runtime-strategy) decisions for
      the agreed-upon limits.)*

## Automation Follow-ups
- [x] Diff successive overlay rescans by comparing the committed `ml_extra_sanity` metadata snapshot against fresh runs, emitting actionable reports when fields diverge.【F:docs/porting/iteration-32.md†L5-L17】
- [x] Extend the sanity CLI to accept a baseline snapshot path and highlight changes relative to the canonical artefact produced during iteration 31.【F:docs/porting/iteration-32.md†L9-L17】
- [x] Wire `ml_extra_snapshot_guard` into the overlay refresh automation so rescans fail fast when the committed baseline diverges from freshly decoded metadata.【F:scripts/prototypes/ml_extra_refresh_pipeline.py†L1-L77】【F:tests/test_ml_extra_cli.py†L139-L194】
- [x] Add an opt-in JSON mode or baseline-refresh flag to the snapshot guard so CI jobs can capture machine-readable diffs or bless intentional overlay updates without manual edits.【F:scripts/prototypes/ml_extra_snapshot_guard.py†L24-L105】【F:tests/test_ml_extra_cli.py†L206-L267】

## Host Integration Follow-ups
- [ ] Wire the `ConsoleService` indicator helpers (`set_pause_indicator`, `set_abort_indicator`, `set_spinner_glyph`, `set_carrier_indicator`) into the modern runtime once the host UI event loop is available so status toggles reuse the documented API.【F:docs/porting/iteration-40.md†L56-L75】
- [ ] Route the host idle timer refresh through `update_idle_timer_digits` when session scheduling lands, ensuring the colon at `$04df` remains untouched as noted in iteration 40's rationale.【F:docs/porting/iteration-40.md†L66-L72】
- [x] Trace which routine fills `tempbott+40` and `var_4078` between buffer swaps so the host can request the same payloads before rotating overlays.【F:docs/porting/iteration-41.md†L1-L32】
- [ ] Decide whether the host UI should mirror the five-phase `lbl_adca` blink cadence or substitute a standard timer before finalising the masked-pane API.【F:docs/porting/iteration-40.md†L49-L50】
- [x] Replace the manual chat/sysop block swap loops with a `ConsoleRegionBuffer`
      helper so 240-byte screen spans and 80-byte colour spans travel through
      `ConsoleService.swap_region`, keeping transcript handling centralised.【F:docs/porting/iteration-40.md†L8-L16】【F:scripts/prototypes/device_context.py†L360-L470】
- [ ] Wire the `ConsoleService` indicator helpers (`set_pause_indicator`, `set_abort_indicator`, `set_spinner_glyph`, `set_carrier_indicator`) into the modern runtime once the host UI event loop is available so status toggles reuse the documented API.【F:docs/porting/iteration-40.md†L5-L30】
- [ ] Route the host idle timer refresh through `update_idle_timer_digits` when session scheduling lands, ensuring the colon at `$04df` remains untouched as noted in iteration 40's rationale.【F:docs/porting/iteration-40.md†L11-L29】
- [x] Catalogue the BASIC staging routines that refill `tempbott+40`/`var_4078` so the host can cache the masked-pane payload before `outscn` consumes it. *(Iteration 47 documents the macro-driven producers and their implicit `&,50` flushes.)*【F:docs/porting/iteration-47.md†L10-L21】
- [ ] Mirror the iteration-47 staging map in the host runtime so cached payloads are queued ahead of the `outscn` equivalent.【F:docs/porting/iteration-47.md†L23-L25】
- [ ] Feed the cached staging bytes into the host's pane-rotation helper immediately before invoking the `outscn` equivalent, keeping the swap timing aligned with the original buffer rotation.【F:docs/porting/iteration-44.md†L15-L19】
