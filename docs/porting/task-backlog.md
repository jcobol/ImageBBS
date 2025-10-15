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

## Design Tasks
- [ ] Outline a host-platform abstraction layer for disk, console, and modem I/O
      that can mimic Commodore DOS semantics used by the BASIC program.
- [ ] Define an approach for representing the `im` BASIC program's control flow in
      a modern language (e.g., module decomposition, state machine extraction).

## Open Questions for Stakeholders
- [ ] Confirm target runtime environment (emulation wrapper vs. full rewrite).
- [ ] Determine priority subsystems for parity (sysop UI, messaging, file
      transfers, networking).
- [ ] Identify acceptable deviations from original hardware behaviors (e.g.,
      timing, color codes, PETSCII rendering).
