# Agent Notes for ImageBBS Repository

## Entry Point Information
- The BASIC loader in `v1.2/source/image12.asm` vectors execution to the `stack` routine, which clears the display, prints the Image 1.2 banner, stages the `ml 1.2` module, and jumps into the machine-language overlay at `$c000`.
- Inside the overlay the startup path begins at label `lbl_c000` in `v1.2/source/ml-1_2-y2k.asm`, immediately tail-calling `gotoc00b` to finalise loader configuration before continuing with system initialisation.

## Porting Considerations
- ImageBBS 1.2 targets the Commodore 64 hardware directly. The BASIC loader patches Kernal vectors and assumes the machine-language module will run at the canonical memory layout.
- Assembly routines interact with CIA/ACIA registers (for example the SwiftLink driver), manipulate zero-page buffers, and depend on ROM entry points. Porting requires reimplementing interrupt handlers, buffering, and modem control flows rather than translating syntax line-for-line.
- Commodore BASIC code interleaves user features with direct register and screen-memory manipulation (`POKE`, `OPEN`, `PRINT#`). Higher-level behaviour depends on those side effects, so confirm the routines’ intent under emulation before attempting rewrites.
- Treat a port as a ground-up reimplementation: document observed behaviour under emulation, design abstractions for storage/networking/terminal I/O on the target platform, and rebuild functionality from that specification. Embedding the original code in a C64 emulator is an alternative that trades extensibility for rapid integration.

## Research & Task Tracking Guidance
- Maintain a “porting log” that records findings about routine intent, hardware interactions, open questions, and decisions. Link each entry to corresponding code locations so future contributors avoid repeating reverse-engineering work.
- Keep a living task backlog (Markdown checklist, issue tracker, etc.) that references the porting log. This keeps research synchronised with actionable tasks and highlights where user decisions are required.
- Python remains the recommended coordination language: it is broadly readable, works well for notebooks/scripts that analyse binaries, and can automate documentation updates tied to the porting log.

## Analysis Practices
- Trace how routines interact rather than relying on external documentation. For example, following the BASIC `stack` routine into `gotoc00b` exposes the runtime initialisation flow without needing disassembly comments.

## Codex Collaboration Tips
- Review the iteration logs in `docs/porting/` before starting a task; they capture the latest discoveries about bootstrap behaviour, SwiftLink integration, and outstanding research questions.
- Use the task backlog at `docs/porting/task-backlog.md` to understand current priorities. When closing an item, reference the specific iteration note or code change that satisfied the task.
- Prefer incremental updates to documentation and code per iteration. Pull requests should tie new findings back to the relevant routines in `v1.2/source/` so future reverse-engineering passes have context.
- When scripting analyses, place helpers in `scripts/prototypes/` and document their usage in the iteration log. Reuse shared helpers such as `ml_extra_defaults` and `ml_extra_sanity` so overlay metadata, hashes, and reports stay aligned across the CLI surface area.
- Surface overlay metadata via `ml_extra_dump_macros --metadata` or `ml_extra_disasm --metadata` when reviewing macro changes; both commands now print the flag dispatch summary, tail text, and per-slot hashes alongside the lightbar/palette defaults recovered by `MLExtraDefaults`.
