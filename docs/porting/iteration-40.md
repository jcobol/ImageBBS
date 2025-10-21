# Iteration 40 – Masked sysop pane refresh spec

## Goals
- [x] Trace how `loopad37`, `sub_ad62`, and `loopb94e` share buffers when the masked sysop pane is active.
- [x] Derive host-side APIs capable of replaying the `$0518/$0770` spans and colour RAM writes during chat buffer swaps.

## Findings

### Screen, colour, and staging ranges
| Region | Address span | Colour span | Backing buffer | Primary routines |
| --- | --- | --- | --- | --- |
| Masked sysop glyph row | `$0518-$053F` (40 bytes) | `$D918-$D93F` (`colorram+280`) | `tempbott+40` (next glyphs) → `tempbott` (current glyphs) | `sub_ad62`, `loopb8fb`, `loopb94e`【F:v1.2/source/ml-1_2-y2k.asm†L2404-L2455】【F:v1.2/source/ml-1_2-y2k.asm†L3986-L4107】 |
| Masked sysop colour strip | — | `$DBCC-$DBDB` (`colorram+972`, 16 cells) | `colortbl` palette | `loopad37`【F:v1.2/source/ml-1_2-y2k.asm†L2404-L2428】【F:v1.2/source/ml-1_2-y2k.asm†L2506-L2506】 |
| Bottom status overlay | `$0770-$0797` (40 bytes) | `$DB70-$DB97` (`colorram+880`) | `tempbott` / `$4050` (colour), staged in `var_4078` | `loopb94e`【F:v1.2/source/ml-1_2-y2k.asm†L4091-L4107】 |

```
chat buffer swap
│
├─ tempbott+40[40]  ──► tempbott[40] ──► $0770-$0797
│        │                    │
│        └─ cleared to $20    └─ mirrored into $0518-$053F when key echo fires
└─ var_4078[40]    ──► $4050-$4077 ──► $DB70-$DB97
         │                    │
         └─ filled with mcolor└─ reused as masked row colours
```

### Routine coordination
- `loopad37` runs from the idle loop (`gotoad0f`) whenever split-screen mode is active (`scnmode=0`). It loads a palette entry from `colortbl` using the cycling index in `var_42ec`, but forces entry `0` while chat buffer 0 is active. The routine paints 16 consecutive colour RAM cells at `$DBCC-$DBDB`, refreshing the highlighted strip beneath the sysop pane.【F:v1.2/source/ml-1_2-y2k.asm†L2404-L2428】
- `sub_b9c9` snapshots BASIC's cursor state (screen pointer `pnt`, column `tblx`, and colour `color`) into shadow variables (`lbl_ad64+1/2`, `lbl_ad68+1/2`, `mcolor`, `zp_02`). Each masked-pane keystroke calls `sub_b9c9` before `sub_ad6c`, so the machine-language overlay knows which byte inside `$0518` should be refreshed.【F:v1.2/source/ml-1_2-y2k.asm†L3890-L3945】【F:v1.2/source/ml-1_2-y2k.asm†L4149-L4172】
- `sub_ad6c`/`sub_ad62` gate writes into `$0518` and `$D918` by checking the staged cursor bounds (`lbl_b9c6`/`lbl_b9c7`) and the blink counter in `lbl_adca`. When `skipad3d+1` is non-zero, `gotoad0f` copies the currently buffered glyph (`key`) and colour (`mcolor`) into the masked pane via `STA var_0518,y` and `STA colorram+280,y`, applying reverse-video every other pass to mimic the Commodore blink.【F:v1.2/source/ml-1_2-y2k.asm†L2404-L2455】
- `loopb94e` replays the 40-byte bottom overlay from `tempbott` and `$4050` to `$0770-$0797` and `$DB70-$DB97`. During the same pass it rotates staging buffers: characters waiting in `tempbott+40` become the next preserved copy in `tempbott`, colours in `var_4078` move into `$4050`, the staging arrays are cleared to `$20` (PETSCII space), and `var_4078` is refilled with the most recent `mcolor`. This keeps the host-facing cache aligned with whatever mask the BASIC half prepared before the swap.【F:v1.2/source/ml-1_2-y2k.asm†L4091-L4107】
- `sub_b975` primes the staging pointers (`(user)` → colour buffer, `(pnt)` → screen buffer) with spaces and the current `color`, ensuring the sysop mask remains blanked when no chat buffer overlay is queued.【F:v1.2/source/ml-1_2-y2k.asm†L4109-L4118】

