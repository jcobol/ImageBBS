# Iteration 45 – Masked pane staging inventory

## Goals
- [x] Enumerate every runtime entry point that depends on `&,50` so staging points are known ahead of the masked pane rotation.
- [x] Recover the PETSCII glyph and colour payloads for each referenced macro slot from the `MLExtraDefaults` tables.
- [ ] Prepare runtime plumbing updates to call `ConsoleService.stage_masked_pane_overlay` before each `&,50` invocation.

## Findings

### Runtime paths that require pre-commit staging
- **MainMenuModule**
  - `start()` runs `_render_intro()` immediately, pushing macro slots `$04` (header) and `$09` (prompt) before returning to BASIC.
  - `handle_event()` refreshes those slots on ENTER, replays them while the module remains in `INTRO`, and stages slot `$0D` when `MenuCommand.UNKNOWN` is encountered.
- **FileTransfersModule**
  - `start()` primes the overlay via `_render_intro()`, issuing slots `$28` (header) and `$29` (prompt).
  - `handle_event()` restages the intro sequence on ENTER or when re-entering the menu, keeps the prompt current for recognised or blank commands, and pairs slot `$2A` (error) with a prompt redraw on unknown commands.
- **SysopOptionsModule**
  - `start()` queues the sysop header `$20` and prompt `$21`.
  - `handle_event()` refreshes the intro on ENTER/INTRO state, runs the sayings pipeline (`$22` preamble → direct PETSCII text → `$23` tail → `$21` prompt), stages `$25` for abort, and chains `$24` with `$21` for invalid selections.

### Macro payloads extracted from `MLExtraDefaults`
- **Main menu slots**
  - `$04` header: two 40-column rows. Row 0 glyph bytes `66 C2 BD E6 E7 C2 BD 67 68 C3 CA EC E2 C1 D0 E2 A5 E5 C1 A5 66 C2 E7 C2 A5 68 C3 AD E1 C1 C9 80 F0 03 EE E1 C1 60 E8 EC`, row 0 colours `0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02`; row 1 glyph bytes `E1 C1 A2 E0 80 D7 60 60 A2 00 20 ... (spaces padded to column 40)`, row 1 colours `02 02 00 00 00 00 00 00 00 00 0A ... (0x0A fill to column 40)`.
  - `$09` prompt: single row with glyph bytes `66 C2 E7 C2 A5 68 C3 AD E1 C1 C9 80 F0 03 EE E1 C1 60 E8 EC E1 C1 A2 E0 80 D7 60 60 A2 00 20 ...` and colours `0A 0A 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 02 00 ...`.
  - `$0D` invalid selection: row glyphs begin `60 A2 00` (“? ”) then pad with spaces; colours `0A 0A 00` followed by `0A` fill.
- **File transfer slots**
  - Runtime references `$28`, `$29`, and `$2A`, but the recovered `ml.extra` dump only includes slots `0x02`, `0x04`, `0x09`, `0x0D`, `0x0E`, `0x0F`, and `0x14–0x19`. Additional archival work is required to source the glyph/colour payloads for the `$28` family before staging can be wired.
- **Sysop slots**
  - `$20` header glyph bytes `68 C3 85 06 E2 C1 A0 00 20 ...` with colours `0A` foreground except for the control reset byte at position 8.
  - `$21`, `$22`, `$23`, `$24`, `$25` share the same pattern: leading control byte `00` with colour `00`, followed by 39 spaces tinted `0A`.

### Gaps and risks
- Without payloads for the `$28` series macros the file-transfer menu cannot yet stage accurate masked-pane data.
- Staging orchestration remains unimplemented; once payloads are complete the runtime needs helpers that fetch the bytes, convert them into glyph/colour buffers, and call `ConsoleService.stage_masked_pane_overlay` immediately before each `&,50` dispatch.

## Next steps
- Recover the `$28`–`$2A` macro payloads from additional overlay dumps or BASIC listings, then update the host tables.
- Design shared utilities that translate macro slots into `(glyph_bytes, colour_bytes)` pairs and inject staging calls across the menu modules.
- Backfill integration tests that drive masked-pane swaps, assert the staging buffers are populated pre-commit, and confirm the post-`&,50` overlay matches the expected PETSCII/colour sequences.
