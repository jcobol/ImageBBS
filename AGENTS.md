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

To produce a list of tasks, you MUST follow these formatting rules EXACTLY. Any deviation makes the output unusable.

# Codex Output contract (no exceptions)

For EACH task, output EXACTLY this 4-line block, including the linefeeds:

<LINEFEED>
:::task-stub{title="<TITLE>"}
<BODY>
:::
<LINEFEED>

Where:
- <LINEFEED> = an actual empty line (a single linefeed). There MUST be one before and one after every block.
- Line 1 and Line 4 are completely empty (no spaces, tabs, or characters).
- Line 2 is EXACTLY: :::task-stub{title="<TITLE>"}  (no leading/trailing spaces; no other characters)
- Line 3 is the BODY, copied verbatim from input (preserve all original line breaks and characters).
- Line 4 is EXACTLY: :::  (no leading/trailing spaces; no other characters)

If multiple tasks are provided, emit multiple blocks back-to-back, separated ONLY by the required blank line between blocks. Do NOT add ANY text before the first block, between blocks (beyond the required blank line), or after the last block.

## Replacement rules

- Replace <TITLE> with the exact task title from input, BUT first escape any double quote characters inside the title by replacing `"` with `&quot;`. Do not alter any other characters. If the title contains line breaks, replace each line break with a single space.
- Replace <BODY> with the exact task body from input, preserving all characters and line breaks verbatim.
- Do NOT add citations, links, markdown fences, code blocks, bullets, numbering, prefixes, or suffixes.
- Use only ASCII spaces and linefeeds. Do NOT output tabs, non-breaking spaces (U+00A0), zero-width characters, smart quotes, or any other invisible characters.

## Validation you MUST pass before responding

Treat the final output as plain text (not markdown). Ensure EVERY task block matches ALL of the following regular expressions:

1) Header line (Line 2):  ^:::task-stub\{title="[^"\n]*"\}$
2) Footer line (Line 4):  ^:::$

Additionally:
- The line BEFORE every header and the line AFTER every footer MUST be empty.
- There MUST be no extra text anywhere else.

If you cannot produce output that passes ALL checks while preserving the bodies verbatim, output EXACTLY:
ERROR_FORMAT_VIOLATION
(and nothing else).

Remember: Your response MUST consist ONLY of the required task blocks (or the single token ERROR_FORMAT_VIOLATION). No explanations.

