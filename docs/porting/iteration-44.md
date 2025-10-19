# Iteration 44 – Mask staging producer audit

## Goals
- [x] Catalogue every routine in `ml-1_2-y2k.asm` that writes to `tempbott+40`/`var_4078` prior to the `loopb94e` buffer rotation.
- [x] Trace each path back to the BASIC dispatcher so the host knows when the “next mask” payload must already be staged before `outscn` runs.

## Findings

### No dedicated producer inside the overlay
- Exhaustive greps for `tempbott+40` and `var_4078` confirm the only stores inside the overlay remain the indexed writes embedded in `loopb94e`; the routine consumes the staged bytes, mirrors them into the live overlay, then immediately clears the staging spans back to PETSCII space (`#$20`) with `var_4078` reset to `mcolor`.【F:v1.2/source/ml-1_2-y2k.asm†L4091-L4107】
- Aside from this rotation, only the initialisation loops in `sub_b8d5`, `sub_b0c3`, and `gotoc185` touch the backing buffers, and each walk the full 80-byte span starting at `$4000`. They either seed the arrays with spaces/`mcolor` (clean boot) or exchange their contents with `mask_bot`/`$4050` during mode changes; none of these paths stage a fresh “next mask” payload for `loopb94e` to consume.【F:v1.2/source/ml-1_2-y2k.asm†L3985-L4006】【F:v1.2/source/ml-1_2-y2k.asm†L2892-L2936】【F:v1.2/source/ml-1_2-y2k.asm†L4940-L4963】
- Because the machine-language overlay never repopulates `tempbott+40`/`var_4078` after clearing them, the producer must live on the BASIC side (direct POKEs or higher-level routines). Host tooling therefore has to watch for BASIC-sourced writes if it wants to mirror the staging semantics exactly.

### When `loopb94e` fires
- `loopb94e` executes from within `sub_b8d5` once `outscn` determines the masked pane swap guard (`tblx`, `lbl_b9c6`, `lbl_b9c7`) has rolled past the buffered region. The routine copies preserved glyphs/colours from `tempbott`/`$4050` to `$0770/$DB70`, rotates the staging buffers, and blanks `tempbott+40`/`var_4078` for the next cycle.【F:v1.2/source/ml-1_2-y2k.asm†L4044-L4108】
- `outscn` is the only overlay entry point that reaches `sub_b8d5`. It runs in three scenarios: (1) general character output via `sub_a786` (keyboard echo and interpreter printing), (2) pane resets through `disp3` (`&,21`), and (3) any direct `&,50` invocation. All of these paths return straight to BASIC immediately after `outscn` completes, so any host-side staging must happen before these calls fire.【F:v1.2/source/ml-1_2-y2k.asm†L3329-L3340】【F:v1.2/source/ml-1_2-y2k.asm†L3882-L3903】【F:v1.2/source/ml-1_2-y2k.asm†L1528-L1563】

### Host impact
- Since `loopb94e` wipes the staging buffers on every pass and nothing in the overlay back-fills them, the modern runtime must queue the “next mask” payload before control reaches `outscn`. That implies the port either mirrors the BASIC writes that fill `$4028-$404F/$4078-$409F` or introduces an explicit host API that stages the next overlay prior to invoking the buffer rotation helper.

## Follow-ups
- Update the backlog with host-runtime tasks that (a) capture BASIC writes into the staging spans and (b) feed those cached bytes into the rotation helper before each pane swap.
