# Iteration 41 – `tempbott` staging writer trace

## Goals
- [x] Identify the routine that writes `tempbott+40` (`$4028-$404f`) and `var_4078` (`$4078-$409f`) before the masked pane swap.

## Findings

### Writer location
- Searching `ml-1_2-y2k.asm` for stores to `$4028`/`$4078` only surfaced the indexed stores inside `loopb94e`, confirming there are no other writers within the overlay module.【F:v1.2/source/ml-1_2-y2k.asm†L4094-L4105】
- `loopb94e` lives inside `sub_b8d5`. Each pass copies the preserved bottom overlay from `tempbott`/`$4050` to `$0770/$DB70`, then rotates the staging buffers: characters queued in `tempbott+40` become the next on-screen copy, colours queued in `var_4078` feed `$4050`, and both staging arrays are immediately refilled with a PETSCII space (`#$20`) and the current `mcolor`.【F:v1.2/source/ml-1_2-y2k.asm†L4044-L4105】

### Call path back to the host-facing entry points
- `sub_b8d5` executes from `outscn` whenever the masked pane is active (`scnmode=0`) and the tracked cursor range (`tblx`, `lbl_b9c6`, `lbl_b9c7`) indicates a buffered swap is pending.【F:v1.2/source/ml-1_2-y2k.asm†L3882-L3903】【F:v1.2/source/ml-1_2-y2k.asm†L4044-L4108】
- `outscn` is in the overlay call table (`word outscn`) and is invoked whenever BASIC hands a glyph to the machine-language renderer—for example, via `sub_a786` during sysop keystroke handling and via `disp3` when the masked pane gains focus. Both paths funnel into `outscn`, which then triggers `sub_b8d5` and ultimately `loopb94e` when the swap guard trips.【F:v1.2/source/ml-1_2-y2k.asm†L1530-L1563】【F:v1.2/source/ml-1_2-y2k.asm†L3329-L3340】【F:v1.2/source/ml-1_2-y2k.asm†L3882-L3903】

### Host integration implications
- Because `loopb94e` immediately clears `tempbott+40` and repaints `var_4078` with `mcolor` after consuming them, host code must queue the replacement payloads before `outscn` runs again. The call path above is the earliest integration hook: once BASIC calls `outscn`, any pre-staged overlay data will be rotated into the live screen and the staging buffers wiped for the next cycle.【F:v1.2/source/ml-1_2-y2k.asm†L4094-L4105】

## Open questions
- We still need to catalogue which routines populate `tempbott+40`/`var_4078` with non-empty glyphs and colours ahead of the swap cycle. `loopb94e` only clears these arrays after committing them, so the producing routines that write the “next mask” content remain to be traced before the host can emulate their timing.
