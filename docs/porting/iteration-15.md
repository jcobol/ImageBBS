# Iteration 15 – Summarising drive metadata for host tooling

## Goals
- Keep the BASIC `setup` placeholder aligned with the sysop manual's description
  of six drive slots that default to four active devices on a fresh install.
- Provide host-side helpers that expose the same derived drive inventory the
  BASIC stub synthesises when `bd.data` omits the highest-device and drive
  counts.

## `setup` Stub Updates
- The Stage 2 `DATA` block now mirrors the manual's "new install" layout by
  leaving the final two device/drive tuples at zero, matching the unused slots
  that a stock configuration leaves unassigned while still staging the first
  four drives for the system overlays.【F:v1.2/core/setup.stub.txt†L21-L33】

## Host Defaults Helper
- Introduced a `DriveLocator` protocol alongside the `CommodoreDeviceDrive`,
  `DeviceDriveMap`, and `DriveInventory` dataclasses plus a
  `derive_drive_inventory` helper so prototypes can inspect how the stubbed drive
  tuples roll up into highest-device, physical-device, and logical-unit counts
  without reimplementing the BASIC loops, while leaving room to swap in modern
  locator schemes later.【F:scripts/prototypes/setup_defaults.py†L14-L116】【F:scripts/prototypes/setup_defaults.py†L133-L166】
- `SetupDefaults.stub()` now surfaces the derived inventory alongside the
  locator-backed drive assignments and exposes an `active_drives` view that
  filters out the zeroed placeholders, keeping Python experiments in sync with
  the stubbed metadata.【F:scripts/prototypes/setup_defaults.py†L118-L166】
- Re-exported the new helpers from the prototypes package so downstream tooling
  can import them through the shared namespace.【F:scripts/prototypes/__init__.py†L1-L44】

## Follow-ups
- Once an authentic `bd.data` file is recovered, compare its multi-drive and
  Lt. Kernal configurations against the derived inventory to confirm how logical
  units beyond the first six slots should be represented.
