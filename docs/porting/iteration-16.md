# Iteration 16 – Normalising prime-time defaults

## Goals
- Bring the `setup` stub's `e.data` placeholder in line with the manual's
  description of record 20 as a three-number tuple describing the prime-time
  flag and window.
- Ensure the host-side defaults helper exposes the same semantics so Python
  prototypes can determine whether prime-time restrictions apply without
  reinterpreting BASIC state.

## `setup` Stub Updates
- Record 20 in `e.data` is now represented as three numbers—prime-time
  indicator,
  start hour, and end hour—matching the sysop manual's description instead of
  reusing the runtime `pt%` flag. The stub still clears `pt%` so the dispatcher
  can populate it at runtime while keeping the persisted configuration in
  `p1%`–`p3%`.【F:v1.2/core/setup.stub.txt†L40-L50】【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L6989-L7004】

## Host Defaults Helper
- `PrimeTimeWindow` now records the stored indicator and start/end
  hours and exposes an `is_enabled` convenience property, reflecting the
  triad stored in `e.data` record 20.【F:scripts/prototypes/setup_defaults.py†L90-L103】
- The stubbed defaults build a `PrimeTimeWindow` with zeroed minutes and hours,
  keeping the helper aligned with the BASIC stub's placeholder state.【F:scripts/prototypes/setup_defaults.py†L148-L188】

## Follow-ups
- Once an authentic `e.data` dump is available, confirm whether the first field
  represents a raw minute allotment or simply a boolean flag so the helper can
  offer derived durations alongside the stored hours.
