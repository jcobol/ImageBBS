# Iteration 36 – Commodore console renderer fidelity

## Goals
- [x] Capture Commodore fidelity requirements for glyph rendering, PETSCII behaviour, and palette parity from the design decisions log.
- [x] Survey existing extraction helpers to identify palette and PETSCII metadata available to the renderer.
- [x] Outline implementation steps so the host console renderer consumes recovered palette and glyph data while matching Commodore output.

## Findings
### Commodore Fidelity Requirements
- [x] The port must render Commodore 64 glyphs so PETSCII art and layouts remain identical to the original release, preserving both glyph shapes and PETSCII behaviour.【F:docs/porting/design-decisions.md†L47-L49】
- [x] Colour usage has to match the Commodore palette to keep interface elements visually consistent with the 1.2 experience.【F:docs/porting/design-decisions.md†L47-L49】

### Palette & PETSCII Metadata Available from `ml_extra_defaults`
- [x] `EditorPalette` exposes the four VIC-II colour IDs recovered from `ml.extra`, providing the raw palette tuple and helper serialization.【F:scripts/prototypes/ml_extra_defaults.py†L92-L103】
- [x] `LightbarDefaults` captures the overlay’s underline character/colour plus both lightbar bitmap pairs, allowing the renderer to apply PETSCII highlight conventions.【F:scripts/prototypes/ml_extra_defaults.py†L62-L88】
- [x] `MacroDirectoryEntry` and `FlagRecord`/`FlagDispatchTable` include decoded PETSCII strings and pointers that describe glyph sequences and runtime handlers, making PETSCII text payloads and macro mappings accessible for rendering.【F:scripts/prototypes/ml_extra_defaults.py†L32-L208】
- [x] `HardwareDefaults` aggregates VIC register writes for `$d403-$d406`, the SID volume, and buffer pointer presets, letting the host renderer reproduce startup colour/pointer state changes that affect on-screen output.【F:scripts/prototypes/ml_extra_defaults.py†L401-L466】【F:scripts/prototypes/ml_extra_defaults.py†L609-L622】

### Bootstrap integration progress
- [x] The in-memory console now threads the cached overlay defaults through `Console` and `PetsciiScreen`, exposing lightbar, flag-dispatch, macro, and palette tables before rendering to mirror the bootstrap path.【F:scripts/prototypes/console_renderer.py†L17-L78】【F:scripts/prototypes/device_context.py†L13-L19】【F:scripts/prototypes/device_context.py†L122-L166】

## Plan
### Host Console Renderer Implementation Steps
- [x] **Ingest overlay metadata** – Load `MLExtraDefaults.from_overlay()` to obtain the palette tuple, lightbar defaults, PETSCII payloads, and VIC register write sequences; map these into host-side colour IDs and glyph definitions before initialising the renderer.【F:scripts/prototypes/console_renderer.py†L17-L29】【F:scripts/prototypes/console_renderer.py†L43-L71】
- [ ] **Seed VIC-II state** – Apply the recovered `$d403-$d406` writes and SID volume to the renderer’s colour/background registers so the initial frame matches Commodore startup behaviour, mirroring the VIC register handling described for the console renderer component.【F:scripts/prototypes/ml_extra_defaults.py†L401-L466】【F:docs/porting/iteration-08.md†L12-L18】
- [ ] **Build PETSCII glyph table** – Use the `MacroDirectoryEntry` PETSCII payloads and the decoded flag directory text to populate character-cell definitions, ensuring the renderer respects Commodore glyph shapes and PETSCII control semantics.【F:scripts/prototypes/ml_extra_defaults.py†L32-L208】【F:scripts/prototypes/ml_extra_defaults.py†L238-L301】
- [ ] **Implement colour-safe drawing primitives** – Expose render routines that honour the recovered palette indices, applying lightbar underline colours and any palette toggles emitted through VIC register writes to keep colour parity with the C64 output.【F:scripts/prototypes/ml_extra_defaults.py†L62-L103】【F:scripts/prototypes/ml_extra_defaults.py†L401-L466】
- [ ] **Integrate with host abstraction layer** – Attach the renderer to the console endpoint defined in the host abstraction plan so BASIC-equivalent code can issue PETSCII output through a device context while the renderer handles colour, cursor movement, and status line helpers noted for `GOSUB1378`.【F:docs/porting/iteration-08.md†L12-L18】
- [ ] **Validate against Commodore behaviour** – Replay extracted macro and flag payloads through the renderer, comparing screen dumps to C64 captures to confirm glyph fidelity, PETSCII control handling, and palette parity before wiring the console into the broader state machine.【F:docs/porting/iteration-08.md†L12-L18】
