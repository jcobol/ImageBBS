# Iteration 47 – BASIC masked-pane staging map

## Goals
- [x] Audit the recovered BASIC listings for masked-pane producers that feed `tempbott+40`/`var_4078`.
- [x] Catalogue the macro payloads staged prior to each `&,50` flush so host tooling can mirror the glyph/colour queues.

## Findings

### BASIC staging sites for the masked pane
- The `im` dispatcher primes the file-transfer pane by chaining `&,28` with `&,52,21,3`, then fetching the menu macro record (`GOSUB 1011`) before issuing a bare `&` to rotate the staged bytes through `outscn`.【F:v1.2/core/im.txt†L1812-L1816】 The subsequent command handler replays the same sequence on ENTER/INTRO transitions and calls plain `&` again after prompting, ensuring each staged payload hits `loopb94e` on the next ROM print.
- Invalid selections remain within the same loop: the `iff4then:&,28` branch restages the header, while `&,52,5,3`/`&,52,20,3` toggle the sayings/prompt flags before the follow-up bare `&` commits the refreshed buffers.【F:v1.2/core/im.txt†L1842-L1853】 None of these paths perform direct `POKE`s into `$4028-$404F/$4078-$409F`; the staging happens entirely through macro loading and the implicit `&,50` dispatch that follows each flag/macro update.
- Editor setup mirrors the pattern: after `&,52,31,3` seeds the masked-pane offsets the loop drops into `&,54` and immediately executes `&` once the prompt string is printed, reusing the same outscn flush without touching the staging spans manually.【F:v1.2/core/im.txt†L1599-L1615】 These call sites confirm the BASIC side queues content via macro/flag helpers and relies on the bare ampersand to rotate the masked pane on the next character output, matching the `loopb94e` timing described in iteration 41.【F:docs/porting/iteration-41.md†L9-L24】

### Macro payloads queued ahead of `outscn`
- The recovered `MLExtraDefaults` tables expose the glyph and colour matrices consumed by each staging site. Slot `$04` provides the main-menu header (two rows of PETSCII text with `$0A` foreground and `$02` prompt accents), while `$09` supplies the prompt row and `$0D` carries the invalid-selection glyph strip.【26e43c†L7-L29】 These are the payloads staged when the dispatcher primes the primary masked pane before `outscn` fires (iteration 45’s MainMenuModule mirrors the same slots).【F:docs/porting/iteration-45.md†L9-L26】
- Sysop options draw from slots `$14`–`$19`: the header row `$14` paints the “SYSOP OPTIONS” banner in `$0A`, and the subsequent slots are one-byte macros used to refill the masked buffer before pushing sayings, abort banners, or prompt resets.【26e43c†L31-L44】 These align with the `&,52,5,3` and `&,52,20,3` toggles seen in `im.txt`, confirming the BASIC code relies on the macro directory rather than ad-hoc `POKE`s.
- File-transfer flows stage slots `$28`–`$2A`. Slot `$28` carries the six-line menu (all `$0A` on `$08` background), `$29` provides the “COMMAND (Q TO EXIT):” prompt, and `$2A` renders the “?? UNKNOWN COMMAND” pane that replays after the bare `&` flush on invalid entries.【26e43c†L46-L79】 These payloads match the modern `FileTransfersModule` expectations from iteration 45 and 46, which now call `ConsoleService.stage_masked_pane_overlay` before dispatching `&,50`.【F:docs/porting/iteration-45.md†L18-L34】【F:docs/porting/iteration-46.md†L16-L20】

### Implications for the host runtime
- The BASIC listings confirm iteration 44’s hypothesis: the producers live entirely on the BASIC side via macro staging, with no inline `POKE`s refilling `tempbott+40`/`var_4078`. Each macro/flag call is followed immediately by a bare ampersand that routes back to `outscn`, so host tooling must cache the macro payloads before invoking the flush and clear routine.【F:docs/porting/iteration-44.md†L9-L23】【F:v1.2/core/im.txt†L1812-L1853】
- Because the macro slots are static and the flush timing matches `loopb94e`, the host implementation can preload the glyph/colour matrices from `MLExtraDefaults` and stage them ahead of any `&,50` dispatch. The modern console shim already exposes `stage_macro_slot` and `stage_masked_pane_overlay`; wiring these helpers to the staging map above will keep host rotations in lockstep with the C64 overlay.

## Next steps
- Thread the iteration-47 staging map through the host masked-pane helpers so each bare `&` (the implicit `&,50`) receives the queued glyphs/colours before committing the swap.
- Update the console tests to assert that macros `$04/$09/$0D`, `$14-$19`, and `$28-$2A` are staged prior to `&,50`, reusing the matrices recorded here to guard against regressions when new overlays are decoded.
