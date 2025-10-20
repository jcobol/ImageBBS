# Host UI Indicator Event Loop Plan

## Purpose
This plan captures how the modern host event loop should drive the `ConsoleService` indicator helpers without touching the transcript buffers. It synthesises the sequencing rules recovered in the masked-pane research from iterations 40 and 44 so the ported runtime can surface the same UI affordances as the original Commodore 64 build.【F:docs/porting/iteration-40.md†L1-L109】【F:docs/porting/iteration-44.md†L1-L40】

## Overlay sequencing recap
- `outscn` remains the gatekeeper for masked-pane swaps. Each time BASIC hands control to `outscn`, it flows through `sub_b8d5`, which in turn invokes `loopb94e` to restore the preserved bottom overlay, rotate the staging buffers, and clear `tempbott+40` / `var_4078` for the next payload.【F:docs/porting/iteration-44.md†L12-L24】  
- During idle ticks (`gotoad0f`), the overlay refreshes auxiliary status cells: `loopad37` paints the 16-cell colour strip beneath the masked sysop pane, `sub_ad62` / `sub_ad6c` handle masked keystroke echo with blink modulation, and the bottom overlay remains live in `$0770/$DB70` until the next `loopb94e` rotation.【F:docs/porting/iteration-40.md†L12-L55】  
- Because `loopb94e` consumes and clears its staging buffers every swap, BASIC must queue the next payload before calling `outscn`. The host runtime therefore has to capture BASIC-side staging writes and feed them back into the rotation helper at the same scheduling boundary.【F:docs/porting/iteration-44.md†L1-L21】

## Host-side event loop responsibilities
1. **State snapshots before BASIC callbacks** – Maintain mirrors of the BASIC-visible registers that the overlay samples (`pnt`, `tblx`, `color`, cursor row/column) so the host knows when masked keystrokes are staged. This also lets the host reapply palette and cursor context once a swap completes.【F:docs/porting/iteration-40.md†L31-L55】
2. **Swap latch** – Recreate the `skipad3d` style latch so that when BASIC requests a masked glyph commit, the next idle loop pass consumes the buffered glyph and colour bytes exactly once before clearing the latch.【F:docs/porting/iteration-40.md†L44-L55】
3. **Blink cadence** – Preserve the five-phase countdown (`lbl_adca`) that toggles reverse-video on alternating idle passes unless the stakeholders approve a modernised timer. The event loop should expose a monotonic tick so the masked glyph writer can maintain parity with the Commodore cadence.【F:docs/porting/iteration-40.md†L43-L55】
4. **Masked-pane payload capture** – Intercept host-side equivalents of BASIC writes into `$4028-$404F/$4078-$409F` so the next overlay payload is available before invoking the rotation helper. This may require instrumentation on the BASIC interpreter shim or an explicit staging API in the host runtime.【F:docs/porting/iteration-44.md†L1-L21】
5. **Pane rotation sequencing** – Ensure the cached staging bytes are applied immediately before the host analogue of `outscn`/`loopb94e` runs, mirroring the original “restore → rotate → clear” sequence without touching the transcript log.【F:docs/porting/iteration-44.md†L24-L29】

## Indicator helper integration
The event loop should treat each helper as a pure screen/colour RAM operation. Drives are aligned with the BASIC dispatcher, modem state, and masked-pane transitions as follows:

### `set_pause_indicator`
- **Trigger** – Fires when BASIC or the host dispatches the pause toggle (`Ctrl+S` or `&,21` resets). Use the same guard the overlay uses for `skip a739` to prevent duplicate writes during repeated idle passes.【F:docs/porting/iteration-40.md†L63-L75】
- **State dependencies** – Requires the current reverse-video phase from the blink cadence so that pause glyph flashing remains in sync with the masked-pane blink when both are active.
- **Timing** – Apply immediately after BASIC issues the pause command but before the next masked-pane swap, ensuring the indicator reflects the paused state during subsequent idle cycles.

