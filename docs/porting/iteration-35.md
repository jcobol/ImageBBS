# Iteration 35 – Ampersand and service hook backlog

## Goals
- [x] Review the design decision that keeps the port moddable with customization hooks.【F:docs/porting/design-decisions.md†L5-L5】
- [x] Audit existing documentation of ampersand and service hooks to inventory extension points the host runtime must expose.【F:docs/porting/iteration-06.md†L9-L16】【F:docs/porting/iteration-08.md†L21-L34】
- [x] Draft a plan for reproducing or extending those hooks in the host architecture, covering registration, lifecycle, and module integration.【F:docs/porting/iteration-08.md†L25-L34】【F:docs/porting/iteration-19.md†L9-L24】

## Findings
### Design decision review
- [x] The design decisions log explicitly requires the port to “remain moddable in the same spirit as the original Image BBS, including support for customization hooks,” confirming extensibility as a first-order requirement.【F:docs/porting/design-decisions.md†L5-L5】

### Documented ampersand & service extension points
- [x] **Ampersand dispatcher (`sub_cd00`)** – The machine-language wedge parses up to three byte arguments, routes the first to a routine selector table, and passes the remaining values through the 6502 index registers so overlays can call helpers like `chkflags` via statements such as `&,52,13,3`.【F:docs/porting/iteration-06.md†L9-L16】【F:v1.2/core/im.txt†L66-L112】
- [x] **Argument parsing & interpreter loop** – `sub_cc02` and the patched `IGONE` vector reuse ROM helpers to evaluate BASIC expressions, cache register values, and walk every `&` token on a line, letting overlays chain multiple machine invocations without losing interpreter state.【F:docs/porting/iteration-07.md†L9-L17】
- [x] **Host abstraction & service registry concept** – The host architecture plan partitions Commodore device, DOS, overlay, modem, and console services while proposing a shared registry keyed by ampersand opcode numbers so modern modules can implement those routines behind a dispatcher.【F:docs/porting/iteration-08.md†L12-L29】
- [x] **Overlay-driven hooks** – The recovered `setup` and `ml.extra` overlays reintroduce ampersand verbs (notably `&,52`) alongside REL configuration loaders for chat banners, paging state, and lightbar handlers, underscoring the hook points the host runtime must surface.【F:docs/porting/iteration-19.md†L9-L24】【F:v1.2/source/setup.bas†L534-L610】
- [x] **Flag/macro directory** – Disassembly of `ml.extra` captures a 12-entry flag dispatcher that maps ampersand flag indices to macro routines and PETSCII payloads, providing concrete data the host must expose for customization metadata and diagnostics.【F:docs/porting/iteration-23.md†L99-L139】
- [x] **BASIC integration sites** – The bulletin-board subsystems rely on ampersand verbs (e.g., `&,52`, `&,8`) to enter machine-language editors and device helpers, highlighting the coupling between user modules and service hooks that the port must replicate.【F:v1.2/core/im.txt†L60-L134】

### Service registry bootstrap
- [x] The prototype device context now registers the console renderer as a named service and surfaces its recovered palette, cursor, and glyph helpers so host-side BASIC modules can discover the metadata through the shared registry.【F:scripts/prototypes/device_context.py†L141-L213】【F:scripts/prototypes/device_context.py†L452-L476】
- [x] Ampersand default handlers receive the shared service map and stream PETSCII macros through the console service, exposing both renderer state and rendered text to callers without bespoke wiring.【F:scripts/prototypes/ampersand_registry.py†L19-L102】【F:scripts/prototypes/ampersand_registry.py†L118-L149】

## Plan
- [ ] **Ampersand dispatcher façade** – Implement a dispatcher that mirrors `sub_cd00`: accept a routine number plus two byte arguments, resolve handlers through a registry keyed by Image opcode numbers, and back the parser with a BASIC-compatible expression evaluator so chained `&` calls preserve interpreter semantics.【F:docs/porting/iteration-06.md†L9-L16】【F:docs/porting/iteration-07.md†L9-L17】
- [ ] **Service registry & registration API** – Create host-level registration functions for device contexts, DOS helpers, overlay loading, modem services, and console rendering so built-ins and extensions can advertise ampersand handlers, metadata, and dependencies via the shared service layer concept.【F:docs/porting/iteration-08.md†L12-L29】
- [ ] **Lifecycle management for overlays and macros** – Model overlay loading/unloading events so modules can register flag handlers, rehydrate chat/banner state, and publish slot metadata aligned with the recovered `setup` and `ml.extra` artefacts.【F:docs/porting/iteration-19.md†L9-L24】【F:docs/porting/iteration-23.md†L99-L139】
- [ ] **User module integration** – Provide integration points for ported BASIC modules to request ampersand services, DOS helpers, and modem/console façades while preserving the menu-driven control flow observed in `im`.【F:docs/porting/iteration-08.md†L21-L34】【F:v1.2/core/im.txt†L60-L134】
- [ ] **Customization tooling support** – Expose inspection utilities that mirror the existing `ml_extra_defaults` and sanity-report flows so administrators can audit registered hooks, validate payload alignment, and package custom modules confidently.【F:docs/porting/iteration-23.md†L99-L139】【F:docs/porting/iteration-32.md†L4-L19】