### Refresh sequence when chat buffers swap
1. `sub_b9c9` captures the BASIC cursor and colour context before the machine-language overlay touches masked regions, locking out concurrent screen writes via `scnlock`.【F:v1.2/source/ml-1_2-y2k.asm†L4149-L4172】
2. The idle loop drives `loopad37`, repainting the colour strip every five ticks so the active chat buffer is obvious despite palette animations.【F:v1.2/source/ml-1_2-y2k.asm†L2404-L2428】
3. When a new glyph is ready, `sub_ad6c` copies it out of BASIC's screen pointer into `key`/`shft`, sets `skipad3d+1`, and lets the next idle pass push character and colour bytes into `$0518/$D918` through `sub_ad62` with blink modulation from `lbl_adca`.【F:v1.2/source/ml-1_2-y2k.asm†L2458-L2486】
4. `loopb94e` fires as part of the buffer-rotation path, restoring the preserved bottom overlay from `tempbott`/`$4050`, while simultaneously caching the just-written overlay into the same staging arrays for the next swap.【F:v1.2/source/ml-1_2-y2k.asm†L4091-L4107】
5. `sub_adad` clears the `skipad3d` latch after each commit so repeated idle ticks do not duplicate stores, and restores the captured BASIC state via `sub_b9f7` once the host mask is stable.【F:v1.2/source/ml-1_2-y2k.asm†L2448-L2456】【F:v1.2/source/ml-1_2-y2k.asm†L4174-L4192】

### Blink cadence detail
- `ConsoleService.advance_masked_pane_blink()` delegates to `MaskedPaneBlinkScheduler`, which models the `lbl_adca` countdown by decrementing a five-phase register that wraps from `0` back to `4`. The scheduler reports reverse-video whenever the countdown retains bit `$02`, producing a `3 → 2 → 1 → 0 → 4` loop that only flips the glyph twice per cycle.【F:scripts/prototypes/device_context.py†L697-L715】
- Running the harness shows the reverse phase holds for two 200 ms ticks (countdown values `3` and `2`), followed by three ticks of normal video (countdown values `1`, `0`, and `4`), yielding a one-second cadence that feels slower than a simple blink yet keeps the masked glyph legible during rapid key echoes.【F:docs/porting/blink-traces/authentic-five-phase.csv†L1-L7】

### Host abstraction recommendations
- **Span-aware poke helper** – Continue using `ConsoleService.poke_block` (Iteration 39) for `$0770/$DB70` restores, but extend it to accept `length` so the same call can cover the 40-byte masked row or smaller chat-pane edits without slicing payloads manually.【F:docs/porting/iteration-39.md†L7-L33】
- **Complementary peek helper** – Add `ConsoleService.peek_block(screen_address, length)` that returns both screen and colour bytes. Host code can then emulate the `tempbott`/`$4050` rotation by snapshotting `$0770/$DB70` before replacing them, matching the `loopb94e` staging semantics.【F:v1.2/source/ml-1_2-y2k.asm†L4091-L4107】
- **Colour strip fill primitive** – Provide `ConsoleService.fill_colour(address, length, colour)` so the host can replicate `loopad37` without synthesising a 16-byte array for every palette step.【F:v1.2/source/ml-1_2-y2k.asm†L2404-L2428】
- **Blink scheduler** – Expose a lightweight timer that toggles the masked glyph’s reverse bit every other refresh, mirroring how `lbl_adca` controls the `EOR #$80` path. The host can implement this as a flag on the masked row writer instead of per-byte polling.【F:v1.2/source/ml-1_2-y2k.asm†L2404-L2455】
- **Buffer ownership map** – Model the four staging arrays (`tempbott`, `tempbott+40`, `$4050`, `var_4078`) as discrete host buffers so higher-level code knows which payload represents “current mask on screen” versus “next mask to restore”. This mirrors the machine-language rotation performed inside `loopb94e`.【F:v1.2/source/ml-1_2-y2k.asm†L3986-L4107】