### `set_abort_indicator`
- **Trigger** – Update when BASIC transitions into or out of abortable routines (garbage collection, disk I/O). Monitor the same BASIC flag that `sub_b66c` observes to avoid racing with overlay-side flashes.【F:docs/porting/iteration-40.md†L63-L75】
- **State dependencies** – Needs modem carrier context so the indicator can be suppressed when no caller is connected (the original code blanks the column when carrier drops).【F:docs/porting/iteration-40.md†L74-L75】
- **Timing** – Commit the indicator on the same host tick that schedules the blocking operation, before any pane swap so the sysop sees the status change even if the next event is a masked glyph.

### `set_spinner_glyph`
- **Trigger** – Advance on each host idle tick while BASIC remains in the main loop (`gotoad0f` analogue). The host timer that drives masked blink updates can also feed the spinner sequencer.【F:docs/porting/iteration-40.md†L63-L75】
- **State dependencies** – Shares the pause/abort cell row, so the event loop must serialise updates to avoid tearing during masked-pane swaps. Maintain a cached PETSCII index rather than peeking live RAM to keep transcript buffers untouched.
- **Timing** – Execute after the blink cadence update but before masked glyph commits so the spinner frame is visible alongside any newly staged overlay bytes.

### `set_carrier_indicator`
- **Trigger** – Respond to modem carrier state transitions delivered by the host modem abstraction, matching the places where `skipb1ef`/`skipb202` run inside the overlay.【F:docs/porting/iteration-40.md†L72-L75】
- **State dependencies** – Needs both primary and mirrored cells (`$0400` and `$0427`) refreshed atomically so the status bar stays consistent. If the host modem layer debounces carrier, forward the stable signal to this helper.
- **Timing** – Update immediately when carrier transitions so BASIC’s next loop iteration already reflects the correct state. No dependency on pane swaps beyond ensuring the write precedes any `outscn` call triggered by modem events.

### `update_idle_timer_digits`
- **Trigger** – Runs whenever the host session scheduler increments the idle counter (every second).【F:docs/porting/iteration-40.md†L66-L72】
- **State dependencies** – Needs the colon separator preserved; maintain a cached minutes/seconds tuple in host state to compute deltas without peeking the transcript.
- **Timing** – Apply after spinner updates on the same idle tick. Defer if a pane rotation is in flight and the host requires atomic screen updates; otherwise it can safely run before or after masked glyph commits because it touches unrelated addresses.

## Modern runtime signal sources
To satisfy the above sequencing without transcript mutations, expose the following signals from the runtime:
- **BASIC dispatcher hooks** – Emit events before invoking host equivalents of `outscn`, `&,21`, `&,50`, and other commands that manipulate the masked pane or status indicators. Include the cursor position and any pending masked glyph bytes.【F:docs/porting/iteration-40.md†L31-L55】【F:docs/porting/iteration-44.md†L12-L24】
- **Idle tick timer** – Provide a monotonic tick shared by the spinner and blink cadence. When integrating with async runtimes, surface this as an awaitable that fires every 1/5 second to keep parity with the Commodore cadence.【F:docs/porting/iteration-40.md†L43-L55】
- **Modem abstraction callbacks** – Push carrier, DTR, and pause-request signals into the event loop so indicators can flip immediately when remote state changes.【F:docs/porting/iteration-40.md†L63-L75】
- **Masked-pane staging API** – Offer host methods to queue the next overlay payload explicitly, mirroring the BASIC writes into `tempbott+40` / `var_4078`. The event loop should treat these writes as transactional and apply them right before the rotation helper runs.【F:docs/porting/iteration-44.md†L1-L29】

## Unresolved questions for stakeholders
1. **Blink cadence fidelity** – Should the host faithfully mirror the five-phase `lbl_adca` countdown, or can the port adopt a modern timer (e.g., 500 ms toggle) if it preserves the perceived blink rate?【F:docs/porting/iteration-40.md†L43-L55】
2. **Masked-pane staging telemetry** – Do we prefer implicit observation of BASIC writes to the staging spans, or should the runtime expose explicit APIs that BASIC ports must call before triggering a swap?【F:docs/porting/iteration-44.md†L1-L29】
3. **Carrier-loss behaviour** – When modem carrier drops mid-swap, should the host prioritise clearing the carrier indicator or finishing the pending overlay rotation first? Clarifying this ordering will determine whether writes queue or cancel in-progress swaps.