### Outstanding notes
- The repository does not yet identify which routine repopulates `tempbott+40` and `var_4078` between swaps; confirming that producer will be necessary before wiring host callbacks that queue the “next” mask content.【F:v1.2/source/ml-1_2-y2k.asm†L3986-L4107】
- The blink cadence relies on the countdown in `lbl_adca`, which resets to `4` and decrements every idle iteration. Stakeholders have since confirmed the port will retain the authentic five-phase pattern documented above, so host APIs should continue exposing the countdown unchanged.【F:v1.2/source/ml-1_2-y2k.asm†L2404-L2455】【F:docs/porting/host-ui-indicator-plan.md†L66-L78】

---

## Historical goals and implementation notes – Named console indicator helpers

### Goals
- [x] Provide descriptive helpers for the pause/abort cells, idle timer digits, spinner glyph, and carrier indicator.
- [x] Cover the helpers with regression tests that confirm transcript integrity and address targeting.
- [x] Record usage guidance so future host integrations prefer the new API over hardcoded `$0400` offsets.

### Implementation
- Added address-aware wrappers on `ConsoleService` for pause/abort toggles, idle timer digits, the activity spinner, and the carrier indicator, all routing through the existing `poke_*` entrypoints so host code can mutate the renderer without touching the transcript buffer.【F:scripts/prototypes/device_context.py†L372-L466】
- Extended `tests/test_console_address_helpers.py` with pytest coverage that exercises the helpers, checks that the transcript bytes remain unchanged, and verifies the expected PETSCII/colour values via `peek_screen_address`/`peek_colour_address`.【F:tests/test_console_address_helpers.py†L1-L102】
- Introduced `ConsoleRegionBuffer` alongside `capture_region`/`restore_region`/`swap_region` helpers so host integrations can mirror the `tempbott`/`tempcol` swap loops without bespoke copy code, keeping block writes funneled through `Console.poke_block`.【F:scripts/prototypes/device_context.py†L360-L470】
- Added regression tests that stage representative 240-byte screen spans and 80-byte colour spans, invoke the new swapper, and assert both the buffer and live screen RAM reflect the exchanged payloads while the transcript stays untouched.【F:tests/test_console_span_buffer.py†L1-L86】

### Usage rationale
| Helper | Screen RAM touch points | Colour RAM support | Expected usage |
| --- | --- | --- | --- |
| `set_pause_indicator` | `$041e` | Optional single-cell override | Flip the sysop pause glyph when the host detects `Ctrl+S`/`Home` semantics, mirroring `gotoa722` / `skipa739`. |
| `set_abort_indicator` | `$041f` | Optional single-cell override | Toggle the abort column that `sub_b410` seeds and `sub_b66c` flashes during garbage collection. |
| `update_idle_timer_digits` | `$04de/$04e0/$04e1` | Optional three-cell override | Refresh the idle timer minutes/seconds digits that `sub_a91f` updates in place without disturbing the separating colon at `$04df`. |
| `set_spinner_glyph` | `$049c` | Optional single-cell override | Animate the activity spinner driven by `skipb195`/`skipb1ae`. |
| `set_carrier_indicator` | `$0400` and `$0427` | Optional overrides for each cell | Mirror the carrier detect status that `skipb1ef` / `skipb202` slam into the status line. |

### Follow-ups
- Added backlog entries for wiring these helpers into the eventual host UI/event loop so the modern runtime reuses the same abstractions documented here.
